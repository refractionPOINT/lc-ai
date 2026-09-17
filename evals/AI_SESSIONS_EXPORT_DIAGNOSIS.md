# AI Sessions export failure investigation

Investigated the retained `ai-sessions-proof-12ee4246a6` trial on 2026-09-16. This is an analysis of the original transcript and pinned sources, not a rerun or a change to its grade.

The immediate failure was an incorrect LCQL pipeline. The trace explains how it arose: production plugin instructions required a generator unavailable in the controlled eval, a research subagent misinterpreted mixed documentation and returned the wrong command, and the parent repeatedly debugged that command instead of consulting the leaf command help. A separate harness tool-policy discrepancy allowed that delegation despite an intended deny setting.

## Observed sequence

1. The parent tried `auth whoami --check-perm ai_agent.operate`. The broker rejected it. The loaded `lc-essentials/AUTOINIT.md` recommends this preflight.
2. It tried `ai generate-query`. The broker rejected it. Both the essentials AUTOINIT and the fundamentals search skill require generation and prohibit manually constructing LCQL. The public eval notice declared a narrower command surface, but no usable generation fallback was supplied by those skills.
3. It called `limacharlie search --ai-help`. The recorded response listed commands and options, and told it to drill down to leaf help. It did **not** include the full LCQL grammar or concrete pipeline examples present in `search run --ai-help` and `search validate --ai-help`.
4. It invoked the SDK's `Agent` tool for documentation research. That child made eight tool calls, reading the LCQL examples, query index, older interactive CLI guide, and fundamentals search skill.
5. The child incorrectly stated that only the raw query form includes the time/sensor/event-type prefix. Its answer actually contained a correct full raw query, but its proposed modern CLI command omitted the sensor selector. The parent adopted that command.
6. The parent repeatedly varied quoting, field paths, operators and string lengths while preserving the incorrect pipeline shape. It never called the detailed run/validate help and never issued `search run`.
7. The SDK emitted `error_max_turns`. There were 37 accepted CLI calls, 33 nonzero CLI exits, and three additional transport rejections. No `export.jsonl` was produced. The grader recorded six artifact failures and confirmed platform state was unchanged.

The attempted shape was:

```text
LC_EVAL_EXPORT | event/environment == 'production'
```

The working shape, also used by the independent fixture/reference, is:

```text
* | LC_EVAL_EXPORT | event/environment == 'production'
```

The complete task query also needs the supplied `eval_trial_id` filter and time bounds. Removing the raw time prefix does not remove the sensor-selector position. `--stream event` selects the telemetry stream, not the sensor selector or event-type clause.

## Contributing guidance and configuration issues

**Conflicting workflow and available commands.** The loaded skills prescribe `ai generate-query` and regeneration on validation failure. That command is outside `controlled-cli-v1`. They also say to report after three failures; the agent did not follow that recovery rule. The mismatch explains why its prescribed starting path was blocked, but does not excuse the subsequent unproductive loop.

**Mixed documentation and an incorrect research summary.** `documentation/docs/4-data-queries/index.md` contains filter-only modern CLI examples; `query-cli.md` describes the older interactive `set_sensors` / `set_events` / `q` interface. `lcql-examples.md` mostly contains full raw queries with time and sensor components. These are easy to conflate, but the exact incorrect two-component command was constructed by the child, not directly copied from a source. Correct three-component examples were available in leaf CLI help. The parent later even read examples with the sensor component through Grep, yet did not correct its pipeline.

**Weak recovery from diagnostics.** Validation returned parser offsets and expected grammar characters. The parent spent calls inspecting string positions and sweeping query prefixes, rather than revisiting the pipeline grammar. Better contextual error messages could help prevent this failure mode; a controlled rerun would be needed to measure their effect.

**Unintended delegation.** `execution/workspace_runner.py` lists `Task` in `DENIED_TOOLS`, but not `Agent`. The transcript proves an `Agent` child ran: its events carry `parent_tool_use_id`, and its tool result reports eight tool uses. Moreover, the native bridge seeds custom permission patterns rather than setting SDK `allowed_tools` / `disallowed_tools`; the allow list must not be assumed to restrict every built-in tool. A native SDK test is needed to verify any correction, rather than only testing the configured strings. The global trial timeout and broker bounds still applied; this run does not establish an enforced no-delegation profile.

**Trace normalization gap.** The native bridge emits tool results inside `user.payload.content` blocks. The current adapter only normalizes standalone `tool_result` events. The raw transcript retains those results, and the broker records LC calls, so the investigation and state grading remain possible. Normalized tool-result coverage needs improvement; this did not cause the model's query failure.

## Comparison with successful runs

Both retained successful export baselines consulted the detailed leaf help before searching:

- Codex: `initial-proof-v2-e06caa68d1` called `search run --help` and `search run --ai-help`, then used `* | LC_EVAL_EXPORT | ...`.
- Claude Code: `initial-proof-v2-66b49892a8` called `search run --ai-help` and used sensor/event/filter pipelines during its searches.

This comparison identifies a concrete discovery difference. It does not establish that changing one instruction guarantees success: the runner's plugin context and bundled Claude executable also differ from the standalone baseline.

## Follow-up order

1. Choose and document the intended operating profile: support the production query-generation workflow with appropriate scoped authority/accounting, or supply consistent instructions for the restricted manual-query profile. Do not silently mix them.
2. Make delegation policy explicit and verify it against the real SDK, covering both `Agent` and `Task`; retain parent/child identity and nested tool results in normalized telemetry.
3. Put a canonical modern CLI pipeline example in short search help and align the related documentation. Improve malformed-pipeline diagnostics so the missing selector is discoverable.
4. Run small syntax/tool-policy probes, then repeat the full export trial under new recorded fingerprints. Preserve the existing failed attempt.

No model calls, platform mutations or additional live trials were performed for this investigation. Existing scores and cleanup evidence are unchanged. See [the original proof](AI_SESSIONS_PROOF.md) and [sanitized results](results/ai-sessions-proof.json).

Source anchors inspected at the proof's pinned revisions:

- `lc-ai/marketplace/plugins/lc-essentials/AUTOINIT.md:147-223`
- `lc-ai/marketplace/plugins/lc-fundamentals/skills/search-and-query/SKILL.md:13-58`
- `documentation/docs/4-data-queries/lcql-examples.md:15-21,40,48`
- `documentation/docs/4-data-queries/index.md:91-103,134-139`
- `documentation/docs/4-data-queries/query-cli.md:5-15,23-42`
- `python-limacharlie/limacharlie/commands/search.py:1164-1217,1749-1759`
- `lc-ai/evals/src/lc_eval/execution/workspace_runner.py:29-30`
- `ai-sessions/scripts/bridge/claude_native.py:753-764`

## Remediation progress

- Implemented explicit restricted-profile instructions through the native system-prompt suffix and shared CLI notice, directing agents to detailed installed command help. Production plugins remain pinned and loaded.
- Implemented a fingerprinted eval-only SDK overlay restricting built-in tools and denying both delegation names, with an actual startup inventory check. The source repository is unchanged.
- Preserved nested tool-result content, errors, and parent/child identity in normalized events.
- Added native smoke checks for delegation availability and leaf-help access. All 230 offline tests passed. A real native smoke passed after correcting its startup-call allowance; a fresh export trial passed all seven assertions and cleaned its organization. See the [retest record](AI_SESSIONS_EXPORT_RETEST.md).
- Upstream CLI/doc changes and better parser errors remain separate follow-ups; this experiment changes the local profile and harness, not the pinned CLI or platform grammar.
