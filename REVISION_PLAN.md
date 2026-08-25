# PII Extraction Paper — Final Data & Write-Up Plan
_Last updated: 2026-08-25 · target: USENIX Security (measurement/audit paper) · thesis: **Forcing vs. Memorization**_

**Constraint: no more experiments will be run.** The paper must be written from
the data already in hand (run2). The only remaining "compute" is free: (a) let
pythia-2.8b's queued E1 finish (~2026-08-26), and (b) regenerate tables with
`make_tables.py` (CPU, seconds). Everything else below is **writing**.

This plan therefore: (I) fixes the final result set, (II) states exactly which
claims the data supports (and which it does NOT), (III) gives a section-by-section
write-up with the honest numbers, and (IV) frames scope/power as limitations +
future work so reviewers see them as bounded, not as holes.

---

## PART I — THE FINAL DATA (what we have, and only this)

**Have (run2, E1, seed 42, fields = ssn + email, all 8 probes):**
- Table 1 (main forcing-vs-memorization), 3 models now + pythia-2.8b when it lands.
- Table 2 (probe spectrum, 8 probes incl. soft-prompt upper bound & random-restart control).
- E9 continuous-score audit (AUC / TPR@FPR) — inside Table 1.
- Substring-inflation guard, rank-inversion (E16) — from the same log.

**Do NOT have (not run — becomes Future Work):** E3 capacity sweep (Fig.1), E5
frequency response (Fig.2), E7 budget-matched, E10 Pile external validity, E12
defenses. Their `make_tables` sections will print "(no rows)" — that's expected.

### Table 1 — main result (E1, `gcg_free`, seed 42, ssn+email)
| Model | Params | Fixed | GCG | Neg-ctrl (forcing floor) | **Adj [95% CI]** | AUC | n_trained |
|---|---|---|---|---|---|---|---|
| gpt2 | 124M | 0.0 | 52.0 | 52.0 | **+0.0 [−28, 28]** | 0.51 | 25 |
| gpt2-medium | 355M | 0.0 | 66.7 | 33.3 | **+33.3 [−8, 67]** | 0.57 | 12 |
| pythia-1.4b | 1.4B | 0.0 | 60.0 | 50.0 | **+10.0 [−20, 40]** | 0.45 | 20 |
| pythia-2.8b | 2.8B | _fill when it lands_ |||||

> First action once 2.8b lands: `python make_tables.py --run-id run2` and paste
> the refreshed `table1_main.txt` / `table2_probe_spectrum.txt` here.

---

## PART II — CLAIMS THE DATA SUPPORTS (and the ones it does not)

Write ONLY the robust claims as findings; write the rest as bounded observations.

### ✅ Robust (hold even at this sample size) — these are the paper
1. **Without optimization there is no leakage.** Fixed / PII-Compass / PII-Scope ≈ **0%** on trained targets. (natural prompting fails)
2. **Optimization forces never-trained records.** `gcg_free` extracts **33–52%** of negative controls the model provably never saw — the *forcing floor*.
3. **It is optimization, not brute luck.** Random-restart at matched query budget ≈ **0%**, yet GCG succeeds ⇒ the gradient search, not the budget, drives it.
4. **Soft-prompt = forcing upper bound.** ~**100%** on both trained and control ⇒ an unconstrained continuous prefix forces anything.
5. **The raw extraction metric is inflated.** Reporting "GCG extracts 52–67%" overstates memorization by the forcing floor; the memorization-attributable rate is **EMR_adj = EMR(D) − EMR(C)**.

### ⚠️ Bounded / honest-null (state with CIs, do NOT overclaim)
6. **EMR_adj is small and, at our n, not statistically distinguishable from zero** for gpt2 (+0) and pythia-1.4b (+10, CI[−20,40]); gpt2-medium shows +33 (CI[−8,67]) — suggestive but underpowered.
7. **The continuous score barely separates trained from control** (AUC ≈ 0.45–0.57, CIs cross 0.5).

### ❌ Do NOT claim (data can't support it — say so in Limitations)
- No claim about **memorization scaling with model size** (non-monotonic, all CIs cross 0, n small).
- No **per-field** characterization (only ssn + email).
- No **variance across seeds** (single seed).
- No capacity/frequency dose–response figures (E3/E5 not run).

---

## PART III — WRITE-UP PLAN (section by section, with the honest numbers)

Paper skeleton already reframed in `usenix_paper.tex`. Fill `\todo`s from run2.

1. **Title / Abstract.** Lead with the audit result, not scale.
   > "We show that a widely-used class of adversarial PII-extraction attacks
   > conflates memorization with *forcing*. Using never-trained negative controls
   > we find 33–52% of 'extractions' are forced from records the model never saw;
   > the memorization-attributable rate (EMR_adj) is small and often
   > indistinguishable from zero. We argue extraction audits must report EMR_adj."
2. **Introduction.** Motivate with the inflated raw metric; state the 5 robust findings; define EMR_adj; be explicit this is a **measurement/audit** contribution.
3. **§ The Forcing Problem (core).** Formal EMR_adj; the negative-control protocol and its **one invariant**: identical budget + early-stop + decision rule for D and C (this is what makes the comparison valid — foreground it).
4. **Table 1.** The 3–4 model table above. Report Fixed / GCG / Neg-ctrl / **Adj[CI]** / AUC. Emphasize Neg-ctrl and Adj, not GCG.
5. **Table 2 (probe spectrum).** Order by expressivity; soft-prompt as labeled forcing upper bound, random-restart as the compute-matched null. The trend "more expressive ⇒ higher EMR(C), Adj→0" is the argument.
6. **§ Continuous-score audit (E9).** AUC ≈ 0.5 ⇒ the score isn't a membership signal. Include the substring-guard + rank-inversion as robustness (control targets scoring ≥ trained).
7. **Related work.** Position as an **audit** of the GCG / PII-Scope / PII-Compass / ACR line, not an extension. Delete the hallucinated citations (Zou et al. mis-attributed; bogus Llama-2 authors) — verify every reference.
8. **§ Limitations (make it a strength).** State plainly: single seed, two fields, modest n ⇒ EMR_adj CIs are wide; we therefore report EMR_adj as an **upper-bounded, often-null** quantity rather than a point estimate, which is *sufficient for the audit claim* (the finding is that raw rates overstate, and controls are necessary — not a precise memorization measurement).
9. **§ Future work.** The already-built-but-unrun machinery: capacity sweep (E3), frequency dose–response (E5), Pile external validity (E10), budget-matched control (E7), defenses at fixed FPR (E12). Frame as "our released harness supports these; we leave large-scale characterization to future work." (Honest, and shows the work is extensible.)
10. **Ethics / availability.** Auditing framing; synthetic + public data; release code + the per-attempt log schema.

---

## PART IV — CHECKLIST (all writing/CPU; no GPU, no scheduling)

- [ ] **Wait for pythia-2.8b** (adds a 4th Table-1 row; if it never schedules, ship 3 models and say so).
- [ ] `python make_tables.py --run-id run2` → refresh `table1_main.txt`, `table2_probe_spectrum.txt`, `substring_guard.txt`, `rank_inversion_e16.txt`. Paste refreshed tables into the paper.
- [ ] Fill every `\todo` in `usenix_paper.tex` with run2 numbers (Parts I above).
- [ ] Rewrite Abstract/Intro to the audit framing (Part III.1–2).
- [ ] Tables 1 & 2 with **Neg-ctrl + Adj[CI]** foregrounded.
- [ ] Limitations §: single-seed / 2-field / small-n stated as bounded; EMR_adj as upper-bound/null.
- [ ] Future-work §: E3/E5/E7/E10/E12 as extensions (harness released).
- [ ] Verify/repair every citation; remove fabricated ones.
- [ ] Ethics + artifact-availability (code + log schema public on GitHub).

---

## HONEST ASSESSMENT (read this before deciding the venue)

With **1 seed, 2 fields, n=12–25, 3–4 models**, the *message* is sharp and
genuinely useful (negative controls overturn a headline metric), but the
*empirical breadth* is thin for a full USENIX paper — reviewers will flag power
and scope. Two realistic options:

- **A — full paper, tightly scoped as a "cautionary measurement".** Lean 100% on
  the 5 robust claims; present EMR_adj as the methodological contribution; be
  disarmingly honest in Limitations. Highest risk/reward.
- **B — workshop / short paper now, full version later.** Ship the audit result
  and released harness at a workshop; run E3/E5/E10 + more seeds afterward for the
  full venue. Lower risk, keeps the finding timely.

Recommendation: **write it as A** (the framing above is built for it) and submit;
the finding stands on the robust claims alone, and the Limitations/Future-work
sections convert the scope gap into an honest, bounded statement rather than a
hole. If a reviewer demands breadth, the released harness makes the rebuttal
experiments a known, small amount of work.
