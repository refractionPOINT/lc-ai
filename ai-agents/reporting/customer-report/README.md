# Customer Report - Weekly Customer-Facing Security Summary

An AI agent that runs once per week to produce a non-technical, customer-facing summary of
all security activity on a tenant. Designed for MSSP/MDR environments where the service
provider needs to communicate ongoing value to their customers.

## How It Works

```
168h_per_org schedule fires (weekly)
      |
      v
D&R rule matches
      |
      v
AI agent session starts with org context
      |
      v
Bot gathers all cases from the last 7 days
      |
      v
Bot reviews each case to understand activity:
      |
      ├── Threat Detection & Triage
      ├── Incident Investigation
      ├── Incident Response & Containment
      ├── Proactive Threat Hunting
      ├── Malware Analysis
      ├── Vulnerability Assessment
      ├── Attack Surface Monitoring
      ├── Threat Intelligence Updates
      ├── False Positive Tuning
      └── Security Posture Improvements
      |
      v
Writes a plain-language weekly report as a case
      |
      v
Session terminates (one_shot)
```

## Report Format

The agent produces a report written for non-technical stakeholders:

- **Opening summary** — friendly, high-level overview of the week
- **What We Did This Week** — sections covering investigations, threats neutralized, proactive hunts, detection improvements, and security posture
- **By the Numbers** — a table of key metrics
- **What This Means for You** — business value translation (time saved, risk reduced, continuous improvement)

The report uses "we" (the MSSP/MDR team) and "your" (the customer's environment) framing
throughout, and avoids security jargon.

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- A LimaCharlie API key with the following permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `investigation.get` | List and read cases |
| `investigation.set` | Create the report case, add notes |
| `ext.request` | Make requests to extensions (ext-cases) |
| `sop.get` | Read SOPs for operational guidance |
| `sop.get.mtd` | Read SOP metadata |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `sonnet` | Report writing doesn't need deep reasoning |
| `max_turns` | `40` | Enough to gather 7 days of cases and write the report |
| `max_budget_usd` | `1.50` | Cost cap per report session |
| `ttl_seconds` | `600` | Hard timeout (10 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| Schedule | `168h_per_org` | Runs once per week per organization |

## Files

- `hives/ai_agent.yaml` - AI agent definition with customer report prompt
- `hives/dr-general.yaml` - D&R rule triggering weekly via 168h_per_org schedule
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
