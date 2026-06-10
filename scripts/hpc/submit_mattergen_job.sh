#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ] || [ "${2:-}" = "" ]; then
  echo "Usage: $0 PATHWAY_ID constraints.json" >&2
  exit 2
fi

PATHWAY_ID="$1"
CONSTRAINTS_JSON="$2"

HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_KEY_PATH="${HPC_SSH_KEY_PATH:-${HPC_KEY:-}}"
HPC_WORKDIR="${HPC_WORKDIR:-${HPC_PROJECT_DIR:-}}"
HPC_SLURM_PARTITION="${HPC_SLURM_PARTITION:-${HPC_PARTITION:-}}"
HPC_SLURM_ACCOUNT="${HPC_SLURM_ACCOUNT:-}"
HPC_GPU_REQUEST="${HPC_GPU_REQUEST:-${HPC_GPUS:+gpu:${HPC_GPUS}}}"
HPC_TIME_LIMIT="${HPC_TIME_LIMIT:-${HPC_TIME:-04:00:00}}"
HPC_CPUS_PER_TASK="${HPC_CPUS_PER_TASK:-${HPC_CPUS:-8}}"
HPC_MEM="${HPC_MEM:-32G}"
HPC_PYTHON_MODULE="${HPC_PYTHON_MODULE:-}"
HPC_MATTERGEN_ENV="${HPC_MATTERGEN_ENV:-}"
HPC_RSYNC_EXTRA_ARGS="${HPC_RSYNC_EXTRA_ARGS:-}"
HPC_STRICT_HOST_KEY_CHECKING="${HPC_STRICT_HOST_KEY_CHECKING:-true}"
HPC_SSH_CONTROL_PATH="${HPC_SSH_CONTROL_PATH:-}"

if [ -z "$HPC_USERNAME" ] || [ -z "$HPC_WORKDIR" ]; then
  echo "Missing HPC_USERNAME or HPC_WORKDIR. Password automation is not supported." >&2
  exit 2
fi

if [ ! -f "$CONSTRAINTS_JSON" ]; then
  echo "Constraints file not found." >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

JOB_ID="mg_${PATHWAY_ID}_$(date -u +%Y%m%dT%H%M%SZ)"
LOCAL_JOB_DIR="outputs/hpc_jobs/${JOB_ID}"
REMOTE="${HPC_USERNAME}@${HPC_HOST}"
REMOTE_JOB_DIR="${HPC_WORKDIR%/}/jobs/${JOB_ID}"
mkdir -p "$LOCAL_JOB_DIR"
cp "$CONSTRAINTS_JSON" "$LOCAL_JOB_DIR/input.json"

strict="yes"
if [ "$HPC_STRICT_HOST_KEY_CHECKING" = "false" ]; then
  strict="no"
fi

ssh_opts=(-A -o BatchMode=yes -o "StrictHostKeyChecking=${strict}")
if [ -n "$HPC_SSH_CONTROL_PATH" ]; then
  ssh_opts+=(-o ControlMaster=auto -o ControlPersist=10m -o "ControlPath=${HPC_SSH_CONTROL_PATH}")
fi
if [ -n "$HPC_SSH_KEY_PATH" ]; then
  ssh_opts+=(-i "$HPC_SSH_KEY_PATH")
fi

{
  echo '#!/usr/bin/env bash'
  echo "#SBATCH --job-name=af_${JOB_ID:0:20}"
  echo "#SBATCH --output=${REMOTE_JOB_DIR}/logs/slurm-%j.out"
  echo "#SBATCH --error=${REMOTE_JOB_DIR}/logs/slurm-%j.err"
  echo "#SBATCH --time=${HPC_TIME_LIMIT}"
  echo "#SBATCH --cpus-per-task=${HPC_CPUS_PER_TASK}"
  echo "#SBATCH --mem=${HPC_MEM}"
  [ -n "$HPC_SLURM_PARTITION" ] && echo "#SBATCH --partition=${HPC_SLURM_PARTITION}"
  [ -n "$HPC_SLURM_ACCOUNT" ] && echo "#SBATCH --account=${HPC_SLURM_ACCOUNT}"
  [ -n "$HPC_GPU_REQUEST" ] && echo "#SBATCH --gres=${HPC_GPU_REQUEST}"
  cat <<'SLURM'

source /etc/profile >/dev/null 2>&1 || true
set -euo pipefail
export INPUT_JSON="$PWD/input.json"
export OUTPUT_DIR="$PWD/outputs"
mkdir -p "$OUTPUT_DIR" logs
SLURM
  [ -n "$HPC_PYTHON_MODULE" ] && echo "module load $(printf '%q' "$HPC_PYTHON_MODULE")"
  [ -n "$HPC_MATTERGEN_ENV" ] && echo "$HPC_MATTERGEN_ENV"
  cat <<'SLURM'
python - <<'PY'
import json
import re
import subprocess
from pathlib import Path

payload = json.loads(Path("input.json").read_text())
compatible = payload.get("compatible_constraints", payload.get("constraint_set", {}).get("compatible_constraints", payload))
out_dir = Path("outputs")
out_dir.mkdir(parents=True, exist_ok=True)

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
energy_above_hull = number_or_none(compatible.get("energy_above_hull") or compatible.get("stability_or_formation_energy"))
band_gap = number_or_none(compatible.get("band_gap"))
magnetic_density = number_or_none(compatible.get("magnetic_density"))
bulk_modulus = number_or_none(compatible.get("bulk_modulus"))
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
    str(out_dir),
    f"--pretrained-name={model_name}",
    "--batch_size=8",
    "--num_batches=1",
    "--record_trajectories=False",
]
if props:
    cmd.append("--properties_to_condition_on=" + repr(props))
    cmd.append("--diffusion_guidance_factor=2.0")
(out_dir / "application_finder_mattergen_request.json").write_text(json.dumps({"model_name": model_name, "properties": props, "command": cmd}, indent=2))
subprocess.run(cmd, check=True)
PY
SLURM
} > "$LOCAL_JOB_DIR/job.slurm"

ssh "${ssh_opts[@]}" "$REMOTE" "mkdir -p '$REMOTE_JOB_DIR' '$REMOTE_JOB_DIR/logs' '$REMOTE_JOB_DIR/outputs'"
rsync -az ${HPC_RSYNC_EXTRA_ARGS} -e "ssh ${ssh_opts[*]}" "$LOCAL_JOB_DIR/" "$REMOTE:$REMOTE_JOB_DIR/"
ssh "${ssh_opts[@]}" "$REMOTE" "source /etc/profile >/dev/null 2>&1 || true; cd '$REMOTE_JOB_DIR' && sbatch job.slurm"
echo "Submitted Application Finder MatterGen HPC job: ${JOB_ID}"
