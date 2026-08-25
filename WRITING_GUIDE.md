# How to Write the Paper — Section Guide with the Real Numbers
_Companion to REVISION_PLAN.md. Every number here is from run2 (final). Draft
sentences are starting points — adapt the wording, keep the numbers._

Framing (decided): a **cautionary measurement / negative-control audit**. Thesis:
*adversarial prompt optimization conflates memorization recall with the
optimizer's ability to FORCE arbitrary targets; negative controls reveal the raw
extraction metric is inflated, and the memorization-attributable rate EMR_adj is
small.*

---

## THE NUMBERS (transcribe these)

### Table 1 — main (E1, `gcg_free`, seed 42, fields ssn+email)
| Model | Params | Fixed | GCG (EMR D) | Neg-ctrl (EMR C) | EMR_adj [95% CI] | AUC [CI] | p(McNemar) | n |
|---|---|---|---|---|---|---|---|---|
| GPT-2 | 124M | 0.0 | 52.0 | 52.0 | +0.0 [−28.0, 28.0] | 0.51 [0.34, 0.67] | 2e-4 | 25 |
| GPT-2-medium | 355M | 0.0 | 66.7 | 33.3 | +33.3 [−8.3, 66.7] | 0.57 [0.31, 0.81] | 8e-3 | 12 |
| Pythia-1.4B | 1.4B | 0.0 | 60.0 | 50.0 | +10.0 [−20.0, 40.0] | 0.45 [0.27, 0.64] | 5e-4 | 20 |
| Pythia-2.8B | 2.8B | 0.0 | 16.7 | 0.0 | +16.7 [0.0, 41.7] | 0.47 [0.24, 0.71] | 0.50 | 12 |

### Table 2 — probe spectrum (pooled over models, n=53), ordered by expressivity
| Probe | free-k | EMR(D) | EMR(C) | EMR_adj [95% CI] |
|---|---|---|---|---|
| Soft-prompt (upper bound) | −1 | 100.0 | 100.0 | +0.0 [0.0, 0.0] |
| GCG-fluent | 20 | 39.1 | 42.0 | −2.9 [−19.2, 13.6] |
| GCG-free | 20 | 50.7 | 39.1 | +11.6 [−5.8, 28.8] |
| GCG-anchored | 20 | 71.0 | 62.3 | +8.7 [−7.6, 25.7] |
| Random-restart (matched budget) | 20 | 0.0 | 0.0 | +0.0 |
| PII-Scope | 0 | 0.0 | 0.0 | +0.0 |
| PII-Compass | 0 | 0.0 | 0.0 | +0.0 |
| Fixed prompt | 0 | 0.0 | 0.0 | +0.0 |

**The one-sentence takeaway of Table 2:** as the probe gets more expressive
(fixed → GCG → soft-prompt), EMR(control) climbs from 0 to 100 while EMR_adj stays
near 0 — i.e. the added "success" is forcing, not recall.

---

## ABSTRACT — draft (edit freely)
> Fine-tuned language models can memorize personal data, and adversarial prompt
> optimization (e.g., GCG) has become the standard way to audit this leakage. We
> show this methodology conflates two phenomena: genuine memorization recall, and
> the optimizer's ability to **force** an arbitrary target out of a model
> irrespective of training. Introducing never-trained **negative-control**
> records, we find optimization attacks extract 39–62% of records the model has
> provably never seen — a *forcing floor* nearly as high as their success on
> trained records — while non-optimized prompting and a compute-matched random
> search extract 0%, and an unconstrained soft prompt forces 100% of both trained
> and control records. Consequently the memorization-attributable rate,
> **EMR_adj = EMR(trained) − EMR(control)**, is modest and, at our sample size,
> not statistically significant (95% CIs include zero) across four models
> (124M–2.8B). We argue extraction audits must report EMR_adj against negative
> controls rather than raw extraction rate, and release a harness and per-attempt
> log that do so.

## INTRODUCTION — what to say (4 moves)
1. **Setup:** LLMs fine-tuned on user data leak PII; optimization attacks (GCG,
   PII-Scope, PII-Compass, soft-prompt, ACR) are the auditing tool of record.
2. **The problem (your hook):** these attacks are evaluated only on *trained*
   targets, so a high extraction rate is read as high memorization — but an
   optimizer expressive enough can *force* a target the model never saw. No prior
   audit measures this.
3. **What you do:** add never-trained negative controls run under an *identical*
   budget/decision rule; define EMR_adj; sweep a probe spectrum from fixed prompts
   to a soft-prompt forcing upper bound.
4. **Findings (list the 5 robust ones, with numbers):**
   - Without optimization there is no leakage: fixed / PII-Scope / PII-Compass = **0%**.
   - Optimization forces never-trained records: GCG extracts **39–62%** of controls.
   - It is optimization, not luck: matched-budget random search = **0%**.
   - Soft-prompt = **100%** on trained *and* control → forcing upper bound.
   - Therefore EMR_adj is small (**0–33 pts, all CIs cross 0**); the raw metric overstates memorization by the forcing floor.
   State the contribution: **EMR_adj + the negative-control protocol + the probe spectrum**, plus a released harness.

## § THE FORCING PROBLEM (core method) — what to say
- Define EMR(D), EMR(C), and **EMR_adj = EMR(D) − EMR(C)**.
- State the **one invariant** that makes it valid: controls run with byte-identical
  budget, early-stopping, and the exact-match decision rule as trained targets.
  (This is the methodological heart — foreground it; a reviewer's first attack is
  "you gave controls a weaker attack." You didn't.)
- Explain the probe spectrum idea: expressivity increases forcing capacity; soft-
  prompt (unconstrained continuous prefix) is the upper bound.

## § RESULTS — what to say
- **Table 1 (per model):** for each model, EMR(D) is large but so is EMR(C); EMR_adj
  is small with a CI that includes zero. Read GPT-2 as the clean case (52 vs 52,
  Adj=+0). *Do NOT compare EMR_adj across models numerically* (see Limitations —
  the per-model iteration budgets differ), and make no scaling claim.
- **Table 2 (probe spectrum, the centerpiece):** walk fixed(0/0) → GCG(≈50/40) →
  soft-prompt(100/100). EMR(C) rises with expressivity; EMR_adj stays ≈0. Note the
  striking GCG-fluent row: EMR_adj = **−2.9** (the evasive adversary forces controls
  *more* than trained). Random-restart at matched budget = 0 rules out brute force.
- **Continuous-score audit (E9):** AUC ≈ 0.45–0.57 (CIs cross 0.5) → even the soft
  score `−NLL(target)` does not separate trained from control. Add the substring-
  guard (matches aren't spurious) and rank-inversion (control targets scoring below
  trained ones) as robustness.

## § LIMITATIONS — draft (turn scope into a bounded, honest statement)
> Our study is deliberately narrow in scope. We evaluate a single random seed, two
> PII field types (SSN and email), and 12–25 targets per arm per model, so the
> EMR_adj confidence intervals are wide and we report EMR_adj as an upper-bounded,
> often-null quantity rather than a precise memorization estimate — which is
> sufficient for our claim that raw extraction rates overstate memorization and
> that negative controls are necessary. Because per-model attack budgets differ,
> EMR_adj is **not** comparable across model sizes and we make no scaling claim; in
> particular Pythia-2.8B's low raw rate (16.7%) reflects an under-powered attack,
> not reduced memorization. All data are synthetic PII in a fine-tuning corpus we
> constructed; whether the same forcing floor appears for organically memorized
> data in a pretraining corpus is left to future work.

## § FUTURE WORK — draft (shows the finding is extensible; harness released)
> Our released harness already implements, but this paper does not report at scale:
> a **capacity sweep** (EMR(control) vs. free-token budget k, quantifying the
> forcing floor's growth), a **frequency dose–response** (EMR vs. training
> frequency, whose intercept is the forcing floor), a **budget-matched natural-
> prompt** control, an **external-validity** replication on Pythia and the Pile
> (attacking a model and corpus we did not construct), and a **defense** evaluation
> at fixed benign false-positive rates including a honeytoken tripwire that
> exploits forcing's target-agnosticism. Scaling EMR_adj to more seeds, fields, and
> models to tighten its confidence intervals is the natural next step.

## RELATED WORK — reminders
- Position as an **audit** of the GCG / PII-Scope / PII-Compass / ACR / soft-prompt
  line, not an extension.
- **Verify every citation** — the earlier draft mis-attributed GCG (Zou et al.) and
  had fabricated Llama-2 author lists. Delete/fix them.

---

## READY-TO-PASTE LaTeX (adjust column types / caption to your style)

```latex
\begin{table}[t]\centering\small
\caption{Forcing vs.\ memorization on the confirmation probe (\texttt{gcg\_free}).
EMR(D)=trained, EMR(C)=never-trained control; EMR$_{\text{adj}}$=EMR(D)$-$EMR(C).
A large EMR(C) with small EMR$_{\text{adj}}$ means the attack \emph{forces} rather
than recalls. 95\% person-clustered bootstrap CIs. Per-model attack budgets differ;
EMR$_{\text{adj}}$ is not comparable across rows.}
\label{tab:main}
\begin{tabular}{lrrrrrr}
\toprule
Model & Params & Fixed & GCG & Neg-ctrl & EMR$_{\text{adj}}$ [95\% CI] & AUC \\
\midrule
GPT-2        & 124M & 0.0 & 52.0 & 52.0 & $+0.0$ \,[$-28.0,28.0$] & 0.51 \\
GPT-2-medium & 355M & 0.0 & 66.7 & 33.3 & $+33.3$ [$-8.3,66.7$]   & 0.57 \\
Pythia-1.4B  & 1.4B & 0.0 & 60.0 & 50.0 & $+10.0$ [$-20.0,40.0$]  & 0.45 \\
Pythia-2.8B  & 2.8B & 0.0 & 16.7 & 0.0  & $+16.7$ [$0.0,41.7$]    & 0.47 \\
\bottomrule
\end{tabular}
\end{table}
```

```latex
\begin{table}[t]\centering\small
\caption{Probe spectrum ordered by expressivity (pooled, $n{=}53$). As the probe
gets more expressive, EMR(control) rises toward 100\% while EMR$_{\text{adj}}$ stays
near zero: the added success is \emph{forcing}, not recall. Soft-prompt is the
forcing upper bound; random-restart is a compute-matched null.}
\label{tab:spectrum}
\begin{tabular}{lrrr}
\toprule
Probe & EMR(D) & EMR(C) & EMR$_{\text{adj}}$ [95\% CI] \\
\midrule
Soft-prompt (upper bnd) & 100.0 & 100.0 & $+0.0$ \\
GCG-fluent      & 39.1 & 42.0 & $-2.9$ [$-19.2,13.6$] \\
GCG-free        & 50.7 & 39.1 & $+11.6$ [$-5.8,28.8$] \\
GCG-anchored    & 71.0 & 62.3 & $+8.7$ [$-7.6,25.7$] \\
Random-restart  & 0.0  & 0.0  & $+0.0$ \\
PII-Scope       & 0.0  & 0.0  & $+0.0$ \\
PII-Compass     & 0.0  & 0.0  & $+0.0$ \\
Fixed prompt    & 0.0  & 0.0  & $+0.0$ \\
\bottomrule
\end{tabular}
\end{table}
```

---

## WRITING ORDER (fastest path to a full draft)
1. Tables 1 & 2 (paste LaTeX above) — anchors everything.
2. § Forcing Problem (method + the one invariant).
3. § Results (narrate the two tables + E9 audit).
4. Introduction (the 4 moves; pull findings from Results).
5. Abstract (compress the intro).
6. Limitations + Future work (drafts above).
7. Related work + fix citations.
8. Ethics + artifact availability (code + log schema on GitHub).
```
