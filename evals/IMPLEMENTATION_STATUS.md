# Implementation status

Branch: `eval/limacharlie-cli-ai`. Implementation started 2026-09-16.

| Milestone | Status | Evidence / remaining work |
|---|---|---|
| M0 Configuration/package | Implemented | Branch confirmed; Python 3.11.2, Docker 29.7.2 and local CLI authentication verified. |
| M1 Journal/controller | Implemented | Live crash drill `fault-05046ba64cc944b3` proved acquisition, abrupt interruption, journal recovery and sustained clean deletion. |
| M2 Isolated CLI execution | Implemented | Live direct-versus-broker CLI parity and isolation checks passed in `calibration-b4ba166555`. |
| M3 Harnesses and budget | Implemented for subscriptions | Both real subscription smoke tests passed after packaging fixes; bounded time/turn/tool execution and token-only accounting. |
| M4 Live fixtures | In progress | Hive fixture works live. Adapter enrollment contract corrected to IID; event uploads now paced at 4 KiB/s for new-org throughput. Export/routing calibration pending. |
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

- Follow-up calibration `calibration-125938eba4` disproved the first key-format fix: hosted USP adapters still rejected `json_key`. Source trace through `go-uspclient` and `legion_usp_proxy/service/auth.go` establishes that this adapter field is the **installation record UUID (`iid`)**, passed unchanged as the protocol `iid`. CLI help describing `json_key` as suitable for adapters is misleading for this path. The fixture now follows the backend contract; the candidate CLI is unchanged. The failed calibration is retained and cleanup is running.

- `calibration-ceb3c441ef`: UUID-based adapter enrollment succeeded (sensor appeared); ingestion then hit the new organization free-tier ceiling, `over throughput of 10240 bytes/s for free tier`. Fixture uploads are being paced below that ceiling. HTTP acceptance alone remains insufficient; all expected event IDs must be independently searchable before candidate execution. No paid-tier change was made.
- Adapter and acceptance review: 138 offline tests passed. Subscription reports now suppress both dollar fields; Codex tool limits self-terminate; native configuration cannot override the pinned model; acceptance excludes smoke trials and requires complete reference evidence.

- `calibration-b4ba166555`: all seven live transport/isolation checks passed (version, help, JSON lookup, missing-key exit behavior, API proxy denial, direct egress denial, host Docker socket denial).
- Fixture sender now caps exact uncompressed batches at 4 KiB and paces 4 KiB/s across consecutive sends. Backend throughput counts decoded USP envelopes, so this leaves headroom below the 10 KiB/s free-tier limit. Routing readiness now retries fresh transient-failure queries with a bounded deadline and preserves infrastructure diagnostics.

- Hive calibration complete: `calibration-b4ba166555` passed, `calibration-8a4c4fe68a` failed the intended no-op assertion, both with completed execution and sustained clean deletion.
- `calibration-7c7091eba2`: paced injection avoided throughput errors and independently retrieved 4,836 events over continuation pages. The missing IDs were exactly injection positions 0–303, proving initial HTTP acceptance preceded sensor enrollment. The run was interrupted for cleanup; setup now needs a search-confirmed warmup probe before bulk data injection. The live Search limits endpoint reports 300 results per page (actual pages may include backend batches larger than that).

- Search-confirmed hosted-webhook warmup is implemented before bulk export injection. Routing verification now re-sends only missing original probe IDs during its bounded convergence window, retaining at-least-once delivery semantics; negative observation starts only after searchable ingestion and both positive delivery controls.
- Efficiency reports now aggregate CLI output bytes, execution seconds, failed commands and rejected requests from broker evidence. Incomplete command evidence yields unknown totals. Current review checkpoint: 150 offline tests passed.

- `fault-05046ba64cc944b3` (**initial-proof campaign**): live interruption recovery passed after acquiring an organization, candidate API key, isolated networks and all runtime containers; recovery removed every owned resource and confirmed sustained organization absence. This is recovery evidence, not an AI trial.
