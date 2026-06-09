from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from ..config import settings
from ..exceptions import ConfigurationError, DependencyUnavailableError
from ..schemas import HPCCheckResult, HPCJob, HPCJobStatus, HPCJobType


class HPCSlurmService:
    def require_configured(self) -> None:
        if not settings.hpc_enabled:
            raise ConfigurationError("HPC worker is disabled. Set HPC_ENABLED=true to enable SSH/Slurm automation.")
        if settings.hpc_mode != "slurm_ssh":
            raise ConfigurationError(f"Unsupported HPC_MODE: {settings.hpc_mode}")
        missing = []
        if not settings.hpc_host:
            missing.append("HPC_HOST")
        if not settings.hpc_username:
            missing.append("HPC_USERNAME")
        if not settings.hpc_workdir:
            missing.append("HPC_WORKDIR")
        if missing:
            raise ConfigurationError(f"Missing HPC configuration: {', '.join(missing)}")

    def check_connection(self) -> HPCCheckResult:
        self.require_configured()
        result = self._run_ssh("printf 'ok'", timeout=20)
        ok = result.returncode == 0 and result.stdout.strip() == "ok"
        return HPCCheckResult(
            ok=ok,
            status="available" if ok else "unavailable",
            message="HPC SSH connection succeeded." if ok else "HPC SSH connection failed.",
            details=self._safe_details(result),
        )

    def check_slurm(self) -> HPCCheckResult:
        self.require_configured()
        command = "command -v sbatch >/dev/null && command -v squeue >/dev/null && command -v sacct >/dev/null"
        result = self._run_ssh(command, timeout=20)
        ok = result.returncode == 0
        return HPCCheckResult(
            ok=ok,
            status="available" if ok else "unavailable",
            message="Slurm commands are available." if ok else "Slurm commands were not found on the remote PATH.",
            details=self._safe_details(result),
        )

    def check_mattergen(self) -> HPCCheckResult:
        self.require_configured()
        env_block = self._remote_env_block()
        command = f"""{env_block}
python - <<'PY'
import importlib.util
import json
try:
    import torch
    cuda = bool(torch.cuda.is_available())
except Exception:
    cuda = False
spec = importlib.util.find_spec("mattergen")
print(json.dumps({{"mattergen_importable": spec is not None, "cuda_available": cuda}}))
PY"""
        result = self._run_ssh(command, timeout=45)
        ok = result.returncode == 0 and "mattergen_importable" in result.stdout
        return HPCCheckResult(
            ok=ok,
            status="available" if ok else "unavailable",
            message="MatterGen environment check completed." if ok else "MatterGen environment check failed.",
            details=[self._sanitize(line) for line in [result.stdout.strip(), result.stderr.strip()] if line],
        )

    def submit(self, job: HPCJob, local_workdir: Path, input_json: Path, slurm_script: Path) -> HPCJob:
        self.require_configured()
        remote_job_dir = self.remote_job_dir(job.job_id)
        self._run_ssh(f"mkdir -p {shlex.quote(remote_job_dir)} {shlex.quote(remote_job_dir + '/outputs')} {shlex.quote(remote_job_dir + '/logs')}", timeout=30, check=True)
        self._rsync_to(local_workdir, remote_job_dir)
        result = self._run_ssh(f"cd {shlex.quote(remote_job_dir)} && sbatch {shlex.quote(slurm_script.name)}", timeout=30, check=True)
        match = re.search(r"Submitted batch job\s+(\d+)", result.stdout)
        if not match:
            raise DependencyUnavailableError("Slurm submission did not return a job id.")
        job.slurm_job_id = match.group(1)
        job.remote_workdir = remote_job_dir
        job.input_ref = f"{remote_job_dir}/{input_json.name}"
        job.status = HPCJobStatus.submitted
        return job

    def poll(self, job: HPCJob) -> HPCJob:
        self.require_configured()
        if not job.slurm_job_id:
            job.status = HPCJobStatus.unknown
            return job
        squeue_cmd = f"squeue -h -j {shlex.quote(job.slurm_job_id)} -o '%T' | head -n 1"
        squeue = self._run_ssh(squeue_cmd, timeout=20)
        state = squeue.stdout.strip().splitlines()[0].strip() if squeue.stdout.strip() else ""
        if not state:
            sacct_cmd = f"sacct -n -j {shlex.quote(job.slurm_job_id)} --format=State -P | head -n 1"
            sacct = self._run_ssh(sacct_cmd, timeout=20)
            state = sacct.stdout.strip().split("|")[0].strip() if sacct.stdout.strip() else ""
        job.status = self.map_slurm_state(state)
        job.metadata["scheduler_state"] = state or "unknown"
        return job

    def retrieve(self, job: HPCJob, local_workdir: Path) -> HPCJob:
        self.require_configured()
        if not job.remote_workdir:
            job.remote_workdir = self.remote_job_dir(job.job_id)
        local_workdir.mkdir(parents=True, exist_ok=True)
        self._rsync_from(f"{job.remote_workdir}/", local_workdir)
        output_dir = local_workdir / "outputs"
        log_dir = local_workdir / "logs"
        job.output_files = [
            str(path.relative_to(local_workdir))
            for path in sorted(local_workdir.glob("**/*"))
            if path.is_file() and ".slurm" not in path.name
        ]
        job.log_excerpt = self._log_excerpt(log_dir)
        job.output_ref = str(output_dir)
        job.status = HPCJobStatus.output_retrieved
        return job

    def cancel(self, job: HPCJob) -> HPCJob:
        self.require_configured()
        if not job.slurm_job_id:
            raise ConfigurationError("Cannot cancel an HPC job before a Slurm job id exists.")
        self._run_ssh(f"scancel {shlex.quote(job.slurm_job_id)}", timeout=20, check=True)
        job.status = HPCJobStatus.cancelled
        return job

    def render_slurm_script(self, job: HPCJob) -> str:
        remote_job_dir = self.remote_job_dir(job.job_id)
        output_dir = f"{remote_job_dir}/outputs"
        log_dir = f"{remote_job_dir}/logs"
        lines = [
            "#!/usr/bin/env bash",
            f"#SBATCH --job-name=af_{job.job_type.value[:10]}_{job.job_id[-6:]}",
            f"#SBATCH --output={log_dir}/slurm-%j.out",
            f"#SBATCH --error={log_dir}/slurm-%j.err",
            f"#SBATCH --time={settings.hpc_time_limit}",
            f"#SBATCH --cpus-per-task={settings.hpc_cpus_per_task}",
            f"#SBATCH --mem={settings.hpc_mem}",
        ]
        if settings.hpc_slurm_partition:
            lines.append(f"#SBATCH --partition={settings.hpc_slurm_partition}")
        if settings.hpc_slurm_account:
            lines.append(f"#SBATCH --account={settings.hpc_slurm_account}")
        if settings.hpc_gpu_request:
            lines.append(f"#SBATCH --gres={settings.hpc_gpu_request}")
        lines.extend(
            [
                "",
                "set -euo pipefail",
                f"export INPUT_JSON={shlex.quote(remote_job_dir + '/input.json')}",
                f"export OUTPUT_DIR={shlex.quote(output_dir)}",
                f"export LOG_DIR={shlex.quote(log_dir)}",
                'mkdir -p "$OUTPUT_DIR" "$LOG_DIR"',
                self._remote_env_block(),
                self._job_body(job.job_type),
            ]
        )
        return "\n".join(line for line in lines if line is not None) + "\n"

    def remote_job_dir(self, job_id: str) -> str:
        return f"{(settings.hpc_workdir or '').rstrip('/')}/jobs/{job_id}"

    def map_slurm_state(self, state: str) -> HPCJobStatus:
        normalized = state.upper().split()[0] if state else ""
        if normalized in {"PENDING", "CONFIGURING", "REQUEUED"}:
            return HPCJobStatus.queued
        if normalized in {"RUNNING", "COMPLETING", "SUSPENDED"}:
            return HPCJobStatus.running
        if normalized in {"COMPLETED"}:
            return HPCJobStatus.completed
        if normalized in {"CANCELLED", "CANCELLED+"}:
            return HPCJobStatus.cancelled
        if normalized in {"FAILED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}:
            return HPCJobStatus.failed
        return HPCJobStatus.unknown

    def _ssh_base(self) -> List[str]:
        strict = "yes" if settings.hpc_strict_host_key_checking else "no"
        cmd = ["ssh", "-A", "-o", "BatchMode=yes", "-o", f"StrictHostKeyChecking={strict}"]
        if settings.hpc_ssh_key_path:
            cmd.extend(["-i", str(settings.hpc_ssh_key_path)])
        cmd.append(self._target())
        return cmd

    def _target(self) -> str:
        return f"{settings.hpc_username}@{settings.hpc_host}"

    def _run_ssh(self, remote_command: str, timeout: int = 60, check: bool = False) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [*self._ssh_base(), remote_command],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if check and result.returncode != 0:
            raise DependencyUnavailableError("HPC SSH/Slurm command failed: " + "; ".join(self._safe_details(result)))
        return result

    def _rsync_to(self, local_dir: Path, remote_dir: str) -> None:
        local = str(local_dir).rstrip("/") + "/"
        remote = f"{self._target()}:{remote_dir.rstrip('/')}/"
        self._run_rsync(local, remote)

    def _rsync_from(self, remote_dir: str, local_dir: Path) -> None:
        local_dir.mkdir(parents=True, exist_ok=True)
        remote = f"{self._target()}:{remote_dir.rstrip('/')}/"
        self._run_rsync(remote, str(local_dir).rstrip("/") + "/")

    def _run_rsync(self, source: str, dest: str) -> None:
        strict = "yes" if settings.hpc_strict_host_key_checking else "no"
        ssh_parts = ["ssh", "-A", "-o", "BatchMode=yes", "-o", f"StrictHostKeyChecking={strict}"]
        if settings.hpc_ssh_key_path:
            ssh_parts.extend(["-i", str(settings.hpc_ssh_key_path)])
        extra_args = shlex.split(settings.hpc_rsync_extra_args)
        result = subprocess.run(
            ["rsync", "-az", *extra_args, "-e", " ".join(shlex.quote(part) for part in ssh_parts), source, dest],
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            raise DependencyUnavailableError("HPC file transfer failed: " + "; ".join(self._safe_details(result)))

    def _remote_env_block(self) -> str:
        lines = []
        if settings.hpc_python_module:
            lines.append(f"module load {shlex.quote(settings.hpc_python_module)}")
        if settings.hpc_mattergen_env:
            lines.append(settings.hpc_mattergen_env)
        return "\n".join(lines)

    def _job_body(self, job_type: HPCJobType) -> str:
        if job_type == HPCJobType.mattergen_generation:
            return _MATTERGEN_GENERATION_BODY
        if job_type == HPCJobType.mattergen_validation:
            return _PLACEHOLDER_BODY.replace("__LABEL__", "mattergen_validation")
        if job_type == HPCJobType.large_embedding_index_build:
            return _PLACEHOLDER_BODY.replace("__LABEL__", "large_embedding_index_build")
        if job_type == HPCJobType.bulk_pdf_processing:
            return _PLACEHOLDER_BODY.replace("__LABEL__", "bulk_pdf_processing")
        if job_type == HPCJobType.dft_validation_placeholder:
            return _PLACEHOLDER_BODY.replace("__LABEL__", "dft_validation_placeholder")
        if job_type == HPCJobType.em_simulation_placeholder:
            return _PLACEHOLDER_BODY.replace("__LABEL__", "em_simulation_placeholder")
        return _PLACEHOLDER_BODY.replace("__LABEL__", "custom_user_job_placeholder")

    def _safe_details(self, result: subprocess.CompletedProcess[str]) -> List[str]:
        details = []
        if result.stdout.strip():
            details.append(self._sanitize(result.stdout.strip()[-1200:]))
        if result.stderr.strip():
            details.append(self._sanitize(result.stderr.strip()[-1200:]))
        if not details:
            details.append(f"exit_code={result.returncode}")
        return details

    def _log_excerpt(self, log_dir: Path) -> str:
        chunks = []
        if log_dir.exists():
            for path in sorted(log_dir.glob("*"))[-4:]:
                if path.is_file():
                    chunks.append(f"== {path.name} ==\n{path.read_text(encoding='utf-8', errors='ignore')[-2500:]}")
        return self._sanitize("\n\n".join(chunks)[-6000:])

    def _sanitize(self, text: str) -> str:
        sanitized = text
        replacements = []
        if settings.hpc_ssh_key_path:
            replacements.append((str(settings.hpc_ssh_key_path), "[ssh-key-path]"))
        if settings.hpc_workdir:
            replacements.append((settings.hpc_workdir, "[hpc-workdir]"))
        if settings.hpc_host and settings.hpc_username:
            replacements.append((self._target(), "[hpc-target]"))
        if settings.hpc_host:
            replacements.append((settings.hpc_host, "[hpc-host]"))
        if settings.hpc_username:
            replacements.append((settings.hpc_username, "[hpc-user]"))
        for raw, replacement in replacements:
            if raw:
                sanitized = sanitized.replace(raw, replacement)
        return sanitized


_PLACEHOLDER_BODY = r"""python - <<'PY'
import json
import os
from pathlib import Path

input_path = Path(os.environ["INPUT_JSON"])
output_dir = Path(os.environ["OUTPUT_DIR"])
payload = json.loads(input_path.read_text())
summary = {
    "job_id": payload.get("job_id"),
    "job_type": "__LABEL__",
    "status": "placeholder_completed",
    "note": "This Application Finder HPC job type is wired through Slurm and ready for a concrete scientific workflow implementation.",
}
(output_dir / "application_finder_hpc_summary.json").write_text(json.dumps(summary, indent=2))
PY"""


_MATTERGEN_GENERATION_BODY = r"""python - <<'PY'
import json
import os
import re
import subprocess
from pathlib import Path

input_path = Path(os.environ["INPUT_JSON"])
output_dir = Path(os.environ["OUTPUT_DIR"])
payload = json.loads(input_path.read_text())
constraint_set = payload.get("constraint_set") or {}
compatible = constraint_set.get("compatible_constraints") or {}
output_dir.mkdir(parents=True, exist_ok=True)

def number_or_none(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            return float(match.group(0))
    return None

props = {}
model_name = "mattergen_base"
chemical_system = compatible.get("chemical_system")
if not chemical_system and isinstance(compatible.get("include_elements"), list):
    elements = [str(item) for item in compatible["include_elements"] if str(item).isalpha()]
    if 2 <= len(elements) <= 4:
        chemical_system = "-".join(elements)

band_gap = number_or_none(compatible.get("band_gap"))
magnetic_density = number_or_none(compatible.get("magnetic_density"))
bulk_modulus = number_or_none(compatible.get("bulk_modulus"))
energy_above_hull = number_or_none(compatible.get("energy_above_hull") or compatible.get("stability_or_formation_energy"))

if chemical_system and energy_above_hull is not None:
    model_name = "chemical_system_energy_above_hull"
    props = {"chemical_system": chemical_system, "energy_above_hull": energy_above_hull}
elif chemical_system:
    model_name = "chemical_system"
    props = {"chemical_system": chemical_system}
elif magnetic_density is not None:
    model_name = "dft_mag_density"
    props = {"dft_mag_density": magnetic_density}
elif band_gap is not None:
    model_name = "dft_band_gap"
    props = {"dft_band_gap": band_gap}
elif bulk_modulus is not None:
    model_name = "ml_bulk_modulus"
    props = {"ml_bulk_modulus": bulk_modulus}

cmd = [
    "mattergen-generate",
    str(output_dir),
    f"--pretrained-name={model_name}",
    "--batch_size=8",
    "--num_batches=1",
    "--record_trajectories=False",
]
if props:
    cmd.append("--properties_to_condition_on=" + repr(props))
    cmd.append("--diffusion_guidance_factor=2.0")

summary = {
    "job_id": payload.get("job_id"),
    "pathway_id": payload.get("pathway_id"),
    "model_name": model_name,
    "conditioning_properties": props,
    "command": cmd,
}
(output_dir / "application_finder_mattergen_request.json").write_text(json.dumps(summary, indent=2))
subprocess.run(cmd, check=True)
files = sorted(str(path.relative_to(output_dir)) for path in output_dir.glob("**/*") if path.is_file())
summary["output_files"] = files
(output_dir / "application_finder_hpc_summary.json").write_text(json.dumps(summary, indent=2))
PY"""
