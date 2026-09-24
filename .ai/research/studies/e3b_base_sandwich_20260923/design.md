# Frozen-target GPT-2 base-model follow-up

This prospective follow-up fills the base-model row of the E3b 2-by-2
trained/control design at `k=20`. It is a single-checkpoint diagnostic, not a
leave-one-out causal experiment or the archived four-model E2 study. The full
execution contract, pins, predictions, and cost gate are in
[`../capacity_axis_20260902/e3b_base_followup_plan.md`](../capacity_axis_20260902/e3b_base_followup_plan.md).

Primary prediction, recorded before the pilot: the fine-tuned control success
rate will be at least the original GPT-2 base control success rate at `k=20`.
A null or negative difference is a valid outcome. We will report all four cell
rates and person-clustered uncertainty without claiming that their ordering
identifies a per-record causal effect or a DP parameter. Attack seeds repeat
optimization against the same model and people; they are not independent
training replicates.
