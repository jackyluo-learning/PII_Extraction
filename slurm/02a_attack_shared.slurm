#!/usr/bin/env bash
# FIELD-PARALLEL workflow, part A. Array over (model, seed). Runs the per-person
# and all-field-cheap attacks ONCE per combo: baselines (per-person) + random-
# restart control + discovery (PII-Scope/PII-Compass). These are NOT sharded by
# field. The expensive GCG is handled separately by 02b_gcg_by_field.slurm.
#SBATCH --job-name=pii-shared
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=16:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=slurm/logs/%x-%A_%a.out
#SBATCH --error=slurm/logs/%x-%A_%a.err

set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
cd "$PROJECT_ROOT"
mkdir -p slurm/logs
# A venv built from a MODULE-provided Python needs that module loaded here too:
# SLURM does not inherit the login shell's module environment, and .venv/bin/python
# is a symlink into the module tree. Without this the job dies on a broken
# interpreter. Set PII_MODULES to whatever `module avail python` showed.
for _m in ${PII_MODULES:-Python/3.11.5-GCCcore-13.2.0}; do
  module load "$_m" 2>/dev/null || echo "[warn] module load $_m failed (not a module cluster?)"
done
# module load cuda/12.1
# shellcheck disable=SC1091
source .venv/bin/activate
# shellcheck disable=SC1091
source slurm/sweep_config.sh
export HF_HOME="$PROJECT_ROOT/.hf_cache"
export TOKENIZERS_PARALLELISM=false

i="${SLURM_ARRAY_TASK_ID}"
mi=$(( i / NSEEDS )); si=$(( i % NSEEDS ))
model="${MODELS[$mi]}"; seed="${SEEDS[$si]}"
export PII_MODELS="$model"; export PII_SEEDS="$seed"
# IMPORTANT: do NOT set PII_FIELDS here — baselines/controls run over all fields.
unset PII_FIELDS || true

echo "[shared] task=${i} model=${model} seed=${seed} host=$(hostname)"
nvidia-smi || true
python run_experiments.py --stage baselines_only
python run_experiments.py --stage controls_only
echo "[shared] DONE: model=${model} seed=${seed}"
