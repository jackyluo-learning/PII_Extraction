# CODE_MAP — Paper-to-Code Mapping and Experiment Status

_Compiled 2026-08-31 against repo HEAD `5b6d27d`. This document answers three questions: which code
implements each concept in the paper, which experiments have actually run, and where the code and
the paper disagree._

Companion visual documents:
- [GCG attack walkthrough](https://claude.ai/code/artifact/29d5ea65-d8be-4fbd-83cd-b593d80533fa) — one full attack, from random gibberish to early stop on a hit
- [Experiment inventory](https://claude.ai/code/artifact/dc9d2854-37b1-4d05-93d6-062b43794123) — status of all 21 E-numbers

---

## 0. Four things to know before touching anything

1. **The authoritative draft is not in this repo.** It is
   `~/Documents/Phd/UAB/Research/usenix_PromptExtraction_PrivacyAuditing.pdf` —
   *Forcing, Not Remembering: Calibrating Optimization-Based Memorization Audits of Language Models*,
   17 pages, USENIX format. Propositions 1–5, Corollaries 1–5, Algorithm 1, forcing capacity β,
   critical capacity k⋆, empirical ε lower bound, forcing-honeytoken defense.
   **Only the PDF exists on this machine — there is no .tex.** Extract it with pypdf; poppler is not
   installed, so the Read tool cannot render it.

2. **`usenix_paper.tex` is a stale scaffold.** Title still reads "Forcing vs. Memorization",
   25 unfilled `\todo{}`, **zero propositions / zero capacity / zero DP / zero honeytoken**, and
   leftover 44%/45.5% placeholder numbers. `7874_Adversarial_Prompt_Optimi.pdf` is the earlier ACL
   submission. **Treat neither as current.**

3. **`results/`, `data/`, and `models/` are gitignored and do not exist locally.** The data lives on
   the cluster. Every run2 number below comes from `WRITING_GUIDE.md` and the draft PDF, not from a
   fresh run.

4. **The repo contains two parallel pipelines** — see the next section. This is the easiest trap to
   fall into when reading the code.

---

## 1. Two pipelines

### B · Current pipeline (the one the forcing paper uses)

```
experiments.py --exp E1 --model gpt2 --seed 42
   ↓ one row per attack attempt (27-column schema in attempt_log.py)
results/attempts/<run>__<exp>__<shard>.parquet
   ↓ make_tables.py --run-id run2
results/tables/*.txt + *.csv
```

The 2×2 design is two columns of that schema: `model_state ∈ {finetuned, base}` ×
`target_membership ∈ {trained, control}`, with `train_frequency = 0` encoding a control record.
**Every number in the paper comes from this pipeline.**

### A · Legacy pipeline (ACL-submission era)

```
run_experiments.py --stage data|train|attack|adaptive|discovery|eval|defense|ablation
   ↓
results/*.json + results/summary_tables.txt
```

`baselines.py`, `defense_eval.py`, and `linguistic_analysis.py` belong to this one.

### The only connection between them

`run_E12_defenses` (pipeline B) reuses primitives from A — `build_benign_queries`,
`compute_prompt_perplexity`, `extract_prompt_features`, `FEATURE_NAMES` — but reads the new attempt
log.

> ⚠️ **Never use pipeline A's output to fill the forcing paper's tables.** The metric units differ:
> A is record-level, B is a per-(person, field) micro-average
> (`eval_cfg.metric_unit = "person_field"`).

---

## 2. Paper concept → code location

| Paper | Code | Notes |
|---|---|---|
| `A_k`, k free tokens | `config.py` `GCGConfig.prompt_length_k = 20` | E3 overrides per shard via `PII_CAP_K` |
| `Dec(M, p)` greedy decode | `experiments.py` `InstrumentedGCG._check` | `do_sample=False`, `max_new_tokens = T + 20` |
| `⊑` normalized containment | `evaluate.py` `exact_match` | numeric fields digits-only; rejects `len(t) < 4` |
| `EMR(·)` | `make_tables.py` `_cluster_emr_ci` | person-clustered bootstrap, N=10000 |
| `α_k` forcing floor (Def. 2) | same, filtered to `target_membership == "control"` | |
| `τ̂rec` (Eq. 7) | `make_tables.py` `_cluster_diff_ci` | **The Newcombe intervals in the paper's Table 4 are not in the code**; the code produces bootstrap intervals |
| `k_min(t)` (Def. 3) | `make_tables.py` `_kmin_table` | requires E3 data |
| `β` forcing capacity (Def. 3) | `make_tables.py` `capacity_e3` | **dimensionally inconsistent with the paper** — see §5 |
| `k⋆` (Def. 4) | `make_tables.py` `_crossing_k` | computes both the 1% and 5% crossings |
| `Mem(t)` (Def. 5) | **not implemented** | |
| `H(t)` self-information | `attempt_log.py` `target_self_information` | held-out ref model = `ling_cfg.reference_model = "gpt2"` |
| AUC (§3.6) | `make_tables.py` `_auc` | Mann-Whitney U, score = `−final_target_nll` |
| `TPR@α` (Def. 6) | `make_tables.py` `_tpr_at_fpr` | **implemented and printed by Table 1, but absent from the paper** |
| `ε̂` (Cor. 4) | **not implemented** (nothing in the repo) | Table 2 nonetheless marks it ✓ |
| ACR (§3.5) | `make_tables.py` `acr_e13` | `ACR≥1 ⟺ k_min < target_len_tokens`; depends on E3 |
| `τ̂mod` (Prop. 4) | `experiments.py` `run_E2_control_model` | never run |
| Honeytoken (Prop. 5) | `experiments.py` `run_E12_defenses` | never run |
| A1 exchangeability | `experiments.py` `run_E17_match_controls` | matching is **with replacement** |

---

## 3. Status of all 21 E-numbers

| ID | What it is | Code | Status | In the paper |
|---|---|---|---|---|
| **E1** | Negative controls: 8 probes × 2 arms × 4 models | `run_E1_negative_controls` | ✅ **ran (run2)** | Table 4/5 · Fig 2/3 |
| **E17** | Covariate matching | `run_E17_match_controls` | ✅ ran (E1 prerequisite) | §6.1 · Alg 1; balance table not reported |
| **E9** | ROC / AUC / TPR@FPR | `make_tables.table1_main` | ✅ has data | AUC column only; TPR@α unreported |
| **E16** | Rank inversion | `make_tables.rank_inversion_e16` | ✅ has data | **appears 0 times in the draft** |
| E3 | Capacity sweep, k ∈ {1…64} | `run_E3_capacity_sweep` + `slurm/exp_capacity.slurm` | ⏳ pending | Fig 4 has the analytic curve + 1 measured point |
| E5 | Frequency dose-response | `run_E5_frequency_response` | ⏳ pending | §3.6 describes the idea, no data |
| E2 | Control-model (base) arm | `run_E2_control_model` | ⏳ pending | §3.3 defers to "a larger study" |
| E7 | Budget-matched natural prompts | `run_E7_budget_matched` | ⏳ pending | §4 claims compute-matched |
| E10 | Pythia + the Pile, external validity | `run_E10_pile_membership` | ⏳ pending (needs `PII_PILE_SHARD`) | §9 future work |
| E12 | Three defenses at fixed FPR | `run_E12_defenses` | ⏳ pending (needs E1/E4 logs) | §8 has zero experimental numbers |
| E4 | Anchored vs free at matched k | `run_E4_anchored_gcg` | ⏳ pending | Table 5's anchored row actually comes from E1 |
| E13 | ACR head-to-head | `make_tables.acr_e13` | ⏳ blocked on E3 | §5.4 future work |
| E14 | Norm-constrained soft-prompt sweep | config grid + schema column only, **no driver** | ❌ | §4 mentions it |
| E6 | Scale + multiple seeds (n≥761/arm) | not a driver — a config decision (`PII_N_INDIVIDUALS` / `PII_N_CONTROLS`) | ❌ | §9 Limitations admits it |
| E21 | Prompt linguistics (24 features) | `linguistic_analysis.py` (pipeline A) | ❌ not wired into B | Appendix D describes the features, no results |
| E20 | Convergence curves | legacy-pipeline ablation only | ❌ | — |
| E11 | Modern models | commented out in config | ❌ | — |
| E8 · E15 · E18 · E19 | Named only in EXPERIMENTS.md's tier list | **no spec, no code** | ❌ | — |

> `EXPERIMENTS.md` says "See the pasted experiment list for the full E1–E21 spec" —
> **that spec is not in the repo**, which is why E8/E15/E18/E19 are numbers without content.

### run2's actual configuration (`slurm/submit_per_model.sh`)

| Model | Training | max_targets | gcg_iters |
|---|---|---|---|
| gpt2 124M | full fine-tune | 25 | 200 |
| gpt2-medium 355M | full fine-tune | 12 | 120 |
| pythia-1.4b | **LoRA** r=16 (`query_key_value`) | 20 | 150 |
| pythia-2.8b | **LoRA** r=16 | 12 | 120 |

Single seed (42), fields restricted to `ssn,email`. Row count =
(2 arms × n persons) × 2 fields × 8 probes ≈ **2208 rows** — that is the paper's entire experimental
record. **Per-model iteration budgets differ**, so τ̂ is not comparable across models.

---

## 4. What is actually in the paper

### Only 4 places carry experimental numbers, all from E1

| Location | Content | Produced by |
|---|---|---|
| Table 4 | Per model: n / EMR(D) / EMR(C) / τ̂rec[CI] / AUC | `table1_main` |
| Table 5 | Probe spectrum, 8 rows pooled | `table2_probe_spectrum` |
| Figure 2 | ROC-space scatter | = two columns of Table 4 |
| Figure 3 | Forcing-axis bar chart | = two columns of Table 5 |

Two further claims appear in prose with **no number attached**: §7.1 "training loss on the PII
documents falls to near zero" (from `train_meta.json`'s `pii_eval_losses`) and §7.3 "the
random-record match rate is near zero".

### Conceptual, no data

Table 1 (three audit settings) · Table 2 (formal objects, ✓/◦) · Table 3 (probes ordered
qualitatively) · Table 6 (notation) · Figure 1 (overview) · **Figure 4** (Prop. 1's analytic curve
plus a single measured red point at k=20, 39%).

### run2 results

**Table 4** — E1, `gcg_free`, k=20, seed 42, ssn+email:

| Model | n | Fixed | EMR(D) | EMR(C)=α | τ̂rec [95% CI] | AUC |
|---|---|---|---|---|---|---|
| GPT-2 124M | 25 | 0.0 | 52.0 | **52.0** | +0.0 [−26, 26] | 0.51 |
| GPT-2-M 355M | 12 | 0.0 | 66.7 | 33.3 | +33.3 [−6, 61] | 0.57 |
| Pythia-1.4B | 20 | 0.0 | 60.0 | 50.0 | +10.0 [−19, 37] | 0.45 |
| Pythia-2.8B | 12 | 0.0 | 16.7 | 0.0 | +16.7 [−10, 45] | 0.47 |

**Table 5** — probe spectrum, pooled:

| Probe | Free capacity | Conditioning | Gradient search | EMR(D) | EMR(C) | τ̂rec |
|---|---|---|---|---|---|---|
| fixed | 0 | yes | no | 0.0 | 0.0 | +0.0 |
| piicompass | 0 | true prefix | no | 0.0 | 0.0 | +0.0 |
| piiscope | 0 | yes | no | 0.0 | 0.0 | +0.0 |
| random_restart | k=20 | no | **no** | 0.0 | 0.0 | +0.0 |
| gcg_fluent | constrained | no | yes | 39.1 | **42.0** | −2.9 |
| gcg_free | k=20 | no | yes | 50.7 | **39.1** | +11.6 |
| gcg_anchored | k=20 | yes | yes | 71.0 | **62.3** | +8.7 |
| softprompt | ∞ | no | yes (continuous) | 100.0 | **100.0** | +0.0 |

The eight probes form a controlled comparison matrix. Four contrasts matter:

```
fixed     vs gcg_anchored   same conditioning, differs in optimization    0    → 71.0
gcg_free  vs random_restart same capacity & no cue, optimization vs budget 0    → 50.7
gcg_free  vs gcg_anchored   same optimization & capacity, differs in cue  50.7 → 71.0
gcg_free  vs softprompt     the two ends of the capacity axis             39.1 → 100 (control arm)
```

Read as a 2×2 factorial: **conditioning alone achieves nothing (fixed = random_restart = 0),
optimization alone reaches 50.7%, and the two together reach 71.0%.**

---

## 5. Known code-vs-paper mismatches

Ordered by how urgently each must be settled before adding experiments.

| # | Where | Issue |
|---|---|---|
| 1 | **β's dimension** | Paper Def. 3 is `median H(t)/k_min(t)` (**bits/token**); `capacity_e3` computes `linregress(H_bits → k_min).slope` (**tokens/bit**) — reciprocal units. The acceptance check right below it prints `beta / log2\|V\|`, which only type-checks for bits/token. **E3 produces this number the moment it runs; settle the definition first.** |
| 2 | **`n_random_restarts`** | Hardcoded to 512 in `config.py`; not derived from GCG's measured forward count. gcg_free at 120 iterations evaluates 61,440 candidates — a **120× gap**. §4 and Appendix C claim "at GCG's exact forward-pass budget / exact rather than nominal". The probe that actually matches budgets is E7. |
| 3 | **`forward_passes` units differ** | GCG counts **batched forward calls** (1 gradient + 8 candidate minibatches = 9/iteration); `random_restart` counts **generations**; `piiscope` counts prompts; `softprompt` counts optimizer steps. Cross-probe comparison needs conversion. |
| 4 | **`ε̂` has no implementation** | Cor. 4's empirical ε lower bound. Table 2 marks it ✓; nothing in the repo computes it. Table 1 already holds (TPR, FPR) and everything Clopper–Pearson needs — roughly ten lines. |
| 5 | **No λ-sweep driver** | `adaptive_fluency_lambda = 0.1` is a single float; no experiment iterates over multiple λ. Cor. 3's fluency-equals-capacity equivalence has therefore **never been tested** — not tested and failed, simply not tested. |
| 6 | **E14 is a shell** | `softprompt_norm_grid` is in config and `softprompt_norm` is in the schema, but `_probe_static` always returns `None` and no driver fills it. |
| 7 | **Inconsistent CI method** | §6.3 says "person-clustered bootstrap"; Table 4's caption says "Newcombe (Wilson-score)". The code implements only bootstrap; the Newcombe intervals were computed by hand. |
| 8 | **`fixed` probe implementation** | §4 describes it as "best of k variants" (direct/completion/few-shot/role-play). E1's `_run_fixed_probe` is a **single prompt, single greedy generation**; the multi-variant version lives in `baselines.py` and in E7's `fixed_budget` (5 variants). |
| 9 | **Template count** | §6.1 says seven templates; `TEMPLATES` actually holds **nine** (plus `onboarding_ticket` and `verification_note`), and `data_cfg.template_types` — the seven-item list — **is never read**. |
| 10 | **Anchored target asymmetry** | `gcg_anchored` targets the bare value (6 tokens); `gcg_free` targets the labelled string (9 tokens). A shorter target is inherently easier to hit, so that effect is confounded with conditioning. |
| 11 | **Training used LoRA** | §6.2 says only "end-to-end with AdamW". In fact `use_lora_for()` thresholds at 0.5B: both GPT-2s are fully fine-tuned, **both Pythias use LoRA** (r=16, `query_key_value` only, lr=2e-4). |
| 12 | **Padding enters the loss** | `CorpusDataset` pads to 512 with `padding="max_length"` and sets `labels = input_ids.clone()` — pad positions are **not masked to −100**. Short documents (e.g. `contact_list`, one line) are mostly padding. |
| 13 | **E17 matches with replacement** | `run_E17_match_controls` matches with replacement (50 controls covering 100 trained records); the paper does not mention this. It weakens the independent-binomial assumption and inflates effective n. |
| 14 | **No disjointness assertion for D/C** | `generate_individuals(n, seed)` vs `generate_individuals(n, seed + 1000)` — a seed offset, with **no assertion that the generated values are disjoint**. Appendix B calls it a "disjoint seed stream". |
| 15 | **β undefined when k_min = ∞** | Def. 3 takes a median, but a failed attack gives `k_min = ∞`. Pythia-2.8B's EMR(C) = 0/12 makes the median ∞. Needs a stated convention. |

---

## 6. Computed by the code, unused by the paper

The cheapest gap to close — these numbers already exist in `make_tables` output.

| Quantity | Code status | Paper status |
|---|---|---|
| `TPR@1%` / `TPR@5%` | `table1_main` prints both columns | Absent from Table 4, although §3.6 demands all five quantities together and Def. 6 defines it explicitly |
| McNemar p-values | `_paired_mcnemar` computes them | §6.3 says they will be used; that is the only mention, and no p-value appears in the text |
| Rank inversion (E16) | `rank_inversion_e16` computes it | "rank inversion" appears 0 times in the draft |
| `random_record_match` | logged on every row | Only the qualitative claim "near zero" |
| E17 covariate balance | persisted to `results/e17_matches_*.json` | Algorithm 1 step 2 requires reporting the distributional overlap; the draft does not |

**The first four are pure transcription — no new run required.**

---

## 7. Zero-GPU material already in hand

`dump_all_results.py --run-id run2` extracts 8 tables from the **same run2 log**:

1. Overview (models / probes / fields / seeds / counts)
2. Per-model headline table = Table 1
3. **Per-model × per-probe (4 × 8)**
4. **Per-field (ssn / email) × per-probe** ← the per-field breakdown the paper lacks
5. **Frequency dose-response (the script calls it a "poor-man's E5")**
6. Substring-inflation guard
7. Rank inversion
8. Compute profile (forward_passes / wallclock)

Item 5 works because the corpus is generated with `frequency_groups = {10:1, 30:5, 60:20}` and
`cap_targets` samples "evenly across the registry so all frequency tiers stay represented" — so
**E1's log already contains four frequency tiers** (1 / 5 / 20 plus the controls at 0). E5's
"fitted intercept vs directly measured α" cross-check can be approximated from this alone.

---

## 8. Priority order for the experiments still to run

| Order | Experiment | What one run unlocks | Retrain? |
|---|---|---|---|
| 1 | **E3 capacity sweep** | Turns `β`, `k⋆`, and `Mem(t)` from ◦ to ✓; upgrades Figure 4 from "analytic curve + 1 point" to a measured curve; **also unblocks E13 (ACR)** | No |
| 2 | **E5 frequency response** | A **second independent estimate of the forcing floor** (fitted intercept vs directly measured α); `frequency_e5` prints `WITHIN CI` / `OUTSIDE CI` automatically | Only for the full 7 tiers; not for the 4 already present |
| 3 | **E6 more controls** | α's CI is governed by the control arm's n. `build_corpus()` does `corpus = pii_docs + public`, so **controls never enter the corpus and adding them requires no retraining** | **No** (adding *trained* records does) |
| 4 | **E2 control-model arm** | `τ̂mod`, completing the lower half of the 2×2 and Prop. 4's sandwich and falsification test | No |
| 5 | E7 / E10 / E12 | E7 makes "compute-matched" true; E10 answers the synthetic-data objection; E12 puts numbers in §8 | No |

```bash
# E3 (sharded by k: 13 k-values × models × seeds)
sbatch --export=ALL,PII_CAP_K=20 slurm/exp_capacity.slurm

# E2 / E5 (single task each)
python experiments.py --exp E2 --model gpt2 --seed 42
python experiments.py --exp E5 --model gpt2 --seed 42

# More controls, no retraining
PII_N_CONTROLS=800 python run_experiments.py --stage data

# Tier-1
sbatch --export=ALL,EXP=E7,MODEL=gpt2,SEED=42,PII_RUN_ID=run2 slurm/exp_tier1.slurm

# Rebuild tables (CPU, seconds)
python make_tables.py --run-id run2
python dump_all_results.py --run-id run2
```

---

## 9. Implementation quick reference

**GCG inner loop** (`InstrumentedGCG.run`; k=20, B=256, 512 candidates/step, minibatch 64)

```
per iteration:  1 forward+backward → grads (20, 50257)
                topk(256) per row → 20 × 256 = 5120 candidates (each differs in 1 position)
                random.sample → 512 → 8 batched forwards → argmin
                free_ids replaced unconditionally; best_free updated only on improvement
                  (so the search may move uphill and escape a local optimum)
                every 10 iterations: _check(free_ids) — free generation + exact_match; break on hit
on exit:        if never hit, one final _check on best_free
accounting:     forward_passes = 9/iteration (1 gradient + 8 candidate batches); generation excluded
```

- Gradients are taken w.r.t. the input-layer one-hot only; `_load_model` sets model weights to
  `requires_grad_(False)` and **no optimizer is ever instantiated**
- The loss uses teacher forcing (target tokens are concatenated into the input); the decision uses
  free generation — **low loss does not imply success**
- `logits[start : start+T]` with `start = P + k + S − 1` (position i's logit predicts token i+1)
- `final_target_nll = best_tloss × T` = the whole target string's negative log probability in nats;
  negated, it becomes the continuous score for the ROC
- `steps_to_first_success` is **quantized to multiples of 10** (checks only fire at `it % 10 == 0`);
  `first_success == steps_run == N` means the hit came from the post-loop fallback check

**Decision rule** (`evaluate.exact_match`, the only one in the repo)

- Compares against `value`, not `target_text` (the model need not reproduce the `"SSN: "` label)
- `ssn` / `phone` / `credit_card` → `_digits_only` (strips every non-digit from **both** sides);
  everything else → `normalize_text` (NFKC + lowercase + whitespace collapse, **punctuation kept**)
- **Substring containment**, not equality; rejects targets with `len(t) < 4`

**Data generation** (`data_generation.build_corpus`)

- `Faker.seed(42)` → 100 trained individuals; `Faker.seed(1042)` → 50 negative controls
- `corpus = pii_docs + public` — **controls enter only `target_registry`, never the corpus**
- 1360 PII documents + 100k public passages ⇒ PII is ≈ 1.34% of the corpus
- Surface perturbation at `perturb_prob=0.5`: numeric fields get new separators, text fields get case
  changes, labels get variants; **email is never touched** (`@` and `.` are matched verbatim); the
  canonical values are never modified

---

## 10. Currency of the repo's documentation

Ten markdown files of very different vintage. When they conflict, the "current" group wins.

| Document | Status | Note |
|---|---|---|
| `CODE_MAP.md` | **current** | this file: paper↔code map + experiment status |
| `REVISION_PLAN.md` | **current** | final run2 data + write-up plan |
| `WRITING_GUIDE.md` | **current** | section-by-section guide with run2 numbers and paste-ready LaTeX |
| `EXPERIMENTS.md` | **current** | E-suite design and tier order (but the full E1–E21 spec is not in the repo) |
| `RUN.md` | **current** | SLURM runbook |
| `IMPROVEMENT_PLAN.md` | historical | round-1 revision strategy, pre-forcing-pivot |
| `CHANGES.md` | historical | round-1 changelog, points at IMPROVEMENT_PLAN |
| `PAPER_UPDATE_PLAN.md` | historical | written for an **earlier** run (GPT-2 × 3 seeds); superseded by run2 |
| `Reviews.md` | historical | reviewer comments on the older ACL-era submission |
| `IRI_outline.md` | **a different paper** | IEEE IRI 2026, 6 pages, "afterlife of personal data" framing, paired with `IRI_paper.tex`. **Not the forcing paper — do not merge its claims.** |

Every plan in the historical group targets `usenix_paper.tex` as its working file and cites results
that no longer stand; following them reintroduces stale numbers.

---

## 11. Claude Code persistent memories (full text)

The same routing information is stored in
`~/.claude/projects/-Users-xuqiluo-PycharmProjects-PII-Extraction/memory/` and loaded automatically
at the start of every session. **That directory lives outside the repo and is not in git**, so the
three memories are reproduced verbatim below — anyone cloning this repo gets the full context
without needing it.

Index file `MEMORY.md`:

```markdown
- [CODE_MAP.md is the entry point](pii-code-map-is-entry-point.md) — read it before exploring the PII_Extraction code; two pipelines, only E1 has run, 15 code/paper mismatches.
- [Forcing draft lives outside the repo](forcing-draft-lives-outside-repo.md) — the current paper is a PDF in ~/Documents/Phd/UAB/Research, not the repo's stale usenix_paper.tex.
- [Which repo docs are current](pii-repo-doc-currency.md) — REVISION_PLAN/WRITING_GUIDE/CODE_MAP are live; IMPROVEMENT_PLAN/PAPER_UPDATE_PLAN/CHANGES/Reviews are historical; IRI_* is a separate paper.
```

### 11.1 `pii-code-map-is-entry-point.md`

```markdown
---
name: pii-code-map-is-entry-point
description: CODE_MAP.md is the entry point for the PII_Extraction repo; it records the paper-to-code mapping, experiment status, and 15 known code/paper mismatches.
metadata:
  type: project
---

`CODE_MAP.md` (repo root, written 2026-08-31) is the routing document for this
project. Read it before exploring the code. It records:

- the **two parallel pipelines** — `experiments.py` + `attempt_log` +
  `make_tables` (current, forcing paper) vs `run_experiments.py`'s 8 stages
  (old ACL era). Metric units differ (per-(person,field) micro-average vs
  record-level), so their outputs must never be mixed.
- paper concept → code location table (α_k, τ̂rec, β, k⋆, TPR@α, ACR …)
- status of all 21 E-numbers: **only E1 has ever run** (run2), plus E17 as its
  prerequisite; E9/E16 are free analyses with data; seven drivers are implemented
  but unrun; E8/E15/E18/E19 have no spec anywhere in the repo
- 15 verified code/paper mismatches, incl. β's dimension being inverted between
  Def. 3 and `capacity_e3`, `n_random_restarts` hardcoded at 512 (not
  budget-matched), `ε̂` having no implementation, and no λ-sweep driver
- `dump_all_results.py` yields 8 extra tables from the existing log at zero GPU
  cost, including a "poor-man's E5" frequency dose-response

**Why:** the repo has 10 markdown files and two pipelines; without this map a
session re-derives the same facts or edits the wrong file.
**How to apply:** read `CODE_MAP.md` first, then the draft PDF
([[forcing-draft-lives-outside-repo]]). See also [[pii-repo-doc-currency]].
```

### 11.2 `forcing-draft-lives-outside-repo.md`

```markdown
---
name: forcing-draft-lives-outside-repo
description: The authoritative "Forcing, Not Remembering" draft is a PDF outside the repo; usenix_paper.tex is a stale scaffold.
metadata:
  type: project
---

The current authoritative draft is
`~/Documents/Phd/UAB/Research/usenix_PromptExtraction_PrivacyAuditing.pdf`
— "Forcing, Not Remembering: Calibrating Optimization-Based Memorization Audits
of Language Models", 17 pages, USENIX format. Propositions 1–5, Corollaries 1–5,
Algorithm 1, forcing capacity β, critical capacity k*, empirical ε lower bound,
forcing-honeytoken defense. **Only the PDF exists on this machine — no .tex.**
Extract it with pypdf (poppler is not installed, so the Read tool cannot render it).

Do NOT treat these as current: `usenix_paper.tex` (old scaffold, title "Forcing
vs. Memorization", 25 unfilled `\todo{}`, zero propositions, stale 44%/45.5%
placeholder numbers) or `7874_Adversarial_Prompt_Optimi.pdf` (earlier ACL
submission).

**Why:** working from the repo's .tex silently discards the entire theory section
and regresses the paper by two revisions.
**How to apply:** read the PDF above as the single source of truth; ask for the
.tex if edits are needed. Start from [[pii-code-map-is-entry-point]].
```

### 11.3 `pii-repo-doc-currency.md`

```markdown
---
name: pii-repo-doc-currency
description: Which of PII_Extraction's markdown docs are current vs historical, and that IRI_paper.tex is a separate second paper.
metadata:
  type: project
---

The repo has 10 markdown files of very different vintage.

**Current** — `CODE_MAP.md` (paper↔code map + experiment status),
`REVISION_PLAN.md` and `WRITING_GUIDE.md` (both carry the final run2 numbers:
4 models, seed 42, ssn+email), `EXPERIMENTS.md` (E-suite design), `RUN.md`
(SLURM howto).

**Historical, do not act on** — `IMPROVEMENT_PLAN.md` and `CHANGES.md`
(round-1 revision, pre-forcing-pivot), `PAPER_UPDATE_PLAN.md` (written for an
earlier run of GPT-2 × 3 seeds, superseded by run2), `Reviews.md` (reviewer
comments on the older ACL-era submission).

**`IRI_outline.md` + `IRI_paper.tex` are a SEPARATE second paper** — IEEE IRI
2026, 6 pages, "afterlife of personal data / data-reuse" framing. Not the
forcing paper; don't merge their claims.

**Why:** several plans target `usenix_paper.tex` and cite numbers from runs that
no longer stand, so following them silently reintroduces stale results.
**How to apply:** when a plan doc conflicts with `WRITING_GUIDE.md` or
`CODE_MAP.md`, the latter two win. See [[pii-code-map-is-entry-point]].
```

> When these memories and this document disagree, **this document wins** — the memories are routing
> summaries and will go stale as experiments proceed (especially "only E1 has run"). After running
> anything new, update §3's status table and the `pii-code-map-is-entry-point` memory together.
