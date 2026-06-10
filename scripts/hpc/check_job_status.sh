#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 SLURM_JOB_ID" >&2
  exit 2
fi

SLURM_JOB_ID="$1"
HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_KEY_PATH="${HPC_SSH_KEY_PATH:-${HPC_KEY:-}}"
HPC_STRICT_HOST_KEY_CHECKING="${HPC_STRICT_HOST_KEY_CHECKING:-true}"
HPC_SSH_CONTROL_PATH="${HPC_SSH_CONTROL_PATH:-}"

if [ -z "$HPC_USERNAME" ]; then
  echo "Missing HPC_USERNAME. Password automation is not supported." >&2
  exit 2
fi

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

REMOTE="${HPC_USERNAME}@${HPC_HOST}"
ssh "${ssh_opts[@]}" "$REMOTE" "source /etc/profile >/dev/null 2>&1 || true; squeue -j '$SLURM_JOB_ID' || sacct -j '$SLURM_JOB_ID' --format=JobID,State,Elapsed,ExitCode"
