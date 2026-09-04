#!/usr/bin/env bash
# Array job: one task per model (train_cfg.get_models() restricted to a single
# model via PII_MODELS). Distinct model dirs => no write races. Cheap vs GCG.
# Resource flags (partition/gres/time/account) are normally supplied by
# submit_all.sh; the #SBATCH defaults below let you also submit this standalone.
#SBATCH --job-name=pii-train
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=slurm/logs/%x-%A_%a.out
#SBATCH --error=slurm/logs/%x-%A_%a.err

set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
cd "$PROJECT_ROOT"
mkdir -p slurm/logs

# module load cuda/12.1        # <-- EDIT if your cluster uses modules
# shellcheck disable=SC1091
# Load the Python module the venv was built from, so the job does not depend on
# the state of the shell that submitted it.
#
# sbatch's default --export=ALL DOES copy the submitting shell's environment,
# and `module load` works by setting env vars (PATH, LD_LIBRARY_PATH,
# LOADEDMODULES), so a module loaded before sbatch usually does propagate.
# Relying on that is fragile: it breaks on a fresh shell that forgot to load it,
# under a site --export=NONE policy, and on requeue. The failure is also opaque
# -- .venv/bin/python is a symlink and resolves by absolute path, but the
# GCCcore shared libraries are not on LD_LIBRARY_PATH, so the interpreter dies
# on a missing .so rather than saying "no module loaded", after queueing.
#
# Set PII_MODULES to whatever `module avail python` showed.
for _m in ${PII_MODULES:-Python/3.11.5-GCCcore-13.2.0}; do
  module load "$_m" 2>/dev/null || echo "[warn] module load $_m failed (not a module cluster?)"
done
source .venv/bin/activate
# shellcheck disable=SC1091
source slurm/sweep_config.sh
export HF_HOME="$PROJECT_ROOT/.hf_cache"
export TOKENIZERS_PARALLELISM=false
# export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # if compute nodes lack internet

model="${MODELS[$SLURM_ARRAY_TASK_ID]}"
export PII_MODELS="$model"
echo "[train] task=${SLURM_ARRAY_TASK_ID} model=${model} host=$(hostname) profile=${PII_DEVICE_PROFILE}"
nvidia-smi || true

python run_experiments.py --stage train
echo "[train] DONE: ${model}"
