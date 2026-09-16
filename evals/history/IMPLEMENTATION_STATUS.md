> Historical record of the initial build (2026-09-16). Do not use this as the current implementation checklist. See [running evals](../RUNNING.md) and [adding evals](../ADDING_EVALS.md).

# Implementation status

Branch: `eval/limacharlie-cli-ai`. Implementation started 2026-09-16.

| Milestone | Status | Evidence / remaining work |
|---|---|---|
| M0 Configuration/package | Implemented | Branch confirmed; Python 3.11.2, Docker 29.7.2 and local CLI authentication verified. |
| M1 Journal/controller | Implemented | Live crash drill `fault-05046ba64cc944b3` proved acquisition, abrupt interruption, journal recovery and sustained clean deletion. |
| M2 Isolated CLI execution | Implemented | Expanded live parity (seven CLI cases) and three isolation checks passed in `calibration-4313564b3f`. |
| M3 Harnesses and budget | Implemented for subscriptions | Both real subscription smoke tests passed after packaging fixes; bounded time/turn/tool execution and token-only accounting. |
| M4 Live fixtures | Implemented and verified | All three correct references passed against real LC resources; hosted webhook warmup, paced ingestion, genuine pagination and signed output delivery are verified. |
| M5 Scenarios/graders | Live calibration complete | All three correct references passed; each incorrect reference failed its intended assertion. `validate-suite --campaign calibration` passed after cleanup. |
| M6 Reporting | Implemented | JSON/HTML reports, missing-metric handling, compatibility checks and acceptance criteria implemented. |
| M7 Live proof | Complete | Eight genuine passes, both compatible Hive A/A pairs, reference/negative calibration, crash recovery, final cleanup and acceptance passed. See [ACCEPTANCE.md](../ACCEPTANCE.md). |

Receiver, graders/reporting and harness modules are assigned to GPT-5.6 Sol agents. Controller, fixture lifecycle, configuration and integration remain with the primary agent. No unrelated files are included.

## Decisions and deviations

- Installed local harnesses use Claude/ChatGPT subscriptions. The plan's API-key hard-dollar budget cannot be claimed for those auth modes. User explicitly selected subscription limits. The initial loop uses that mode; API-key dollar budgeting is optional.
- The main package does not import the candidate CLI. Independent verification will use authenticated HTTP with tokens obtained from the trusted host CLI, keeping candidate dependencies out of the controller.

## Verification evidence

- Offline suite: 108 tests passed at the hardened transport/controller checkpoint; full Ruff check passed.
- `org-probe-1789581947`: real org creation, authenticated independent identity read, confirmed deletion; ledger empty.
- `hive-probe-1789582514`: two real lookup records seeded with metadata, restricted candidate key created and revoked, org deleted; ledger empty.
- Initial Docker build exposed an invalid image-ID `FROM`; fixed to the pulled immutable repository digest. Native Volta Codex executable resolution is covered separately from its launcher.

The entries below are chronological investigation history. Final acceptance is complete; later entries supersede earlier in-progress statements without removing failed-attempt evidence.

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

- `calibration-5043d08d42`: routing reference passed all six independent assertions: ingestion, receiver health, full negative window, signed matching delivery, exclusion of negative probes, and preservation of the baseline output. Cleanup is in progress.
- Current offline checkpoint after warmup, probe retries, command metrics and nonempty-continuation proof: **154 tests passed; Ruff clean**.

- `calibration-238879db8a`: **export reference passed all seven assertions**. Search-confirmed warmup took 97 seconds; all 5,140 fixture events were observed, with page rows `[4560, 580, 0]`, proving a nonempty continuation. The transported candidate CLI exported exactly 5,003 production events with exact values, unique IDs and no platform mutations.
- `calibration-5043d08d42` routing cleanup completed cleanly. All three correct scenario references have now passed; remaining negative references and genuine AI trials are pending.

- `calibration-b357bb665e`: negative export calibration correctly failed `export.membership` and `export.count` after readiness proved all 5,140 events and nonempty continuation. File safety, valid JSONL, values of retained rows and platform preservation still passed, isolating the intended completeness failure. Cleanup is in progress.

- `calibration-be7ae8e001`: negative routing calibration failed only `routing.negatives_excluded`; ingestion, signed matching delivery, receiver health, full observation window and baseline preservation passed. Cleanup is in progress. All three intended negative failures have now been observed.

- `validate-suite --campaign calibration` returned **reference_validation_passed: true** for all three scenarios after all reference cleanup completed. The eight-trial genuine AI campaign `initial-proof` is now running sequentially from evaluator commit `fa77838`.

### Real-agent transport correction

- `initial-proof-1352f4c9e2` (Claude Code) and `initial-proof-9677f5415d` (Codex) both passed all Hive assertions and cleaned up. Trace review found that the broker rejected native CLI-supported `--ai-help` and global options after subcommands. Those extra errors are evaluator-induced friction.
- Both results retain their original task grades, tokens, command evidence and cleanup, with `invalid: true` and an explicit classification audit excluding them from scoring/comparison. The campaign stopped before other AI scenarios.
- The broker is being corrected against the pinned native CLI global-option hoisting contract, and live parity will include these cases. The scored suite will restart as **`initial-proof-v2`**, keeping the earlier attempts visible.

- Broker correction verified: **175 unit tests passed; Ruff clean**. `calibration-4313564b3f` passed all seven CLI parity cases (including root/group/leaf AI help and trailing global output), all three isolation checks, and all five Hive assertions.

- Expanded parity reference `calibration-4313564b3f` completed with verified clean deletion; reference validation passed again. Scored campaign **`initial-proof-v2`** runs from evaluator commit `d2bbb5a`. First Hive trials `initial-proof-v2-b11473c260` (Claude) and `initial-proof-v2-e88759af32` (Codex) passed all assertions and cleaned up. Export and routing trials, Hive repeats, and final acceptance remain in progress.

- Export setup attempts `initial-proof-v2-ea2df2ef91` (Codex) and `initial-proof-v2-3549abcc93` (Claude) were infrastructure-inconclusive before agent launch: all 5,140 events were independently searchable, but the backend returned only one nonempty page. Both cleaned up without model usage. Backend pagination operates on storage batches; fixed event count alone does not guarantee continuation. Fixture reliability and pre-agent reporting classification are under investigation; no export success is claimed.

- Both genuine routing trials passed all six assertions: `initial-proof-v2-c52050447d` (Claude) and `initial-proof-v2-bf63fd326e` (Codex). Signed matching delivery, full negative observation, excluded probes, ingestion and baseline preservation all passed. Claude cleanup is complete; Codex cleanup and Hive A/A repeats are in progress.

- Frozen `initial-proof-v2` campaign completed: six genuine task passes (four Hive including both repeats, two routing), two export pre-agent infrastructure failures, all cleaned. Updated reporting excludes pre-agent failures from model rates and coverage; both Hive A/A pairs are compatible.
- `039427e`: adaptive export growth now implements the planned bounded schedule (5,140 → 10,140 → 15,140 → 20,140 → 25,000), respects configured event/byte ceilings, and records actual nonempty continuation or unsupported status. New manifests include LC location; legacy comparisons use only persisted organization evidence. **191 tests passed; Ruff clean**. Canada reference `calibration-c81636c596` is in progress; its first two complete datasets were single-page, and growth is continuing without agent token usage.

- `calibration-c81636c596` passed all seven export assertions and verified cleanup in **Canada**. Bounded growth proved full searchable membership at each stage; 5,140 and 10,140 were single-page, while 15,140 events produced nonempty continuation. The trusted transported CLI exported exactly 15,003 production rows. Reference validation passed again, and real Codex/Claude export retries are now queued under `initial-proof-v2`, using private `config-canada.json` and evaluator `039427e`.

- Genuine Codex export `initial-proof-v2-e06caa68d1` passed all seven assertions in Canada after adaptive readiness proved 15,140 searchable events and nonempty continuation. The exported artifact contains exactly 15,003 unique production rows with correct values and no platform mutations. Cleanup is in progress; Claude export remains queued. Every initial scenario now has a genuine AI success, but full harness coverage and final cleanup/acceptance remain pending.

## Final acceptance — complete

- `initial-proof-v2-66b49892a8` (Claude export) passed all seven assertions after readiness grew to 20,140 searchable events and proved nonempty continuation; exported exactly 20,003 production rows. Both export retry cleanups completed.
- Campaign result: **8/8 genuine passes**, 10 recorded attempts including two pre-agent infrastructure failures. Two earlier broker-confounded Hive attempts remain invalid in the separate `initial-proof` campaign. Both Hive A/A comparisons are compatible; this is plumbing/calibration evidence, not a statistical performance claim.
- Final validation: **193 tests passed; Ruff and diff checks clean**. Targeted `--repetition` is implemented for the full documented mixed-region recipe.
- Final exact-ownership audit passed all five journals: zero pending resources, runtime leftovers or inventory errors. A private audit-checker mismatch for Docker absent-network wording was corrected; its initial failed output is retained.
- `validate-suite`, `report`, and `acceptance` returned success. [ACCEPTANCE.md](../ACCEPTANCE.md) and [sanitized results](../results/initial-proof-v2.json) contain outcomes, manifests, accounting and limitations. Subscription usage is token-only; dollar cost remains unknown.
