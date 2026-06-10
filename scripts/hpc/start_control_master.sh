#!/usr/bin/env bash
set -euo pipefail

HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_KEY_PATH="${HPC_SSH_KEY_PATH:-${HPC_KEY:-$HOME/.ssh/id_ed25519}}"
HPC_STRICT_HOST_KEY_CHECKING="${HPC_STRICT_HOST_KEY_CHECKING:-true}"
HPC_SSH_CONTROL_PATH="${HPC_SSH_CONTROL_PATH:-$HOME/.ssh/application-finder-hpc-%r@%h:%p.sock}"

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

echo "Starting an SSH control master for ${REMOTE}."
echo "If prompted, enter the HPC password interactively. It is not stored by Application Finder."
ssh -A -M -N -f \
  -o "ControlMaster=yes" \
  -o "ControlPersist=8h" \
  -o "ControlPath=${HPC_SSH_CONTROL_PATH}" \
  -o "StrictHostKeyChecking=${strict}" \
  -i "$HPC_SSH_KEY_PATH" \
  "$REMOTE"

ssh -A \
  -o BatchMode=yes \
  -o "ControlMaster=auto" \
  -o "ControlPath=${HPC_SSH_CONTROL_PATH}" \
  -o "StrictHostKeyChecking=${strict}" \
  "$REMOTE" "printf ok"
echo
echo "HPC SSH control master is ready."
