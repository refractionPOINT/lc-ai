# Implementation status

Branch: `eval/limacharlie-cli-ai`. Implementation started 2026-09-16.

| Milestone | Status | Evidence / remaining work |
|---|---|---|
| M0 Configuration/package | Implemented | Branch confirmed; Python 3.11.2, Docker 29.7.2 and local CLI authentication verified. |
| M1 Journal/controller | In progress | SQLite journal, exclusive campaign lock, CLI/controller state machine, exact cleanup reconciliation implemented; crash drill pending. |
| M2 Isolated CLI execution | In progress | Docker networks/proxies, pinned worker build, bounded CLI broker and credential/path policy implemented; live parity checks pending. |
| M3 Harnesses and budget | Implemented for subscriptions | Both real subscription smoke tests passed after packaging fixes; bounded time/turn/tool execution and token-only accounting. |
| M4 Live fixtures | Pending | Disposable org lifecycle live probe passed: create, auth, independent read, confirmed deletion; zero remaining resources. |
| M5 Scenarios/graders | In progress | Three manifests, public prompts and deterministic Hive/export/routing graders implemented; unit calibration passes. |
| M6 Reporting | Implemented | JSON/HTML reports, missing-metric handling, compatibility checks and acceptance criteria implemented. |
| M7 Live proof | Pending | No model trials yet; organization and Hive fixture/key lifecycle probes passed. |

Receiver, graders/reporting and harness modules are assigned to GPT-5.6 Sol agents. Controller, fixture lifecycle, configuration and integration remain with the primary agent. No unrelated files are included.

## Decisions and deviations

- Installed local harnesses use Claude/ChatGPT subscriptions. The plan's API-key hard-dollar budget cannot be claimed for those auth modes. User explicitly selected subscription limits. The initial loop uses that mode; API-key dollar budgeting is optional.
- The main package does not import the candidate CLI. Independent verification will use authenticated HTTP with tokens obtained from the trusted host CLI, keeping candidate dependencies out of the controller.

## Verification evidence

- Offline suite: 108 tests passed at the hardened transport/controller checkpoint; full Ruff check passed.
- `org-probe-1789581947`: real org creation, authenticated independent identity read, confirmed deletion; ledger empty.
- `hive-probe-1789582514`: two real lookup records seeded with metadata, restricted candidate key created and revoked, org deleted; ledger empty.
- Initial Docker build exposed an invalid image-ID `FROM`; fixed to the pulled immutable repository digest. Native Volta Codex executable resolution is covered separately from its launcher.

These are infrastructure checks, not completed model-trial acceptance. The whole-loop proof is still in progress.

- `calibration-6dbc7b7414`: first complete live Hive reference **passed**, including independent semantic grading and verified cleanup.
- Earlier `hive-reference-a3b7439936` exposed Docker file-staging failure; corrected staging now uses a fixed trusted worker writer with exclusive/no-follow file creation. The failed attempt was retained and cleaned.
- Subscription smoke: Codex authenticated and reported token usage; its tool host was missing from the initial image. Claude rejected the empty MCP config shape before a model call. Both packaging corrections are in progress; these are not scored model failures.
- `calibration-5ff175384d`: complete-export preparation hit repeated regional search HTTP 500 responses; trial marked infrastructure-inconclusive and cleaned. Investigation compares independent HTTP against the trusted CLI before any export model trial.

## Initial execution-profile limits

The public task discloses the initial command/flag allowlist, fixed `/work` cwd, and exclusion of CLI checkpoint/resume and output-file options (shell redirection works). Input files are snapshotted without following symlinks and staged outside the shared workspace. The trial key has only scenario permissions. Resource-name restrictions are checked by graders rather than broker policy. These controls narrow the first calibration; wider CLI coverage requires deliberate profile revisions.

### Cleanup audit correction

A later independent owner-inventory audit found four exact journal-owned test organizations visible again after earlier deletion polls had observed them absent. The previous per-probe `cleanup: clean` results therefore **do not establish sustained deletion**. The account subsequently rejected org creation at its organization limit. Live scenario scheduling is paused while exact owned IDs are reconciled and deletion convergence is strengthened. No unrelated organization is in scope. Acceptance cannot pass until this audit is clear; historical failed cleanup evidence is retained.

- Rebuilt harness smoke **passed for both real CLIs**: `harness-smoke-v2-c7ee3e2b60` (Claude Code) and `harness-smoke-v2-52f5f0ded0` (Codex). Both wrote the requested file and invoked the transported CLI successfully, then cleaned their isolated runtimes. These are smoke checks, not scored scenario results.
- Exact re-cleanup of the four historical owned organizations completed; owner inventory remained empty for 62 continuous seconds. The defect was the initial absence shortcut skipping deletion entirely. Normal lifecycle logic and historical-result auditing are being strengthened accordingly.

- Search diagnostic `search-diagnostic-beccc28abacc` isolated the 500 to a missing/new Insight dataset: validation and initiation succeeded; one failed query ID stayed failed, while a fresh trusted-CLI query later succeeded. Fixture readiness now retries fresh queries within its deadline. The initial proof pins `--location usa` (rather than `auto`) because the service error identifies `usa-1` as supported for Search. Diagnostic cleanup passed with sustained absence.

- Current offline checkpoint: **125 tests passed**, including controller finalization, exact cleanup, adapter stream handling, scoped broker, receiver signatures and deterministic graders.
- `calibration-b4dfd758dd`: export preparation revealed cloud-adapter `last_error: adapter: lc installation key not authorized`. Accepted webhook HTTP batches alone are not ingestion evidence. The calibration was interrupted for exact cleanup; installation-key setup is being corrected before a fresh trial.

- The hosted-adapter enrollment defect is fixed: `installation-key create --get` returns both `key` (native sensor/RPCM) and `json_key` (adapters); fixtures now require `json_key` and reject a binary-only response. Focused regression tests pass. The interrupted calibration completed cleanup with no pending resources.
