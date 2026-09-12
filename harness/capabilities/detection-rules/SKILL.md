---
name: detection-rules
description: "Create, edit, validate, test and deploy D&R automation and false-positive rules with the correct event target."
---

# Detection and response rules

First choose the evaluation surface: ordinary telemetry/automation D&R, email verdict (`dr-mail`), or cloud posture (`cloudsec_policy`). Load email-security or cloud-security for those specialized rules; shared detect syntax does not imply shared envelopes, paths, operators or response actions.

For ordinary D&R, establish rule namespace and target. The default target is `edr`; alternate targets include detection, deployment, artifact, artifact_event, schedule, audit and billing. Their event structure and permitted actions differ. A detection-target event name is the originating report name. Inspect a real representative event and schema, then read the relevant operator and action documentation. Match the correct field level (`event/`, `routing/`, or target-specific root). Use `scope` when conditions must match one array element. Verify string case, regex fields and missing-field behavior against the operator reference.

Author the smallest rule meeting the request. AI generation is an optional drafting helper; generated content needs the same validation. Preserve enabled status, namespace and unrelated metadata when editing. Check existing rules for overlapping matches and avoid response loops, especially rules responding to detections or audit events they create. Bound repeated responses using documented suppression/stateful mechanisms.

Before deploying, save separate detect and respond artifacts and run `dr validate`; require an affirmative valid result, not merely a zero process exit. Run `dr test` on the full candidate with separate positive and negative fixture events (including a likely false positive). Check returned errors and expected responses. Validation checks compilation, not intent. If replay is appropriate, set an explicit time/sensor scope, inspect its estimate or limits where available, and track the returned job to completion; historical volume is not an exact future cost forecast.

Deploy the exact tested artifact, then read it back from the same namespace and check enabled state. Changes after testing invalidate previous test evidence. Distinguish saved, enabled, evaluated and observed firing. When no safe live trigger exists, say the deployment is verified but live firing has not been observed. FP suppressions need narrow predicates and a negative control showing unrelated detections survive.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `3-detection-response/index.md`
- `3-detection-response/alternate-targets.md`
- `3-detection-response/tutorials/dr-rule-building-guidebook.md`
- `3-detection-response/unit-tests.md`
- `8-reference/detection-logic-operators.md`
- `8-reference/response-actions.md`
- `3-detection-response/false-positives.md`
