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

The initial authorized billing mode is **subscription_limits**: one trial at a time, 600 seconds per agent, Claude 30 turns, Codex 80 tool calls, and 80 CLI invocations. Token counts come from native harness streams. Dollar cost is unknown. The optional request-budget gateway is separate and is not wired into the subscription controller.

## Run and inspect

```sh
# First calibrate the complete execution path with a deterministic reference.
./evals/.venv/bin/lc-eval run --campaign hive-reference --scenario hive-preserve-update --reference

# A single real-agent trial.
./evals/.venv/bin/lc-eval run --campaign hive-claude --scenario hive-preserve-update --adapter claude_code

# All eight initial suite trials, sequentially.
./evals/.venv/bin/lc-eval run --campaign initial-proof

# Calibrate all three scenarios with good and deliberately bad references
# before claiming acceptance; retain every failed attempt.
./evals/.venv/bin/lc-eval validate-suite --campaign calibration
./evals/.venv/bin/lc-eval fault-drill --campaign initial-proof
./evals/.venv/bin/lc-eval acceptance --campaign initial-proof

./evals/.venv/bin/lc-eval status
./evals/.venv/bin/lc-eval report --campaign initial-proof
./evals/.venv/bin/lc-eval cleanup
```

Every trial gets a disposable organization in the configured location (`usa` by default for the initial Search proof). Fresh Insight datasets can take time to initialize; readiness retries fresh bounded queries rather than repeatedly polling a failed query ID. The controller journals creation intent before creating resources, uses a separate scoped CLI worker, freezes artifacts after stopping execution, reads platform state with independent HTTP verification, and attempts cleanup in a `finally` path. `cleanup` reconciles exact owned resources after interruption; never run a broad organization deletion command. An unresolved cleanup stops the campaign.

The candidate container receives the public task and documentation. Its `limacharlie` executable is a transport to the pinned real CLI in a separate worker. The worker has the trial key; the agent has no LimaCharlie credentials. Agent and worker networks have separate restricted HTTPS proxies. Harness subscription material is isolated from the user's original files. The controller, graders, private fixtures, journal, and receiver administration stay outside both containers.

JSON and HTML reports are written under the private run directory. A failed task is distinct from an incomplete observation or cleanup failure. Missing usage stays unknown. A/A comparisons require compatible manifests and measure efficiency only for paired successes. Three scenarios prove the machinery; the capability catalog records the broader platform scope and future expansion.

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for verified progress and remaining acceptance work, and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the full plan.
