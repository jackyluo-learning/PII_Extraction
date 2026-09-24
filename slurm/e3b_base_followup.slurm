#!/usr/bin/env bash
# E3b-matched base-model follow-up, one seed per job. The pilot uses fewer
# frozen pairs and a distinct run ID; formal jobs use all 25 pairs.
#SBATCH --job-name=pii-e3b-base
#SBATCH --partition=amperenodes
#SBATCH --account=jluo
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=slurm/logs/%x-%j.out
#SBATCH --error=slurm/logs/%x-%j.err

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit from the clean follow-up checkout}"
mkdir -p slurm/logs
module load Python/3.11.5-GCCcore-13.2.0

: "${E3B_SOURCE_ROOT:?Set E3B_SOURCE_ROOT to the accepted E3b checkout}"
: "${E3B_BASE_SEED:?Set E3B_BASE_SEED to 42, 1337, or 2024}"
: "${E3B_RUN_ID:?Set a unique pilot or formal run ID}"
: "${E3B_PILOT_PAIRS:=25}"

export PII_FIELDS=ssn,email
export PII_GCG_ITERS=200
export PII_DEVICE_PROFILE=a100_80
export PII_CAP_SWEEP_N=25
export PII_RUN_ID="$E3B_RUN_ID"
export HF_HOME=/data/user/jluo/PII_Extraction/.hf_cache
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

base_snapshot="$HF_HOME/hub/models--gpt2/snapshots/607a30d783dfa663caf39e06633721c8d4cfcd7e"
target_manifest="$E3B_SOURCE_ROOT/results/target_sets/e3b.json"

echo "[E2B] seed=$E3B_BASE_SEED pairs=$E3B_PILOT_PAIRS run_id=$E3B_RUN_ID job=$SLURM_JOB_ID"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
.venv/bin/python run_e3b_base_followup.py \
  --target-manifest "$target_manifest" \
  --base-snapshot "$base_snapshot" \
  --seed "$E3B_BASE_SEED" \
  --pilot-pairs "$E3B_PILOT_PAIRS" \
  --run-id "$E3B_RUN_ID"
echo "[E2B] DONE seed=$E3B_BASE_SEED pairs=$E3B_PILOT_PAIRS"
