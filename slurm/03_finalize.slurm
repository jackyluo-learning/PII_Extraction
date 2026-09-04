#!/usr/bin/env bash
# Single job (runs after the whole attack array succeeds): aggregates across ALL
# models and seeds. eval => unified metric + paired stats + GCG-vs-random control
# + linguistic analysis; defense => filters vs naive+adaptive at fixed benign FPR;
# ablation => k-sweep, fluency-lambda sweep, convergence. Needs a GPU.
#SBATCH --job-name=pii-final
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=slurm/logs/%x-%j.out
#SBATCH --error=slurm/logs/%x-%j.err

set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
cd "$PROJECT_ROOT"
mkdir -p slurm/logs

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
# module load cuda/12.1
# shellcheck disable=SC1091
source .venv/bin/activate
# shellcheck disable=SC1091
source slurm/sweep_config.sh
export HF_HOME="$PROJECT_ROOT/.hf_cache"
export TOKENIZERS_PARALLELISM=false
# export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

# Aggregate over the FULL sweep: comma-join the arrays for the config overrides.
export PII_MODELS="$(IFS=,; echo "${MODELS[*]}")"
export PII_SEEDS="$(IFS=,; echo "${SEEDS[*]}")"
echo "[finalize] models=${PII_MODELS} seeds=${PII_SEEDS} host=$(hostname)"
nvidia-smi || true

python run_experiments.py --stage eval
python run_experiments.py --stage defense
python run_experiments.py --stage ablation
echo "[finalize] DONE. Results in ${PROJECT_ROOT}/results/"
