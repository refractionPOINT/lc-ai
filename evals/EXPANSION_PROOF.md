# Initial expansion proof

Five new scenarios extend the original lookup, search export and webhook routing loop. Each has a real-platform positive-reference pass and deliberately bad-reference failure, with clean teardown. Reference outcomes validate the fixtures and graders; they are not AI scores. [Sanitized calibration evidence](results/expansion-calibration.json).

| Scenario | Platform effect independently verified | Current boundary |
|---|---|---|
| Configuration reconciliation | Exact lookup and D&R data/metadata, unchanged unrelated records and exact record sets | Clean, stale and already-correct fixture recipes; the initial proof uses seed 51002 |
| Cases maintenance | Exact status/severity, linked detection, entity and private note, preserved existing and unrelated records | Existing-case workflow; native creation is blocked by the pinned CLI/backend encoding mismatch |
| Cloud Security findings | Complete native CSV export, exact requested owner/accepted disposition, unchanged other findings and policy | Real SARIF ingestion into Cloud Security; supplied security decisions; acceptance-reason persistence is not graded |
| Scoped key rotation | Exact privileges, matching secret artifact, allowed read, denied administration, old-key fresh-token denial, unrelated keys preserved | Previously issued JWT revocation is not claimed |
| Native endpoint onboarding | Real isolated Linux sensor, exact online identity, tag, native process-task response containing an independently observed marker, key/sensor preservation | Container deployment contract; no host installation or kernel-telemetry coverage |

The native installer is downloaded from LimaCharlie and its hash and derived image digest are recorded. The sensor runs with all container capabilities dropped, a read-only root, no host mounts/network/PID namespace, and bounded CPU/memory/processes. Its private data tmpfs permits execution because the sensor loads signed modules there. The agent supplies an installation key through an explicit evaluator-owned endpoint deployment document; ordinary LC sensor/key/tag/task operations still use the CLI.

## Context and scored scope

The first scored matrix runs Codex in `bare` and `lc_ai` on all five scenarios, plus both contexts for Claude Code and AI Sessions on configuration reconciliation. Seed 51002 is fixed, runs are sequential, and each matrix cell is one observation. Genuine task failures remain visible. Untested cells and setup failures are not treated as successful trials.

All three harnesses passed both context probes. Standalone harnesses receive fresh homes/workspaces and selected subscription authentication, with personal settings, memory and skills excluded. The skills treatment uses 43 LC skills from a pinned Git archive. AI Sessions uses native plugin initialization; standalone harnesses use normalized native user-skill files and pinned supporting assets. These are the same source corpus, not identical prompts. [Context proof](CONTEXT_PROOF.md).

The checkpoint for the expansion implementation is `23dbdaa`; grading/readiness checkpoints include `e65672c`, `90d820f`, `053c1b5`, `bcebd5a`, `9423bc1`, `801c87a`, and `2b8eb89`. Trial manifests retain the exact evaluator, fixture, scenario and execution-context hashes. No model or harness comparison should ignore those identities.

## Calibration corrections

The initial Cases agent run received an empty list because fixture setup did not wait for the backend subscribed-tenant cache to include the new organization. A separate diagnostic observed privileged and candidate list counts of 0/0 twice, followed by 4/4 without changing permissions or data. Numbered reads succeeded throughout; adding metadata permissions did not resolve the visibility delay, and those extra permissions were reverted. Corrected references discover the case through native listing and linked detections, using the same scoped worker as the candidate. The superseded run is excluded from task scores.

Native fixture setup waits for the three default extension installation keys before freezing its baseline. Grading then requires exact key membership and preserved records; it does not exempt later keys based on their descriptions or tags. Case records use exact multiset preservation, and key rotation checks final-response secret disclosure. The public calibration record selects fresh live references for the changed discovery/readiness paths and links an offline regrade of saved evidence for the other deterministic assertions.

## Reproduction and interpretation

Use the `--scenario` and `--context` commands in [Running evals](RUNNING.md). The original `validate-suite` acceptance gate still targets the original three-scenario milestone. The calibration record linked above separately records positive/negative checks for these additions.

Agent limits are 600 seconds and 80 brokered CLI calls. Claude-based profiles configure 30 turns; Codex bounds completed tool calls at 80. Billing uses existing subscriptions, so dollar cost is unknown. Preserve native token classes and missing-value distinctions when comparing usage.

The [results README](README.md) holds the dated task matrix and measurements. [Sanitized scored records](results/expansion-proof.json) retain assertion outcomes and context/provenance identities. Raw evidence, command transcripts, keys and full platform snapshots stay outside this public repository.
