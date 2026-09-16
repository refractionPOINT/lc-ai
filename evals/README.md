# LimaCharlie CLI agent eval

This evaluates whether an agent can operate LimaCharlie through its CLI. It measures task outcomes, preservation, complete data retrieval, real output delivery, and operational efficiency. It does not measure cybersecurity judgment.

The initial suite contains three scenarios: preserve and update a Hive lookup; export a complete paginated event dataset; and configure hosted webhook ingestion, production-only automation, and signed webhook delivery. Claude Code and Codex adapters use fresh isolated sessions. Workspace is explicitly unsupported until its isolation contract is verified.

## Local setup

Requirements: Python 3.11+, Docker, an authenticated `limacharlie` executable, authenticated local Claude Code and Codex, and clean sibling `python-limacharlie` and `documentation` checkouts. Run from `lc-ai`:

```sh
./evals/scripts/bootstrap.sh
./evals/.venv/bin/lc-eval init-local --subscription
./evals/.venv/bin/lc-eval doctor
./evals/.venv/bin/lc-eval build
./evals/.venv/bin/pytest evals/tests/unit -q
```

Configuration defaults to `~/.local/share/lc-eval/config.json`. Review its source commits, model selections, timeout/turn limits, and authentication **paths**. Runtime data, copied credentials, raw transcripts, and receipts are private and stay outside the checkout. Source artifacts are built from the recorded commits; Docker image digests and native harness binary hashes are recorded.

The configuration is schema version 1 and rejects unknown fields. Its top-level fields are `run_data_dir`, `sources`, `lc`, `receiver`, `agents`, `limits`, `suite`, `seed`, and `profile`. `lc.location` is a literal organization-creation location for every trial selected by one command. `agents` pins the adapter, executable/version, model, effort, auth mode/file, 600-second execution timeout, and Claude turn limit. `limits` contains the single-trial concurrency, organization/event/byte ceilings, CLI command bounds, verification windows, lease duration, and billing mode. `init-local --subscription` writes JSON, which is also valid YAML; edit only non-secret values and paths.

The initial authorized billing mode is **subscription_limits**: one trial at a time, 600 seconds per agent including harness startup, Claude 30 turns, a single Codex `exec` turn bounded to 80 completed tool calls, and 80 CLI invocations. Token counts come from native harness streams; uncached, cached, cache-write, total input, and output counts remain distinct when the provider reports them. Dollar cost is unknown. The optional request-budget gateway is separate and is not wired into the subscription controller.

## Run and inspect

Create two non-secret configuration copies that share one private run directory and differ only in the explicit LC region. The files contain credential **paths**, never credential values. Replace the generic directory below with an absolute private path:

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
    destination = base.with_name(f"lc-eval-{region}.json")
    destination.write_text(json.dumps(regional, indent=2) + "\n")
    destination.chmod(0o600)
PY
./evals/.venv/bin/lc-eval doctor --config /absolute/private/lc-eval-usa.json
./evals/.venv/bin/lc-eval doctor --config /absolute/private/lc-eval-canada.json
```

```sh
# Calibrate each scenario; bad-reference runs must exit 1 with their named failure.
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign calibration --scenario hive-preserve-update --seed 41001 --reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign calibration --scenario hive-preserve-update --seed 41001 --bad-reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-canada.json --campaign calibration --scenario search-complete-export --seed 42001 --reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-canada.json --campaign calibration --scenario search-complete-export --seed 42001 --bad-reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign calibration --scenario webhook-production-routing --seed 43001 --reference
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign calibration --scenario webhook-production-routing --seed 43001 --bad-reference
./evals/.venv/bin/lc-eval validate-suite --config /absolute/private/lc-eval-usa.json --campaign calibration

# Real harness smoke and the complete eight targeted trials.
./evals/.venv/bin/lc-eval smoke --config /absolute/private/lc-eval-usa.json --campaign harness-smoke
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign initial-proof --scenario hive-preserve-update --adapter claude_code --seed 41001 --repetition 1
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign initial-proof --scenario hive-preserve-update --adapter codex --seed 41001 --repetition 1
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-canada.json --campaign initial-proof --scenario search-complete-export --adapter codex --seed 42001 --repetition 1
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-canada.json --campaign initial-proof --scenario search-complete-export --adapter claude_code --seed 42001 --repetition 1
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign initial-proof --scenario webhook-production-routing --adapter claude_code --seed 43001 --repetition 1
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign initial-proof --scenario webhook-production-routing --adapter codex --seed 43001 --repetition 1
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign initial-proof --scenario hive-preserve-update --adapter claude_code --seed 41001 --repetition 2
./evals/.venv/bin/lc-eval run --config /absolute/private/lc-eval-usa.json --campaign initial-proof --scenario hive-preserve-update --adapter codex --seed 41001 --repetition 2

./evals/.venv/bin/lc-eval fault-drill --config /absolute/private/lc-eval-usa.json --campaign initial-proof
./evals/.venv/bin/lc-eval cleanup --config /absolute/private/lc-eval-usa.json
./evals/.venv/bin/lc-eval report --config /absolute/private/lc-eval-usa.json --campaign initial-proof
./evals/.venv/bin/lc-eval acceptance --config /absolute/private/lc-eval-usa.json --campaign initial-proof
./evals/.venv/bin/lc-eval status --config /absolute/private/lc-eval-usa.json
```

The targeted `--repetition` option defaults to 1, accepts integers of at least 1 only with `--scenario`, and leaves suite-defined repetitions unchanged.

Every trial gets a disposable organization in the configured location. The calibrated region pins are `usa` for Hive and routing and `canada` for export. Because `lc.location` is configuration-wide, use USA- and Canada-pinned configuration files for scenario-targeted live runs; `run` without `--scenario` executes all eight suite entries at one configured location and is not the mixed-region M7 retry command.

Export starts with 5,003 matching and 137 nonmatching events, then adds 5,000 production events per stage until search returns a nonempty continuation or a configured ceiling is reached. The hard schema ceilings are 25,000 events and 100 MB; lower `limits.max_events` and `limits.max_fixture_bytes` values are honored and each growth stage is recorded. Live Canada trials proved pagination at 15,140 events for the reference and Codex, and 20,140 for Claude. All eight genuine trials passed and final acceptance is complete; see [ACCEPTANCE.md](ACCEPTANCE.md). Live export preparation can take 20–30 minutes under the free-tier ingestion ceiling; the 600-second agent timer begins after preparation.

Fresh Insight datasets can take time to initialize; readiness retries fresh bounded queries rather than repeatedly polling a failed query ID. The controller journals creation intent before creating resources, uses a separate scoped CLI worker, freezes artifacts after stopping execution, reads platform state with independent HTTP verification, and attempts cleanup in a `finally` path. `cleanup` reconciles exact owned resources after interruption; never run a broad organization deletion command. An unresolved cleanup stops the campaign.

The candidate container receives the public task and documentation. Its `limacharlie` executable is a transport to the pinned real CLI in a separate worker. The worker has the trial key; the agent has no LimaCharlie credentials. Agent and worker networks have separate restricted HTTPS proxies. Harness subscription material is isolated from the user's original files. The controller, graders, private fixtures, journal, and receiver administration stay outside both containers.

JSON and HTML reports are written under the private run directory. A failed task is distinct from an incomplete observation or cleanup failure. Missing usage stays unknown. A/A comparisons require compatible manifests and measure efficiency only for paired successes. Three scenarios prove the machinery; the capability catalog records the broader platform scope and future expansion.

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for verified progress and remaining acceptance work, and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the full plan.
