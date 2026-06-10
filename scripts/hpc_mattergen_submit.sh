#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 PATHWAY_ID [constraints_json_path]" >&2
  exit 2
fi

PATHWAY_ID="$1"
CONSTRAINTS_JSON="${2:-}"

HPC_HOST="${HPC_HOST:-login.hpc.qmul.ac.uk}"
HPC_USERNAME="${HPC_USERNAME:-${HPC_USER:-}}"
HPC_SSH_KEY_PATH="${HPC_SSH_KEY_PATH:-${HPC_KEY:-}}"

if [ -z "$HPC_USERNAME" ]; then
  echo "Set HPC_USERNAME before submitting MatterGen jobs." >&2
  exit 2
fi

HPC_WORKDIR="${HPC_WORKDIR:-${HPC_PROJECT_DIR:-/data/scratch/${HPC_USERNAME}/gap2material-em}}"
HPC_SLURM_PARTITION="${HPC_SLURM_PARTITION:-${HPC_PARTITION:-gpushort}}"
HPC_TIME_LIMIT="${HPC_TIME_LIMIT:-${HPC_TIME:-01:00:00}}"
HPC_MEM="${HPC_MEM:-32G}"
HPC_CPUS_PER_TASK="${HPC_CPUS_PER_TASK:-${HPC_CPUS:-8}}"
HPC_GPU_REQUEST="${HPC_GPU_REQUEST:-${HPC_GPUS:+gpu:${HPC_GPUS}}}"
HPC_GPU_REQUEST="${HPC_GPU_REQUEST:-gpu:1}"
MATTERGEN_BATCH_SIZE="${MATTERGEN_BATCH_SIZE:-8}"
MATTERGEN_NUM_BATCHES="${MATTERGEN_NUM_BATCHES:-1}"
REMOTE="${HPC_USERNAME}@${HPC_HOST}"

SSH_OPTS=(-A -o BatchMode=yes)
SCP_OPTS=(-o BatchMode=yes -o ForwardAgent=yes)
if [ -n "$HPC_SSH_KEY_PATH" ]; then
  SSH_OPTS+=(-i "$HPC_SSH_KEY_PATH")
  SCP_OPTS+=(-i "$HPC_SSH_KEY_PATH")
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REMOTE_JOB_DIR="$HPC_WORKDIR/jobs/$PATHWAY_ID"

ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p '$REMOTE_JOB_DIR' '$HPC_WORKDIR/outputs/$PATHWAY_ID'"

if [ -n "$CONSTRAINTS_JSON" ]; then
  scp "${SCP_OPTS[@]}" "$CONSTRAINTS_JSON" "$REMOTE:$REMOTE_JOB_DIR/constraints.json"
else
  TEMP_CONSTRAINTS="$(mktemp -t application_finder_constraints.XXXXXX.json)"
  cat > "$TEMP_CONSTRAINTS" <<'JSON'
{
  "note": "Replace this file with constraints exported from Application Finder before scientific use.",
  "compatible_constraints": {},
  "unsupported_em_properties": []
}
JSON
  scp "${SCP_OPTS[@]}" "$TEMP_CONSTRAINTS" "$REMOTE:$REMOTE_JOB_DIR/constraints.json"
  rm -f "$TEMP_CONSTRAINTS"
fi

ssh "${SSH_OPTS[@]}" "$REMOTE" "cat > '$REMOTE_JOB_DIR/mattergen_${PATHWAY_ID}.slurm' <<REMOTE_SLURM
#!/usr/bin/env bash
#SBATCH --job-name=mg_${PATHWAY_ID}
#SBATCH --partition=${HPC_SLURM_PARTITION}
#SBATCH --gres=${HPC_GPU_REQUEST}
#SBATCH --cpus-per-task=${HPC_CPUS_PER_TASK}
#SBATCH --mem=${HPC_MEM}
#SBATCH --time=${HPC_TIME_LIMIT}
#SBATCH --output=${REMOTE_JOB_DIR}/slurm-%j.out
#SBATCH --error=${REMOTE_JOB_DIR}/slurm-%j.err

set -euo pipefail
cd '${HPC_WORKDIR}/repo/tools/mattergen'
source .venv/bin/activate

python - <<'PY'
import json
from pathlib import Path
import subprocess
import torch

constraints = json.loads(Path('${REMOTE_JOB_DIR}/constraints.json').read_text())
out_dir = Path('${HPC_WORKDIR}/outputs/${PATHWAY_ID}')
out_dir.mkdir(parents=True, exist_ok=True)

compatible = constraints.get('compatible_constraints', constraints)
props = {}
model_name = 'mattergen_base'

def number_or_none(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        import re
        match = re.search(r'-?\\d+(?:\\.\\d+)?', value)
        if match:
            return float(match.group(0))
    return None

chemical_system = compatible.get('chemical_system')
if not chemical_system and isinstance(compatible.get('include_elements'), list):
    elements = [str(item) for item in compatible['include_elements'] if str(item).isalpha()]
    if 2 <= len(elements) <= 4:
        chemical_system = '-'.join(elements)

band_gap = number_or_none(compatible.get('band_gap'))
magnetic_density = number_or_none(compatible.get('magnetic_density'))
bulk_modulus = number_or_none(compatible.get('bulk_modulus'))
energy_above_hull = number_or_none(compatible.get('energy_above_hull') or compatible.get('stability_or_formation_energy'))

if chemical_system and energy_above_hull is not None:
    model_name = 'chemical_system_energy_above_hull'
    props = {'chemical_system': chemical_system, 'energy_above_hull': energy_above_hull}
elif chemical_system:
    model_name = 'chemical_system'
    props = {'chemical_system': chemical_system}
elif magnetic_density is not None:
    model_name = 'dft_mag_density'
    props = {'dft_mag_density': magnetic_density}
elif band_gap is not None:
    model_name = 'dft_band_gap'
    props = {'dft_band_gap': band_gap}
elif bulk_modulus is not None:
    model_name = 'ml_bulk_modulus'
    props = {'ml_bulk_modulus': bulk_modulus}

print('CUDA available:', torch.cuda.is_available())
print('Selected model:', model_name)
print('Conditioning properties:', json.dumps(props, indent=2))
print('Output directory:', out_dir)

cmd = [
    'mattergen-generate',
    str(out_dir),
    f'--pretrained-name={model_name}',
    '--batch_size=${MATTERGEN_BATCH_SIZE}',
    '--num_batches=${MATTERGEN_NUM_BATCHES}',
    '--record_trajectories=False',
]
if props:
    cmd.append('--properties_to_condition_on=' + repr(props))
    cmd.append('--diffusion_guidance_factor=2.0')

print('Running:', ' '.join(cmd))
subprocess.run(cmd, check=True)
PY
REMOTE_SLURM
sbatch '$REMOTE_JOB_DIR/mattergen_${PATHWAY_ID}.slurm'"
