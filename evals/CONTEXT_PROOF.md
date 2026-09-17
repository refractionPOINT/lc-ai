# Native context profile proof

Campaign `expansion-context-final` ran the `bare` and `lc_ai` profiles through Claude Code, Codex, and the native AI Sessions runner. All six probes completed, passed their context assertion, and cleaned their Docker resources. No probe created a LimaCharlie organization or received platform authority.

| Harness | Version and model | Bare evidence | `lc_ai` evidence |
|---|---|---|---|
| Claude Code | 2.1.273; `claude-sonnet-5` | Isolated user skill directory absent; canary phrase, inventory, invocation, and read were absent | All 43 pinned LC skill names appeared in the 59-entry startup inventory; native `Skill` invocation observed; exact passive-canary phrase returned |
| Codex | 0.154.0; `gpt-6-astra` | Isolated user skill directory absent; canary phrase, inventory, invocation, and read were absent | Pinned canary file was explicitly read from the native user-skill directory and its exact phrase returned; this proves use, while the event stream did not independently expose startup discovery |
| AI Sessions | runner `bbe82892282e3989005e70ca9c4415f77866c563`; `claude-sonnet-5` | Isolated user skill directory absent and baked LC plugin/catalog paths unreadable; no canary evidence | Native plugin autoinit used the pinned corpus; native `Skill` invocation and exact passive-canary phrase observed |

Each probe had a 90-second execution limit and an eight-turn limit. Runs used authenticated subscriptions with token accounting and no dollar-cost claim. Provider builtin skills remain possible in every mode; `bare` means the LimaCharlie corpus is absent, not that the provider has no builtin skills. Documentation remained available read-only in both modes.

The passive runtime canary was `lc-fundamentals--platform-config` for standalone harnesses and native `platform-config` for AI Sessions. Its pinned source hash was `fb37832e3347a683c0ac234017b4909848d9d451913b546e8ab59a9788a970b1`; the standalone normalized copy was `e24bb8456af14a3051de3d3e8d14a32d25dc744fb5ad68fe48aa196a248ed740`. The probe requested documentation loading only and prohibited operational execution.

The controlled inputs were:

- LC skills commit `8ab473d023dc6a07dc285149d14cef8e36519a58`, 43 skills, source corpus `eb6c65a0b00dc3683338342b9f569a205cb0f5e034bcf466c60fe2334c67b768`.
- Standalone transformed corpus `660cc1ebb1fe040630e9add66fc9414d35b23e99fbed45b1b1874cba68058587` and support bundle `44acd527064b01a5e6f2cb3b8089efc4ea5e9af3f38b049c5af5b5fcc44043ff`.
- Documentation commit `3eeeb95207730af2e93f600ca93cdad82ef47f73` and CLI commit `fe67856c4cdd1265b0b90a452247b1fb395f7d08`.
- Candidate image `sha256:f860e0c1fdba6ae68d6fc07a810127040e34ff76906f67e5caed606d4e4448d3`.
- AI Sessions image `sha256:feca83783942b6f2e87205e2e127aafb6c37efbe60e161f626c3e96d647d3052` and runner binary `96608f655fe5c3f1e8cc23b6eb24a3b863e4b86d307172fafbaaeb5bbc0b97a9`.

The sanitized machine-readable record is [results/expansion-context-probes.json](results/expansion-context-probes.json). It contains only whitelisted identities, hashes, limits, aggregate usage, timing, and boolean probe evidence. Raw transcripts and private runtime artifacts remain outside the repository.
