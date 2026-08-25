# PII Extraction Paper — Results Digest & Revision Plan
_Last updated: 2026-08-25 · target venue: USENIX Security · thesis: **Forcing vs. Memorization**_

This is the authoritative working doc for the revision. It (I) organizes every
real result we have, (II) states the framing the data supports, (III) gives a
prioritized plan to turn it into a submittable paper, and (IV) lists risks and
the decision points. It supersedes the earlier IMPROVEMENT_PLAN.md /
PAPER_UPDATE_PLAN.md where they disagree, because those predate real data.

---

## PART I — RESULTS SO FAR (organized)

All numbers below are **real runs** written through the unified per-attempt log
(`attempt_log.py`) and produced by `make_tables.py` — no placeholders. Every
attack attempt is one logged row; all tables derive from that single log, so they
cannot disagree.

### Table A — Main result (E1, `gcg_free`, seed 42, fields = ssn + email) · run2

| Model | Params | Fixed | **GCG** | **Neg-ctrl (forcing floor)** | **Adj = GCG−Negctl [95% CI]** | AUC [CI] | p(McN) | n_trained |
|---|---|---|---|---|---|---|---|---|
| gpt2 | 124M | 0.0 | 52.0 | **52.0** | **+0.0 [−28, 28]** | 0.51 [.34,.67] | .0002 | 25 |
| gpt2-medium | 355M | 0.0 | 66.7 | **33.3** | **+33.3 [−8, 67]** | 0.57 [.31,.81] | .008 | 12 |
| pythia-1.4b | 1.4B | 0.0 | 60.0 | **50.0** | **+10.0 [−20, 40]** | 0.45 [.27,.64] | .0005 | 20 |
| pythia-2.8b | 2.8B | — | — | — | _pending (queued, ETA ~2026-08-26)_ | — | — | — |

**How to read every column**
- **Fixed** = a single natural prompt ("Name: X\nSSN:"). Extracts **0%** everywhere → the model never leaks without optimization.
- **GCG** = optimized `gcg_free` EMR on **trained** targets. The headline number the prior literature would report.
- **Neg-ctrl** = same attack on **never-trained** control records (the forcing floor). **33–52%** — the attack forces records it could not possibly have memorized.
- **Adj** = GCG − Neg-ctrl = the memorization-attributable part. **Small, and every CI crosses 0.**
- **AUC** ≈ 0.5 (CIs cross 0.5) → the continuous score (`−final_target_nll`) barely separates trained from control.
- **p(McN)** tiny → GCG ≫ Fixed, but that gap is **forcing power**, not recall.

### Table B — Probe spectrum (Table 2) · ⚠ PRELIMINARY (from the n=3 pilot, needs re-read from run2)

| Probe | k | EMR(D) | EMR(C) | Adj [CI] | note |
|---|---|---|---|---|---|
| softprompt | −1 | 100 | 100 | +0 [0,0] | forcing UPPER bound — forces everything |
| gcg_anchored | 20 | 100 | 70 | +30 [10,50] | only probe with CI excluding 0 (n=3!) |
| gcg_free | 20 | 83 | 60 | +23 [−13,55] | |
| gcg_fluent | 20 | 67 | 40 | +27 [−5,63] | fluent adversary |
| random_restart | 20 | 0 | 0 | +0 | compute-matched random ≈ 0 → GCG ≠ luck |
| piiscope / piicompass / fixed | 0 | 0 | 0 | +0 | non-optimized query attacks ≈ 0 |

> Action: regenerate this from run2 (`make_tables.py --run-id run2`) — the pilot
> used n=3 and the buggy vocab/field code. The **shape** is expected to hold:
> expressive probes raise EMR(C); Adj stays near 0.

### Provenance / scale of the current run (run2)
- Corpus: 200 trained individuals (freq tiers 20@f1 / 60@f5 / 120@f20) + 800 negative controls; real public passages; format-perturbed. `frequency_groups` orphan bug fixed → all 200 individuals are actually in the corpus.
- Attack: `PII_MAX_TARGETS` per **arm** (25/12/20 trained; controls matched via E17), `GCG_ITERS` 120–200, fields ssn+email, **1 seed (42)**.
- All five run1 bugs fixed: padded-vocab (Pythia), per-model field decode, per-arm target cap, partition wall, submission-loop stdin.

### What the data says (interpretation)
1. **The field's headline metric is inflated.** Reporting "GCG extracts 52–67%" is misleading: 33–52% of that is forcing (proved by never-trained controls).
2. **No reliable memorization signal above the floor**, at any scale — all Adj CIs cross 0, and Adj is **non-monotonic** (0 → +33 → +10).
3. **Optimization ≠ luck**: random-restart at matched budget ≈ 0, so GCG's success is the optimizer, not brute force. But that optimizer forces controls too.
4. **AUC ≈ 0.5** independently confirms the score can't tell trained from control.
5. The **gpt2-medium +33.3** point is the one hint of real memorization; at n=12 with a CI of [−8, 67] it is **not yet trustworthy**.

---

## PART II — THE FRAMING DECISION

### Recommended framing (what the data currently supports): **an auditing / negative-control paper**
> _"Adversarial prompt optimization does not measure memorization — it measures
> the optimizer's capacity to FORCE arbitrary targets. Using negative controls we
> show a widely-used extraction metric overstates memorization by 33–52 points;
> we introduce EMR_adj and a capacity-sweep diagnostic that recover the true,
> and much smaller, memorization-attributable signal."_

This is a strong, defensible USENIX contribution (methodology critique + a fix),
and it does **not** depend on Adj growing with scale. The contributions are:
1. **The forcing phenomenon**, demonstrated with first-class negative controls.
2. **EMR_adj = EMR(D) − EMR(C)** as the memorization-attributable metric.
3. **The capacity sweep (E3)**: the forcing floor α_k rises with free-token budget → any target is forceable given enough capacity.
4. **A probe spectrum** ordering attacks by expressivity, with soft-prompt as the forcing upper bound.
5. **External validity (E10)** and **defense re-analysis (E12)** — see P1.

### Contingency branches (resolved once 2.8b + more power land)
- **B1 (Adj ≈ 0 at all scales, tighter CIs):** clean forcing-audit paper (above). Strongest, simplest story.
- **B2 (Adj reliably > 0 and grows with scale):** "big models do leak, but only negative-control-adjusted rates reveal it; raw metrics conflate." Still centered on EMR_adj.
- **B3 (mid-scale bump like gpt2-medium's +33 survives):** "memorization is real but small and non-monotonic in scale; the raw metric's apparent scale trend is an artifact of forcing." Most nuanced.

Either way, **negative controls + EMR_adj are the contribution** — the framing is robust; only the scale sub-claim flexes.

---

## PART III — REVISION PLAN (prioritized)

### P0 — Complete the core evidence (blocking; finish before writing numbers)
| # | Task | Why | Status / how |
|---|---|---|---|
| P0.1 | **pythia-2.8b E1** | 4th scale point | queued, ETA 2026-08-26 (no action) |
| P0.2 | **Add power: ≥3 seeds (42,123,456) × n≥40/arm** | current CIs (±28–37 pp) can't distinguish Adj from 0 | re-run per-model, `PII_SEEDS=42,123,456`, bump `max_targets` |
| P0.3 | **All 6 fields** (add phone, address, credit_card, name) | ssn+email only now; fields differ in forceability | add to `PII_FIELDS` |
| P0.4 | **E2 base-model placebo** for each model | shows Adj≈0 on an untrained model = design sanity | `--exp E2` |
| P0.5 | **E3 capacity sweep** (α_k vs k) | the signature figure (forcing floor rising with capacity) | `exp_capacity.slurm`, small `PII_CAP_SWEEP_N` for big models |
| P0.6 | **Regenerate all tables from run2** | Table 2 / capacity / freq still show pilot data | `make_tables.py --run-id run2` |

### P1 — Strengthen & external validity (Tier-1 drivers already written)
| # | Task | Kills which objection | Command |
|---|---|---|---|
| P1.1 | **E10 Pythia + the Pile** | "it's an artifact of YOUR synthetic fine-tuning" (W2) — attacks a model+corpus we did not build | `exp_tier1.slurm EXP=E10`, needs `PII_PILE_SHARD` |
| P1.2 | **E7 budget-matched control** | "GCG just uses more queries" — natural prompts at GCG's own budget still ≈0 | `EXP=E7` |
| P1.3 | **E12 defenses at fixed FPR** | "why not just filter?" — perplexity/classifier/honeytoken-tripwire, honest benign-FPR | `EXP=E12` (after E1) |
| P1.4 | **E5 frequency response** | dose–response: does EMR rise with training frequency? intercept = forcing floor | `--exp E5` |

### P2 — Paper writing (section by section; `usenix_paper.tex` already reframed)
1. **Abstract / intro** — lead with the forcing problem; state EMR_adj; give the headline (raw 52–67% vs Adj ≈ 0–33, CIs cross 0). Replace all `\todo` with run2 numbers.
2. **Table 1** — paste run2 Table A once P0 complete (4 models × ≥3 seeds × 6 fields). Report Fixed/GCG/Neg-ctrl/Adj/AUC/TPR/p.
3. **Fig. 1 (capacity)** — α_k vs k from E3 (`capacity_curve.csv`).
4. **Fig. 2 (frequency)** — EMR vs train_frequency from E5; intercept = forcing floor.
5. **Table 2 (probe spectrum)** — from run2; soft-prompt as forcing upper bound.
6. **§ Forcing problem** — formalize EMR_adj; state the negative-control protocol (identical budget/rule for D and C — the key invariant).
7. **§ External validity** — E10 (Pile) results.
8. **§ Defenses** — E12 honest operating points; the honeytoken-tripwire insight (forcing makes canaries a reliable detector).
9. **Related work** — position vs PII-Scope / PII-Compass / GCG / ACR; we AUDIT this line, not extend it. Fix the hallucinated citations flagged earlier (Zou et al., Llama-2 authors).
10. **Limitations** — synthetic corpus (mitigated by E10), single language, white-box, n/power.
11. **Ethics** — auditing framing; no new real-PII leaks beyond public Pile/Enron already public.

### P3 — Original reviewer weaknesses (map each to a fix)
- **W1 (novelty / "just GCG on PII")** → reframed as an audit that overturns the metric; EMR_adj is new.
- **W2 (synthetic data confound)** → format perturbation (done) + **E10 real Pile** + optional Enron.
- **W (unfair baseline)** → unified per-(person,field) metric, identical for all probes (done in `evaluate.py`).
- **W (defenses strawman)** → E12 honest benign-FPR + adaptive (fluent) attack.
- **W (fabricated stats)** → everything now regenerated from logs; delete hallucinated refs.

### Experiment matrix (what to run next, and where)
| Exp | Models | Seeds | Fields | n/arm | Partition | Note |
|---|---|---|---|---|---|---|
| E1 (power-up) | 4 | 42,123,456 | 6 | 40–50 | small→ampere,pascal; big→medium | the main table |
| E2 base | 4 | 42 | 6 | 40 | same | placebo |
| E3 capacity | gpt2, gpt2-medium, 1.4b | 42 | ssn,email | 30 | ampere,pascal | Fig.1 |
| E5 freq | gpt2, 1.4b | 42 | 6 | all tiers | ampere,pascal | Fig.2 |
| E7/E10/E12 | gpt2, 1.4b | 42 | 6 | 30 | per driver | Tier-1 |

Keep each task inside its partition wall via per-model `max_targets`/`iters` in
`slurm/submit_per_model.sh` (already parameterized).

---

## PART IV — RISKS, DECISIONS, TIMELINE

### Risks
- **Scheduling / fair-share** is the real bottleneck (not compute). Mitigations in place: pascalnodes(P100) for small jobs, per-model right-sized walltimes, afterany finalize, skip-train on cached checkpoints. Big models on the 48h medium queue just wait.
- **Underpowering**: n=12–25, 1 seed → CIs too wide to conclude. P0.2/P0.3 fix this.
- **gpt2-medium anomaly**: the +33.3 may be noise; more seeds/n will confirm or dissolve it. Do not build the story on it until it survives P0.
- **Compute-node internet** for E10 needs a local Pile shard (`PII_PILE_SHARD`) or the offline smoke; login node has internet.

### Decision points (resolve after P0)
1. Which framing branch (B1/B2/B3)? — decided by the 4-model × 3-seed Adj CIs.
2. Keep or drop soft-prompt in the main paper? (99–100% = pure forcing; use it only as the labeled upper bound.)
3. Include Enron real-PII in addition to Pile? (only if reviewers still push on W2.)

### Suggested order / timeline
1. **Now:** wait for pythia-2.8b (P0.1). Regenerate run2 tables (P0.6).
2. **Next batch (run3):** E1 power-up — 4 models × 3 seeds × 6 fields, per-model scope. This is the paper's Table 1.
3. **Parallel:** E3 capacity (Fig.1), E2 placebo.
4. **Then:** E5 (Fig.2), E7/E10/E12 (Tier-1).
5. **Write:** fill `usenix_paper.tex` `\todo`s from the regenerated tables; finalize framing per the 4-model result.

### One-liners to regenerate / launch
```bash
# regenerate every table from the current logs
python make_tables.py --run-id run2

# power-up main table (run3): 4 models × 3 seeds × 6 fields
PII_RUN_ID=run3 PII_SEEDS=42,123,456 PII_FIELDS_SWEEP=ssn,email,phone,address,credit_card,name \
  bash slurm/submit_per_model.sh      # per-model max_targets/iters set in the script's spec
```
