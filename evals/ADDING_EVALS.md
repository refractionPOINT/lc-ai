# Adding evals

Use this guide to add a new LimaCharlie workflow to the existing evaluator. Do not restart the controller design or treat the historical build plan as unfinished work. See [Architecture](ARCHITECTURE.md) for boundaries and [Running evals](RUNNING.md) for operator commands.

## Start with a task contract

Choose a bounded operation from the [capability catalog](catalog/capabilities.yaml). Write down:

- The user's objective, supplied security criteria, authorized scope and required deliverable.
- Initial state, distractors and the properties that must remain unchanged.
- Observable success and a plausible incorrect result that must fail.
- Required region, entitlements, resources, readiness evidence and exact teardown.
- What the agent may see versus private expected values and verifier-only evidence.

For example, an export task should specify the filter and output fields, not the command sequence or private expected IDs. An automation task should specify matching behavior and excluded cases, not ask the model to make a cybersecurity judgment.

Resolve whether the service can produce the necessary evidence before spending model tokens. Keep setup outside the candidate session unless setup itself is the task being evaluated.

## Add the scenario files

Use [hive-preserve-update](scenarios/hive-preserve-update/) for a small state-preservation example, [search-complete-export](scenarios/search-complete-export/) for exact dataset/artifact grading, or [webhook-production-routing](scenarios/webhook-production-routing/) for asynchronous behavioral evidence.

Create `evals/scenarios/<scenario-id>/` with:

| File | Purpose |
|---|---|
| `task.yaml` | ID/revision, capability tags, public files, fixture intent, allowed scope, declared budgets, assertions and deliverables |
| `prompt.md` | The user-facing goal and literal `{{ variable_name }}` placeholders |
| `public/` files, if needed | Schemas or task inputs the agent is permitted to inspect |

Copy the structure of an existing `task.yaml`, replace its scenario-specific contract, and keep assertion IDs stable and descriptive. The current loader reads `prompt.md` directly and replaces placeholders using `fixture['public']`; unresolved placeholders fail. It is not a general template engine. Static `public_files` are copied into `/work` by basename, so avoid collisions. Fixture-generated public filenames must satisfy `safe_id`.

The entire scenario directory contributes to its content hash. Keep private answers, runtime outputs and scratch files out of it. Increment the scenario revision when changing task meaning or grading requirements.

**YAML does not register or enforce everything.** The current loader is a thin YAML reader, not a complete scenario schema engine. `fixture.parameters`, `allowed_scope`, declared capability requirements and task budgets do not automatically provision resources or constrain execution. Wire enforcement into the actual fixture, broker, permissions and resolved runtime configuration.

## Implement fixture, collection and references

Implement trusted setup under [fixtures/](src/lc_eval/fixtures/). Follow the existing lifecycle:

1. Journal resource-creation intent before the external action; record the exact acquired identity afterward. Add cleanup/reconciliation support for any new resource kind, including partial creation and interruption.
2. Provision only the required test resources. Preserve a baseline for unrelated state.
3. Prove readiness independently. HTTP acceptance alone is not ingestion; a nonempty first page is not pagination; configuration existence is not output delivery.
4. Return private expected state plus `public` task variables. Only explicitly public values/files go to the agent. Existing runtime objects use `_`-prefixed fixture keys and stay out of serialized fixture evidence.
5. Collect independent post-execution state after the candidate stops. Bound retries and observation windows and retain failure evidence.
6. Supply a correct reference and a deliberately incorrect reference through the same controlled CLI environment. References receive fixture facts, but their outputs must be graded using the same verifier as real agents.

Do not place cleanup only after successful setup. The controller must recover resources even when provisioning never returns a fixture. Reuse [organization.py](src/lc_eval/fixtures/organization.py), [keys.py](src/lc_eval/fixtures/keys.py) and [journal.py](src/lc_eval/journal.py) rather than inventing broad deletion logic.

Readiness should fail as infrastructure/inconclusive when the world cannot be observed. Preserve genuine agent failures once execution has begun. For eventual delivery, wait for required positive controls and a full negative window rather than treating early silence as success.

## Implement deterministic grading

Add a verifier under [verifiers/](src/lc_eval/verifiers/) and export it from its `__init__.py`. Existing functions use `(manifest, fixture, frozen, evidence)` and return assertion records understood by `grade_assertions`.

Use exact semantic comparisons where possible: IDs, fields, membership, metadata, scope and actual external effects. Accept any valid solution rather than matching the reference's commands. Check preservation as well as desired changes. Read candidate files through the frozen artifact contract; do not execute candidate-generated verification code or accept its own logs as platform truth.

A useful test set proves:

- A correct outcome passes.
- A plausible incorrect outcome fails the intended assertion.
- Missing observations are inconclusive rather than fabricated failures or passes.
- Unrelated-state changes, incomplete exports and duplicate/malformed artifacts are detected when relevant.
- Cleanup survives failure and interruption for newly introduced resource types.

Use the existing verifier, fixture, broker and controller fault tests in [tests/unit/](tests/unit/) as examples. Test behavior and evidence boundaries, not a duplicate implementation of the code under test.

## Wire the current integration points

A new directory alone will not run. Review every applicable point below; current fallthrough branches assume one of the original three scenarios.

| Integration point | Required change |
|---|---|
| [cli.py](src/lc_eval/cli.py), `run --scenario` | Add the scenario to the explicit Click choices. |
| [controller.py](src/lc_eval/controller.py), `trial` and `reference` | Add explicit provisioning, collection, verifier and reference dispatch. Do not let a new scenario fall through to export setup or routing grading. Review fixture digest selection. |
| [fixtures/scenario_runtime.py](src/lc_eval/fixtures/scenario_runtime.py) | Extend its dispatch if the new scenario uses this coordinator; otherwise call a dedicated fixture module explicitly. |
| [fixtures/keys.py](src/lc_eval/fixtures/keys.py), `PERMISSIONS` | Add least-privilege candidate permissions for the new scenario. |
| [execution/broker.py](src/lc_eval/execution/broker.py) | If necessary, extend `_COMMANDS`, option validation, input-file handling and the public `CONTROLLED_CLI_V1_NOTICE`. Verify native syntax parity and prohibited bypasses. |
| [execution/parity.py](src/lc_eval/execution/parity.py) and broker tests | Exercise any new transport behavior against the pinned native CLI. Rejections caused by the evaluator must not masquerade as CLI/model defects. |
| [acceptance.py](src/lc_eval/acceptance.py) | Extend `SCENARIOS` and `BAD_ASSERTIONS` if reference validation should require the new scenario. |
| [reporting/results.py](src/lc_eval/reporting/results.py) | Deliberately update the expected acceptance scenario/harness matrix when expanding the milestone. Generic result reporting and initial-loop acceptance are different concerns. |
| [suites/initial-loop.yaml](suites/initial-loop.yaml) and [cli.py](src/lc_eval/cli.py) | Add trials to a deliberately expanded suite or implement real suite selection. `config.suite` currently does not change the hard-coded YAML path. |
| [catalog/capabilities.yaml](catalog/capabilities.yaml) | Link the scenario to the appropriate family and record coverage conservatively. |

A small explicit dispatch change is sufficient for a new scenario. If introducing a registry, migrate all selection and acceptance points together with tests; do not document a plugin interface that the runtime cannot load.

When changing permissions or execution boundaries, check whether a new profile/revision is appropriate and retain old baseline results. Do not grant owner credentials to the agent simply to make a new task work.

## Prove it before adding it to routine campaigns

After wiring the scenario, run the appropriate offline tests and lint:

```sh
./evals/.venv/bin/pytest evals/tests/unit -q
./evals/.venv/bin/ruff check evals/src evals/tests
```

Then use a fresh campaign and a configuration pinned to the supported environment. Replace `new-scenario` only after registering it:

```sh
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-region.json --campaign new-scenario-calibration --scenario new-scenario --seed 51001 --reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-region.json --campaign new-scenario-calibration --scenario new-scenario --seed 51001 --bad-reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-region.json --campaign new-scenario-agents --scenario new-scenario --seed 51001 --adapter codex
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-region.json --campaign new-scenario-agents --scenario new-scenario --seed 51001 --adapter claude_code
./evals/.venv/bin/lc-eval report --config /absolute/private/lc-eval-region.json --campaign new-scenario-agents
./evals/.venv/bin/lc-eval cleanup --config /absolute/private/lc-eval-region.json
```

Inspect the correct reference before proceeding. The bad reference must fail its named assertion (normally exit 1); an infrastructure error is not successful negative calibration. The global `validate-suite` still requires all registered reference scenarios, so a one-scenario campaign alone does not satisfy it. Retain a complete calibration campaign when using that gate.

Freeze implementation and task semantics before comparative agent runs. No coaching or repairs during a trial. Preserve setup failures, invalid attempts, model failures and cleanup results. Publish a dated, sanitized result record with source/fixture/profile identities and known limitations; keep raw secrets and traces private. Update the operator guide and catalog only to the extent actually demonstrated.

## Add a harness separately

Keep task meaning and grading unchanged. Implement the lifecycle/capabilities contract in [adapters/base.py](src/lc_eval/adapters/base.py), test native stream parsing and cancellation, and wire the adapter into configuration, CLI selection, `Controller.run_agent`, and Docker packaging/auth/proxy setup. The current controller accepts only Claude Code and Codex; a new adapter class alone is insufficient.

Prove fresh sessions, appropriate shell/files access, isolated authentication, enforceable limits, usage provenance and reliable stop behavior before live scenario trials. Run a real smoke task through the controlled CLI, then the existing scenarios. Return unsupported for unmet requirements. Workspace remains in this category until its environment and telemetry controls are verified.
