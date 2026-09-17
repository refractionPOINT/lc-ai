# LimaCharlie CLI AI evals

How effectively can an AI agent operate LimaCharlie through its CLI? These evals give agents concrete platform tasks and independently verify the results in disposable, live organizations. The task supplies the security criteria; the eval measures platform operation, not cybersecurity judgment.

**Results as of September 16, 2026.** Eight scenarios have live evidence. The original three cover lookup preservation, complete search export and webhook routing. Five additions cover configuration reconciliation, Cases, Cloud Security, key rotation and native endpoint onboarding, with explicit bare/skills profiles. This is early coverage, not an all-platform certification or a model leaderboard.

## Explicit context profiles

New runs select `--context bare` or `--context lc_ai`. Both retain the same pinned CLI and documentation. Bare excludes personal local settings, skills and history and carries no LC corpus; `lc_ai` loads 43 skills from a pinned repository archive. Provider builtin context remains possible. AI Sessions uses native plugins; standalone harnesses use native user-skill directories. [Isolation audit](CONTEXT_PROFILES.md) and [runtime proof](CONTEXT_PROOF.md).

| Context check | Claude Code | Codex | AI Sessions |
|---|:---:|:---:|:---:|
| Bare: LC corpus absent | Pass | Pass | Pass |
| Pinned LC corpus usable | Pass | Pass | Pass |

These six probes validate context handling, not LimaCharlie task performance. Historical results below retain their original profiles and are not relabeled as bare-versus-skills comparisons.

## Expansion results — explicit contexts

Counts are **passed / scored trials shown**. A dash means untested. The initial matrix uses seed 51002 and one live trial at a time. These observations establish an operational loop, not success probabilities or a demonstrated benefit from skills.

| Eval | Claude bare | Claude + skills | Codex bare | Codex + skills | AI Sessions bare | AI Sessions + skills |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| [Configuration reconciliation](scenarios/config-reconcile-preserve/prompt.md) | ✅ 1/1 | ✅ 1/1 | ✅ 1/1 | ✅ 1/1 | ✅ 1/1 | ✅ 1/1 |
| [Cases maintenance](scenarios/case-maintain-records/prompt.md) | — | — | ✅ 1/1 | ✅ 1/1 | — | — |
| [Cloud Security findings](scenarios/cloudsec-findings-triage/prompt.md) | — | — | ✅ 1/1 | ✅ 1/1 | — | — |
| [Scoped key rotation](scenarios/access-key-rotation/prompt.md) | — | — | ✅ 1/1 | ✅ 1/1 | — | — |
| [Native endpoint onboarding](scenarios/native-sensor-onboarding/prompt.md) | — | — | ✅ 1/1 | ✅ 1/1 | — | — |

All five scenarios have positive-reference and deliberately bad-reference calibration, separate from these AI scores. Cases uses an existing-case variant; native creation remains blocked by the pinned CLI/backend encoding mismatch. Acceptance-reason persistence and previously issued JWT revocation are outside the Cloud Security and key-rotation claims, respectively. [Scope and calibration](EXPANSION_PROOF.md).

One earlier Cases trial was superseded after fixing fresh-tenant listing readiness. Its empty case list was a fixture fault, and it is excluded from this matrix. Corrected reference discovery and the replacement run are recorded in the evidence. Genuine task failures are retained.

### Expansion measurements

| Harness | Context | Eval | Grade | Agent seconds | CLI calls | Failed calls | LC skill requests |
|---|---|---|:---:|---:|---:|---:|---:|
| Codex | bare | Configuration reconciliation | Pass | 41.0 | 9 | 0 | 0 |
| Codex | lc_ai | Configuration reconciliation | Pass | 52.5 | 14 | 0 | 1 |
| Codex | bare | Cases maintenance | Pass | 39.7 | 18 | 0 | 0 |
| Codex | lc_ai | Cases maintenance | Pass | 48.2 | 20 | 0 | 1 |
| Codex | bare | Cloud Security findings | Pass | 39.1 | 14 | 0 | 0 |
| Codex | lc_ai | Cloud Security findings | Pass | 50.9 | 15 | 0 | 1 |
| Codex | bare | Scoped key rotation | Pass | 78.0 | 10 | 0 | 0 |
| Codex | lc_ai | Scoped key rotation | Pass | 73.1 | 10 | 0 | 1 |
| Codex | bare | Native endpoint onboarding | Pass | 152.6 | 17 | 0 | 0 |
| Codex | lc_ai | Native endpoint onboarding | Pass | 138.4 | 14 | 0 | 2 |
| Claude Code | bare | Configuration reconciliation | Pass | 27.9 | 14 | 0 | 0 |
| Claude Code | lc_ai | Configuration reconciliation | Pass | 203.0 | 11 | 0 | 0 |
| AI Sessions | bare | Configuration reconciliation | Pass | 36.4 | 9 | 0 | 0 |
| AI Sessions | lc_ai | Configuration reconciliation | Pass | 30.1 | 8 | 0 | 0 |

The last column counts distinct LC skills observed in native skill/read requests or successful Codex skill-file reads. Zero does not prove the absence of influence from startup context. Exact names are retained in JSON. Agent time includes harness startup and excludes provisioning, verification and teardown. Source/configuration hashes and native token classes are retained in the [sanitized scored records](results/expansion-proof.json). The first Codex reconciliation pair was collected during final grading work on other scenarios; its broad evaluator digests differ even though the reconciliation grader was unchanged. Treat its timing comparison as exploratory. Later comparisons retain the frozen evaluator identity.

[Live reference records](results/expansion-calibration.json) · [Offline regrade of saved evidence](results/expansion-calibration-regrade.json) · [Context probes](results/expansion-context-probes.json)

## Original three-scenario results

The matrix shows the latest verified evidence for each harness/eval combination. Superseded runs affected by resolved harness bugs are omitted. Counts are **passed / verification trials shown**, not lifetime success rates.

| Eval | Claude Code | Codex | AI Sessions |
|---|:---:|:---:|:---:|
| [Preserve and update a lookup](scenarios/hive-preserve-update/prompt.md) | ✅ **2/2** | ✅ **2/2** | ✅ **1/1** |
| [Complete search export](scenarios/search-complete-export/prompt.md) | ✅ **1/1** | ✅ **1/1** | ✅ **1/1** |
| [Production webhook routing](scenarios/webhook-production-routing/prompt.md) | ✅ **1/1** | ✅ **1/1** | ✅ **1/1** |

The two lookup trials per standalone harness include one repeat. All other cells contain a single verification trial. AI Sessions' lookup and routing passes used the earlier runner profile; export used the updated profile. This combines the latest evidence per eval, not a complete rerun of all scenarios on one revision. Counts are not estimated success probabilities.

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
| AI Sessions baseline | AI Sessions | Lookup / 1 | Pass | 36.1 | 7 | 0 |
| AI Sessions baseline | AI Sessions | Routing | Pass | 95.7 | 16 | 0 |
| AI Sessions updated | AI Sessions | Export | Pass | 69.7 | 7 | 0 |

Export fixture sizes differ: Codex exported 15,003 matching rows, Claude Code 20,003, and revised AI Sessions 5,003. Each fixture independently demonstrated pagination, but these differences prevent a controlled speed comparison. The lookup repeats verify the comparison machinery; two trials do not establish repeatability statistically.

## Verification scope

The updated AI Sessions profile aligns the instructions with the available CLI, enforces the SDK tool inventory, and preserves nested tool results. Export passed all seven assertions with zero failed or rejected CLI calls. Hive and routing have not been rerun with those changes, nor have the standalone harnesses been rerun with the revised shared instructions. [Export verification and changes](AI_SESSIONS_EXPORT_RETEST.md).

Setup, smoke, correct-reference, deliberately bad-reference and crash-recovery checks are infrastructure validation, separate from the task matrix. The published verification records report clean resource teardown and successful cleanup audits.

## Evidence and limits

| Evidence source | Results shown here | Human-readable record | Sanitized data |
|---|---|---|---|
| `initial-proof-v2` | 8 passed / 8 trials | [Initial acceptance](ACCEPTANCE.md) | [JSON](results/initial-proof-v2.json) |
| `ai-sessions-proof` | Lookup and routing passes | [Runner verification](AI_SESSIONS_PROOF.md) | [JSON](results/ai-sessions-proof.json) |
| `ai-sessions-export-fix` | 1 passed / 1 trial | [Export retest](AI_SESSIONS_EXPORT_RETEST.md) | [JSON](results/ai-sessions-export-fix.json) |

Runs use the `controlled-cli-v1` profile: a restricted CLI command surface, a separate credentialed CLI worker, independent graders, and disposable organizations. Full trials allow 600 agent seconds and 80 brokered CLI calls, with one live trial at a time. Claude-based harnesses have a configured 30-turn limit; Codex has an 80-completed-tool-call limit. Native SDK terminal turn counts can exceed the configured number; exact counts are retained in the evidence records.

Billing uses existing subscriptions. **Dollar cost is unknown**; these runs do not claim a hard $50 cap. Provider-reported token classes remain separate, and missing values stay unknown. The AI Sessions bridge omits cache classes and total input, so its input totals cannot be compared directly with fully reported standalone usage.

Public records expose outcomes, metrics, configuration fingerprints, failures and cleanup evidence. Raw transcripts, credentials, receiver secrets and full platform snapshots stay outside this public repository. The published data is sanitized, not a complete raw trace archive. See [running evals](RUNNING.md) to reproduce a trial and inspect its private evidence.

## Coverage still to build

Broader integrations and outputs, vulnerability and email workflows, other endpoint platforms, and much of the platform remain untested. The expansion matrix explicitly marks harness/context combinations that have not been run. Creating and deleting organizations is exercised by the trusted fixture controller; it is not yet an agent-scored provisioning task. The full production command surface and other model/provider combinations are also untested here. Track expansion in the [coverage plan](DESIGN.md) and [capability catalog](catalog/capabilities.yaml).

## Run, extend and update

| I want to… | Start here |
|---|---|
| Set up, run an eval, inspect reports or recover cleanup | [Running evals](RUNNING.md) |
| Add a scenario, fixture, verifier or harness | [Adding evals](ADDING_EVALS.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Audit bare/skills isolation and native discovery | [Context profiles](CONTEXT_PROFILES.md) |
| Understand the lifecycle and trust boundaries | [Architecture](ARCHITECTURE.md) |
| Investigate CLI issues found during evaluation | [CLI findings](CLI_FINDINGS.md) |
| Read the original implementation history | [Build history](history/README.md) |

When publishing new results, add a dated evidence record and sanitized JSON, then update this matrix and performance table from those records. Show the latest verified result for each harness/eval and identify the revision that produced it. Supersede results affected by resolved harness bugs after a verified rerun. Keep genuine task failures visible, distinguish untested combinations, identify repetitions, and update the snapshot date. This README is a manually maintained evidence snapshot, not an automatically refreshed CI badge.
