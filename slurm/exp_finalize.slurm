#!/usr/bin/env bash
# Forcing suite finalize: merge every attempt-log shard and produce all
# tables/figures. CPU-only and fast, but kept as a dependent job so it runs
# automatically after the experiment arrays complete.
#SBATCH --job-name=pii-expfin
#SBATCH --partition=express
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=slurm/logs/%x-%j.out
#SBATCH --error=slurm/logs/%x-%j.err

set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
cd "$PROJECT_ROOT"; mkdir -p slurm/logs
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
export PYTHONUNBUFFERED=1

RUN_ID="${PII_RUN_ID:-run1}"
echo "[finalize] make_tables --run-id ${RUN_ID}"
python make_tables.py --run-id "$RUN_ID"
echo "[finalize] DONE. Tables in ${PROJECT_ROOT}/results/tables/"
