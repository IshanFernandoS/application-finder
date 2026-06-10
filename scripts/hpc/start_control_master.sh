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
    "HPC_SSH_KEY_PATH": str(settings.hpc_ssh_key_path or ""),
    "HPC_STRICT_HOST_KEY_CHECKING": "true" if settings.hpc_strict_host_key_checking else "false",
    "HPC_SSH_CONTROL_PATH": settings.hpc_ssh_control_path or os.path.expanduser("~/.ssh/application-finder-hpc-%r@%h:%p.sock"),
}
for key, value in values.items():
    print(f"{key}={shlex.quote(value)}")
PY
)"

if [ -z "$HPC_USERNAME" ]; then
  echo "Missing HPC_USERNAME. Password automation is not supported." >&2
  exit 2
fi

strict="yes"
if [ "$HPC_STRICT_HOST_KEY_CHECKING" = "false" ]; then
  strict="no"
fi

REMOTE="${HPC_USERNAME}@${HPC_HOST}"
mkdir -p "$(dirname "${HPC_SSH_CONTROL_PATH//%r/$HPC_USERNAME}")"
ssh_key_args=()
if [ -n "$HPC_SSH_KEY_PATH" ]; then
  ssh_key_args=(-i "$HPC_SSH_KEY_PATH")
fi

echo "Starting an SSH control master for the configured HPC account."
echo "If prompted, enter the HPC password interactively. It is not stored by Application Finder."
ssh -A -M -N -f \
  -o "ControlMaster=yes" \
  -o "ControlPersist=8h" \
  -o "ControlPath=${HPC_SSH_CONTROL_PATH}" \
  -o "StrictHostKeyChecking=${strict}" \
  "${ssh_key_args[@]}" \
  "$REMOTE"

ssh -A \
  -o BatchMode=yes \
  -o "ControlMaster=auto" \
  -o "ControlPath=${HPC_SSH_CONTROL_PATH}" \
  -o "StrictHostKeyChecking=${strict}" \
  "$REMOTE" "printf ok"
echo
echo "HPC SSH control master is ready."
