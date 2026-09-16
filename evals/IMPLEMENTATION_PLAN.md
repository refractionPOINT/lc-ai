# Implementation plan: prove the LimaCharlie CLI evaluation loop

Status: implementation handoff, 2026-09-16. No eval implementation or live trial has been performed. Read this document first when resuming. It specifies the work to build and demonstrate the initial complete loop; [DESIGN.md](DESIGN.md) describes the eventual coverage and [ARCHITECTURE.md](ARCHITECTURE.md) explains the boundaries.

## 1. Objective and working rules

Implement an eval application that provisions an isolated real LimaCharlie environment, gives a natural-language task to an AI harness, observes CLI execution, independently verifies the result, writes an evidence-backed report, and cleans up. Demonstrate it on three scenarios through two real harness adapters. A scripted reference runner validates fixtures and graders but does not count as an AI harness.

Work in `lc-ai`, branch `eval/limacharlie-cli-ai`. Keep all code, documentation, dependency declarations and deployment artifacts for this project here. Sibling repositories are read-only references. Do not optimize or fix the candidate CLI during this milestone. Record candidate bugs with reproductions. Preserve unrelated changes, including the pre-existing untracked `ai-agents/operations/prompt-maintainer/` directory.

Start by checking the branch, worktree status and applicable `AGENTS.md` instructions. Do not reset the checkout, delete files, switch an occupied checkout to another branch, or include unrelated files in commits. Commit completed logical increments on the dedicated branch; keep an implementation checklist and evidence index under `evals/`.

The evaluated agent gets an isolated public workspace, not this repository. Do not expose the implementation plan, reference solutions, ground truth, controller credentials, or backend source to it.

### Definition of done

- The three scenario reference executions pass on real LC resources and clean up successfully.
- Deliberately incorrect executions fail the intended assertions; no-op or fake success does not pass.
- Two configured real harnesses each run all three scenarios through the same controller and CLI boundary. Every trial has a terminal result and cleanup evidence.
- Each scenario has at least one genuine AI success in the recorded acceptance campaign. Failures from the other harness remain visible. If this cannot be achieved within the authorized budget, report that the implementation is validated but the AI success criterion remains unmet; do not weaken graders or hide attempts.
- A live interruption drill proves resources can be recovered after controller termination.
- A report includes task outcomes, usage, commands, evidence, exclusions and cleanup results. A paired A/A comparison proves comparison plumbing without claiming a CLI improvement.
- Offline tests and documented live acceptance commands are reproducible from a fresh session after the external inputs below are supplied.

Do not equate an offline simulator run, successful reference script, or saved configuration with completion of this milestone.

## 2. Resolved user decisions and remaining preflight checks

The user supplied these decisions during planning. They persist for the implementation session; do not ask for the same permission again.

| Input | Decision |
|---|---|
| LC access | Use the local `limacharlie` executable, assumed authenticated, to create a new test organization and set it up as needed. Delete the test organization when the eval is done. |
| Harnesses | Local Claude Code and local Codex. Workspace follows the initial proof. |
| Model spend | $50 total across the initial campaign, including model smoke tests and retries; one live trial at a time. |
| Output receiver | Deployment of a small HTTPS receiver is authorized. No specific cloud project was selected. |

Implementation defaults within that scope: use the local CLI's existing authentication/environment, `org create --location auto`, no org template, unique run-owned names, and explicit `--oid` on subsequent calls. Record the actual assigned region before creating comparison fixtures; use that same supported location for paired trials. Do not redirect tests to an exp environment or an existing org by inference. Do not use `--use` or change the user's default org.

Run the receiver locally and publish only its ingest listener through a temporary Cloudflare Quick Tunnel. This avoids requiring a cloud project or persistent deployment. Install a pinned `cloudflared` binary/image within eval-managed tooling, not as a replacement for user tooling. It was not on PATH during planning. Public URL discovery and readiness are automated. Keep the management listener on a separate local-only port that is never tunneled. This testing use matches the [Cloudflare Quick Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/); its lack of an uptime guarantee means a tunnel failure is an infrastructure event. An existing receiver remains an optional configuration path.

Ceilings for the small proof: one active trial, two owned orgs maximum, at most 25,000 generated events per pagination fixture, 100 MB fixture payload per trial, one receiver/tunnel, and a 24-hour resource lease. Track LC usage separately from model cost. Do not provision persistent compute, buy domains, or change billing plans. If the selected account requires additional purchases to enable a mandatory feature, report the specific dependency.

The model auth modes and accessible model IDs are runtime preflight checks, not yet established facts. Prefer existing authorized local harness authentication; isolate only the minimum required auth material or use a local credential-injecting gateway. Do not scan unrelated credential stores, mount whole home directories, print credentials, or assume a subscription auth flow supports the same API transport as a key. If access is missing, request the specific authentication step and continue offline work. The budget enforcement gate in M3 must pass before paid calls.

Allocate the $50 campaign ledger as follows: up to $2 total for the two harness smoke tests, up to $5 for each of six initial scored trials ($30), up to $3 for each of two A/A repeat trials ($6), and the remaining $12 for disclosed diagnostic/retry trials. Unspent allowances can be reassigned within the $50 cap; no task cap overrides the campaign cap. If a configured model's conservative request reservation exceeds its task allowance, reduce the declared context/output limits or adjust allocation before launch, never exceed the campaign limit. This budget may be insufficient for a particular model or failure investigation; partial completion must be reported honestly.

No further architecture choices require a user answer now. Offline implementation is unblocked. Live preflight must establish actual account permissions, entitlements, model auth, budget enforcement and receiver reachability. Record a precise blocker if one fails; do not call the loop proved without live evidence.

### Trusted bootstrap CLI and independent verification

Resolve the host `limacharlie` executable once, store its absolute path/version/digest, and keep it fixed for the campaign. It is distinct from the pinned candidate CLI in the worker. During planning the host executable was `/home/maxime/.local/bin/limacharlie`, version `5.2.2.dev2+g262e362ce.d20260418`; its create/delete/key/token help interfaces were checked, but authentication was not exercised.

Implement `LocalCliProvisioner` for org creation/deletion and privileged setup. Run argv arrays, capture stdout privately, and parse expected JSON with a bounded decoder that tolerates documented surrounding status text. Validate response shape and ownership before recording IDs. Never blindly extract the first UUID from output. For auth-bearing calls, log only command kind/status and sanitized metadata.

Bootstrap sequence: `org create --name <owned-name> --location auto --output json`; resolve the new OID; `auth test --oid <new-oid>` to refresh/test access; create the scoped candidate API key via `api-key create --oid <new-oid> --name <owned-key> --permissions <validated-list> --output json`. Capture the one-time key secret directly into protected worker provisioning. Record its key hash for revocation without exporting the secret.

For independent evaluator reads, obtain a short-lived token through `auth get-token --oid <new-oid> --hours 1 --format json` captured in memory, and initialize the pinned SDK with `Client(oid=<new-oid>, jwt=<token>)`. Refresh through the trusted CLI before expiry or on an authenticated expiry response. The candidate never receives the user's token, config or identity. Setup may use the trusted CLI's generic API command where no dedicated setup command exists; authoritative checks use independent SDK/HTTP requests.

Cleanup uses the trusted host CLI's two-step `org delete --oid <owned-oid>` / `--confirm-token <returned-token>`, with all outputs sanitized. Delete only OIDs backed by create intents and verified ownership in the run ledger, never the user's default organization. If inherited authentication is org-scoped and cannot create organizations, live doctor reports that concrete mismatch without trying another identity.

## 3. Investigation results and source map

These observations are from the local checkout, not live validation. Pin full commit SHAs and content digests at implementation start; reject or explicitly snapshot dirty candidate sources rather than silently building an unidentified revision.

| Source | Finding / implementation consequence |
|---|---|
| `../python-limacharlie/limacharlie/client.py` | `Client(oid=..., api_key=..., uid=...)`, `refresh_jwt(...)`; avoid inherited credentials/cache. Use an explicit evaluator configuration and refresh after creating an org. |
| `../python-limacharlie/limacharlie/sdk/organization.py` | `Organization.create_org`, `delete_org`, installation-key and API-key lifecycle, org URL discovery. Deletion is GET confirmation followed by DELETE with the returned token. |
| `../lc_api-go/cmd/org_e2e_test/README.md` and `main.go` | Existing lifecycle tests explain refreshed user claims and asynchronous deletion. Their documentation disagrees on default locations, so do not copy a default location. Use the user-selected value and live preflight. |
| `../python-limacharlie/limacharlie/sdk/hive.py` | `Hive`, `HiveRecord`, metadata and etags. Data updates and metadata updates have different routes. Preserve user metadata, not volatile system timestamps. |
| `../python-limacharlie/limacharlie/commands/_hive_shortcut.py` | Supports `data` / `usr_mtd` input wrappers; new records default to disabled unless enabled explicitly. |
| `../python-limacharlie/limacharlie/commands/cloud_sensor.py` | CLI name `cloud-adapter`; Hive name `cloud_sensor`; hosted webhook configuration includes identity, platform, seed and secret. |
| `../documentation/docs/2-sensors-deployment/adapters/tutorials/webhook-adapter.md` | Hosted hooks accept JSON objects, arrays or JSONL, optionally gzipped. Resolve the regional `hooks` URL; authenticate using `lc-secret` rather than putting the secret in the URL. Older CLI examples here should not be copied blindly. |
| `../go-limacharlie/limacharlie/webhook.go` | Confirms `https://{hooks}/{oid}/{escaped-hook-name}`, POST JSON/gzip and `lc-secret`. Normalize URLs that already include a scheme. |
| `../python-limacharlie/limacharlie/sdk/search.py` | Search result items contain `rows` and `nextToken`; the SDK follows continuation tokens. A completed poll can still have another page. Do not confuse result-item count with event count. |
| `../python-limacharlie/limacharlie/commands/search.py` | `search run --query ... --start ... --end ... --stream event --output jsonl`; normally follows pages. Completeness can be tested without demanding manual pagination. |
| `../python-limacharlie/limacharlie/sdk/outputs.py` and `commands/output_cmd.py` | Webhook output uses `dest_host`, `secret_key`; stream `detect` plus `cat` can select a category. No documented arbitrary event-field filter here: implement production-only selection using D&R. |
| `../legion_endpoint-go/endpoint/storage/storage.go`, `webhook.go` | `lc-signature` uses hex HMAC-SHA256. Verify exact transmitted bytes before JSON parsing. Confirm compression/signing order with a live small probe; start with uncompressed single-event webhook output. Local/private output destinations are blocked by the output dialer. |
| `../legion_config_hive/hivedef/registry.go` | Authoritative Hive permission mapping: `lookup.*`, `cloudsensor.*`, and `dr.list/set/del` for `dr-general`. Derive permissions from this and the API routes rather than guessed CLI names. |
| `../ai-sessions/internal/runner/workspace_protocol.go` | Public workspace context is not a full tool trace; usage summaries exist. |
| `../ai-sessions/internal/sessionmanager/jobs.go`, `internal/k8sjobs/session_jobs.go` | Runner image comes from service configuration. A per-task image override is not established by the inspected interface. |
| `../python-limacharlie/limacharlie/commands/ai.py` | Session launch exposes model, budget, tools, plugins and env overrides; no demonstrated per-session runner-image flag. |

Observed source heads: LC AI `94d5518`, Python CLI `fe67856`, documentation `3eeeb952`, AI sessions `bbe8289`. These short IDs identify the planning inspection, not sufficient build pins.

Local commands available during planning: Docker server `29.7.2`, Codex `0.154.0`, Claude Code `2.1.272`, and the older host CLI described in section 2. No model authentication or live LC connectivity was exercised. Do not assume the host CLI and the sibling source checkout are the same version.

Verified harness documentation: [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) documents JSONL execution events and invocation-specific API authentication. [Claude Code programmatic execution](https://code.claude.com/docs/en/headless) documents print mode and streaming results. Recheck the pinned binaries' help when implementing the adapters; store their version/help fingerprints. Current web docs and installed versions may diverge.

## 4. Concrete implementation choices

Use Python 3.11+ and a standalone installable project in `evals/pyproject.toml`, with console entry point `lc-eval`. Use a `src/lc_eval` package, Click for the command surface, Pydantic v2 for strict typed manifests, PyYAML safe loading for scenario/config files, HTTPX for evaluator HTTP and receiver management, aiohttp for the small receiver/broker/gateway HTTP servers, pytest for tests, and Ruff for linting. Use uv with `evals/uv.lock` and a pinned bootstrap script; install via `uv sync --locked --extra test --project evals`. Use stdlib SQLite for the durable journal and JSONL/files for artifacts. Keep the independently pinned LC SDK in the evaluator environment and candidate wheel in a separate image.

Use Docker for local isolation. The controller runs on the host or in its own environment; it owns Docker and never exposes its socket to the candidate. First implementation uses one host, one campaign at a time and trial concurrency 1. Use an advisory process lock as well as the journal to prevent two controllers acquiring the same environment.

Do not adopt Harbor in this milestone. The adapters and manifests are sufficient for the first proof; a framework bridge is follow-up work. Do not build a whole-platform emulator or an LLM grader.

Proposed layout:

```text
evals/
  README.md                       # installation and operator commands
  IMPLEMENTATION_PLAN.md
  IMPLEMENTATION_STATUS.md         # milestones and evidence pointers
  pyproject.toml
  uv.lock
  scripts/bootstrap.sh            # pinned uv bootstrap and locked install
  config/example.yaml             # non-secret configuration schema example
  catalog/capabilities.yaml
  suites/initial-loop.yaml
  scenarios/<task-id>/
    task.yaml
    prompt.md
    public/                       # task-specific public samples
  src/lc_eval/
    cli.py, models.py, config.py
    controller.py, journal.py, resources.py
    fixtures/{organization,local_cli,hive,webhook,search_dataset}.py
    adapters/{base,scripted,claude_code,codex,workspace}.py
    execution/{docker,broker,shim,egress,model_gateway,budget}.py
    evidence/{events,artifacts,redaction}.py
    verifiers/{base,hive,export,routing}.py
    receiver/{app,store,client}.py
    reporting/{results,compare,html}.py
  references/                     # evaluator-only reference executors
  docker/                         # Dockerfiles and local topology
  deploy/                         # local receiver/tunnel lifecycle assets
  tests/{unit,integration,live}/
```

Use a configurable run-data directory outside the git checkout. Store its absolute path in the resolved operator config. Local artifact files default to user-only permissions. Add ignore rules for generated local configs, environments, credentials, databases and run artifacts as defense in depth; never rely on ignores for secrecy.

## 5. Contracts to implement before components

Define the following versioned, extra-fields-forbidden records. Treat IDs as opaque strings and timestamps as UTC. Enforce finite positive time/size limits and disallow path traversal in task IDs and artifacts.

| Record | Required content |
|---|---|
| `ScenarioSpec` | schema version, ID/revision, capability tags, prompt/public files, fixture kind/parameters, allowed scope, required adapter capabilities, timeout/convergence/probe budgets, assertion IDs, required deliverable paths. |
| `RunConfig` | sources and immutable pins, agent configurations, secret references, environment mode/location/OID allowlist, receiver endpoints, resource caps, model pricing/budget semantics, run-data directory. |
| `TrialManifest` | run/trial IDs, scenario hash/revision, variant seed, attempt, logical-to-real identity map reference, candidate/doc/evaluator digests, actual harness/image/tools/model/effort, observed backend settings, limits. |
| `ResourceLease` | resource kind/ID, trial owner, create intent ID, creation status, cleanup handle, lease expiry, dependencies, cleanup state; no inline secrets in exported records. |
| `ExecutionEvent` | version, trial ID, producer, sequence, event ID, wall and monotonic timestamps, event type, source event ID, sanitized payload/artifact references. |
| `AssertionResult` | assertion ID, required flag, pass/fail/unknown, expected/observed summary, evidence references, explanation. |
| `TrialResult` | execution status, pass/fail/inconclusive/not-run grade, assertion list, usage with known/unknown fields, trace completeness, cleanup state, termination reason, timings and failure attribution. |

Fixture interface: `provision(context)`, `ready(handle)`, `baseline(handle)`, `public_view(handle)`, `observe(handle)`, `cleanup(handle)`, `verify_cleanup(handle)`. All remote operations have explicit deadlines. Handle partial provisioning with a journaled resource ledger.

Adapter interface: `capabilities()`, `prepare(public_spec, execution_env)`, `start()`, `events()`, `stop(deadline)`, `collect()`. Transport scripted interactions from scenario facts; initial tasks require no discretionary user clarification. Workspace implements a capability inspection/stub until its prerequisites are established; it must return unsupported instead of simulating a successful remote trial.

Verifier interface: `verify(manifest, fixture_handle, frozen_artifacts, evidence) -> assertions`. It uses evaluator credentials and independent SDK/HTTP reads. Assertions never import or execute the candidate package in the evaluator process.

Lifecycle: `planned → provisioning → ready → running → stopping → settling → verifying → cleaning → finished`. Any failure after acquiring resources reaches `cleaning`. Persist transitions atomically. A restart reconciles interrupted trials, stops survivors and cleans up; it does not resume the agent as if nothing happened.

### Exit and result semantics

`lc-eval run` exits 0 only if all selected trials meet success and cleanup requirements; 1 for graded task failure; 2 for invalid configuration/preflight/unsupported required capability; 3 for infrastructure or inconclusive verification; 4 for unresolved cleanup. For mixed results, precedence is cleanup, infrastructure, preflight, task failure. Write a complete machine-readable report regardless of exit code. `acceptance` separately evaluates the milestone definition of done, so genuine model failures remain recorded without confusing them with a broken controller.

## 6. CLI execution boundary

Implement the strict local path for the three initial tasks. Name the profile `controlled-cli-v1`; report its limits rather than calling it universally compatible.

- Candidate container: harness, ordinary shell/file tools, read-only docs and a `limacharlie` shim; writable `/work`; no real LC management credential, no evaluator storage, no Docker socket, no host mounts beyond the explicit public workspace.
- CLI worker: immutable candidate wheel/image, separate credential/config directory and explicit environment; access only to `/work` plus its own runtime. Runs a fixed executable as an argument array, never a shell command assembled from user text.
- Shim/broker: forward argv, bounded stdin, `/work`-relative cwd, and cancellation; stream stdout/stderr separately and return the actual exit code. Use a per-trial authenticated channel. Worker and candidate see the same `/work` files so YAML input and output redirection behave normally. No arbitrary executable or environment override RPC.
- Candidate network: only its model endpoint/proxy and broker; no direct LC API, hooks or receiver access. Worker egress: only required LC services resolved for the authorized org and approved authentication endpoints. Reject arbitrary proxy destinations and resolved private/metadata addresses. Include IPv6, redirects and raw sockets in boundary tests.
- Fix Python invocation with isolated import behavior and an immutable package environment. Ignore candidate `PYTHONPATH`, `PYTHONSTARTUP`, credential env overrides and user site packages. Do not load executable configuration from `/work`. Treat shared-workspace symlinks and artifact paths as hostile.
- A worker may read task files, but the broker must not expose worker credential files or arbitrary file-read endpoints. Audit CLI commands that can display credentials or execute external tools; initial scoped keys exclude key/user/org administration and unrelated execution capabilities.
- Support pipes, JSON/JSONL, YAML input files, relative paths, concurrent command requests, and cancellation. Interactive TTY/auth flows and long-lived interactive streams are declared unsupported in v1 and never selected by initial tasks.

A shim alone is not the enforcement mechanism; the container/network boundary is. Validate that the agent cannot bypass it with Python, curl, an alternate installed SDK, a changed PATH, or an absolute binary path. Keep candidate permission to request generic `limacharlie api` operations within its authorized LC scope; do not confuse that supported CLI escape hatch with a direct API bypass.

Record broker overhead separately. Compare direct and brokered executions of benign CLI commands for byte/exit-code parity, including file paths and errors. The broker must not repair commands, hide help, change output, or add hints. Do not change the candidate CLI to instrument it. Backend request counts may remain unavailable in v1: report null with provenance rather than equating one CLI invocation to one request.

If this boundary cannot be made compatible on the selected host, stop the strict acceptance lane with a diagnosed blocker. An explicitly labeled observational diagnostic run is useful but does not silently replace the promised controlled profile.

## 7. The three initial scenarios

### A. `hive-preserve-update`

**Public request:** In the named organization, update one named lookup entry's `owner` from its existing value to `platform-ops`. Preserve all other entries, fields and user metadata, including the record's enabled state, tags and comment. Do not create another lookup. Return the record name and a brief description of the change.

**Fixture:** Two lookup records, one target and one similarly named distractor. Target data uses the documented `lookup_data` format: several asset keys with nested metadata including owner, team and ticket; the target asset also has nested fields to preserve. Use `HiveRecord` with explicit enabled/tags/comment. Record a deep baseline of both records, excluding volatile `sys_mtd` fields. Candidate permissions include lookup reads/data writes and required metadata operations; no deletion permission is needed for the valid solution.

**Reference:** CLI get → modify the one field in a local file → CLI set with preserved data/metadata → CLI get. Read back through the independent evaluator SDK as the oracle. Accept any equivalent CLI route.

**Assertions:** Exact semantic expected data and user metadata; distractor unchanged; record set unchanged; required output identifies the right record. An etag change is acceptable; demanding timestamp equality is not.

**Bad references:** no-op with “done”; overwrite only the desired entry and erase siblings; change the distractor. Each must fail the corresponding assertion. Reapply a correct update as a no-op/idempotency reference probe and verify semantic state stays unchanged.

### B. `search-complete-export`

**Public request:** Export every telemetry event from the supplied trial/time window whose `environment` is `production` into `/work/export.jsonl`, one JSON object per unique `eval_event_id`, containing `eval_event_id`, `environment`, and `message`. Exclude other events, include the complete set, and report the count. The agent receives the event schema, trial selector and time window, but not the exact expected ID set/count.

**Fixture:** Evaluator provisions and enables a hosted JSON webhook adapter with `mapping.event_type_path: event_type`. Generate 5,003 matching events and 137 nonmatching events initially. Each contains a UUID/random ID generated independently from public samples, `eval_trial_id`, `event_type: LC_EVAL_EXPORT`, `environment` and a distinctive message. Store expected IDs and field values outside the candidate. Ingest in bounded JSON-array batches via the regional hook URL and `lc-secret`.

**Readiness:** Independently query the entire fixture window, prove every unique input event is searchable, check its field values, and prove the matching retrieval traverses at least one nonempty `nextToken` continuation with additional rows. Event count alone is not proof of pagination. If pagination does not occur, grow the fixture deterministically within the configured 25,000-event ceiling and record the final fixture size. If still single-page, mark fixture unsupported; do not claim paginated coverage. If ingestion is retried after an ambiguous response, account for duplicates by unique event ID; grade the explicitly requested one-row-per-ID export.

**Reference query shape:** `* | LC_EVAL_EXPORT | event/eval_trial_id == '<trial>' and event/environment == 'production'`, with explicit epoch start/end and stream `event`. Validate through the pinned SDK before publishing the scenario. Use `search run` JSONL and local projection/deduplication as needed. Do not assume CLI `--limit` means event-row count; omit it for the reference. Verify actual JSONL row shape against the selected CLI, then freeze parser fixtures and reference commands.

**Assertions:** File exists within `/work`, parses as JSONL within resource bounds, exact expected ID set and values, no duplicate IDs, no extra/nonmatching rows, count correct, no platform mutation. Completeness ground truth comes from the injection ledger plus independent readiness queries, not the candidate query output.

**Bad references:** first page only; missing last ID; duplicated ID with correct line count; nonmatching row substituted for a matching row; correct count but fabricated IDs. Every one fails.

### C. `webhook-production-routing`

**Public request:** Configure the named hosted JSON webhook source and an automation that reports only events with the supplied event type, trial ID and `environment: production`. Send those detections under a specified category to the supplied webhook destination. Preserve an existing unrelated output. Return the adapter/rule/output names and a concise completion statement. A controller feed service will send documented sample events periodically while the task runs; final verification will send fresh events after the agent stops.

**Why detections:** The output command documents category filtering, not arbitrary JSON-field predicates. A D&R rule provides the field matching, and a `detect` webhook output selects its report category. This tests input → automation → output using supported platform mechanisms.

**Fixture:** Controller leases a fresh tenant, creates an installation key and per-trial ingestion secret, and provides those scoped input facts plus a read-only configuration skeleton/public event samples. The agent must create/enable the named cloud adapter, rule and output. Existing baseline output uses a different category/path so it cannot accidentally satisfy target assertions. The receiver has distinct ingest paths for target/baseline and a management API available only to the evaluator.

The feed service resolves the fixed adapter name and tries a small sample batch on a bounded cadence. Missing/unready adapter is expected while the candidate configures it. This is a declared environmental stimulus, not evaluator repair. Public prompts must explain the feed and how the agent can inspect LC ingestion/detections. Once stopping begins, stop the public feed and generate secret evaluator-only probe IDs.

**Reference rule intent:** `detect` has `op: and`, event `LC_EVAL_ROUTE`, and equality checks on `event/eval_trial_id` and `event/environment`; `respond` contains `action: report` with the specified report name/category. Enable the rule explicitly. Configure a webhook output with stream `detect`, `cat` matching that category, receiver `dest_host`, and `secret_key`. Validate the exact rule/output syntax through the selected CLI and independent readback during the reference preflight.

**Verification:** Stop the candidate and its worker mutation channel. Permit configuration propagation within a bounded settling interval. Inject fresh probes through the resulting adapter: production matches, staging/nonproduction negatives, wrong-event-type negatives and wrong-trial negatives. Confirm all probes were ingested before interpreting absent detections. Verify matching detections arrive at the target receiver, negative IDs do not, and the baseline output definition is unchanged. Use an evaluator-owned positive-control output/path to establish receiver delivery health; keep its probe traffic distinguishable and do not count it as target success. Inspect target detection state to distinguish no detection from failed delivery.

Start with a 180-second negative-observation window after positive delivery and ingestion readiness, within a 600-second total verification ceiling. These are configurable fixture bounds to calibrate on the chosen backend. A healthy bounded window with missing required effects fails; outage or insufficient evidence is inconclusive. Never claim eternal non-delivery from a finite window.

**Bad references:** save disabled rule; configure output without valid delivery; overbroad rule forwarding staging; change baseline output; fake success without configuration. Include a signed but stale receipt: it must not satisfy fresh probe assertions. Duplicate deliveries of a matching event are diagnostic, not failure, unless exactly-once behavior was explicitly requested.

No cybersecurity classification or live customer data is required for any scenario.

## 8. Ordered milestones and acceptance gates

### M0 — Repository setup and resolved configuration

1. Verify branch/worktree and record source SHAs/digests.
2. Create package skeleton, lockfile, README and status checklist. Define `lc-eval --help` and a schema-checked example config.
3. Implement `init --from-local`: generate a non-secret operator configuration using the resolved local LC executable, sibling source revisions, local harness versions, `location: auto`, `receiver.mode: quick_tunnel`, concurrency 1 and the approved $50 budget. Discover model/auth metadata only through supported harness interfaces or narrowly selected configuration fields. Copy no credential values into this file. Freeze model IDs/effort after access is verified; if absent, report the exact missing field. Implement `doctor`: check Python, Docker, run-data path, immutable candidate source/image, harness binaries/flags and required authentication availability without printing values.
4. Write `preflight.json` with each check, evidence and missing action. Dry preflight never creates resources or calls a model.

Gate: package installs from the lock; config validation rejects unresolved live inputs, incorrect paths and incompatible selected profiles. Offline mode remains usable with no credentials.

### M1 — Journal, lifecycle and scripted runner

1. Implement models and SQLite tables for campaigns, trials, transitions, create intents and leases. Persist create intent before remote creation and resource ID immediately afterwards.
2. Use unique trial-owned names plus exact ledger IDs to recover ambiguous create outcomes. On a timeout, reconcile by the known owner/name before retrying; never blindly create a duplicate.
3. Implement controller state machine, hard wall timeout, signal handling, independent cleanup and restart reconciliation.
4. Implement a scripted adapter for known success/failure/timeout executions against test fixture providers. Test doubles serve interface/lifecycle tests, not benchmark scores.
5. Store artifacts atomically and produce a minimal JSON result for every terminal path.

Gate: tests inject failures at every state transition, terminate during provisioning and execution, replay cleanup twice, and prove no tracked resources are lost. A failed cleanup remains retryable and prevents a clean acceptance result.

### M2 — Candidate isolation and CLI broker

1. Build pinned worker and candidate images; generate allowlisted public workspaces from scenario packages.
2. Implement broker/shim, cancellation, separate stdout/stderr, size limits, and persisted CLI events.
3. Implement network separation and provider egress configuration; prove no route to evaluator stores, receiver management or direct LC services from the candidate.
4. Test byte/exit-code equivalence for CLI help, schema, invalid commands, input files, stdin, redirected output, multi-command shells and cancellation. Run non-secret offline cases first, then small live cases in M4.
5. Test symlink/path traversal and attempts to import attacker-controlled Python into the worker. Extract final artifacts only after the candidate is stopped and the artifact view is frozen; reject symlinks/devices and reads outside the workspace.

Gate: boundary tests pass and actual CLI image digest is recorded. No uninstrumented CLI route exists in the controlled profile. v1 limitations appear in adapter capability output.

### M3 — Real harness adapters

1. Implement Claude Code and Codex adapters around subprocesses inside the candidate container, with fresh configuration/session directories and explicitly permitted file/shell tools.
2. Launch subprocesses with argv arrays and feed task text via stdin; do not interpolate prompts into shell command strings. Maintain harness-native system instructions, adding only identical task context and documented environment facts.
3. Claude launch basis: `claude -p --output-format stream-json --verbose --model <configured-model> --max-budget-usd <trial-cap>`. Use the pinned version's supported clean-config options (the inspected binary provides `--bare` for API-key automation) and explicit tool configuration. Capture raw events and final usage/result without double-counting cumulative usage.
4. Codex launch basis: `codex exec --json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --model <configured-model> -`. Use explicitly configured noninteractive permission/sandbox settings compatible with the external container; validate tool access before scoring.
5. Normalize messages, command/tool events, errors, usage and completion. Keep native traces and mark absent metrics unknown. Read pipes continuously to avoid deadlock and allow final trace drain before forced termination.
6. Enforce fresh sessions; disable memory, plugin auto-discovery, external MCP and delegated agents for this profile. Do not mount development credentials beyond the selected model auth mechanism.
7. Implement generic adapter registration and conformance tests. Workspace entry performs capability checks and explains unsupported requirements; do not hard-code the task catalog to local adapters.

Budget enforcement: the inspected Codex exec help does not expose a USD cap. Controller stop based on turn-end usage cannot enforce the approved $50 limit. Implement a local model gateway/budget ledger, or use a demonstrably equivalent existing hard-cap mechanism; do not silently substitute a soft cap.

The gateway is part of the evaluator, not a public deployment. Configure the selected harness's supported provider/base-URL route to it. It forwards the native request/stream without prompt rewriting, injects authorized upstream credentials outside the candidate, and rejects upstream model calls not belonging to an active trial. Confirm API-key versus subscription-auth transport compatibility in preflight; never point subscription credentials at a guessed API endpoint. The [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) documents provider configuration; record the selected fields in the adapter manifest. For a missing compatible model credential, request that specific auth setup rather than implementing an undocumented auth workaround.

Before forwarding each billable request, atomically reserve its conservative maximum charge against the shared campaign ledger using the pinned model's supported input/output bounds and maximum applicable rates, including cache-write or other billed token classes. Reject unknown models, rates, billable built-in tools and unbounded requests. Use the full model input limit when an exact trusted token bound is unavailable; never estimate a hard ceiling from output characters. Set/validate a supported maximum output-token limit as part of the recorded experimental configuration. Reconcile reservations from trusted upstream usage, keep the full reservation on uncertain/cancelled requests until settled, and reserve anew for every upstream retry. Persist the ledger across controller restarts. Paid smoke calls share the same ledger. Stop new requests when reservations plus settled spend would exceed $50.

This is a small native-protocol forwarding adapter, not a replacement agent loop. Test streaming cancellation, duplicate usage, missing usage, retries and concurrent reservations using a fake upstream before a paid call. If the selected auth mode cannot provide reliable bounded billing, the paid lane stays blocked pending a compatible auth/gateway configuration. Subscription runs must report actual billing separately from estimated model-equivalent cost; unknown billing is not zero.

Gate: captured representative stream fixtures pass parser tests; a tiny real shell task per selected harness verifies actual launch/auth/stop only after budget authorization. This smoke task is not one of the three scored scenarios.

### M4 — Live fixture preflight and cleanup

1. Apply the resolved user decisions in section 2; produce `resolved-config.json` with secret references only. Do not re-request org lifecycle or receiver permission.
2. Implement `LocalCliProvisioner` as specified in section 2. Create and delete orgs using the fixed authenticated local CLI, refresh/test access after creation, wait for org readiness and entitlements, then issue trial-scoped candidate credentials through that CLI. Use private token acquisition for independent evaluator SDK/HTTP reads. Keep user credentials on the host.
3. Validate permissions with real reads plus reversible writes in the disposable environment. For the initial scenarios, start from org/sensor discovery, lookup permissions, `cloudsensor.*`, installation-key permissions, `dr.list/set` and output permissions as needed; resolve search permissions from the current endpoints. Freeze the minimal proven list in fixture metadata. Do not give candidates org deletion, API-key administration or unrelated tenant access.
4. Implement the local receiver with separate ingest and management listeners, then automate a pinned `cloudflared tunnel --url http://127.0.0.1:<ingest-port>` process in a fresh eval-owned configuration directory. Tunnel only the ingest listener; never change an existing `.cloudflared` configuration. Capture and validate the generated HTTPS URL, journal process/container ownership and probe public reachability before giving the destination to an agent. Public ingest accepts POSTs only; local authenticated management creates/reads/deletes trial receipt buckets. Persist before acknowledging; bound request size; verify hex HMAC-SHA256 with constant-time comparison; parse declared JSON forms; keep raw bytes/digest, receive time and signature verdict. Start the tunnel before final fixture/prompt compilation and keep its hostname fixed during a trial. A restarted tunnel with a new hostname invalidates the affected trial; do not silently rewrite agent-created outputs.
5. Implement hosted webhook fixture, sender and LCQL readiness reader. Distinguish API acceptance, adapter enrollment, ingested/searchable data, detections and output delivery.
6. Probe a small real batch and a signed output round trip before seeding the large dataset. Store sanitized API response fixtures and exact observed field shapes for future tests.
7. Exercise two-step deletion and its completion checks. Stop producers/adapters, remove outputs/rules and revoke credentials as applicable. Confirm deletion via independent privileged state/list checks, not a 403 from the revoked candidate key. Preserve original identity mapping for audit.
8. Record receiver/tunnel process or container IDs and stop them after evidence capture. Deletion of an LC org must precede retiring its delivery destination where feasible, to avoid unnecessary retries. A pre-existing shared receiver is not deleted; only trial-owned receipt data/tokens are removed after retaining evidence. Retain receiver health information through the complete negative-probe window.

Gate: a provision → small input/output probe → cleanup cycle succeeds, and resource ledger reconciliation is empty. Unknown schema/entitlement failures are recorded before spending model tokens on the full suite.

### M5 — Scenarios, references and independent graders

1. Implement the three packages in section 7 and add them to `initial-loop.yaml`.
2. Build fixture factories, expected-state builders, reference runners and deterministic verifiers. Reference runners use the same CLI broker as real agents; privileged preparation stays in the fixture layer.
3. Prove reference success on each real fixture, then execute deliberately bad references against separate fixtures. Require named failed assertions, not merely a nonzero process status.
4. Record exact scenario/fixture revisions after calibration. Validate every hidden assertion against the public prompt; revise ambiguous prompts before real agent comparisons.
5. Add identity randomization, distractors and path-safe artifact checks. Retain the injection ledger outside the public workspace; don't expose complete expected exports as public samples.

Gate: all good references pass and every bad reference fails for the intended reason; collector outage yields inconclusive, not an invented agent failure; pagination is proven by observed continuation. These are tests of grader validity, not model performance.

### M6 — Reporting and comparison

1. Produce JSON plus a static HTML report linking each assertion to evidence. Escape all agent-controlled HTML and text; never render command output as executable markup.
2. Report full success, stage assertions, task grade, cleanup, CLI invocation count, output bytes, errors, active/wait/verification time, tokens/cost and metric provenance.
3. Compare compatible configurations by scenario/seed/repetition; normalize logical fixture IDs across tenants. Reject comparisons with mismatched scenario revision, docs, fixture recipe or uncontrolled CLI/model settings unless explicitly presented as a different experiment.
4. Show the paired-success subset for efficiency, plus success rate and total spend across all attempts. No statistical significance claims from this tiny calibration suite. Include all invalid and excluded trials.
5. Regrading uses frozen artifacts and recorded evidence; assertions requiring new live probes are unknown until rerun.

Gate: synthetic A/A and known differing result fixtures produce correct aggregates, missing usage stays null, dangerous HTML is escaped, and incompatible comparisons are rejected with a reason.

### M7 — Initial live acceptance campaign

1. Run offline checks, live doctor and reference/bad-reference suites.
2. Run each scenario once with each selected real harness, in fresh fixtures (six trials total for two harnesses). Alternate harness order to limit systematic timing effects. No hints, manual interventions or task repairs mid-trial.
3. Review traces and outcomes. Fix controller/fixture/verifier bugs only with evidence; revision changes invalidate affected comparisons and require new linked trials. Preserve original attempts. Agent/CLI failures remain valid failures.
4. If budget remains, repeat the same manifest/seed per harness as independent trials. Permit at most two additional attempts per scenario/harness for the calibration campaign, retaining all results. This is a disclosed repeated-trial campaign, not selective pass-until-green testing.
5. Perform a live interruption drill on a separate reference fixture: terminate the controller after a resource/agent has started, invoke reconciliation, confirm candidate shutdown and exact owned-resource cleanup. Never kill the implementation session or unrelated Docker workloads.
6. Run one additional `hive-preserve-update` trial per harness using the same seed and identical CLI image as its first run, in a fresh equivalent fixture. These two reserved A/A trials bring the planned scored total to eight. Generate paired A/A comparisons; observed stochastic differences are not CLI gains. Additional repetitions from step 4 can also provide pairs, but the mandatory A/A check must not depend on optional unbudgeted work.
7. Run the acceptance evaluator against the definition of done and produce `ACCEPTANCE.md` with full command invocations, manifest hashes, artifact locations, observed grades, spend, known limitations and unresolved resource count.

Gate: the definition of done is satisfied. If genuine AI success, external infrastructure, budget or cleanup remains unresolved, state exactly which criterion is unmet. Do not call the initial loop proved merely because the report generator ran.

## 9. Operator commands the implementation must provide

The commands below specify the intended interface. They do not exist yet. Implement and exercise them in this order; include final copy-paste installation commands using the chosen lockfile in README.

```bash
cd /home/maxime/goProjects/github.com/refractionPOINT/lc-ai
git branch --show-current
git status --short
bash evals/scripts/bootstrap.sh
evals/.venv/bin/python -m pytest evals/tests/unit
evals/.venv/bin/ruff check evals/src evals/tests

evals/.venv/bin/lc-eval init --from-local --config /absolute/private/eval.yaml --run-data /absolute/private/eval-runs --model-budget-usd 50
evals/.venv/bin/lc-eval doctor --config /absolute/private/eval.yaml --offline
evals/.venv/bin/lc-eval build --config /absolute/private/eval.yaml
evals/.venv/bin/python -m pytest evals/tests/integration
evals/.venv/bin/lc-eval doctor --config /absolute/private/eval.yaml --live
evals/.venv/bin/lc-eval fixtures probe --config /absolute/private/eval.yaml
evals/.venv/bin/lc-eval validate-suite --suite initial-loop --config /absolute/private/eval.yaml --live
evals/.venv/bin/lc-eval smoke --config /absolute/private/eval.yaml --campaign initial-proof
evals/.venv/bin/lc-eval run --suite initial-loop --config /absolute/private/eval.yaml --campaign initial-proof
evals/.venv/bin/lc-eval fault-drill --config /absolute/private/eval.yaml --campaign initial-proof
evals/.venv/bin/lc-eval reconcile --config /absolute/private/eval.yaml --campaign initial-proof
evals/.venv/bin/lc-eval report --config /absolute/private/eval.yaml --campaign initial-proof
evals/.venv/bin/lc-eval acceptance --config /absolute/private/eval.yaml --campaign initial-proof
```

`doctor --live` uses read-only checks; provisioning occurs in fixture/run operations. `build` creates local images only. Fixture lifecycle automatically starts/stops the local receiver and temporary HTTPS tunnel; no manual cloud deployment step is needed. `validate-suite --live` runs references and bad references, not LLMs. `smoke` exercises model launch, a harmless local shell action and termination for both harnesses. `run` executes the configured campaign matrix including the two A/A repeats. `reconcile` operates only on the exact ledger-owned resources, never all orgs matching a broad prefix. `fault-drill` explains and targets only its own child controller and resources. All live model smoke tests must name the same budget ledger as `initial-proof`; do not accidentally give doctor, smoke and run separate $50 allowances.

Repeat campaign names must not overwrite records or resume agent state. Require an explicit new attempt/campaign ID or return the existing manifest/result. Trial timeouts and failures still produce reports. Cleanup failure exits nonzero and reports remaining IDs.

`bootstrap.sh` installs a pinned uv tool in eval-managed storage and runs `uv sync --locked --extra test --project evals`, without editing the user's tool installations. Use it for CI/live acceptance. Replace `/absolute/private/...` with explicit local paths when generating the resolved runbook; do not leave template placeholders in the final acceptance command transcript.

## 10. Configuration fields to finalize

Create a commented non-secret YAML example containing these groups:

- `schema_version`, `run_data_dir`, `suite`, `seed`, `repetitions`.
- `sources`: full CLI/docs commits, wheel SHA256, evaluator SDK pin, source dirty policy, candidate/worker images by digest.
- `lc`: `auth_mode: local_cli`, absolute bootstrap executable/digest, inherited environment selector, `location: auto` initially, `fresh_org`, org/resource ceilings, readiness/deletion timeouts. Dynamically minted secrets stay outside the exported config.
- `receiver`: mode `quick_tunnel` by default or `existing`, tunnel binary/image pin, ingest/private management ports, generated public URL, management credential reference, retention/cleanup settings.
- `agents`: adapter, binary/image version, model ID, effort, auth reference/mode, permission/tool profile, price-table reference, token/time/spend limits and hard/soft budget semantics.
- `execution`: `controlled-cli-v1`, egress configuration, `/work` size cap, max command duration/output, shutdown grace and broker limits.
- `limits`: approved campaign model budget, infrastructure allowance, concurrency, max fixture events/bytes, verification and lease bounds.

Model IDs and prices are explicit operator inputs resolved against actual accessible models before launch. Do not choose an unverified “latest” alias or invent a price. Record cache accounting, actual versus estimated cost and gaps. The campaign reserves resources/budget before starting a trial and stops scheduling new ones when funds or quotas are insufficient.

Suggested starting timing defaults for calibration: 600 seconds agent execution per focused task, 900 for routing, 600 fixture readiness, 600 verification, 360 org deletion, 15 seconds process shutdown grace. They are limits to validate and version, not claims about actual service latency. Platform settling does not secretly extend agent execution time.

## 11. Required tests and evidence checklist

- Configuration/schema rejection, path traversal and secret-reference handling.
- State-machine recovery, ambiguous create reconciliation, duplicate cleanup, lease expiry, expired credentials and container shutdown.
- Broker parity, multi-command accounting, stdin/files/output, blocked bypass routes, symlinks and cancellation.
- Harness parsing from realistic fixtures including split lines, partial output, nonzero exits, permission denial, missing final usage and duplicate/cumulative usage events.
- HMAC tampering, stale receipts, large payload limits, duplicate receipts, missing receiver health and protected management access.
- Graders: exact nested state preservation, export membership/value/count, actual output delivery, negative probes and inconclusive evidence.
- Live reference passes, named bad-reference failures, six actual AI trial results, required AI successes and cleanup proof.
- One restart/interruption recovery result, paired A/A report, final unresolved resource count of zero.
- Artifact export is redacted; public prompts contain no answer manifests; HTML reports escape content.

Do not add implementation-mirroring unit tests to pad coverage. Test observable contracts and failure paths above. Never skip a mandatory live assertion solely to get acceptance green.

## 12. Follow-up work after the initial proof

The initial three-task suite is a calibration milestone, not the platform-wide benchmark. Register every capability family from DESIGN.md with coverage status now; expand later through tenant creation by the agent, real endpoint enrollment/tasking, Cloud Security provider/finding fixtures, cases, email, vulnerabilities, IaC and AI services.

Workspace adapter completion comes next unless the user chooses it for the initial campaign. Establish remote image/CLI pinning, tool traces, clean memory/session configuration, artifact retrieval and enforceable CLI transport. Existing session start/attach/history APIs provide useful lifecycle building blocks, but do not prove these controls. Keep changes to `ai-sessions` out of this branch; if backend changes are necessary, report the concrete dependency for a separately authorized change.

Use supported code-result ingestion as one candidate for a future Cloud Security finding fixture; `cloudsec code ingest` and CAASM ingestion exist in the CLI. Validate real finding generation separately before claiming general Cloud Security fixture support. A JSON adapter sensor does not count as an EDR endpoint enrollment test.

The next phase adds scenario families and held-out variants using the same controller, adapters and independent verifiers. Do not expand all platform fixtures before proving M7.
