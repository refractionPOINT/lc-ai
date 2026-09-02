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
| `mailsec.get` | Read reports, parsed message details, campaigns, and sender history. |
| `ai_agent.operate` | **Required.** The platform guardrail that lets a key be driven by an AI agent to take actions at all. The playbook checks it first and refuses the whole triage without it, so a leaked agent key that lacks it cannot act. It is distinct from `mailsec.act`, not implied by it. |
| `org.get` | Basic organization context. |
| `mailsec.set` | Resolve a report after reaching a supported disposition. |
| `mailsec.act` | Optional. Move mail (quarantine/banner/trash/restore) or write a verdict. Omit for an investigate-only agent — it is then refused, server-side and audited, if it tries to act. |

Do not grant `mailsec.get.eml` to this agent. Raw EML is a separate privileged workflow;
the playbook is intentionally grounded in the parsed message model and indexed evidence.

## Safety and cost controls

- The agent and both rules ship with `usr_mtd.enabled: false`.
- `max_budget_usd: 0.50` is the AI Sessions-enforced per-run cap.
- `max_turns: 20` and `ttl_seconds: 180` bound the run to the P3 three-minute target.
- Both triggers share a 60-per-minute org-local suppression key.
- Message and report triggers use distinct work identifiers and per-work-item debounce keys.
- Campaign actions are previewed before confirmation.
- Action authority is the API key's permissions — `ai_agent.operate` to act at all, `mailsec.act` to move mail — enforced server-side and audited. The prompt is not a security boundary.

## Trigger semantics

- `mailsec-triage-suspicious` runs on `EMAIL_MESSAGE` only when the deterministic scorer
- `mailsec-triage-submitted` runs on `EMAIL_ACTION` where `action == submit_to_triage`
  AND `result == ok` — the org's own automation asking for a look. The `result` filter is
  load-bearing: an `alert_only` org still emits the action as audit, and matching the
  action alone would start paid sessions for exactly the orgs that chose alert-only.
  says `suspicious`. `malicious` mail is already actionable through normal automations.
- `mailsec-triage-user-report` runs on every `EMAIL_USER_REPORT`, without filtering on the
  scorer's verdict. A human report is new evidence and must not disappear because the
  scorer disagreed.

User reports can lack `original_msg_uuid` when the original predates collection or landed
outside protected scope. The playbook falls back to the forwarded report message and must
surface that coverage gap rather than inventing an original.

## Current state

The server substrate an agent needs is shipped and live-verified: report resolve/reopen,
provider actions, and the verdict write-back — `revise_verdict`, which stamps `mode: ai`
with a structured rationale and emits an `EMAIL_VERDICT` event. (An earlier version of this
note said the `mode: ai` write-back did not exist yet; it does.)

The remaining gap is in the AGENT'S RUNTIME, not the server: an AI Sessions agent drives
this substrate through the `limacharlie mailsec ...` CLI, and that command group must be
present in the runtime's `limacharlie` install. Runtimes shipping an older CLI (observed:
`v5.6.2`, which has no `mailsec` noun) let the agent start and investigate but not act — the
agent will correctly report the coverage gap and leave the work for a human rather than
fabricate. Persisting the rationale onto the report (`ms_reports.ai_summary`) and an
agent-composed reporter reply are not yet wired. The full dual-provider live run remains a
separate gate; do not read a working session as proof it has passed.

## Files

- `hives/ai_agent.yaml` — provider-neutral, credential-free, disabled agent definition.
- `hives/dr-general.yaml` — disabled suspicious-message and user-report triggers.
- `mailsec-triage.yaml` — one bundle including the definition and both triggers.
