from __future__ import annotations

import importlib.util
import platform
import subprocess
from pathlib import Path

from ..config import settings
from ..schemas import MatterGenStatus


class MatterGenSetupService:
    def status(self) -> MatterGenStatus:
        path = settings.mattergen_path
        local_python = path / ".venv" / "bin" / "python"
        importable = importlib.util.find_spec("mattergen") is not None or self._local_env_importable(local_python)
        checkpoints_found = self._real_checkpoints_found(path)
        gpu_available = self._gpu_available()
        python_version = tuple(int(part) for part in platform.python_version_tuple()[:2])
        python_compatible = python_version >= (3, 10)
        worker_configured = bool(settings.mattergen_worker_url)
        details = []
        if not path.exists():
            details.append("MATTERGEN_PATH does not exist.")
        if not importable:
            details.append("The `mattergen` Python package is not importable in this environment.")
        if not checkpoints_found:
            details.append("No real MatterGen checkpoint files were found under MATTERGEN_PATH; Git LFS pointer files do not count.")
        if not gpu_available and not worker_configured:
            details.append("No local CUDA GPU was detected and no remote worker URL is configured.")
        if not python_compatible:
            details.append("MatterGen typically needs a Python 3.10+ environment; this runtime is older.")

        if worker_configured:
            status = "available" if settings.mattergen_api_key or settings.mattergen_worker_url else "setup_needed"
        elif not path.exists():
            status = "path_missing"
        elif not importable:
            status = "dependency_missing"
        elif not checkpoints_found:
            status = "installed_but_missing_checkpoints"
        elif not gpu_available:
            status = "gpu_unavailable"
        else:
            status = "available"
        return MatterGenStatus(
            status=status,
            mode=settings.mattergen_mode,
            path=str(path),
            importable=importable,
            checkpoints_found=checkpoints_found,
            gpu_available=gpu_available,
            worker_configured=worker_configured,
            python_compatible=python_compatible,
            details=details,
        )

    def _gpu_available(self) -> bool:
        try:
            import torch  # type: ignore

            return bool(torch.cuda.is_available())
        except Exception:
            return False

    def _local_env_importable(self, python_path: Path) -> bool:
        if not python_path.exists():
            return False
        try:
            result = subprocess.run(
                [str(python_path), "-c", "import mattergen"],
                cwd=str(settings.mattergen_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _real_checkpoints_found(self, path: Path) -> bool:
        if not path.exists():
            return False
        for checkpoint in path.glob("**/*.ckpt"):
            try:
                if checkpoint.stat().st_size < 1024:
                    text = checkpoint.read_text(encoding="utf-8", errors="ignore")
                    if "git-lfs.github.com/spec" in text:
                        continue
                return True
            except Exception:
                continue
        return False
