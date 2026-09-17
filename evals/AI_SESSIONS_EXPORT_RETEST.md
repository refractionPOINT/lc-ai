# AI Sessions export retest — 2026-09-16

This is a new experiment following the [export failure investigation](AI_SESSIONS_EXPORT_DIAGNOSIS.md). The original failed trial and its grade are preserved. Implementation commits: `6a0bf7e`, `e40cbf6`.

## Changes under test

- The shared controlled-CLI notice and native system-prompt suffix explicitly override incompatible production workflows: transport authentication is already supplied, query generation is unavailable, and manual queries should follow detailed installed CLI help.
- A fingerprinted eval-only overlay restricts the SDK built-in tool inventory and denies both `Agent` and `Task` plus scheduling tools. Native permission callbacks remain in place. This is not a change to production Workspace.
- Normalized telemetry retains native nested tool results and parent/child identity. Offline replay of the original failure recovered all 39 tool results and retained parent identity on 16 child events.

The model (`claude-sonnet-5`), native effort, CLI, native source, production plugins, documentation, seed (`42001`), region (Canada), and full-trial limits remain pinned to the original experiment. The runner image and evaluator code changed. This is a combined remediation test, not an attribution experiment for any single change or a statistically meaningful performance comparison.

## Verification

All 230 offline tests and Ruff checks passed. The real native smoke trial `ai-sessions-export-fix-smoke-9acf2b9c07` passed in 8.8 seconds. The SDK reported exactly `Bash`, `Edit`, `Glob`, `Grep`, `Read`, `Skill`, and `Write`; there were no forbidden tool calls or child events, and the installed leaf help was retrieved with its correct pipeline example.

The earlier smoke `ai-sessions-export-fix-smoke-9136a5557c` is retained as failed: native startup discovery consumed the original four CLI calls before the leaf-help probe. Its tool-inventory checks passed. The smoke-only CLI allowance was increased to eight; the full trial remains limited to 600 agent seconds, configured 30 turns and 80 CLI calls, one live trial at a time. Both smoke attempts were cleaned.

## Live result

Fresh trial `ai-sessions-export-fix-29213a234c` **passed all seven assertions**, completed its lifecycle, and cleaned its test organization. The independent cleanup audit found zero remaining resources and no errors. [Sanitized results](results/ai-sessions-export-fix.json) retain the image, overlay, source and evaluator fingerprints.

| Metric | Result |
|---|---:|
| Exported matching rows | 5,003 |
| Agent execution | 69.7 seconds |
| Accepted CLI calls | 7 |
| Failed / rejected CLI calls | 0 / 0 |
| Native reported turns | 12 |
| Output tokens | 3,163 |
| Normalized tool results | 11 |
| Child events | 0 |

The agent read the detailed run and validation help, validated a correct query, executed the search, and produced the exact JSONL artifact. All membership, uniqueness, field/value, row-count, safe-file, bounded-JSONL, and platform-preservation assertions passed.

The fixture became ready at 5,140 total events (5,003 production and 137 nonmatching), with independent search pages containing 4,752, 388 and zero events. This proves a nonempty continuation, but the fixture was smaller than the original 20,140-event attempt. Consequently, the raw timing/token differences are descriptive, not a measured speedup or a success-rate estimate. The full lifecycle took 605.2 seconds, including provisioning, ingestion, readiness, execution, verification and cleanup.

Subscription dollar cost and unreported cache/input totals remain unknown. The original failed export remains unchanged in its own campaign; this fresh result does not replace it. The other two scenarios were not rerun under the revised profile.
