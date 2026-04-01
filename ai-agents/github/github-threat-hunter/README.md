# GitHub Threat Hunter - Daily Proactive Security Analysis

An AI-powered threat hunter that runs daily to perform deep analysis of GitHub audit log
data, detecting threats that require cross-event correlation, behavioral analysis, and
pattern detection.

## How It Works

```
24h_per_org schedule fires (daily)
      |
      v
D&R rule matches
      |
      v
AI agent session starts with org context
      |
      v
Bot discovers GitHub sensors in org
      |
      v
Bot runs 6 hunt modules:
      |
      ├── Hunt 1: Impossible Travel Detection
      │   Geolocates actor IPs via MaxMind, flags physically
      │   impossible location changes between events
      │
      ├── Hunt 2: Mass Data Operations
      │   Detects bulk cloning/download patterns
      │   indicating data exfiltration
      │
      ├── Hunt 3: Authentication Anomalies
      │   Flags suspicious credential creation patterns
      │   and subsequent abuse
      │
      ├── Hunt 4: Permission Escalation Chains
      │   Detects gradual privilege escalation over 7 days
      │   indicating insider threat or compromised admin
      │
      ├── Hunt 5: Supply Chain Risks
      │   Analyzes GitHub Actions, webhooks, and app installs
      │   for potential supply chain attacks
      │
      └── Hunt 6: Security Configuration Drift
          Identifies weakened security posture over 7 days
          (branch protection, scanning, 2FA, etc.)
      |
      v
Creates cases for each finding with full evidence
      |
      v
Outputs summary report
      |
      v
Session terminates (one_shot)
```

## Hunt Modules

### Hunt 1: Impossible Travel Detection

Detects users accessing GitHub from geographically distant locations in impossibly short
time periods. Uses MaxMind for IP geolocation (city-level with lat/lon) and ASN lookup.

**Thresholds:**
- Different countries AND <2 hours apart
- Same country, >500km apart AND <1 hour apart
- Any distance >1000km AND <2 hours apart

**Confidence adjustments:**
- Lower: VPN/cloud provider ASNs, different auth methods
- Higher: Same `hashed_token` from both locations, sensitive actions from suspicious location

### Hunt 2: Mass Data Operations

Detects potential data exfiltration via bulk `git.clone` (>10/day) or `repo.download_zip`
(>5/day) operations. Excludes known CI/CD bots and GitHub App service accounts.

### Hunt 3: Authentication Anomalies

Flags suspicious credential patterns:
- Multiple PATs created in <1 hour
- PAT creation followed by high-volume git operations
- SSH key additions from unusual IPs
- OAuth authorizations for unfamiliar applications

### Hunt 4: Permission Escalation Chains (7-day window)

Detects gradual privilege escalation:
- Self-grants of elevated access
- Outside collaborators added to sensitive repos
- Escalated users subsequently performing high-risk actions

### Hunt 5: Supply Chain Risks

Analyzes GitHub Actions and integrations:
- Workflow runs with secrets passed to external contributors
- New GitHub App installations with broad permissions
- Webhooks pointing to suspicious external endpoints
- Self-hosted runner abuse indicators

### Hunt 6: Security Configuration Drift (7-day window)

Tracks weakening of security posture:
- Branch protection removals (listing affected repos)
- Security features disabled (secret scanning, Dependabot)
- Repos made public
- Org-wide settings weakened (2FA, OAuth restrictions)
- Checks whether changes were reverted or persist

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
| `insight.evt.get` | Query GitHub audit log events (up to 7-day windows) |
| `investigation.get` | List and read existing cases |
| `investigation.set` | Create cases, add notes, entities, telemetry |
| `ext.request` | Make requests to extensions (ext-cases) |
| `org_notes.*` | Read and write org notes |
| `sop.get` | Read SOPs for operational guidance |
| `sop.get.mtd` | Read SOP metadata |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Complex analysis requires deep reasoning |
| `max_turns` | `80` | High turn count for 6 hunt modules |
| `max_budget_usd` | `5.0` | Cost cap per hunt session |
| `ttl_seconds` | `1200` | Hard timeout (20 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| `debounce_key` | `github-threat-hunter` | Serializes sessions |
| Schedule | `24h_per_org` | Runs once per day per organization |
| Suppression | `2/24h` | Safety cap on daily invocations |

## Files

- `hives/ai_agent.yaml` - AI agent definition with 6 hunt module prompts
- `hives/dr-general.yaml` - D&R rule triggering daily via 24h_per_org schedule
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
