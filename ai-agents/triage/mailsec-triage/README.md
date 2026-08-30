# Mailsec Triage

`mailsec-triage` is the optional AI Sessions playbook for LimaCharlie Email Security. It
uses the ordinary `limacharlie mailsec ...` CLI surface to investigate a suspicious
message or user report, optionally quarantine a message or campaign, and resolve a report
when the evidence supports a decision.

The bundle contains the agent and both triggers. All three records are disabled by
default. Installing this bundle therefore starts no session, spends no AI budget, and
touches no mailbox. An operator must configure credentials and then deliberately enable
the agent and whichever trigger rules match the organization's workflow.

## Why this is a catalog bundle

`ext-email-security` does not auto-install these records. The earlier auto-install design
would have put disabled, incomplete Hive records into every subscribing organization even
though the operator still had to choose a provider, credential, permissions, and trigger
volume. Keeping the bundle here makes installation an explicit composition decision while
still shipping the agent and its compatible rules as one reviewable unit.

## Prerequisites

- The private-beta `ext-email-security` extension is enabled and a mail provider is connected.
- A LimaCharlie API-key secret exists at `secret/mailsec-triage-key`.
- The agent record is completed with exactly one supported AI provider credential source.
  The checked-in record deliberately selects no provider and contains no AI secret.
- The deployed `limacharlie` CLI includes the Email Security commands.

Recommended LimaCharlie API-key permissions:

| Permission | Purpose |
|---|---|
| `org.get` | Basic organization context. |
| `mailsec.get` | Read reports, parsed message details, campaigns, and sender history. |
| `mailsec.set` | Resolve a report after reaching a supported disposition. |
| `mailsec.act` | Optional. Quarantine a message or campaign. Omit for investigate-only operation. |

Do not grant `mailsec.get.eml` to this agent. Raw EML is a separate privileged workflow;
the playbook is intentionally grounded in the parsed message model and indexed evidence.

## Safety and cost controls

- The agent and both rules ship with `usr_mtd.enabled: false`.
- `max_budget_usd: 0.50` is the AI Sessions-enforced per-run cap.
- `max_turns: 20` and `ttl_seconds: 180` bound the run to the P3 three-minute target.
- Both triggers share a 60-per-minute org-local suppression key.
- Message and report triggers use distinct work identifiers and per-work-item debounce keys.
- Campaign actions are previewed before confirmation.
- Action authority is only `mailsec.act` on the API key. The prompt is not a security boundary.

## Trigger semantics

- `mailsec-triage-suspicious` runs on `EMAIL_MESSAGE` only when the deterministic scorer
  says `suspicious`. `malicious` mail is already actionable through normal automations.
- `mailsec-triage-user-report` runs on every `EMAIL_USER_REPORT`, without filtering on the
  scorer's verdict. A human report is new evidence and must not disappear because the
  scorer disagreed.

User reports can lack `original_msg_uuid` when the original predates collection or landed
outside protected scope. The playbook falls back to the forwarded report message and must
surface that coverage gap rather than inventing an original.

## Current P3 boundary

The current API can resolve a report and can perform provider actions, but it does not yet
persist the AI session's structured rationale into `ms_reports.ai_summary`, update the
message with an `EMAIL_VERDICT` event in `mode: ai`, or send the reporter reply after that
verdict. The playbook says this plainly and must not be used as evidence that the P3 binary
gate has passed. Those server paths and the dual-provider live run remain separate gates.

## Files

- `hives/ai_agent.yaml` — provider-neutral, credential-free, disabled agent definition.
- `hives/dr-general.yaml` — disabled suspicious-message and user-report triggers.
- `mailsec-triage.yaml` — one bundle including the definition and both triggers.
