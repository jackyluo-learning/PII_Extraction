#!/usr/bin/env bash
# Stage 0: build the corpus (CPU + internet). Streams real public passages from
# HuggingFace, so it needs outbound network. Scale is set REPRODUCIBLY via env
# (PII_N_INDIVIDUALS / PII_N_CONTROLS / PII_N_PUBLIC) rather than local edits.
# Writes data/ (individuals.json, negative_controls.json, target_registry.json,
# corpus/train.json, corpus_metadata.json).
#SBATCH --job-name=pii-data
#SBATCH --partition=amperenodes
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=slurm/logs/%x-%j.out
#SBATCH --error=slurm/logs/%x-%j.err

set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
cd "$PROJECT_ROOT"; mkdir -p slurm/logs
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
export PYTHONUNBUFFERED=1

# Real-run scale (override at submit if you want a different size).
export PII_N_INDIVIDUALS="${PII_N_INDIVIDUALS:-200}"
export PII_N_CONTROLS="${PII_N_CONTROLS:-800}"
export PII_N_PUBLIC="${PII_N_PUBLIC:-100000}"

echo "[data] host=$(hostname) individuals=$PII_N_INDIVIDUALS controls=$PII_N_CONTROLS public=$PII_N_PUBLIC"
python run_experiments.py --stage data
echo "[data] DONE — registry: $(python -c "import json;print(len(json.load(open('data/target_registry.json'))))" ) entries"
