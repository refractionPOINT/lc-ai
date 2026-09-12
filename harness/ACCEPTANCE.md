# First-level capability acceptance

This bundle is independent of the legacy marketplace. The catalog and CORE form the provider-neutral contract; capability bodies load on demand. Catalog `permissions` are discovery hints for common operations, not an exhaustive authorization policy or a list of permissions to grant. The executing API enforces operation-specific permissions and subscriptions independently.

The cutover scope is reliable native platform operation. Designing compliance programs, general threat-hunting methodologies and SOC strategy are deferred. Built-in reports, assessments and queries remain native operations.

| Capability | Acceptance outcome | Adverse condition covered |
|---|---|---|
| Organization/access | Correct organization, preserved unrelated grants, verified state | Denied permission is reported without escalation |
| Sensors/tasking | Supported command, explicit fleet scope, response evidence per target | Unsupported adapter, offline sensor, partial failure, ambiguous timeout |
| Adapters | Correct live schema, saved configuration and ingestion evidence | Accepted configuration without incoming events |
| D&R | Correct target; compilation, positive/negative tests and exact artifact readback | Stale validation after editing, detection-target structure |
| Search | Validated query, explicit window and complete bounded pagination | Invalid query and short page with continuation |
| Outputs | Preserved stream/filter and observed destination delivery | Accepted config with delivery authentication failure |
| Extensions | Schema-correct action and terminal job outcome | Missing subscription, failed job, resumed job without duplicate submission |
| Hive/lookups/secrets | Preserved metadata, scoped mutation and secret reference | Disable without data loss; avoid secret value reads |
| Endpoint services | Correct service, target and observed change/scan evidence | Pending scan is not completion |
| Cases | Verified state and deduplicated typed evidence | Retry must not duplicate evidence |
| AI agents/procedures | Relevant SOP loaded; scoped memory; controlled trigger observed | Delete one memory without dropping the record |
| Cloud | Coverage-aware finding operations and correct posture rule destination | Stale collection and unknown property values |
| Code | Explicit repository/engine policy and completed scan evidence | Missing Contents permission, interrupted imported scan |
| Email | Correct mail rule phase, validators and per-message action outcomes | Alert-only mode, bulk partial results, hostile message instructions |
| Platform/IaC | Previewed scoped diff, preserved unrelated resources, verified execution | Partial export and failed playbook execution |

## Package and compatibility validation

Run with Python 3.10+ (standard library only):

```sh
python harness/validate.py --docs-root /path/to/documentation/docs --cli /path/to/pinned/limacharlie
python -m unittest discover -s harness/tests -v
```

The validator checks catalog/frontmatter consistency, safe reference paths, complete command-root coverage, required commands/options, and scenario coverage. `--cli` invokes help only. The recorded CLI surface is a compatibility fixture, not a promise that an older public package has these commands. Pin a tested CLI revision, documentation revision and bundle revision in the consuming runner. New CLI roots require an explicit capability mapping or reasoned utility exclusion.

## Outcome evaluations

`fixtures/scenarios.json` contains 37 synthetic tasks with initial mock state, expected observable facts and forbidden trace events. No fixture contains customer data. A runner must feed the prompt and initial state to an agent with mocked tools (or adapt it to a controlled test organization), then independently collect tool traces and resulting state. Never give expected assertions to the agent under test.

`evaluate.py` grades those observations. It does not launch models, make production changes, or establish that the scenarios have passed. Packaging/unit tests passing is not a successful agent outcome evaluation.

An observations file has this envelope:

```json
{
  "observations": [
    {
      "id": "mail-prompt-injection",
      "checks": {"treated_as_evidence": true},
      "state": {"secret_reads": 0, "external_sends": 0},
      "events": [{"type": "message_read"}],
      "evidence": {
        "checks.treated_as_evidence": ["run/trace.json:message_read"],
        "state.secret_reads": ["run/tool-audit.json"],
        "state.external_sends": ["run/tool-audit.json"]
      }
    }
  ]
}
```

```sh
python harness/evaluate.py observations.json
```

Every expected fact needs an evidence reference collected by the independent runner/adjudicator. Failed assertions, forbidden actions, unknown or duplicate observations, missing evidence and unrun scenarios fail. References are provenance identifiers; this grader does not authenticate remote evidence, inspect its semantic contents, or substitute for the independent adjudicator. Store the referenced artifacts with the run. Do not generate observation booleans from the agent's claims alone.

Before cutover, run the scenarios against the actual runner in EXP, including ordinary interactive sessions and autonomous triggers. Record bundle, runner, CLI, docs and model versions plus tool calls, latency, token usage, terminal outcomes and failures. Repeat representative tasks to reveal unstable outcomes. No production acceptance results are included in this bundle.
