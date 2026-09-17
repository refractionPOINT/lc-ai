# Unified live campaign proof

Campaign `unified-2026-09-17` reruns eight evals across Claude Code, Codex and the native AI Sessions harness, once in `bare` and once in `lc_ai`: **48 scored agent attempts**. This replaces the mixed historical matrix in the [results README](README.md). Historical evidence remains linked separately.

**45/48 completed normally and passed.** Task grade and harness execution status are independent. See the README for all cells, execution limits and the onboarding failure. This is one observation per cell, not a statistical estimate of reliability.

## Frozen inputs

The evaluator code stayed unchanged throughout the campaign. CLI, documentation, skill corpus, models and images were pinned. The CLI includes the merged [case-detection encoding fix](https://github.com/refractionPOINT/python-limacharlie/pull/381). Existing-case maintenance is tested; clean case creation still needs its own calibration.

| Input | Pin |
|---|---|
| cli_commit | `289b4e9e3a66cf96e7746b2d81e42745e0d917c9` |
| documentation_commit | `3eeeb95207730af2e93f600ca93cdad82ef47f73` |
| lc_ai_commit | `d811347d71d9e73152328aaceb65b42d445a446b` |
| ai_sessions_commit | `bbe82892282e3989005e70ca9c4415f77866c563` |
| candidate_image_id | `sha256:f860e0c1fdba6ae68d6fc07a810127040e34ff76906f67e5caed606d4e4448d3` |
| worker_image_id | `sha256:8a126585777beeb62b147b63ee99096a8aedf0045e6454dd716e060c0725b341` |
| ai_sessions_image_id | `sha256:2ae14b56a819d2004086de11df930606a0fea4a4698763df1b715778772d9052` |

Evaluator digest: `d45dae8758cbf5270e34acc086d10a8191d5432ab1a7bb26e3f8d2649759b466`. Scenario, fixture, tools, documentation and CLI identities are recorded per trial in the [sanitized scored records](results/unified-2026-09-17.json).

All platform trials ran sequentially with subscription authentication, 600 agent seconds and 80 brokered CLI calls. Claude-based harnesses configured 30 turns; Codex bounded completed tool calls at 80. Dollar cost is unknown. Native token counters are retained without treating missing cache/input fields as zero.

Export uses Canada and a 64,000,000-byte command-output cap. Other scenarios use USA and 16,000,000 bytes. An initial export reference exceeded the smaller cap after fixture growth; the cap was adjusted before any scored export agent ran. No evaluator code or grading requirements changed. All six export agents use the same corrected cap.

## Context and calibration

All six isolated context probes passed before the platform trials. Bare excludes personal skills/settings/history and the LC corpus while retaining pinned documentation and CLI help; the skills treatment loads the pinned corpus through each harness’s native mechanism. Provider built-in context may remain. [Probe evidence](results/unified-2026-09-17-context.json) and [isolation contract](CONTEXT_PROFILES.md).

| Scenario | Positive reference | Deliberately bad reference | Cleanup |
|---|:---:|:---:|:---:|
| `access-key-rotation` | Pass | Expected fail | Clean |
| `case-maintain-records` | Pass | Expected fail | Clean |
| `cloudsec-findings-triage` | Pass | Expected fail | Clean |
| `config-reconcile-preserve` | Pass | Expected fail | Clean |
| `hive-preserve-update` | Pass | Expected fail | Clean |
| `native-sensor-onboarding` | Pass | Expected fail | Clean |
| `search-complete-export` | Pass | Expected fail | Clean |
| `webhook-production-routing` | Pass | Expected fail | Clean |

The 16 references validate fixtures and graders, not AI performance. Bad references must fail required assertions with complete evidence and normal execution. [Calibration records](results/unified-2026-09-17-calibration.json).

## Invalid infrastructure attempts

These attempts are excluded from the 48 scored cells and the 16 completed reference checks. They remain in `invalid_attempts` in the public records; all cleaned up before their replacements. No genuine agent failure was rerun to improve the matrix.

| Attempt | Reason |
|---|---|
| `unified-2026-09-17-11fc4b62d6` | Temporary receiver hostname failed DNS resolution before agent startup |
| `unified-2026-09-17-5a7a0a2781` | Temporary receiver hostname failed DNS resolution before agent startup |
| `unified-2026-09-17-ca013b0927` | Temporary receiver hostname failed DNS resolution before agent startup |
| `unified-2026-09-17-calibration-a6258ef4e7` | Reference search exceeded the original 16,000,000-byte command-output cap before calibration completed; export cap raised to 64,000,000 bytes before any scored export attempt |

The three receiver failures occurred before agent startup: temporary tunnel hostnames were not resolvable during startup but subsequently resolved. Each replacement used a fresh receiver and organization. The export reference failed at the broker output cap, after successful fixture readiness; it was not an agent attempt.

## Export readiness

Every scored export fixture must independently establish complete search visibility and a nonempty continuation page before launching the agent. The fixture can grow up to 25,000 events within its existing byte ceiling. Fixture size varies, so cross-harness timing is not a controlled speed comparison.

| Harness | Context | Fixture events | Pagination proven |
|---|---|---:|:---:|
| `claude_code` | `bare` | 5,140 | Yes |
| `claude_code` | `lc_ai` | 10,140 | Yes |
| `codex` | `bare` | 15,140 | Yes |
| `codex` | `lc_ai` | 10,140 | Yes |
| `ai_sessions` | `bare` | 15,140 | Yes |
| `ai_sessions` | `lc_ai` | 15,140 | Yes |

## Interpretation and known limitations

The native onboarding failure began with an empty installation key. The agent later found a valid key, but the evaluator deployment helper had already stopped watching after rejecting the first request. The result is retained, with the helper’s one-shot recovery limitation disclosed. It does not establish that the harness cannot onboard sensors generally.

Two routing agents achieved all required platform effects but did not complete normally: Claude Code bare reached its turn limit and AI Sessions bare reached the execution timeout. These are task passes with execution limits, not full passes.

AI Sessions runs the native coordinator and SDK bridge in a reduced local image, not the full hosted Workspace environment. Cloud Security does not grade acceptance-reason persistence, and key rotation does not claim revocation of existing JWTs. Organization creation/deletion belongs to the trusted controller and is not scored as agent work.

## Cleanup and reproduction

Final cleanup audit at **2026-09-17 23:29 UTC** checked all **74 campaign attempts/probes** and **68 owned organizations**, including invalid attempts. Exact organization inventory confirmed their absence. [Audit record](results/unified-2026-09-17-cleanup.json). The audit reported **0 remaining resources, 0 errors and 0 pending resources in the journal**. All 48 scored results, 16 completed references, six context probes and four invalid infrastructure attempts have clean teardown.

The implementation unit suite passed all **335 tests** before this campaign. Evaluator code remained frozen; subsequent changes only publish documentation and sanitized campaign evidence. Public evidence is allowlisted: no raw transcripts, credentials, receiver secrets or platform snapshots are committed.

See [Running evals](RUNNING.md#reproduce-the-unified-eight-eval-matrix) for scenario seeds, regions, profiles, calibration and cleanup steps. Subscription-based execution has time/turn/call limits, not a request-level dollar cap.
