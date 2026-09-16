# AI Sessions runner proof — 2026-09-16

The local `ai_sessions` harness completed the full run–grade–cleanup loop for all three existing scenarios. **Two tasks passed; complete search export failed.** The failure is retained as a scored agent attempt, not relabeled as infrastructure or rerun until successful.

Implementation: `941fa4d`. Machine-readable evidence: [sanitized results](results/ai-sessions-proof.json). Run commands: [Running evals](RUNNING.md#run-through-the-ai-sessions-runner).

## Results

| Scenario | LC region | Grade | Agent seconds | CLI calls | Failed CLI calls | Output tokens | Cleanup |
|---|---|---|---:|---:|---:|---:|---|
| Hive preservation update | USA | Pass | 36.1 | 7 | 0 | 1,653 | Clean |
| Production webhook routing | USA | Pass | 95.7 | 16 | 0 | 6,040 | Clean |
| Complete search export | Canada | **Fail** | 359.2 | 37 | 33 | 23,098 | Clean |

CLI calls count accepted broker executions. Additional rejected requests were 1, 1 and 3 respectively. These are single trials, not estimates of repeatability or a controlled performance comparison with standalone Claude Code or Codex.

- Hive passed all five assertions: exact target data and metadata, unchanged distractors and record set, and an identified deliverable.
- Routing passed all six assertions: ingested probes, receiver health, the full observation window, matching signed deliveries, excluded negatives, and unchanged baseline output.
- Export preparation independently confirmed all 20,140 fixture events were searchable with real continuation pages. The task required exactly 20,003 production events. The agent did not create `export.jsonl`; six artifact assertions failed, while the platform-unchanged assertion passed.

The export agent repeatedly validated queries beginning `LC_EVAL_EXPORT | ...`. The working LCQL structure used by the independent fixture and reference includes the sensor selector: `* | LC_EVAL_EXPORT | ...`. It explored invalid variants and exhausted its turn allowance without executing a successful export. The native result was `error_max_turns`: the configured cap was 30, and the SDK reported `num_turns: 31` in its terminal result. The evaluator records completed harness execution separately from the failed task grade.

## Runtime and bounds

This used the genuine Go `session-runner` and its Python bridge from `ai-sessions` commit `bbe82892282e3989005e70ca9c4415f77866c563`, with a local evaluator control plane for configuration, task delivery and native event collection. It used the existing Claude subscription with model `claude-sonnet-5`.

- Runner image: `sha256:f0e4f9ab07ef73106fe558ad30da6c7c96f31bbb2a0b5414213a055f76ccd04b`.
- Claude Agent SDK: `0.1.63`; its bundled Claude Code executable reported `2.1.114`.
- `lc-ai` plugins/catalogues: commit `8ab473d023dc6a07dc285149d14cef8e36519a58`.
- Documentation: commit `3eeeb95207730af2e93f600ca93cdad82ef47f73`.
- CLI source: commit `fe67856c4cdd1265b0b90a452247b1fb395f7d08`.
- Limits: one live trial at a time, 600 seconds per agent, configured 30-turn ceiling, 80 brokered CLI calls. Fixture preparation and verification are separate phases.

The image includes the native coordinator, bridge, four explicitly selected LC plugins, native terminal cards, catalogues and documentation. It is a reduced dependency image; this does not prove the hosted Workspace service, other model providers, or the production container's unrelated cloud tools. Scenarios, broker policy and independent graders were unchanged.

Effort is recorded as `native_default`. Native events provide uncached input and output counts but omit cache classes and total input. Those fields remain unknown. Estimated native dollar amounts are not treated as subscription billing; reported dollar cost is unknown.

## Retained setup attempts and cleanup

The final real-agent smoke passed in 10.2 seconds. Two earlier smoke startup attempts failed before a native provider result. Diagnostic capture exposed the production wrapper's per-UID process limit counting the host user's threads; the runner now uses a distinct non-root UID while retaining the existing container limits and scoped CLI broker.

One webhook attempt failed before agent execution because its temporary public receiver hostname did not resolve. It remains an inconclusive infrastructure record. A fresh receiver succeeded on the next attempt.

Every recorded trial was cleaned, including failed setup attempts and the failed export. The independent cleanup audit found no unresolved resources. Raw transcripts, credentials, receipt bodies and full fixture evidence remain in the private run directory outside the checkout.

The report's original initial-loop acceptance matrix still targets Claude Code and Codex, including their repeats and fault drill. This is a separately scoped AI Sessions harness proof; its task success rate is **2/3**.
