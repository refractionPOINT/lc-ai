---
name: detection-rules
description: "Create, edit, validate, test and deploy D&R automation and false-positive rules with the correct event target."
---

# Detection and response rules

First choose the evaluation surface: ordinary telemetry/automation D&R, email verdict (`dr-mail`), or cloud posture (`cloudsec_policy`). Load email-security or cloud-security for those specialized rules; shared detect syntax does not imply shared envelopes, paths, operators or response actions.

For ordinary D&R, establish rule namespace and target. The default target is `edr`; alternate targets include detection, deployment, artifact, artifact_event, schedule, audit and billing. Their event structure and permitted actions differ. A detection-target event name is the originating report name. Inspect a real representative event and schema, then read the relevant operator and action documentation. Match the correct field level (`event/`, `routing/`, or target-specific root). Use `scope` when conditions must match one array element. Verify string case, regex fields and missing-field behavior against the operator reference.

External rule conversion through `dr convert-rules` must use dry-run; deploy converted candidates individually through the artifact workflow. Author the smallest rule meeting the request. AI generation is an optional drafting helper; generated content needs the same validation. Preserve enabled status, namespace and unrelated metadata when editing. Check existing rules for overlapping matches and avoid response loops, especially rules responding to detections or audit events they create. Bound repeated responses using documented suppression/stateful mechanisms.

Build one full Hive envelope before validation: `data` contains `detect`, `respond` and other rule fields; `usr_mtd` includes an explicit boolean `enabled` and the intended metadata. For an existing rule, first read the same namespace/key, preserve every existing metadata field unless deliberately changing it, and copy `sys_mtd.etag` into the candidate's top-level `etag` for compare-and-swap protection. A concurrent change requires a fresh read and reconciliation, not an unconditional overwrite. A new rule still needs explicit enabled state. Bare detect/respond objects can be tested, but cannot complete deployment.

Execute the artifact workflow through `lc_prepare` and `lc_execute`, not raw CLI validation or writes. Keep the same `artifact_path`, `resource_key`, `namespace` and organization for all steps:

1. `validate` compiles the candidate's components through the installed CLI. Require the harness's passing result; validator response shapes vary by CLI/API version, so do not assume a `success: true` field or infer validity solely from process exit.
2. `test-positive` uses a separate `events_path` containing a nonempty JSON array of representative matching events.
3. `test-negative` uses another nonempty JSON array representing a likely false positive that must not match. Inspect errors and observed matching behavior; compilation alone does not establish intent.
4. `preview` compares the complete candidate against the current resource and checks explicit metadata and the existing record's etag.
5. `apply` writes the exact candidate only after the prior gates pass.
6. `verify` reads the same resource back and checks the applied data and metadata.

Each preparation returns a token and exact argv; pass both to execution. Editing any candidate bytes, including metadata or etag, invalidates earlier validation and tests. Restart those steps after a change. The harness handles component extraction internally; do not separately manufacture component files for deployment.

If historical replay is appropriate, set an explicit time/sensor scope, inspect its estimate or limits where available, and track the returned job to completion. Historical volume is not an exact future cost forecast.

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
- `8-reference/schedule-events.md`
