# GitHub Security Monitor - Real-Time Audit Log Analysis

An AI-powered security monitor that detects and investigates high-risk GitHub audit log events in real time, creating cases for genuine security threats.

## How It Works

```
High-risk GitHub audit log event fires
(e.g., branch protection removed, 2FA disabled, repo made public)
      |
      v
D&R rule matches specific event type
      |
      v
Suppression check (max 5/min)
      |
      v
Debounce check (one active session at a time)
      |
      v
AI agent session starts with event context
      |
      v
Bot discovers GitHub sensors in org
      |
      v
Bot queries last 4 hours of security-relevant events (batch)
      |
      v
For each suspicious event:
  - Analyzes actor (who, IP, auth method)
  - Assesses impact (target, blast radius)
  - Classifies threat (severity, category)
  - Correlates with related events (attack chains)
      |
      v
Creates cases with full context:
  - Summary, analysis notes, entities, telemetry
  - Correlated events grouped into single cases
      |
      v
Session terminates (one_shot)
```

## Detected Event Types

The monitor triggers on and analyzes:

| Category | Events | Severity |
|----------|--------|----------|
| Security Controls | 2FA disabled, secret scanning off, OAuth restrictions removed, Dependabot disabled | CRITICAL |
| Repository Exposure | Visibility changed to public, repo transferred out, repo deleted | CRITICAL-HIGH |
| Branch Protection | Protection removed, protection bypassed (force push) | HIGH |
| Access Management | New GitHub App installed, new deploy key, external collaborator added | HIGH |
| Permission Escalation | Member → Admin role change | HIGH |
| Webhook Manipulation | New webhook, webhook config change | MEDIUM |
| `sop.get` | Read SOPs for operational guidance |
| `sop.get.mtd` | Read SOP metadata |

## Correlation Patterns

The monitor looks for attack chains across events:

- **Account compromise:** Permission escalation → security control changes → data access
- **Credential abuse:** New token/key → unusual API activity
- **Defense evasion:** Multiple security controls disabled in sequence
- **Code integrity attack:** Branch protection removed → force push
- **Persistent access:** New webhook to external URL + security controls disabled

## Prerequisites

- GitHub audit log streaming configured via a LimaCharlie cloud adapter (GCS, S3, etc.)
- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- A LimaCharlie API key with the following permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | Discover GitHub audit log sensors |
| `sensor.get` | Get sensor details (hostname, platform) |
| `insight.evt.get` | Query GitHub audit log events |
| `investigation.get` | List and read existing cases |
| `investigation.set` | Create cases, add notes, entities, telemetry |
| `ext.request` | Make requests to extensions (ext-cases) |
| `org_notes.*` | Read and write org notes |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `sonnet` | Fast, cost-effective model for event triage |
| `max_turns` | `50` | Maximum CLI tool calls per session |
| `max_budget_usd` | `2.0` | Cost cap per session |
| `ttl_seconds` | `600` | Hard timeout (10 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| `debounce_key` | `github-security-monitor` | Serializes sessions: one at a time, pending re-fire |
| Suppression | `5/min` | Maximum agent invocations per minute (global) |

## Files

- `hives/ai_agent.yaml` - AI agent definition with security monitoring prompt
- `hives/dr-general.yaml` - D&R rules triggering the bot on high-risk GitHub events
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
