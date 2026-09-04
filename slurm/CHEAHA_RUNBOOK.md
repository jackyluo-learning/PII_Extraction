# Cheaha runbook — study `capacity_axis_20260902`

Written for someone who has never used a cluster. The **login hostname is confirmed**:
`cheaha.rc.uab.edu` (resolved and completed an SSH handshake on 2026-09-03). Still unverified:
whether jobs need an **`--account=` allocation string**. Everything else is checked against this
repo's own scripts.

---

## 0 · The mental model

A cluster is not a bigger laptop. It is **two different machines**:

| | Login node | Compute node |
|---|---|---|
| You get there by | `ssh` | `sbatch` / `srun` — never directly |
| Has internet | **yes** | often **no** |
| Has GPUs | **no** | yes |
| Shared with | everyone, right now | just your job |
| What belongs here | `git`, `pip install`, editing, `squeue` | training, attacks — anything that computes |

**The one rule: never compute on the login node.** Running `python train.py` after `ssh` is the
classic first-timer mistake — it is slow, it has no GPU, and it degrades the machine everyone else is
using to submit jobs. Staff notice.

---

## 1 · Log in

```bash
ssh jluo@cheaha.rc.uab.edu
```

**For a brand-new account, log in through the browser interface (Open OnDemand) first** — it
confirms in one step both that the credentials work and that the home directory is initialised. The
Quick Start link has the address.

### If SSH closes the connection right after the password

This is **not** a network or hostname problem — the handshake succeeded. A wrong password returns
`Permission denied` and re-prompts; closing *after* authentication is a different failure. Diagnose:

```bash
ssh -vvv jluo@cheaha.rc.uab.edu 2>&1 | tail -40
```

| Tail output | Means |
|---|---|
| closes after `Authentications that can continue: publickey,keyboard-interactive` | a second factor (Duo) is required |
| authenticates, then `Connection closed` | account or shell not provisioned — initialise via the web portal |
| repeated `Permission denied` | wrong password; RC accounts typically use the campus BlazerID password, and the provisioning email supplies no separate one |

Off-campus access may also need the VPN. Failing that: **support@listserv.uab.edu** with the
`ssh -vvv` tail, or the **Monday/Thursday 10 AM–noon Zoom office hours**, which is faster for a first
setup.

---

## 2 · Where files go — **the first real trap**

Your account has three places, and they are not interchangeable:

| Path | Size | Lifetime | Use it for |
|---|---|---|---|
| `/home/jluo` | shares 5 TB with `$USER_DATA` | permanent | dotfiles, small configs |
| **`/data/user/jluo`** | 5 TB | **permanent** | **this repo, the corpus, checkpoints, the parquet evidence** |
| `/scratch/jluo` | 100 TB | **files unused 30 days are deleted** | big temporary intermediates only |

> **Do not put this study in `/scratch`.** The sweep finishes, then the parquet shards sit untouched
> while the analysis is written — and "untouched for 30 days" is exactly the deletion rule. You would
> lose the evidence and not find out until you looked. Submission is 2026-09-29; the gap is real.

```bash
cd /data/user/jluo
git clone https://github.com/jackyluo-learning/PII_Extraction.git
cd PII_Extraction
git checkout exp/e2-e5          # the phase-0 gates are on this branch, NOT main
git log --oneline -3            # expect 4739e24 / 77b6739 / cd52034
```

---

## 3 · Build the environment — on the **login** node

This step needs internet, which compute nodes usually lack. That is why the repo keeps it separate.

```bash
cd /data/user/jluo/PII_Extraction
module load Python/3.11.5-GCCcore-13.2.0     # confirmed present on Cheaha
python3 --version                            # expect 3.11.5
bash slurm/setup_env.sh
```

**Name the version explicitly.** The default `(D)` in `module avail python` is **3.13.1**, and a
bare `module load Python` takes it — 3.13 has the least certain wheel coverage for this stack
(torch, spacy, lifelines). 3.11 is the safest. The system `/usr/bin/python3` is **3.6.8**, on which
torch 2.x cannot install; `setup_env.sh` now refuses outright rather than failing later with a
confusing resolver error.

> **The same module must be loaded inside the jobs.** SLURM does not inherit the login shell's
> module environment, and `.venv/bin/python` is a symlink into the module tree — without it a job
> dies on a broken interpreter. Every `slurm/*.slurm` now loads it, defaulting to
> `Python/3.11.5-GCCcore-13.2.0`; override with `export PII_MODULES="..."`.

It creates `.venv`, installs `requirements.txt` (including the exactly-pinned `lifelines==0.30.0`),
prefetches the base model into a project-local `.hf_cache`, and builds the corpus.

If your cluster serves Python through modules, uncomment the `module load python/3.11` line near the
top of that script first. `module avail python` lists what exists.

**Check the corpus came out clean** — the C4 halt and the Faker disjointness assertion both fire
during this step and would have stopped it, but confirm:

```bash
source .venv/bin/activate
python -c "import json; print(json.load(open('data/corpus_metadata.json'))['public_passages']['source_counts'])"
```

`c4` must be absent or `0`. If C4 contributed, real PII may be in the corpus — regenerate, do not
proceed.

---

## 4 · Retrain gpt2-124M — as a **job**, not on the login node

```bash
sbatch --partition=amperenodes --gres=gpu:1 --cpus-per-task=8 --mem=64G \
       --time=01:00:00 --job-name=pii-train \
       --wrap="cd /data/user/jluo/PII_Extraction && source .venv/bin/activate && \
               PII_DEVICE_PROFILE=auto python train.py --model gpt2"
```

`sbatch` prints a job id. That is the handle for everything below.

---

## 5 · Submit the sweep — 42 shards as one job array

A **job array** is one submission that becomes many independent tasks. `exp_capacity.slurm` already
decodes `(model, seed, k)` from `SLURM_ARRAY_TASK_ID`, so the whole sweep is one command.

The grid for this study — one model, three seeds, fourteen `k` including the `k=0` anchor:

```bash
cd /data/user/jluo/PII_Extraction
export PII_MODELS=gpt2
export PII_SEEDS="42 1337 2024"
export PII_KGRID="0 1 2 3 4 6 8 12 16 20 24 32 48 64"
export PII_GCG_ITERS=200
export PII_CAP_SWEEP_N=25
export PII_FIELDS=ssn,email
export PII_RUN_ID=e3a
source slurm/sweep_config.sh
echo "$NE3SHARDS shards"        # must print 42
```

**Split the submission by walltime.** `exp_capacity.slurm` requests `--time=11:45:00`, which is
*exactly* the `amperenodes` cap — zero margin. The large-`k` shards are the expensive ones and the
cost estimate is a floor, not a bound, so send them to `amperenodes-medium` (48 h):

```bash
# task ids are model-major, then seed, then k: id = (si * NK) + ki
# with NK=14 and k=32,48,64 at ki=11,12,13 -> the last three of each seed's block
sbatch --array=0-10,14-24,28-38   slurm/exp_capacity.slurm                              # small/medium k
sbatch --array=11-13,25-27,39-41  --partition=amperenodes-medium --time=24:00:00 \
                                  slurm/exp_capacity.slurm                              # k=32,48,64
```

If your cluster requires an allocation, add `--account=<yours>` to both, or
`export ACCOUNT=<yours>` — the repo's submitters already pass it through.

---

## 6 · Watch it

```bash
squeue -u jluo                       # what is queued or running
squeue -u jluo -t RUNNING            # only what is running
sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS,ExitCode    # history, including finished
seff <jobid>                         # efficiency after it finishes -- did it use the GPU?
scancel <jobid>                      # kill a job
scancel <jobid>_7                    # kill one array task
tail -f slurm/logs/pii-expcap-<jobid>_0.out
```

`PENDING` with reason `Resources` or `Priority` is normal — you are in a queue. `seff` after the
first shard tells you whether the walltime request is sane for the rest.

---

## 7 · Read the gates before trusting anything

**`α_0` is the sanity gate. Read it before any other shard's numbers.**

```bash
source .venv/bin/activate
python - <<'PY'
import glob, json, pandas as pd, run_manifest
a0 = pd.concat([pd.read_parquet(p) for p in glob.glob("results/attempts/e3a__*_k0.parquet")])
c = a0[a0.target_membership == "control"]
print(f"alpha_0 = {c.exact_match.mean():.4f}  n={len(c)}   <-- must be ~0")

for p in sorted(glob.glob("results/manifests/e3a__*.json")):
    d = json.load(open(p))
    print(f"  k={str(d['shard']['capacity_k']):<3} arms={d['arm_sizes']} "
          f"tiers={d['tier_composition']} subset={d['target_subset_hash']}")
print(run_manifest.compare(sorted(glob.glob("results/manifests/e3a__*.json"))))
PY
```

Three things must hold, and each is a stop rather than a warning:

* `alpha_0` ≈ 0 — otherwise `exact_match` fires with zero capacity and every `k` above it is offset.
* `tier_composition` contains `20` — otherwise the stratified-selection gate did not land and the
  trained arm is missing its most-memorised tier.
* `compare()` reports `ok: True` — otherwise the shards attacked different people and the paired
  design across `k` is gone. **Do not analyse the shards that agree**; that is choosing a subset
  after seeing the data.

---

## 8 · Bring the evidence home

Small — a few MB. From your laptop, not from Cheaha:

```bash
rsync -av jluo@cheaha.rc.uab.edu:/data/user/jluo/PII_Extraction/results/attempts/ results/attempts/
rsync -av jluo@cheaha.rc.uab.edu:/data/user/jluo/PII_Extraction/results/manifests/ results/manifests/
```

The checkpoint and corpus stay on Cheaha.

---

## Cheat sheet

| Want to | Command |
|---|---|
| submit a script | `sbatch script.slurm` |
| submit a one-liner | `sbatch --wrap="..."` |
| submit an array | `sbatch --array=0-41 script.slurm` |
| see my jobs | `squeue -u jluo` |
| see a finished job | `sacct -j <id>` |
| did it use the GPU | `seff <id>` |
| kill it | `scancel <id>` |
| interactive GPU shell (debugging only) | `srun --partition=amperenodes --gres=gpu:1 --time=01:00:00 --pty bash` |
| what partitions exist | `sinfo -s` |

## Partitions used here

_Verified against `docs.rc.uab.edu/cheaha/hardware/`, 2026-09-03._

| Partition | GPU | Walltime cap | Capacity | Used for |
|---|---|---|---|---|
| `amperenodes` | A100 | **12:00** | 2 GPU/node, 20 nodes | most shards (the script requests 11:45, i.e. 15 min of margin) |
| `amperenodes-medium` | A100 | **48:00** | 2 GPU/node, 20 nodes | `k = 32, 48, 64` |
| `pascalnodes` | P100 | 12:00 | 4 GPU/node, 18 nodes | ~3x slower; backfill |
| `express` | none | **2:00** | 48 cores | table building (**not 00:30** — that is the repo's own request, not the cap) |

> **The docs describe no special access request for GPU partitions.** So
> `Invalid account or account/partition combination` on a new account is a **missing Slurm
> association**, not a permissions policy — `sacctmgr show assoc` returning only headers confirms it.
> No value of `--account=` works around it, because no account exists to name.
