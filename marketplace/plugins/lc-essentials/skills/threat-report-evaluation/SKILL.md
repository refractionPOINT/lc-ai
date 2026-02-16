---
name: threat-report-evaluation
description: Evaluate threat reports, breach analyses, and IOC reports to search for compromise indicators across LimaCharlie organizations. Extract IOCs (hashes, domains, IPs, file paths), perform IOC searches, identify malicious behaviors, generate LCQL queries, create D&R rules and lookups. Use when investigating threats, APT reports, malware analysis, breach postmortems, or threat intelligence feeds. Emphasizes working ONLY with data from the report and organization, never making assumptions.
allowed-tools:
  - Task
  - Read
  - Bash
  - Skill
  - AskUserQuestion
  - WebFetch
---

# Threat Report Evaluation & IOC Analysis

Systematically evaluate threat reports to determine organizational impact and create comprehensive defense-in-depth detections.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output json [flags]
```

For command help: `limacharlie <command> --ai-help`
For command discovery: `limacharlie discover`

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **LCQL Queries** | Write query syntax manually | Use `limacharlie ai generate-query` first |
| **D&R Rules** | Write YAML manually | Use `limacharlie ai generate-detection` + `limacharlie rule validate` |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |

---

## Architecture

This skill uses specialized sub-agents to reduce context usage and enable parallel processing:

```
Main Skill (Orchestrator)
├── Phase 0: Download report to /tmp/ (keeps content out of main context)
├── Phase 1: Spawn threat-report-parser → Get structured IOCs/behaviors
├── Phase 2: Platform check (lightweight API call)
├── Phase 3: Spawn ioc-hunter agents (parallel, one per org)
├── Phase 4: Spawn behavior-hunter agents (parallel, one per org)
├── Phase 5: User checkpoint - present findings
├── Phase 6: Spawn detection-builder agents (parallel, by layer)
├── Phase 7: User approval - confirm rules to deploy
├── Phase 8: Deploy approved rules
└── Phase 9: Generate final report from aggregated summaries
```

## Critical Principles

- Extract IOCs and behaviors ONLY from the provided report
- Search ONLY in the specified LimaCharlie organization(s)
- NEVER fabricate or assume data not present
- Ask for user confirmation before creating any resources
- Use sub-agents for context-heavy operations

## Required Information

Before starting, obtain:
- **Threat Report**: URL, PDF, or text
- **Organization ID (OID)**: Target LimaCharlie org (or multiple for parallel hunting)
- **Time Window**: Search depth (default: 7 days for behaviors, 30 days for IOCs)

---

## Phase 0: Download Report (if URL provided)

**IMPORTANT**: Before spawning the parser agent, download the report to a local file. This keeps the report content out of the main context and allows sub-agents to process it independently.

### For URL reports:

```bash
# Download HTML/web reports
curl -sL "https://example.com/threat-report.html" -o /tmp/threat_report.html

# Download PDF reports
curl -sL "https://example.com/report.pdf" -o /tmp/threat_report.pdf
```

### For storage URLs (cloud-hosted PDFs):

```bash
# Google Cloud Storage
curl -sL "https://storage.googleapis.com/bucket/report.pdf" -o /tmp/threat_report.pdf

# S3 (public)
curl -sL "https://bucket.s3.amazonaws.com/report.pdf" -o /tmp/threat_report.pdf
```

**Important Notes**:
- Always use `/tmp/` for downloaded files
- Use `-sL` flags to follow redirects silently
- Pass the **file path** (not URL) to the parser agent
- The parser agent uses `Read` tool which handles PDFs natively

---

## Phase 1: Parse Threat Report

Spawn the `threat-report-parser` agent to extract all IOCs and behaviors. Always pass the **local file path** from Phase 0 (not the original URL).

```
Task(
  subagent_type="lc-essentials:threat-report-parser",
  prompt="Parse threat report and extract all IOCs and behaviors:

Report Source: /tmp/threat_report.pdf
Report Type: pdf"
)
```

**Agent returns structured JSON with**:
- Report metadata (title, author, threat name)
- IOCs categorized by type (hashes, domains, IPs, paths, etc.)
- Behaviors with MITRE ATT&CK mappings
- Platform requirements

**Display to user**: Summary of extracted IOCs and behaviors with counts.

---

## Phase 2: Platform Check

Use a lightweight API call to verify platforms exist in target org(s).

```bash
limacharlie event types --oid <oid> --output json
```

Filter IOCs and behaviors to matching platforms only.

---

## Phase 3: IOC Hunting (Parallel)

Spawn one `ioc-hunter` agent per organization. For multi-org scenarios, spawn all agents in a SINGLE message for parallel execution.

```
Task(
  subagent_type="lc-essentials:ioc-hunter",
  prompt="Search for IOCs in organization '{org_name}' (OID: {oid})

IOCs:
{iocs_json}

Time Window: 30 days"
)
```

**Spawn multiple in parallel for multi-org**:
```
# Single message with multiple Task calls = parallel execution
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org1...")
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org2...")
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org3...")
```

**Agent returns**:
- Findings classified by severity (critical/high/moderate/low)
- Affected sensors with hostnames
- IOCs not found

---

## Phase 4: Behavior Hunting (Parallel)

Spawn one `behavior-hunter` agent per organization.

```
Task(
  subagent_type="lc-essentials:behavior-hunter",
  prompt="Search for behaviors in organization '{org_name}' (OID: {oid})

Behaviors:
{behaviors_json}

Platforms Available: {platforms}
Time Window: 7 days"
)
```

**Agent returns**:
- Behaviors found with sample events (max 5 per behavior)
- LCQL queries used
- Classification by event count

---

## Phase 5: User Checkpoint

Present aggregated findings to user:

```markdown
## IOC Hunt Results

### Critical Findings (Immediate Investigation)
- [IOC type]: [value] - Found on [X] sensors

### High Priority Findings
- ...

### No Findings
- [X] IOCs searched, [Y] not found

## Behavior Hunt Results

### Suspicious Activity Detected
- [Behavior]: [X] events on [Y] sensors
  - Sample: [hostname]: [command_line]

### No Activity Detected
- ...

## Affected Sensors Summary
| Hostname | IOC Hits | Behavior Hits | Action Required |
|----------|----------|---------------|-----------------|
```

**Ask user**: "Continue with detection creation? Which layers are needed?"

---

## Phase 6: Detection Building (Parallel by Layer)

Based on findings and user input, spawn `detection-builder` agents for each detection layer.

**Detection Layers**:
1. **process** - Process execution, command-line, parent-child
2. **network** - DNS, connections, HTTP patterns
3. **file** - File creation, hash matching
4. **persistence** - Registry, scheduled tasks, services
5. **credential** - Credential dumping, priv-esc tools
6. **lateral** - Remote execution, authentication
7. **evasion** - Log clearing, masquerading
8. **stateful** - Chained detections, thresholds
9. **lookup** - IOC lookup matching rules
10. **fp_management** - False positive exclusions

```
Task(
  subagent_type="lc-essentials:detection-builder",
  prompt="Build detections for layer 'process' in organization '{org_name}' (OID: {oid})

Threat Name: {threat_name}

Detection Requirements:
{detection_requirements_json}"
)
```

**Spawn layers in parallel**:
```
Task(subagent_type="lc-essentials:detection-builder", prompt="...layer: process...")
Task(subagent_type="lc-essentials:detection-builder", prompt="...layer: network...")
Task(subagent_type="lc-essentials:detection-builder", prompt="...layer: file...")
```

**Agent returns**:
- Validated D&R rules ready for deployment
- Validation failures with error details

---

## Phase 7: User Approval

Present all generated rules for approval:

```markdown
## Generated Detection Rules

### Process Detections (5 rules)
| Rule Name | MITRE | Priority | Status |
|-----------|-------|----------|--------|
| apt-x-process-encoded-powershell | T1059.001 | 8 | validated |

### Network Detections (3 rules)
| Rule Name | MITRE | Priority | Status |
|-----------|-------|----------|--------|

[Show full YAML for each rule if requested]

## Validation Failures
- apt-x-network-exfil: Schema error - bytes_sent not available

## Deploy Rules?
- [ ] Deploy all validated rules
- [ ] Select specific rules to deploy
- [ ] Skip deployment (rules returned for manual review)
```

---

## Phase 8: Deploy Approved Rules

For each approved rule, deploy using:

```bash
limacharlie rule create <rule_name> --detect '<detect_yaml>' --respond '<respond_yaml>' --oid <oid>
```

Also create IOC lookup tables:

```bash
limacharlie lookup set <threat>-<ioc-type> --data '<ioc_data>' --oid <oid>
```

---

## Phase 9: Final Report

Generate final report from aggregated agent outputs:

```markdown
# Threat Report Evaluation: [Report Name]
Date: [YYYY-MM-DD]
Organization: [OID(s)]

## Executive Summary
[2-3 sentences on findings from agent summaries]

## IOC Search Results
| IOC Type | Searched | Found | Critical | High |
|----------|----------|-------|----------|------|
| Hashes   | 12       | 2     | 1        | 1    |
| Domains  | 8        | 0     | 0        | 0    |

## Behavioral Query Results
| Behavior | MITRE | Events | Sensors | Status |
|----------|-------|--------|---------|--------|
| Encoded PS | T1059.001 | 45 | 3 | Review |

## Detections Created

### D&R Rules Deployed
| Rule Name | Layer | Priority |
|-----------|-------|----------|

### Lookups Created
| Lookup Name | IOC Count |
|-------------|-----------|

## Affected Sensors
| Sensor | Findings | Action |
|--------|----------|--------|

## Recommendations
1. [Action items based on findings]
```

---

## Detection Checklist

For comprehensive coverage, ensure agents cover:

### Process Detections
- [ ] Malicious process names
- [ ] Command-line patterns
- [ ] Parent-child anomalies
- [ ] Suspicious execution paths
- [ ] Module loading

### Network Detections
- [ ] DNS lookups for threat domains
- [ ] Network connections to threat IPs
- [ ] HTTP/URL patterns
- [ ] Beaconing patterns

### File Detections
- [ ] File creation in persistence locations
- [ ] File hash matching via lookups
- [ ] Suspicious file extensions

### Persistence Detections
- [ ] Registry persistence
- [ ] Scheduled task creation
- [ ] Service installation
- [ ] Startup modifications

### Credential/Privilege Detections
- [ ] Credential dumping
- [ ] Known priv-esc tools

### Lateral Movement Detections
- [ ] Remote execution tools
- [ ] Anomalous authentication

### Defense Evasion Detections
- [ ] Log clearing
- [ ] Security tool tampering
- [ ] Masquerading

### IOC Lookups
- [ ] Hash lookup created
- [ ] Domain lookup created
- [ ] IP lookup created
- [ ] Path lookup created

---

## Rule Naming Convention

All rules follow: `[threat-name]-[layer]-[indicator]`

Examples:
- `apt-x-process-encoded-powershell`
- `apt-x-network-c2-domain`
- `apt-x-file-malicious-dll`
- `apt-x-persistence-runkey`

---

## Response Actions

Priority-based response actions:

**High Priority (8-10)**:
- Report with publish: true
- Add tag with 7-day TTL
- Consider sensor isolation for critical hits

**Medium Priority (5-7)**:
- Report with publish: true
- Add tag with 3-day TTL

**Low Priority (1-4)**:
- Report only
- Add informational tag

All responses include metadata:
- MITRE ATT&CK technique IDs
- Threat campaign name
- Remediation steps

---

## Multi-Organization Workflow

For MSSP scenarios with multiple organizations:

1. **Get org list** via `limacharlie org list --output json`
2. **Spawn ioc-hunter agents in parallel** (one per org in single message)
3. **Spawn behavior-hunter agents in parallel** (one per org in single message)
4. **Aggregate results** across all orgs
5. **Build detections** for each affected org

```
# Parallel IOC hunting across 5 orgs
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org1...")
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org2...")
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org3...")
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org4...")
Task(subagent_type="lc-essentials:ioc-hunter", prompt="...org5...")
```

---

## Troubleshooting

**Download fails**: Check URL accessibility, try with `curl -v` for verbose output

**Parser fails on PDF**: Ensure Phase 0 downloaded to `/tmp/`, then Read tool (handles PDFs natively)

**Too many IOC results**: Check for ubiquitous IOCs (>100 hits) - likely weak indicators

**Behavior queries return excessive events**: Ask agent to refine with more specific exclusions

**Rule validation fails**: Agent will retry; if still failing, review error in output

**Platform missing**: Agent automatically skips behaviors/detections for unavailable platforms

---

## Context Efficiency

This skill uses sub-agents and file-based report handling to reduce main context usage by ~90%:

| Phase | Without Optimization | With Optimization | Savings |
|-------|---------------------|-------------------|---------|
| Report Download | ~200KB in context | ~0KB (file on disk) | 100% |
| PDF Parsing | ~200KB | ~10KB JSON | 95% |
| IOC Search | ~100KB | ~20KB summaries | 80% |
| Behavior Search | ~150KB | ~15KB summaries | 90% |
| Detection Rules | ~50KB | ~25KB validated | 50% |

**Key optimizations**:
- Report downloaded to `/tmp/` - never enters main context
- Parser agent reads file directly and returns only structured JSON
- Each agent receives only the data it needs and returns summarized results
