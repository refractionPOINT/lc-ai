# LimaCharlie CLI AI evals

How effectively can an AI agent operate LimaCharlie through its CLI? These evals give agents concrete platform tasks and independently verify the results in disposable, live organizations. The task supplies the security criteria; the eval measures platform operation, not cybersecurity judgment.

**Campaign: `unified-2026-09-17` — 45/48 completed normally and passed.** Eight evals, three harnesses, two explicit context profiles, one fresh trial per cell. Every result below belongs to this campaign. One trial per cell is an operational snapshot, not an estimated success rate or a model leaderboard.

## Results

| Eval | Claude bare | Claude + skills | Codex bare | Codex + skills | AI Sessions bare | AI Sessions + skills |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| [Preserve and update a lookup](scenarios/hive-preserve-update/prompt.md) | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass |
| [Complete search export](scenarios/search-complete-export/prompt.md) | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass |
| [Production webhook routing](scenarios/webhook-production-routing/prompt.md) | ⚠ Task pass; limit | ✅ Pass | ✅ Pass | ✅ Pass | ⚠ Task pass; limit | ✅ Pass |
| [Configuration reconciliation](scenarios/config-reconcile-preserve/prompt.md) | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass |
| [Cases maintenance](scenarios/case-maintain-records/prompt.md) | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass |
| [Cloud Security findings](scenarios/cloudsec-findings-triage/prompt.md) | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass |
| [Scoped key rotation](scenarios/access-key-rotation/prompt.md) | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass |
| [Native endpoint onboarding](scenarios/native-sensor-onboarding/prompt.md) | ✅ Pass | ❌ Fail | ✅ Pass | ✅ Pass | ✅ Pass | ✅ Pass |

A pass requires both successful task verification and normal harness completion. A task pass with a limit means the requested platform state was correct, but the harness did not finish within its execution budget.

### Observed failures and limits

- **Claude Code + skills, native onboarding:** timed out after initially submitting an empty installation key. The agent later recovered a valid key, but the deployment helper stopped watching after its first rejected request. This is an agent input error compounded by a one-shot helper recovery limitation; the failed attempt is retained.
- **Claude Code bare, webhook routing:** all six task assertions passed, but the harness reached its configured turn limit.
- **AI Sessions bare, webhook routing:** all six task assertions passed, but the harness reached its 600-second execution limit.
- Three receiver-startup attempts failed DNS resolution before an agent started. Their resources were deleted and fresh attempts were run; the invalid attempts remain separately visible in the public evidence. A separate export calibration attempt exceeded the original output cap and was replaced after adjusting that cap for all export trials.

Bare includes the pinned CLI, its help and public documentation, but excludes personal local skills/settings/history and the LC skill corpus. **+ skills** adds the same pinned LC corpus through each harness’s native loading mechanism. Provider builtin context remains possible. All six [context probes](results/unified-2026-09-17-context.json) passed before task execution. See [isolation details](CONTEXT_PROFILES.md).

## What is measured

| Eval | Independent success checks |
|---|---|
| Lookup | Exact requested data; preserved metadata, unrelated records and record set. |
| Complete export | Exact event membership, unique IDs, required values and count; fixture proves a real continuation page. |
| Webhook routing | Real signed HTTPS delivery of matching probes; exclusion of negative probes; preserved baseline output. |
| Configuration reconciliation | Requested lookup and D&R state; no unwanted changes to unrelated records. |
| Cases maintenance | Discover the existing case, apply requested changes and preserve surrounding records. |
| Cloud Security | Correct finding owners and dispositions; unrelated findings preserved. |
| Key rotation | Usable replacement key, read-only authority and denial of fresh authentication with the deleted key. |
| Native onboarding | Real Linux sensor in an evaluator-owned container, required configuration and telemetry. |

Cases tests existing-case maintenance. The CLI creation-encoding fix is included, but clean case creation is not claimed by this scenario. Cloud Security does not claim acceptance-reason persistence, and key rotation does not claim revocation of previously issued JWTs. Organization provisioning/deletion is performed by the trusted controller, not scored as an agent task.

## Harnesses and fixed inputs

| Harness | Version / source | Model | Effort |
|---|---|---|---|
| Claude Code | `2.1.273 (Claude Code)` | `claude-sonnet-5` | `medium` |
| Codex | `codex-cli 0.154.0` | `gpt-6-astra` | `medium` |
| AI Sessions | `session-runner@bbe82892282e3989005e70ca9c4415f77866c563` | `claude-sonnet-5` | `native_default` |

AI Sessions runs the native Go coordinator and Python SDK bridge in the reduced local eval image, with the recorded tool-policy overlay and restricted instructions. These results do not establish hosted Workspace behavior or the full production runner container. Standalone harnesses load native user skills; AI Sessions loads native plugins. The same corpus does not imply identical system prompts.

| Input | Pin |
|---|---|
| cli_commit | `289b4e9e3a66cf96e7746b2d81e42745e0d917c9` |
| documentation_commit | `3eeeb95207730af2e93f600ca93cdad82ef47f73` |
| lc_ai_commit | `d811347d71d9e73152328aaceb65b42d445a446b` |
| ai_sessions_commit | `bbe82892282e3989005e70ca9c4415f77866c563` |

All runs use `controlled-cli-v1`, existing subscriptions, one live trial at a time, 600 agent seconds and at most 80 brokered CLI calls. Claude-based harnesses have a configured 30-turn limit; Codex has an 80-completed-tool-call limit. Native SDK turn counters can differ from the configured limit; execution status is reported independently from task grade. **Dollar cost is unknown.** Native token classes and missing values are preserved separately. AI Sessions does not report all input/cache classes, so token totals are not directly comparable across harnesses.

Export uses Canada and a 64,000,000-byte per-command output cap; other evals use USA and 16,000,000 bytes. The export cap was calibrated before any scored export attempt after the reference exceeded the smaller cap. Each scenario uses the same seed across its six cells. Export grows its fixture until pagination is independently proven, so dataset sizes may differ and raw timing is not a controlled speed comparison. Agent seconds include harness startup and exclude provisioning, verification and teardown.

## Per-trial measurements

| Eval | Harness | Context | Task grade | Execution | Agent seconds | CLI calls | Failed calls |
|---|---|---|:---:|---|---:|---:|---:|
| Preserve and update a lookup | Claude Code | bare | pass | completed | 19.9 | 7 | 0 |
| Preserve and update a lookup | Claude Code | lc_ai | pass | completed | 20.7 | 8 | 0 |
| Preserve and update a lookup | Codex | bare | pass | completed | 38.5 | 8 | 0 |
| Preserve and update a lookup | Codex | lc_ai | pass | completed | 35.3 | 6 | 0 |
| Preserve and update a lookup | AI Sessions | bare | pass | completed | 19.6 | 6 | 0 |
| Preserve and update a lookup | AI Sessions | lc_ai | pass | completed | 22.9 | 7 | 0 |
| Complete search export | Claude Code | bare | pass | completed | 49.9 | 4 | 0 |
| Complete search export | Claude Code | lc_ai | pass | completed | 69.6 | 7 | 0 |
| Complete search export | Codex | bare | pass | completed | 73.8 | 6 | 0 |
| Complete search export | Codex | lc_ai | pass | completed | 66.8 | 5 | 0 |
| Complete search export | AI Sessions | bare | pass | completed | 90.6 | 5 | 0 |
| Complete search export | AI Sessions | lc_ai | pass | completed | 73.9 | 11 | 0 |
| Production webhook routing | Claude Code | bare | pass | failed | 140.7 | 25 | 4 |
| Production webhook routing | Claude Code | lc_ai | pass | completed | 421.9 | 16 | 1 |
| Production webhook routing | Codex | bare | pass | completed | 82.5 | 25 | 5 |
| Production webhook routing | Codex | lc_ai | pass | completed | 105.2 | 25 | 6 |
| Production webhook routing | AI Sessions | bare | pass | timed_out | 600.4 | 21 | 1 |
| Production webhook routing | AI Sessions | lc_ai | pass | completed | 155.1 | 24 | 2 |
| Configuration reconciliation | Claude Code | bare | pass | completed | 29.8 | 8 | 0 |
| Configuration reconciliation | Claude Code | lc_ai | pass | completed | 39.4 | 12 | 0 |
| Configuration reconciliation | Codex | bare | pass | completed | 49.7 | 11 | 0 |
| Configuration reconciliation | Codex | lc_ai | pass | completed | 55.0 | 12 | 0 |
| Configuration reconciliation | AI Sessions | bare | pass | completed | 34.7 | 15 | 0 |
| Configuration reconciliation | AI Sessions | lc_ai | pass | completed | 25.8 | 8 | 0 |
| Cases maintenance | Claude Code | bare | pass | completed | 33.5 | 16 | 0 |
| Cases maintenance | Claude Code | lc_ai | pass | completed | 46.6 | 17 | 0 |
| Cases maintenance | Codex | bare | pass | completed | 37.6 | 15 | 0 |
| Cases maintenance | Codex | lc_ai | pass | completed | 54.0 | 18 | 0 |
| Cases maintenance | AI Sessions | bare | pass | completed | 35.8 | 19 | 0 |
| Cases maintenance | AI Sessions | lc_ai | pass | completed | 34.1 | 15 | 0 |
| Cloud Security findings | Claude Code | bare | pass | completed | 23.2 | 14 | 0 |
| Cloud Security findings | Claude Code | lc_ai | pass | completed | 30.4 | 16 | 0 |
| Cloud Security findings | Codex | bare | pass | completed | 46.7 | 14 | 0 |
| Cloud Security findings | Codex | lc_ai | pass | completed | 57.1 | 16 | 0 |
| Cloud Security findings | AI Sessions | bare | pass | completed | 25.0 | 15 | 0 |
| Cloud Security findings | AI Sessions | lc_ai | pass | completed | 45.3 | 19 | 0 |
| Scoped key rotation | Claude Code | bare | pass | completed | 17.8 | 8 | 0 |
| Scoped key rotation | Claude Code | lc_ai | pass | completed | 31.2 | 8 | 0 |
| Scoped key rotation | Codex | bare | pass | completed | 63.6 | 8 | 0 |
| Scoped key rotation | Codex | lc_ai | pass | completed | 75.0 | 10 | 0 |
| Scoped key rotation | AI Sessions | bare | pass | completed | 38.8 | 6 | 0 |
| Scoped key rotation | AI Sessions | lc_ai | pass | completed | 39.6 | 11 | 0 |
| Native endpoint onboarding | Claude Code | bare | pass | completed | 116.4 | 15 | 0 |
| Native endpoint onboarding | Claude Code | lc_ai | fail | timed_out | 600.4 | 6 | 0 |
| Native endpoint onboarding | Codex | bare | pass | completed | 140.1 | 17 | 0 |
| Native endpoint onboarding | Codex | lc_ai | pass | completed | 143.6 | 16 | 0 |
| Native endpoint onboarding | AI Sessions | bare | pass | completed | 294.9 | 14 | 0 |
| Native endpoint onboarding | AI Sessions | lc_ai | pass | completed | 137.3 | 13 | 0 |

Failed CLI calls are included in total calls; recovering from command errors can still produce a task pass. Rejected commands, assertions, configuration fingerprints, native tokens and cleanup states are in the [sanitized trial records](results/unified-2026-09-17.json). Raw transcripts, credentials, receiver secrets and platform snapshots remain private.

## Calibration and cleanup

Positive and deliberately bad reference trials are separate infrastructure checks, not AI scores. See the [campaign evidence](UNIFIED_PROOF.md) and [reference records](results/unified-2026-09-17-calibration.json) for calibration outcomes, cleanup audit and any campaign exceptions. Genuine agent failures stay visible; invalid infrastructure attempts are disclosed separately and never relabeled as passes.

## Run and extend

| I want to… | Start here |
|---|---|
| Run evals or recover cleanup | [Running evals](RUNNING.md) |
| Add an eval or harness | [Adding evals](ADDING_EVALS.md) |
| Audit context isolation | [Context profiles](CONTEXT_PROFILES.md) |
| Understand trust boundaries | [Architecture](ARCHITECTURE.md) |
| Investigate CLI issues | [CLI findings](CLI_FINDINGS.md) |

Coverage is still limited: broader integrations and outputs, vulnerability and email workflows, other endpoint platforms and much of LimaCharlie remain untested. See the [capability catalog](catalog/capabilities.yaml). This README is a dated evidence snapshot, not an automatically refreshed CI badge.
