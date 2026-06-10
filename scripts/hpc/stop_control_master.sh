#!/usr/bin/env bash
set -euo pipefail

HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_CONTROL_PATH="${HPC_SSH_CONTROL_PATH:-$HOME/.ssh/application-finder-hpc-%r@%h:%p.sock}"

if [ -z "$HPC_USERNAME" ]; then
  echo "Missing HPC_USERNAME." >&2
  exit 2
fi

ssh -O exit \
  -o "ControlPath=${HPC_SSH_CONTROL_PATH}" \
  "${HPC_USERNAME}@${HPC_HOST}" 2>/dev/null || true
echo "HPC SSH control master stopped if it was running."
