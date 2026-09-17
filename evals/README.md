# LimaCharlie CLI AI evals

How effectively can an AI agent operate LimaCharlie through its CLI? These evals give agents concrete platform tasks and independently verify the results in disposable, live organizations. The task supplies the security criteria; the eval measures platform operation, not cybersecurity judgment.

**Results as of September 16, 2026.** Three scenarios have live evidence. Claude Code and Codex passed the initial eight-trial campaign. The local AI Sessions runner passed two scenarios, failed export, and then passed a fresh export trial after harness/profile fixes. This is early coverage, not an all-platform certification or a model leaderboard.

## Results at a glance

Cells show **passed / scored trials** for the named experiment. “Not run” means there is no evidence for that combination; it is not a failure. AI Sessions profiles are separate columns because their instructions and tool policies differ.

| Eval | Claude Code — initial | Codex — initial | AI Sessions — original | AI Sessions — revised |
|---|:---:|:---:|:---:|:---:|
| [Preserve and update a lookup](scenarios/hive-preserve-update/prompt.md) | ✅ **2/2** | ✅ **2/2** | ✅ **1/1** | — Not run |
| [Complete search export](scenarios/search-complete-export/prompt.md) | ✅ **1/1** | ✅ **1/1** | ❌ **0/1** | ✅ **1/1** |
| [Production webhook routing](scenarios/webhook-production-routing/prompt.md) | ✅ **1/1** | ✅ **1/1** | ✅ **1/1** | — Not run |

The two lookup trials per standalone harness include one repeat. All other scored cells contain a single trial. Counts describe these recorded attempts, not estimated success probabilities. Setup failures and invalidated earlier attempts are disclosed [below](#failures-and-retained-attempts).

### What each eval proves

| Eval | Agent task | Independent success checks | Tested region |
|---|---|---|---|
| Preserve and update a lookup | Change the intended lookup data without disturbing surrounding configuration. | Exact target data, preserved metadata, unchanged distractors and record set, identified deliverable. | USA |
| Complete search export | Export every matching telemetry event to JSONL, including continuation results. | Exact event membership, unique IDs, required fields and values, correct count, safe bounded file, unchanged platform state. Fixture readiness must prove a nonempty continuation page. | Canada |
| Production webhook routing | Configure ingestion, detection/response automation and outbound delivery for production events. | Real signed HTTPS delivery of matching probes, exclusion of negative probes over the full observation window, healthy receiver, preserved baseline output. | USA |

### Harnesses and configurations

| Harness | Recorded model | Effort | Environment tested |
|---|---|---|---|
| Claude Code (`claude_code`) | `claude-sonnet-5` | `medium` | Local native CLI inside the controlled eval container. |
| Codex (`codex`) | `gpt-6-astra` | `medium` | Local native CLI inside the controlled eval container. |
| AI Sessions (`ai_sessions`) | `claude-sonnet-5` | `native_default` | Native Go runner and Python SDK bridge, with pinned LC plugins and documentation, in a reduced local image. |
| Hosted Workspace (`workspace`) | — | — | Unsupported by the current eval adapter; no hosted-service results. |

AI Sessions uses an evaluator-supplied local control plane. Its revised image adds explicit restricted-profile instructions and an eval-only SDK tool-policy overlay. It does **not** establish the behavior of the hosted Workspace service or the full production container. Source commits, image digests, SDK versions and overlay hashes are linked in the evidence records.

## Recorded task performance

These are observations, not rankings. Agent seconds include harness startup but exclude fixture preparation, independent verification and cleanup. CLI calls count accepted broker executions; failed calls are included in that count. A task can pass after recovering from command errors. Rejected requests and native token accounting are retained separately in the JSON evidence.

| Experiment | Harness | Eval / repeat | Grade | Agent seconds | CLI calls | Failed calls |
|---|---|---|:---:|---:|---:|---:|
| Initial | Claude Code | Lookup / 1 | Pass | 17.7 | 6 | 0 |
| Initial | Codex | Lookup / 1 | Pass | 53.5 | 10 | 0 |
| Initial | Claude Code | Routing | Pass | 74.2 | 19 | 2 |
| Initial | Codex | Routing | Pass | 88.3 | 21 | 4 |
| Initial | Claude Code | Lookup / 2 | Pass | 22.5 | 10 | 0 |
| Initial | Codex | Lookup / 2 | Pass | 37.0 | 8 | 0 |
| Initial | Codex | Export | Pass | 72.1 | 6 | 0 |
| Initial | Claude Code | Export | Pass | 63.1 | 7 | 0 |
| AI Sessions original | AI Sessions | Lookup / 1 | Pass | 36.1 | 7 | 0 |
| AI Sessions original | AI Sessions | Routing | Pass | 95.7 | 16 | 0 |
| AI Sessions original | AI Sessions | Export | Fail | 359.2 | 37 | 33 |
| AI Sessions revised | AI Sessions | Export | Pass | 69.7 | 7 | 0 |

Export fixture sizes differ: Codex exported 15,003 matching rows, Claude Code 20,003, and revised AI Sessions 5,003. Original AI Sessions was asked for 20,003 and produced no export. Each fixture independently demonstrated pagination, but these differences prevent a controlled speed comparison. The lookup repeats verify the comparison machinery; two trials do not establish repeatability statistically.

## Failures and retained attempts

**AI Sessions' original export failure is still a failure.** Conflicting production instructions required a blocked query generator, a research subagent supplied an incorrect query structure, and the parent exhausted its turn limit after 33 validation failures. Investigation also found that the SDK's `Agent` tool escaped a `Task`-only deny list, and nested tool results were missing from normalized telemetry. [Investigation](AI_SESSIONS_EXPORT_DIAGNOSIS.md).

The revised local profile aligns the instructions with the available CLI, enforces the SDK tool inventory, and preserves nested tool results. A fresh export passed all seven assertions with zero failed or rejected CLI calls. Hive and routing have **not** been rerun with those changes, nor have the standalone harnesses been rerun with the revised shared instructions. [Retest and changes](AI_SESSIONS_EXPORT_RETEST.md).

Other attempts remain visible in their records:

- The initial campaign includes two USA export preparations that failed before an agent started because pagination could not be established. An earlier campaign's two Hive passes were invalidated after broker-induced syntax errors; the scored campaign was restarted after the fix.
- The original AI Sessions campaign includes a routing setup failure caused by receiver DNS readiness, plus two earlier smoke startup failures.
- The revised AI Sessions smoke first failed because startup discovery exhausted its four-call allowance. Its tool-policy checks passed. The smoke passed after a smoke-only increase to eight CLI calls; full-trial limits were unchanged.

These setup and smoke attempts are separate from the scored task matrix. Correct-reference, deliberately bad-reference and crash-recovery checks are infrastructure validation, not additional AI task passes. All three published experiments report clean resource teardown and successful cleanup audits.

## Evidence and limits

| Experiment | Scored outcome | Human-readable record | Sanitized data |
|---|---|---|---|
| `initial-proof-v2` | 8 passed / 8 trials | [Initial acceptance](ACCEPTANCE.md) | [JSON](results/initial-proof-v2.json) |
| `ai-sessions-proof` | 2 passed, 1 failed / 3 trials | [Original runner proof](AI_SESSIONS_PROOF.md) | [JSON](results/ai-sessions-proof.json) |
| `ai-sessions-export-fix` | 1 passed / 1 trial | [Export retest](AI_SESSIONS_EXPORT_RETEST.md) | [JSON](results/ai-sessions-export-fix.json) |

Runs use the `controlled-cli-v1` profile: a restricted CLI command surface, a separate credentialed CLI worker, independent graders, and disposable organizations. Full trials allow 600 agent seconds and 80 brokered CLI calls, with one live trial at a time. Claude-based harnesses have a configured 30-turn limit; Codex has an 80-completed-tool-call limit. Native SDK terminal turn counts can exceed the configured number; the original AI Sessions failure reported 31.

Billing uses existing subscriptions. **Dollar cost is unknown**; these runs do not claim a hard $50 cap. Provider-reported token classes remain separate, and missing values stay unknown. The AI Sessions bridge omits cache classes and total input, so its input totals cannot be compared directly with fully reported standalone usage.

Public records expose outcomes, metrics, configuration fingerprints, failures and cleanup evidence. Raw transcripts, credentials, receiver secrets and full platform snapshots stay outside this public repository. The published data is sanitized, not a complete raw trace archive. See [running evals](RUNNING.md) to reproduce a trial and inspect its private evidence.

## Coverage still to build

There are no published live scenario results yet for native endpoint onboarding, Cloud Security findings, broader integrations and outputs, or the rest of the platform. Creating and deleting organizations is exercised by the trusted fixture controller; it is not yet an agent-scored provisioning task. The full production command surface and other model/provider combinations are also untested here. Track expansion in the [coverage plan](DESIGN.md) and [capability catalog](catalog/capabilities.yaml).

## Run, extend and update

| I want to… | Start here |
|---|---|
| Set up, run an eval, inspect reports or recover cleanup | [Running evals](RUNNING.md) |
| Add a scenario, fixture, verifier or harness | [Adding evals](ADDING_EVALS.md) |
| Understand the lifecycle and trust boundaries | [Architecture](ARCHITECTURE.md) |
| Investigate CLI issues found during evaluation | [CLI findings](CLI_FINDINGS.md) |
| Read the original implementation history | [Build history](history/README.md) |

When publishing new results, add a dated evidence record and sanitized JSON, then update this matrix and performance table from those records. Keep changed profiles separate, retain failed and inconclusive attempts, identify repetitions and untested combinations, and update the snapshot date. A later pass does not erase an earlier failure. This README is a manually maintained evidence snapshot, not an automatically refreshed CI badge.
