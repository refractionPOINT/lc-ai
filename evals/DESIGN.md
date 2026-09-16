# Coverage and expansion

The initial loop is proved. Extend coverage with independently verifiable workflows, using [Adding evals](ADDING_EVALS.md) as the implementation guide and [catalog/capabilities.yaml](catalog/capabilities.yaml) as the inventory. The [original design](history/DESIGN.md) retains the wider rationale.

## What counts as coverage

Coverage means an agent can accomplish a specified LimaCharlie operation and the evaluator can independently prove its outcome, scope and cleanup. A CLI invocation or successful fixture setup alone is not an agent eval. Supply security criteria explicitly: which findings to export, which events should match, and which actions are authorized.

Current live coverage is narrow: Hive data/metadata preservation, complete search export with observed pagination, and hosted webhook ingestion plus D&R/output routing. Organization/key creation supports fixtures; it does not establish agent-driven tenant administration. A hosted JSON sensor does not establish native endpoint enrollment.

## Expansion candidates

| Family | Example bounded task | Required independent evidence |
|---|---|---|
| Tenant and access administration | Create a specified scoped identity or configuration | Exact permissions/state, denied out-of-scope behavior, revocation |
| Native endpoint onboarding | Enroll a disposable endpoint and apply specified tags | Real enrollment, exact target state, endpoint and org cleanup |
| Cloud Security | Export findings matching supplied criteria | Real finding fixture, complete membership/fields, preserved unrelated state |
| Cases and investigations | Create/update a case from supplied records | Exact fields, associations and preserved unrelated cases |
| Integrations and outputs | Connect a supported destination with a specified filter | Actual delivery plus excluded-event controls |
| Configuration management | Reconcile a requested subset of configuration | Semantic diff, preservation, repeat behavior and cleanup |

Choose one bounded vertical slice at a time. Establish feasible provisioning, entitlements, independent observations and teardown before model trials. Add a correct reference and a plausible incorrect reference that fails a named assertion. Expand broker permissions only as required by the task.

## Experimental discipline

Vary one controlled component at a time when measuring CLI or documentation improvements. Keep immutable baselines, fresh sessions, recorded region/fixture conditions and all attempted runs. Separate engineering calibration from held-out evaluation; do not repeatedly tune on the same public examples and call that generalization.

Only mark a catalog family as covered to the extent demonstrated by its scenarios. Record unsupported prerequisites and missing measurements explicitly. More scenario definitions, a reference-only pass or a working adapter stub do not establish broader live coverage.
