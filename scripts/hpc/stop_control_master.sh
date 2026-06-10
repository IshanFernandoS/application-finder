#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

eval "$("$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
import os
import shlex
import sys

root = sys.argv[1]
sys.path.insert(0, root)
from backend.app.config import settings  # noqa: E402

values = {
    "HPC_HOST": settings.hpc_host or "",
    "HPC_USERNAME": settings.hpc_username or "",
    "HPC_SSH_CONTROL_PATH": settings.hpc_ssh_control_path or os.path.expanduser("~/.ssh/application-finder-hpc-%r@%h:%p.sock"),
}
for key, value in values.items():
    print(f"{key}={shlex.quote(value)}")
PY
)"

if [ -z "$HPC_USERNAME" ]; then
  echo "Missing HPC_USERNAME." >&2
  exit 2
fi

ssh -O exit \
  -o "ControlPath=${HPC_SSH_CONTROL_PATH}" \
  "${HPC_USERNAME}@${HPC_HOST}" 2>/dev/null || true
echo "HPC SSH control master stopped if it was running."
