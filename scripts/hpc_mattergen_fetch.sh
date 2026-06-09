#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 PATHWAY_ID" >&2
  exit 2
fi

PATHWAY_ID="$1"
HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_KEY_PATH="${HPC_SSH_KEY_PATH:-${HPC_KEY:-}}"

if [ -z "$HPC_USERNAME" ]; then
  echo "Set HPC_USERNAME before fetching MatterGen outputs." >&2
  exit 2
fi

HPC_WORKDIR="${HPC_WORKDIR:-${HPC_PROJECT_DIR:-/data/scratch/${HPC_USERNAME}/gap2material-em}}"
REMOTE="${HPC_USERNAME}@${HPC_HOST}"

RSYNC_SSH="ssh -A -o BatchMode=yes"
if [ -n "$HPC_SSH_KEY_PATH" ]; then
  RSYNC_SSH="$RSYNC_SSH -i $(printf '%q' "$HPC_SSH_KEY_PATH")"
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p "outputs/mattergen/${PATHWAY_ID}"
rsync -az -e "$RSYNC_SSH" \
  "$REMOTE:$HPC_WORKDIR/outputs/$PATHWAY_ID/" \
  "outputs/mattergen/${PATHWAY_ID}/"

echo "Fetched HPC MatterGen outputs into outputs/mattergen/${PATHWAY_ID}/"
