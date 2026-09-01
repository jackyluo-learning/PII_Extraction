# Research Agenda — Calibrating Optimization-Based Memorization Audits

## Statement

When an optimizer succeeds in making a language model emit a PII record verbatim, that is consistent
with two very different worlds: the model memorized the record, or the optimizer is simply expressive
enough to force an arbitrary target out of it. This lab exists to determine under what conditions
those two can be told apart, with what instrument, and — where they cannot — what an audit should
report instead.

The core instrument is the **never-trained negative control**: attack it under an identical
optimizer, budget, and decision rule, and the resulting success rate is the attack method's own
**forcing floor** `α_k`. The calibrated signal is `τ̂rec = EMR(D) − EMR(C)`, which is simultaneously
the advantage of the induced membership distinguisher and the average treatment effect of corpus
inclusion.

## Driving questions

1. **The identifiability boundary.** Under what conditions may a successful optimization be read as
   "the model retained this record"? Proposition 2 proves non-identifiability when
   `H∞(D₀) ≤ k·log₂|V|` — where does that boundary actually sit?
2. **Capacity versus floor.** How does `α_k` respond to probe capacity `k`? Is there an operating
   point `k⋆` whose floor is low enough to retain dynamic range? What steering rate `β`
   (bits per prompt token) does the model actually realize?
3. **Measurability of the signal.** How many seeds, fields, and models are needed before `τ̂rec` can
   be distinguished from zero? The current 4 models × single seed × 2 fields yields confidence
   intervals that all straddle zero.
4. **Efficacy of the defenses.** At a fixed benign false-positive rate, what detection rate do
   capacity limiting and forcing honeytokens achieve? How much does perplexity filtering retain
   against an adaptive adversary?

## Claims the lab wants to be able to make

- The forcing floor is **large and measurable**, and rises **monotonically** with probe expressivity
  (from 0% for fixed prompts to 100% for an unconstrained soft prompt)
- A raw extraction rate **is not a privacy measurement** — without a floor, no `ε` lower bound follows
- The `(rate, floor)` pair, together with `TPR@α` and `ε̂`, should become the **minimum publishable
  standard** for this class of audit
- Auditing at a measured `k⋆` restores the dynamic range that a high floor destroys

## Scope

- **Data**: a controlled synthetic corpus (Faker-generated fictitious PII embedded in nine document
  templates, mixed into public-domain passages from Wikipedia / PG-19 / arXiv) with complete ground
  truth
- **Models**: self-fine-tuned open models — GPT-2 124M / 355M (full fine-tune), Pythia 1.4B / 2.8B
  (LoRA)
- **Setting**: white-box, **confirmation audit** (the auditor holds the target record)
- **Fields**: high-entropy PII, currently SSN and email, extensible to phone / credit_card / address
- **Probes**: eight points along the capacity axis, from a fixed prompt to an unconstrained soft
  prompt

## Explicit non-goals

- **Not a stronger attack.** The contribution is measurement validity, not attack capability. A
  stronger optimizer only raises the floor, which tightens rather than loosens the constraint on
  what counts as an informative audit.
- **Not a re-audit of any specific published result.** The claim concerns the *class* of
  optimization-based extraction rates.
- **Not discovery attacks** (unknown targets). Different setting, different metrics.
- **No production APIs.** Only models we fine-tune ourselves from open weights.
- **The IEEE IRI 2026 paper** (`IRI_paper.tex` / `IRI_outline.md`) **is out of scope** — a separate
  second paper whose claims are not merged with these.

## What answers would change

This is the test of whether the agenda is worth running at all:

- **If the floor is high and rises with capacity** — the extraction rates that compliance teams act
  on need recomputing, and the probe's `k` must be chosen deliberately rather than inherited from
  jailbreaking's 20. That changes audit practice directly.
- **If the floor is low** — existing audits are broadly sound and this work reduces to a
  methodological footnote. That outcome is **an equally complete study** and gets a lab-notebook
  entry of the same standing.

## Publication target

**IEEE SaTML 2027** (5th edition, early May 2027, Reykjavik, Iceland).

### Schedule (all AoE / UTC−12)

| Milestone | Date |
|---|---|
| Abstract registration | **2026-09-22** |
| **Paper submission** | **2026-09-29** |
| Early reject notification | 2026-11-04 |
| Interactive discussion | 2026-11-25 → 2026-12-09 |
| Decision notification | 2026-12-16 |
| **Revision deadline** | **2027-01-21** |
| Camera-ready | mid-Feb 2027 (TBC) |

**The load-bearing date is not 09-29 but the revision round.** Notification 12-16 → revision 01-21
is roughly five weeks, on top of the 11-25 → 12-09 interactive discussion. So the September
submission **need not be complete** — it needs to be strong enough to survive the 11-04 early
rejection, with the remaining experiments added during the revision window against what reviewers
actually asked for, rather than guessed at now.

**Working backwards from the September window**: writing plus the USENIX→IEEE format conversion take
roughly the last 5 days ⇒ experiments must land by **09-24** ⇒ net of the design and protocol
stages, about **20 days** of compute.

### Why this venue

The contribution is **measurement validity**, not a system or an attack. SaTML's readership studies
secure and trustworthy ML and will recognize what the forcing floor is for; in a systems-leaning
review pool, "we do not propose a stronger attack" is easily misread as a lack of contribution.

**Two consequences to handle**:

1. **Format** — the draft is in USENIX format and must move to **IEEE two-column**. `IRI_paper.tex`
   is already IEEE, so the template can be reused.
2. **Length** — an IEEE page limit will squeeze the theory-to-experiment ratio. The draft is
   theory-heavy (Prop. 1–5, Cor. 1–5, Algorithm 1) and evidence-light (E1 only); the conversion will
   make that imbalance more visible. Either add experiments or move some formalism to an appendix.

Evidence bar: multiple seeds (floor 3), a measured `α_k` curve from a capacity sweep, and at least
one piece of external-validity evidence. run2 (4 models × **single seed** × 2 fields × n=12–25) does
not meet it; the gaps are recorded in `CODE_MAP.md` §3 and §8.

> Unconfirmed: SaTML's page limit — not listed on the site; check the CFP before submitting.

## Current anchors

- Authoritative draft: `~/Documents/Phd/UAB/Research/usenix_PromptExtraction_PrivacyAuditing.pdf`
  (the repo's `usenix_paper.tex` is a stale scaffold)
- Code and experiment status: `CODE_MAP.md`
- Existing results: E1 only (run2), producing the paper's Table 4 / Table 5 / Figure 2 / Figure 3
