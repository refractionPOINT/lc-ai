# Intel SOC - Automated Threat Intelligence Pipeline

A 3-agent pipeline that runs daily to collect open-source threat intelligence, analyze it against your org's actual platform profile, and produce detection rules and IOC lookups.

## Architecture

```mermaid
flowchart TD
    sched["24h_per_org schedule"] --> collector["Intel Collector<br/>(sonnet, ~$0.50)"]
    collector -->|"@intel-analyzer note"| analyzer["Intel Analyzer<br/>(opus, ~$2.00)"]
    analyzer -->|"@rule-engineer note"| engineer["Rule Engineer<br/>(opus, ~$3.00)"]

    collector -.->|fetches| tf["ThreatFox CSV +<br/>Feodo Tracker"]
    collector -.->|fetches| kev["CISA KEV"]
    collector -.->|fetches| dfir["DFIR Report"]
    collector -.->|fetches| sigma["SigmaHQ"]
    collector -.->|fetches| lol["LOLBAS/LOLDrivers"]

    analyzer -.->|checks| sensors["Org Sensors & Platforms"]
    analyzer -.->|checks| existing["Existing D&R Rules"]

    engineer -->|creates| lookups["IOC Lookups<br/>(active)"]
    engineer -->|creates| rules["D&R Rules<br/>(DISABLED)"]
    engineer -->|closes| case["Case with report"]
```

## How It Works

| Step | Agent | What Happens |
|------|-------|-------------|
| 1 | **Intel Collector** | Pulls from 5 threat intel sources daily, creates a case with raw intel |
| 2 | **Intel Analyzer** | Discovers org platforms, extracts IOCs/TTPs, filters by relevance, maps to ATT&CK |
| 3 | **Rule Engineer** | Populates IOC lookups, generates D&R rules (disabled), documents everything in the case |

### What Gets Created

- **IOC Lookups** (`intel-ioc-hashes`, `intel-ioc-domains`, `intel-ioc-ips`, `intel-ioc-urls`) — immediately active, can be matched by existing or new D&R rules
- **D&R Rules** — created in **disabled state** with names like `intel-sigma-t1059-encoded-powershell`. A human reviews and enables them.
- **Case** — closed with full report: what was collected, what was analyzed, what rules/lookups were created, with rules referenced by name (not full content)

### Platform-Aware Analysis

The Intel Analyzer checks what sensors and platforms are actually deployed in the org before recommending rules. If you only have Windows endpoints, it won't recommend Linux-specific detections. If you have no network monitoring, it will deprioritize network IOCs.

## Intel Sources (MVP)

| Source | Type | What It Provides | Update Frequency |
|--------|------|-----------------|-----------------|
| [ThreatFox](https://threatfox.abuse.ch/) + [Feodo Tracker](https://feodotracker.abuse.ch/) | CSV exports | IOCs (C2 IPs, domains, hashes) tagged by malware family; botnet C2 IPs | Continuous |
| [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | JSON feed | CVEs confirmed exploited in the wild | ~Weekly |
| [The DFIR Report](https://thedfirreport.com/) | RSS + scrape | Full intrusion case studies with IOCs and TTPs | ~Monthly |
| [SigmaHQ](https://github.com/SigmaHQ/sigma) | Git commits + raw YAML | Community detection rules with ATT&CK mappings | ~Weekly (30-day window) |
| [LOLBAS](https://lolbas-project.github.io/) / [LOLDrivers](https://www.loldrivers.io/) | Git commits | Legitimate binaries/drivers abused by attackers | ~Monthly (30-day window) |

## Inter-Agent Communication

Agents signal each other by writing case notes with @mentions. D&R rules match on `note_added` events containing the @mention and require `ai_agent.exec` permission.

| Signal | Meaning | Written By | Triggers |
|--------|---------|------------|----------|
| `@intel-analyzer` note | Raw intel ready for analysis | Collector | Analyzer |
| `@rule-engineer` note | Analysis complete, ready for rules | Analyzer | Rule Engineer |

**Lock/status tags** (still tag-based, for concurrency control):

| Tag | Meaning | Added By |
|-----|---------|----------|
| `analyzing-intel` | Analysis in progress (lock) | Analyzer |
| `engineering-rules` | Rule creation in progress (lock) | Rule Engineer |
| `rules-drafted` | Rules created (completion signal) | Rule Engineer |
| `intel-pipeline` | Marks case as part of intel pipeline | Collector |
| `daily-intel` | Marks daily intel report | Rule Engineer |

## Cost Profile

| Agent | Model | Budget | Typical Cost |
|-------|-------|--------|-------------|
| Intel Collector | sonnet | $2.00 | ~$0.50 |
| Intel Analyzer | opus | $5.00 | ~$2.00 |
| Rule Engineer | opus | $5.00 | ~$3.00 |
| **Total per day** | | **$12.00 max** | **~$5.50** |

## Prerequisites

1. **ext-cases extension** must be subscribed and configured with a webhook
2. **Anthropic API key** with access to Claude Sonnet and Opus
3. **Per-agent LimaCharlie API keys** with appropriate permissions (see agent READMEs)

## API Key Permissions

### intel-collector

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `ext.request` | Create cases via ext-cases |
| `investigation.get` | List/read cases (needed to get case_number after create) |
| `investigation.set` | Add notes, tags, update cases |
| `lookup.get` | Read the `intel-seen` dedup ledger |
| `lookup.set` | Write processed item keys to the ledger |
| `ai_agent.operate` | Allow the agent to run |
| `ai_agent.exec` | Trigger Intel Analyzer via @mention note |

### intel-analyzer

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `sensor.list` | Discover org platforms and data sources (EDR sensors + adapter sensors like Okta, AWS, etc.) |
| `dr.list` | Check existing detection coverage |
| `investigation.get` | Read the intel case and notes |
| `investigation.set` | Update case with analysis, add entities/tags |
| `ext.conf.get` | List subscribed extensions |
| `lookup.get` | Check existing lookups to avoid duplicate IOCs |
| `ai_agent.operate` | Allow the agent to run |
| `ai_agent.exec` | Trigger Rule Engineer via @mention note |

### intel-engineer

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context and event schema access |
| `sensor.list` | Find sensors to explore event data for each platform |
| `insight.evt.get` | Research actual event data via LCQL before generating rules |
| `dr.set` | Create new D&R rules |
| `dr.list` | Check existing rules |
| `lookup.set` | Populate IOC lookups |
| `investigation.get` | Read the analyzed case |
| `investigation.set` | Update case with report, close it |
| `ai_agent.operate` | Allow the agent to run |

## Installation

Deploy via the `lc-deployer` skill:
```
/lc-deployer install intel-soc to <org>
```

Or manually with `limacharlie sync push`:
```bash
limacharlie sync push --oid <oid> --input intel-soc.yaml
```

## Files

```
intel-soc/
├── README.md                          # This file
├── intel-soc.yaml                     # Master include file
├── intel-collector/
│   ├── README.md                      # Collector agent docs
│   └── hives/
│       ├── ai_agent.yaml              # Agent definition
│       ├── dr-general.yaml            # 24h schedule trigger
│       └── secret.yaml                # API key placeholders
├── intel-analyzer/
│   ├── README.md                      # Analyzer agent docs
│   └── hives/
│       ├── ai_agent.yaml              # Agent definition
│       └── dr-general.yaml            # @intel-analyzer mention trigger
└── rule-engineer/
    ├── README.md                      # Engineer agent docs
    └── hives/
        ├── ai_agent.yaml              # Agent definition
        └── dr-general.yaml            # @rule-engineer mention trigger
```
