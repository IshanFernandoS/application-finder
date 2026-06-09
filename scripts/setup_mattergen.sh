#!/usr/bin/env bash
set -euo pipefail

MATTERGEN_PATH="${MATTERGEN_PATH:-tools/mattergen}"

echo "MatterGen setup helper"
echo "Target path: ${MATTERGEN_PATH}"
echo "This script does not download private checkpoints or bypass licenses."

if [ ! -d "${MATTERGEN_PATH}" ]; then
  mkdir -p "${MATTERGEN_PATH}"
  echo "Created ${MATTERGEN_PATH}. Clone or install MatterGen there according to its upstream instructions."
fi

python - <<'PY'
import importlib.util
import platform

print("Python:", platform.python_version())
print("mattergen importable:", importlib.util.find_spec("mattergen") is not None)
try:
    import torch
    print("CUDA available:", torch.cuda.is_available())
except Exception as exc:
    print("torch/CUDA check unavailable:", exc)
PY
