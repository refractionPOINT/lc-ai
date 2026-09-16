# Initial live acceptance

**Status: PASS — 2026-09-16.** Eight genuine agent trials passed, covering Claude Code and Codex on all three scenarios plus a Hive repeat for each harness. All owned resources were cleaned.

Branch: `eval/limacharlie-cli-ai`. Final implementation: `6e1da53`. Validation: **193 tests passed; Ruff and diff checks clean**. The final CLI-only addition exposes targeted repetitions; live trials exercised the same controller, adapters and graders through the suite/controller interface.

## Results

| Scenario | Harness | Repetition | Region | Grade | Agent seconds | CLI calls |
|---|---|---:|---|---|---:|---:|
| hive-preserve-update | claude_code | 1 | usa | pass | 17.71 | 6 |
| hive-preserve-update | codex | 1 | usa | pass | 53.53 | 10 |
| webhook-production-routing | claude_code | 1 | usa | pass | 74.24 | 19 |
| webhook-production-routing | codex | 1 | usa | pass | 88.29 | 21 |
| hive-preserve-update | claude_code | 2 | usa | pass | 22.53 | 10 |
| hive-preserve-update | codex | 2 | usa | pass | 36.97 | 8 |
| search-complete-export | codex | 1 | canada | pass | 72.12 | 6 |
| search-complete-export | claude_code | 1 | canada | pass | 63.06 | 7 |

Both Hive A/A pairs are compatible and successful. They demonstrate comparison plumbing, not a statistically established performance difference. Export fixture sizes differ because readiness grows until actual pagination is observed; do not compare those two export timings as a controlled model or CLI benchmark.

## Independent proof

- Hive: exact target data, metadata preservation, unchanged distractors and record set, and target-identifying completion.
- Export: exact membership and values, unique IDs, bounded valid JSONL, safe artifact collection, and no platform mutations. Codex exported 15,003 production rows from 15,140 fixture events; Claude exported 20,003 from 20,140. Both readiness traces contain nonempty continuation pages.
- Routing: real hosted webhook ingestion, signed HTTPS delivery for matching probes, a full 180-second negative window, exclusion of negative probes, and preservation of the baseline output.
- Correct references pass; no-op Hive, truncated export, and overbroad routing references fail their intended assertions. `validate-suite --campaign calibration` exits 0.
- Live crash recovery `fault-05046ba64cc944b3` interrupted an acquired organization/key/container/network lifecycle and recovered all owned resources. Both native harness smokes passed.
- Expanded native-versus-broker parity `calibration-4313564b3f`: seven CLI checks and three isolation checks passed, including AI help and trailing global options.

## Accounting and retained attempts

Scored native usage totals: **1,728,358 total input tokens** (including provider-reported cache classes) and **16,032 output tokens**. These totals cover the eight scored trials only; earlier smoke, calibration and invalid attempts are retained separately. Native provider usage definitions differ, so cache and uncached classes remain separate in the JSON evidence.

Billing uses existing subscriptions. Dollar cost is unknown; no hard $50 cap is claimed. Each agent has 600 seconds including startup; Claude has 30 native turns, Codex has 80 completed tool calls, and both have 80 brokered CLI invocations. One live trial runs at a time.

Two USA export preparations failed before any agent started because all events fit in one nonempty page. They remain in the campaign’s ten recorded rows, excluded from scored totals and real-harness coverage. Two earlier Hive passes in campaign `initial-proof` were invalidated after broker-induced syntax errors; their traces and usage are preserved. The broker was fixed and the scored suite restarted.

Canada export calibration `calibration-c81636c596` passed after growth to 15,140 events. Production batches vary, so each fixture verifies full indexing and grows in bounded 5,000-event increments up to the configured ceiling, never above 25,000 events or 100 MB. A single-page fixture at the ceiling is unsupported, not a pagination pass.

## Cleanup and artifacts

The final exact-ownership audit passed across the main journal and four temporary probe journals: **zero pending resources, zero owned runtime leftovers, zero inventory errors**. It checked 36 organization records, 100 container records, 50 network records and four local-process records. These are historical records, not concurrent resources. The first audit checker misread Docker’s absent-network message; that failed checker output is retained and the corrected audit passed.

- [Sanitized machine-readable results](results/initial-proof-v2.json): every campaign row, usage, assertions, manifests, compatibility results and final audit counts.
- Private reports: `~/.local/share/lc-eval/reports/initial-proof-v2/{report.json,report.html,ACCEPTANCE.md}`.
- Private trial evidence: `~/.local/share/lc-eval/trials/<trial_id>/` (source manifests, command traces, frozen artifacts, grader evidence and fixture-growth traces).
- Private calibration/recovery evidence: `reference-validation.json`, `proof.json`, and `private/final-cleanup-audit.json` under the same run root.
- Raw credentials, receiver secrets and transcripts are not committed. Legacy region metadata is enriched only from persisted organization/journal evidence; original manifest files remain unchanged and their hashes are included in the sanitized results.

## Reproduce and extend

Follow the full configuration, reference, smoke, eight-trial and recovery sequence in [README.md](README.md) or [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Exact commands used for the final export retries and acceptance were:

```sh
./evals/.venv/bin/lc-eval run --config /home/maxime/.local/share/lc-eval/config-canada.json --campaign initial-proof-v2 --scenario search-complete-export --seed 42001 --adapter codex
./evals/.venv/bin/lc-eval run --config /home/maxime/.local/share/lc-eval/config-canada.json --campaign initial-proof-v2 --scenario search-complete-export --seed 42001 --adapter claude_code
PYTHONPATH=evals/src evals/.venv/bin/python /home/maxime/.local/share/lc-eval/private/final-audit.py
./evals/.venv/bin/lc-eval validate-suite --campaign calibration
./evals/.venv/bin/lc-eval report --campaign initial-proof-v2
./evals/.venv/bin/lc-eval acceptance --campaign initial-proof-v2
```

The controlled CLI profile intentionally covers only the initial scenario operations. Workspace remains explicitly unsupported pending its isolation contract. Cloud Security, native endpoint enrollment and the broader capability catalog are future scenario work; this proof does not claim all-platform coverage or evaluate cybersecurity judgment.
