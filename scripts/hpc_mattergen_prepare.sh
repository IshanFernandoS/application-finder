#!/usr/bin/env bash
set -euo pipefail

HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_KEY_PATH="${HPC_SSH_KEY_PATH:-${HPC_KEY:-}}"

if [ -z "$HPC_USERNAME" ]; then
  echo "Set HPC_USERNAME before preparing the HPC workspace." >&2
  exit 2
fi

HPC_WORKDIR="${HPC_WORKDIR:-${HPC_PROJECT_DIR:-/data/scratch/${HPC_USERNAME}/gap2material-em}}"
REMOTE="${HPC_USERNAME}@${HPC_HOST}"

SSH_OPTS=(-A -o BatchMode=yes)
RSYNC_SSH="ssh -A -o BatchMode=yes"
if [ -n "$HPC_SSH_KEY_PATH" ]; then
  SSH_OPTS+=(-i "$HPC_SSH_KEY_PATH")
  RSYNC_SSH="$RSYNC_SSH -i $(printf '%q' "$HPC_SSH_KEY_PATH")"
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Preparing MatterGen on ${REMOTE}:${HPC_WORKDIR}"
echo "This script uses normal interactive SSH authentication. It does not store passwords or passcodes."

ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p '$HPC_WORKDIR' '$HPC_WORKDIR/jobs' '$HPC_WORKDIR/outputs'"

rsync -az --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'frontend/node_modules/' \
  --exclude 'frontend/.next/' \
  --exclude 'tools/mattergen/.git/' \
  --exclude 'tools/mattergen/.venv/' \
  --exclude 'outputs/' \
  -e "$RSYNC_SSH" \
  "$ROOT_DIR/" "$REMOTE:$HPC_WORKDIR/repo/"

ssh "${SSH_OPTS[@]}" "$REMOTE" "cat > '$HPC_WORKDIR/bootstrap_mattergen.sh' <<'REMOTE_SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=\"${PROJECT_DIR:-$HOME/gap2material-em}\"
cd \"$PROJECT_DIR/repo\"

if ! command -v git-lfs >/dev/null 2>&1; then
  echo \"git-lfs is not on PATH. Load/install Git LFS according to Apocrita module policy, then rerun.\"
  exit 2
fi

if [ ! -d tools/mattergen/.git ]; then
  git clone https://github.com/microsoft/mattergen.git tools/mattergen
else
  git -C tools/mattergen pull --ff-only
fi

git -C tools/mattergen lfs install --local
git -C tools/mattergen lfs pull

if ! command -v uv >/dev/null 2>&1; then
  python3 -m pip install --user uv
  export PATH=\"$HOME/.local/bin:$PATH\"
fi

cd tools/mattergen
if [ ! -d .venv ]; then
  uv venv .venv --python 3.10
fi
source .venv/bin/activate
uv pip install -e .
python - <<'PY'
import mattergen, torch
print('mattergen importable:', True)
print('torch:', torch.__version__)
print('cuda available:', torch.cuda.is_available())
PY
REMOTE_SCRIPT
chmod +x '$HPC_WORKDIR/bootstrap_mattergen.sh'"

echo "Remote bootstrap script written:"
echo "  ssh -A $REMOTE 'PROJECT_DIR=<remote-workdir> bash <remote-workdir>/bootstrap_mattergen.sh'"
