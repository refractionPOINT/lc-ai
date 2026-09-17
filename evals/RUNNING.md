# Running evals

Run commands from `lc-ai`. Live runs create real disposable LimaCharlie organizations and use the configured model subscriptions. Each trial provisions, executes, verifies and cleans up automatically.

## Run one existing eval

For an already configured installation, choose a new campaign name and the configuration calibrated for the scenario:

```sh
./evals/.venv/bin/lc-eval doctor --config /absolute/private/lc-eval-usa.json
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign hive-check-001 --scenario hive-preserve-update --adapter codex --context bare --seed 41001
./evals/.venv/bin/lc-eval report --config /absolute/private/lc-eval-usa.json --campaign hive-check-001
```

Replace `codex` with `claude_code` or `ai_sessions` for the other harnesses, and use `--context lc_ai` for pinned LC skills. `report` writes private JSON and HTML paths; it does not start a model. Reusing a campaign name appends trials rather than resuming or replacing an old trial.

| Scenario | Calibrated location | What it checks |
|---|---|---|
| `hive-preserve-update` | `usa` | Update the intended data while preserving metadata and unrelated records. |
| `search-complete-export` | `canada` | Export the exact matching dataset, including real continuation pages. |
| `webhook-production-routing` | `usa` | Configure ingestion and automation with real signed output delivery and negative probes. |
| `config-reconcile-preserve` | `usa` | Reconcile lookup and D&R configuration while preserving unrelated records. |
| `case-maintain-records` | `usa` | Discover and maintain an existing case and preserve surrounding records. |
| `cloudsec-findings-triage` | `usa` | Apply supplied finding owners and dispositions. |
| `access-key-rotation` | `usa` | Replace a scoped key and verify fresh authentication with the old key is denied. |
| `native-sensor-onboarding` | `usa` | Enroll and configure a real sensor in an evaluator-owned container. |

These are the locations exercised by the current campaign, not guarantees about other regions. Export preparation can take 20–30 minutes or longer as the fixture grows and indexing converges. Preparation and verification are separate from the 600-second agent execution allowance.

A single-scenario campaign is useful on its own. `acceptance` checks the initial three-scenario/two-harness milestone, so it will not pass for an intentionally partial campaign.

## First-time setup

Requirements: Python 3.11+, Docker, an authenticated `limacharlie` executable, authenticated local Claude Code and Codex, and clean sibling `python-limacharlie` and `documentation` checkouts. Run from `lc-ai`:

```sh
./evals/scripts/bootstrap.sh
./evals/.venv/bin/lc-eval init-local --subscription
./evals/.venv/bin/lc-eval doctor
./evals/.venv/bin/lc-eval build
./evals/.venv/bin/pytest evals/tests/unit -q
```

Configuration defaults to `~/.local/share/lc-eval/config.json`. Review its source commits, model selections, timeout/turn limits, and authentication **paths**. Runtime data, copied credentials, raw transcripts, and receipts are private and stay outside the checkout. Source artifacts are built from the recorded commits; Docker image digests and native harness binary hashes are recorded.

The configuration is schema version 1 and rejects unknown fields. Its top-level fields are `run_data_dir`, `sources`, `lc`, `receiver`, `agents`, optional `context` skill-source pin and `ai_sessions` image/source identity, `limits`, `suite`, `seed`, and `profile`. `lc.location` is a literal organization-creation location for every trial selected by one command. `agents` pins the adapter, executable/version, model, effort, auth mode/file, 600-second execution timeout, and Claude turn limit. `limits` contains the single-trial concurrency, organization/event/byte ceilings, CLI command bounds, verification windows, lease duration, and billing mode. `init-local --subscription` writes JSON, which is also valid YAML; edit only non-secret values and paths.

The campaign billing mode is **subscription_limits**: one trial at a time, 600 seconds per agent including harness startup, Claude 30 turns, a single Codex `exec` turn bounded to 80 completed tool calls, and 80 CLI invocations. Token counts come from native harness streams; uncached, cached, cache-write, total input, and output counts remain distinct when the provider reports them. Dollar cost is unknown. The optional request-budget gateway is separate and is not wired into the subscription controller.

## Run through the AI Sessions runner

The `ai_sessions` adapter exercises the native Go AI Sessions session runner and its packaged Python SDK bridge locally. Build its pinned image after the normal candidate image; building the Go binary also requires the Go toolchain declared by the pinned `ai-sessions/go.mod`. The default sibling checkout is `../ai-sessions`; pass `--source` when it is elsewhere:

```sh
./evals/.venv/bin/lc-eval build-ai-sessions --config /absolute/private/lc-eval-usa.json --source ../ai-sessions
./evals/.venv/bin/lc-eval smoke --config /absolute/private/lc-eval-usa.json --campaign ai-sessions-smoke --adapter ai_sessions
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign ai-sessions-check --scenario hive-preserve-update --adapter ai_sessions --seed 41001
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign ai-sessions-check --scenario webhook-production-routing --adapter ai_sessions --seed 43001
# Use the Canada configuration for the existing export fixture, with the same source/model pins.
./evals/.venv/bin/lc-eval build-ai-sessions --config /absolute/private/lc-eval-canada.json --source ../ai-sessions
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-canada.json --campaign ai-sessions-check --scenario search-complete-export --adapter ai_sessions --seed 42001
./evals/.venv/bin/lc-eval report --config /absolute/private/lc-eval-usa.json --campaign ai-sessions-check
```

`build-ai-sessions` archives the recorded commits rather than the sibling working trees. It derives a reduced eval image from the pinned candidate image and adds the real Go coordinator, SDK bridge, runtime plugins, selected public `lc-ai` catalogues, and documentation. It intentionally omits the production runner image's unrelated cloud and analysis tools. The resulting image, source commits, archive hashes, SDK versions, and Go binary hash are saved in the configuration and private build manifest.

The controlled profile appends explicit instructions after the production plugin instructions: authentication is already supplied, query generation is unavailable, and manual LCQL should use the installed leaf command help. These instructions are generic across scenarios; they contain no fixture answers.

The reduced image applies an eval-only overlay to the archived native bridge. It sets the SDK built-in tool inventory and denies both `Agent` and `Task` plus scheduling tools, while preserving native permission callbacks. Build manifests record the original bridge, patched bridge, and overlay hashes; image tags include the build key. SDK startup inventories are retained in the transcript. `smoke --adapter ai_sessions` verifies the actual inventory, absence of child calls, and access to detailed search help before a full trial. The native smoke allows eight CLI calls to include startup discovery; full trials retain their 80-call bound. Rebuild older images before using this smoke check. This validates the local restricted profile, not production Workspace permissions.

The command initially clones the Claude subscription profile into an `ai_sessions` agent entry, including its model, credential-file path, timeout, and turn ceiling. Later builds preserve that entry’s settings. AI Sessions uses the provider's native effort behavior, recorded as `native_default`; it does not apply the Claude Code adapter's effort setting. Usage comes from native runner events. Cache totals may remain unknown when the bridge does not report them, and subscription runs do not claim dollar billing.

Use an explicit `--scenario` for `ai_sessions`; the default suite still declares the original Claude Code/Codex matrix. The report’s `initial-loop` acceptance section checks only its fixed three-scenario/two-harness matrix, not the full eight-eval campaign.

This local adapter tests runner and bridge behavior inside the eval isolation boundary. It does not emulate or validate the hosted AI Sessions workspace service. The brokered `limacharlie` transport, independent graders and cleanup rules apply to all harnesses. See the [current results](README.md) for all eight scenarios in both context profiles.

## Calibrate and run a complete campaign

Create two non-secret configuration copies that share one private run directory. Export uses Canada and a 64 MB command-output cap; the other scenarios use USA and 16 MB. Pin `context.lc_ai` and build the AI Sessions image as described above before copying the configuration. The files contain credential **paths**, never credential values. Replace the generic directory below with an absolute private path:

```sh
./evals/.venv/bin/lc-eval init-local --subscription --config /absolute/private/lc-eval-base.json
./evals/.venv/bin/lc-eval doctor --offline --config /absolute/private/lc-eval-base.json
./evals/.venv/bin/lc-eval build --config /absolute/private/lc-eval-base.json
python3 - <<'PY'
import json
from pathlib import Path

base = Path("/absolute/private/lc-eval-base.json")
value = json.loads(base.read_text())
for region in ("usa", "canada"):
    regional = json.loads(json.dumps(value))
    regional["lc"]["location"] = region
    regional["limits"]["max_command_output"] = 64_000_000 if region == "canada" else 16_000_000
    destination = base.with_name(f"lc-eval-{region}.json")
    destination.write_text(json.dumps(regional, indent=2) + "\n")
    destination.chmod(0o600)
PY
./evals/.venv/bin/lc-eval doctor --config /absolute/private/lc-eval-usa.json
./evals/.venv/bin/lc-eval doctor --config /absolute/private/lc-eval-canada.json
```

Run all six context probes and the scenario-specific positive/negative references before the scored trials. Follow the [full matrix](#reproduce-the-unified-eight-eval-matrix) for seeds and the eight scenarios × three harnesses × two contexts. For example:

```sh
./evals/.venv/bin/lc-eval context-probe --config /absolute/private/lc-eval-usa.json --campaign context-check --adapter codex --context bare
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign calibration --scenario hive-preserve-update --seed 41001 --context bare --reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign calibration --scenario hive-preserve-update --seed 41001 --context bare --bad-reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign evaluation-001 --scenario hive-preserve-update --adapter codex --context bare --seed 41001
./evals/.venv/bin/lc-eval cleanup --config /absolute/private/lc-eval-usa.json
./evals/.venv/bin/lc-eval report --config /absolute/private/lc-eval-usa.json --campaign evaluation-001
./evals/.venv/bin/lc-eval status --config /absolute/private/lc-eval-usa.json
```

The bad reference must exit 1 and fail its intended task assertions. Inspect execution and cleanup separately before continuing.

The targeted `--repetition` option defaults to 1, accepts integers of at least 1 only with `--scenario`, and leaves suite-defined repetitions unchanged.

Every trial gets a disposable organization in the configured location. The calibrated region pins are `canada` for export and `usa` for the other seven scenarios. Because `lc.location` is configuration-wide, use USA- and Canada-pinned configuration files for scenario-targeted live runs; `run` without `--scenario` executes all eight suite entries at one configured location and does not reproduce the current matrix.

Export starts with 5,003 matching and 137 nonmatching events, then adds 5,000 production events per stage until search returns a nonempty continuation or a configured ceiling is reached. The hard schema ceilings are 25,000 events and 100 MB; lower `limits.max_events` and `limits.max_fixture_bytes` values are honored and each growth stage is recorded. The current campaign proved pagination with fixtures of 5,140–15,140 events; see the [campaign evidence](UNIFIED_PROOF.md#export-readiness). Live export preparation can take 20–30 minutes under the free-tier ingestion ceiling; the 600-second agent timer begins after preparation.

Fresh Insight datasets can take time to initialize; readiness retries fresh bounded queries rather than repeatedly polling a failed query ID. The controller journals creation intent before creating resources, uses a separate scoped CLI worker, freezes artifacts after stopping execution, reads platform state with independent HTTP verification, and attempts cleanup in a `finally` path. `cleanup` reconciles exact owned resources after interruption; never run a broad organization deletion command. An unresolved cleanup stops the campaign.

The candidate container receives the public task and documentation. Its `limacharlie` executable is a transport to the pinned real CLI in a separate worker. The worker has the trial key; the agent has no LimaCharlie credentials. Agent and worker networks have separate restricted HTTPS proxies. Harness subscription material is isolated from the user's original files. The controller, graders, private fixtures, journal, and receiver administration stay outside both containers.

JSON and HTML reports are written under the private run directory. A failed task is distinct from an incomplete observation or cleanup failure. Missing usage stays unknown. A/A comparisons require compatible manifests and measure efficiency only for paired successes. The results README records the eight calibrated workflows; the capability catalog tracks broader platform coverage.


## Inspect failures and recover

Read the trial's `execution_status`, `grade`, `evidence_complete`, `agent_attempted`, and `cleanup_status` separately. A pre-agent setup failure is infrastructure evidence, not a scored model attempt. A completed agent's failed task remains a real failure. Missing usage is unknown, not zero.

| Exit | Meaning |
|---|---|
| 0 | Selected run succeeded, or the requested report/check completed successfully. |
| 1 | Graded task failure, expected bad-reference failure, or failed acceptance/reference validation. |
| 2 | CLI usage/configuration selection error. |
| 3 | Run infrastructure failure, inconclusive observation, or non-completed execution. |
| 4 | Unresolved resources/cleanup failure; do not start another trial. |

Inspect command output and the persisted result as well as the exit code; unexpected exceptions may also return a generic nonzero exit.

After interruption, use the same private configuration/run directory:

```sh
./evals/.venv/bin/lc-eval status --config /absolute/private/lc-eval-usa.json
./evals/.venv/bin/lc-eval cleanup --config /absolute/private/lc-eval-usa.json
./evals/.venv/bin/lc-eval report --config /absolute/private/lc-eval-usa.json --campaign evaluation-001
```

Cleanup reconciles exact ledger-owned resources. Do not delete unrelated organizations or broadly prune Docker. An active controller owns the run-directory lock; allow it to finish or stop it before recovery. Do not erase a ledger to bypass the cleanup gate.

Under the private run directory, inspect:

- `journal.sqlite` and `trials/<trial_id>/manifest.json`: lifecycle, ownership and experiment identity.
- `public-spec.json`, `commands.jsonl`, `agent.stdout`, `agent.stderr`: public task and execution evidence. Raw traces remain private.
- `webhook-warmup.json`, `injection-progress.json`, `readiness.json`, `fixture-growth.json`: export setup progress, when applicable.
- `frozen.json`, `evidence.json`, `assertions.json`, `result.json`: frozen deliverables and independent grading.
- `reports/<campaign>/report.json` and `report.html`: outcomes, metrics and comparisons.

## Compare changes deliberately

Keep source/model/docs/permissions/region/limits fixed for a repeat experiment. A targeted `--repetition 2` triggers the existing A/A pairing logic against repetition 1 for the same scenario, harness and seed; the report then checks compatibility. It does not make unrelated trials comparable. Current automatic repeat pairing is limited to repetition 2.

For a CLI experiment, pin and build the new CLI revision in a deliberate configuration copy, retain the baseline configuration and results, and keep other controlled inputs fixed. Use paired-success metrics only when compatibility passes. Adaptive export sizes can differ, so do not read raw cross-harness timings as a controlled comparison. The small initial sample establishes the workflow, not statistical significance.

The current `run` implementation reads `suites/initial-loop.yaml` directly when `--scenario` is omitted. The configuration's `suite` field does not yet select an arbitrary suite. `validate-suite` and `acceptance` are also wired to the initial milestone; see [adding evals](ADDING_EVALS.md) before expanding them.

## Compare bare and lc-ai skills contexts

Use explicit `--context bare` or `--context lc_ai` for new comparisons. `legacy` preserves old launch behavior and must not be relabeled as either experimental profile. Bare runs retain pinned CLI help, public documentation and provider built-ins, while excluding personal settings, personal skills and the LC skill corpus. Skills-enabled runs add the committed corpus from four LC plugins, including required shared constants and compliance references. Standalone copies rewrite plugin-relative paths to their isolated support mount and record both original and transformed hashes.

Set `context.lc_ai` in the private configuration to a source pin with `path` (absolute lc-ai checkout path), `commit` (full Git object ID), and `dirty` (checkout metadata). Only the named commit is archived. For AI Sessions, this commit must equal the image's `ai_sessions.lc_ai.commit`; rebuild its image when changing the source or evaluator launcher.

Standalone harnesses receive native user skills with plugin-prefixed names. AI Sessions uses its native plugin loading, including plugin initialization context. Reports disclose these delivery differences; equal corpus contents do not imply identical harness prompts.

```sh
./evals/.venv/bin/lc-eval context-probe --config /absolute/private/lc-eval-usa.json --campaign context-check --adapter claude_code --context bare
./evals/.venv/bin/lc-eval context-probe --config /absolute/private/lc-eval-usa.json --campaign context-check --adapter claude_code --context lc_ai
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign context-comparison --scenario config-reconcile-preserve --adapter claude_code --context bare --seed 51002
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign context-comparison --scenario config-reconcile-preserve --adapter claude_code --context lc_ai --seed 51002
```

Repeat with `codex` or `ai_sessions`. Context probes use no LimaCharlie organization or platform authority and enforce a 90-second execution limit, with eight configured turns for Claude-based harnesses and 80 completed tool calls for Codex. They record native transcript evidence alongside filesystem checks. Run them before spending a full trial on a new profile. Reports separate context identities; differing contexts are intentionally excluded from ordinary A/A efficiency comparisons.

## Expansion workflows

The registered expansion scenarios are `case-maintain-records`, `native-sensor-onboarding`, `cloudsec-findings-triage`, `config-reconcile-preserve`, and `access-key-rotation`. Consult the results page for live calibration status before treating a run as a benchmark.

Cases requires `lc.readiness_seconds >= 360` (default 600). Provisioning waits at least 315 seconds after tenant readiness to expire the backend subscribed-tenant cache, then verifies all seeded cases and detection links are list-visible. This setup time is outside the agent execution limit. Cases maintenance uses an existing case for partial/distractor seeds (`seed % 3` equals 1 or 2). The clean variant remains explicitly disabled pending separate calibration. The current campaign includes the merged CLI detection-encoding fix; see [CLI findings](CLI_FINDINGS.md). Trusted fixture seeding uses the generic extension request with the deployed encoding. Agent operations remain native case commands. Fixture readiness must account for the Cases subscribed-tenant cache before candidate listing; positive references must discover through the same native listing.

Native onboarding downloads the real Linux sensor, records its binary hash, and deploys it in an evaluator-owned container through `/work/endpoint-deployment.json`. It never installs the sensor on the operator's host. Its private sensor-data tmpfs permits loading the sensor’s signed modules; the root filesystem remains read-only, with no host mounts or added capabilities. A normal Docker bridge supplies native sensor connectivity; the candidate's own model/CLI egress boundary remains unchanged.

Cloud Security uses pushed SARIF to seed real findings. It grades owner and disposition; acceptance-reason persistence is not returned by the backend and is outside the task requirements. Key rotation verifies replacement credentials, read-only authority, and denial of fresh authentication with the deleted key; it does not claim that previously issued JWTs are revoked. Configuration reconciliation covers named lookup and D&R records with already-correct/stale variants and unrelated records.

Before a real-agent campaign, run the scenario once with `--reference` and once with `--bad-reference`, using a calibrated seed. A correct reference must pass; the bad reference must complete, fail its intended task assertions, and clean up. The initial `validate-suite`/`acceptance` commands still describe the original three-scenario milestone and do not certify the expansion automatically.

## Reproduce the unified eight-eval matrix

The unified campaign uses eight scenarios × three harnesses × two contexts (48
agent trials), plus six context probes and 16 reference checks. Use a new campaign
name, rebuild both images from deliberate source pins, and make USA/Canada config
copies that share the same private run directory. Export uses Canada and a
64,000,000-byte `limits.max_command_output` cap; the other scenarios use USA and
16,000,000 bytes. Keep the other configuration inputs fixed. The [campaign record](UNIFIED_PROOF.md) lists the published pins.

Run scenarios sequentially; never parallelize live trials. Use these seeds:

| Scenario | Region | Seed |
|---|---|---:|
| `hive-preserve-update` | USA | 41001 |
| `search-complete-export` | Canada | 42001 |
| `webhook-production-routing` | USA | 43001 |
| `config-reconcile-preserve` | USA | 51002 |
| `case-maintain-records` | USA | 51002 |
| `cloudsec-findings-triage` | USA | 51002 |
| `access-key-rotation` | USA | 51002 |
| `native-sensor-onboarding` | USA | 51002 |

For each scenario, run `--reference` and `--bad-reference` first. Verify that the
positive reference passes and the negative reference fails its intended assertions,
with completed execution and clean teardown. Then run each of `claude_code`, `codex`
and `ai_sessions` once with `--context bare` and once with `--context lc_ai`, using
the same campaign name, seed and source pins. Before the first platform trial, run
`context-probe` for all six harness/context combinations.

Keep an attempt ledger. A completed task failure is a result, not a reason to
silently retry. Stop and investigate infrastructure failures; disclose any invalid
attempt and its replacement. Stop immediately on unresolved cleanup. Finish with
`cleanup` (which audits exact owned organizations), generate the private campaign
report and publish only reviewed, sanitized evidence. The original `acceptance`
command checks the earlier milestone and does not certify this full matrix.
