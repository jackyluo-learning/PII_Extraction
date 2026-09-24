# Independent Results Audit — GPT-2 base-model follow-up

An independent statistics review read the six formal parquets and the frozen
pairing file directly, without invoking `analyze_e3b_base_followup.py`. It
confirmed 600 unique attempts and the four cell counts: fine-tuned D 122/150,
fine-tuned C 116/150, base D 79/150, and base C 86/150.

With 25 matched person pairs as bootstrap clusters, keeping both fields and
all three attack seeds together, an independent 100,000-replicate bootstrap
gave `Delta_A3 = +20.0 pp [13.3, 26.7]`, `tau_rec = +4.0 pp [-6.7, 14.0]`,
`tau_mod = +28.7 pp [20.0, 37.3]`, and `tau_base = -4.7 pp [-11.3, 2.0]`.
The main 10,000-replicate analysis differs only by one discrete bootstrap
step in the lower `tau_mod` endpoint (`20.7` rather than `20.0` pp).
The arithmetic identity `tau_mod - tau_rec = Delta_A3 - tau_base = 24.7 pp`
was independently verified; its clustered interval is `[16.7, 32.7]` pp.

**Audit conclusion:** numeric results pass. Interpretation must remain
descriptive. Three attack seeds share one checkpoint and the same 25 matched
people; the base checkpoint is not a leave-one-out counterfactual. The
four-cell order does not prove the causal sandwich, A3 as a general law, or
a differential-privacy parameter. Fine-tuned email success is 75/75 in both
arms, causing a ceiling effect. The field split is exploratory.
