#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 HPC_JOB_ID" >&2
  exit 2
fi

JOB_ID="$1"
HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_KEY_PATH="${HPC_SSH_KEY_PATH:-${HPC_KEY:-}}"
HPC_WORKDIR="${HPC_WORKDIR:-${HPC_PROJECT_DIR:-}}"
HPC_RSYNC_EXTRA_ARGS="${HPC_RSYNC_EXTRA_ARGS:-}"
HPC_STRICT_HOST_KEY_CHECKING="${HPC_STRICT_HOST_KEY_CHECKING:-true}"

if [ -z "$HPC_USERNAME" ] || [ -z "$HPC_WORKDIR" ]; then
  echo "Missing HPC_USERNAME or HPC_WORKDIR. Password automation is not supported." >&2
  exit 2
fi

strict="yes"
if [ "$HPC_STRICT_HOST_KEY_CHECKING" = "false" ]; then
  strict="no"
fi

ssh_opts=(-A -o BatchMode=yes -o "StrictHostKeyChecking=${strict}")
if [ -n "$HPC_SSH_KEY_PATH" ]; then
  ssh_opts+=(-i "$HPC_SSH_KEY_PATH")
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

REMOTE="${HPC_USERNAME}@${HPC_HOST}"
REMOTE_JOB_DIR="${HPC_WORKDIR%/}/jobs/${JOB_ID}"
LOCAL_JOB_DIR="outputs/hpc_jobs/${JOB_ID}"
mkdir -p "$LOCAL_JOB_DIR"
rsync -az ${HPC_RSYNC_EXTRA_ARGS} -e "ssh ${ssh_opts[*]}" "$REMOTE:$REMOTE_JOB_DIR/" "$LOCAL_JOB_DIR/"
echo "Retrieved Application Finder HPC outputs into outputs/hpc_jobs/${JOB_ID}/"
