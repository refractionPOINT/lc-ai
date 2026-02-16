# LimaCharlie Essentials Agents

This directory contains specialized agents for the lc-essentials plugin. These agents handle specific types of queries with optimized models and workflows.

## Available Agents

### sensor-health-reporter

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Check sensor health for a **single** LimaCharlie organization. Designed to be spawned in parallel by the `sensor-health` skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel (one instance per org) by the `sensor-health` skill when users ask about:
- Sensor connectivity status
- Data availability and reporting
- Offline or non-responsive sensors
- Sensor health across organizations

**Architecture Role**:
- **Parent Skill**: `sensor-health` (orchestrates parallel execution)
- **This Agent**: Checks ONE organization's sensors
- **Parallelization**: Multiple instances run simultaneously, one per org

**Expected Input**:
Receives a prompt specifying:
- Organization name
- Organization ID (UUID)
- Check type (e.g., "online but no data", "offline for X days")
- Time window (e.g., "last hour", "7 days")

**Output Format**:
Returns concise findings for its assigned org only:
```markdown
### {Org Name}

**Status**: Found N sensors | No issues found

Sensors with issues (N):
- sensor-id-1
- sensor-id-2
...
```

**Key Features**:
- **Single-Org Focus**: Only checks the one organization specified in its prompt
- **Fast Execution**: Uses Sonnet model + parallel API calls within the org
- **Concise Output**: Returns findings only, no aggregation or analysis
- **Error Tolerance**: Handles API errors gracefully, reports partial results
- **Designed for Parallelism**: Optimized to run alongside other instances

**Skills Used**:
- Bash (for `limacharlie` CLI)

**How It Works**:
1. Extracts org ID, check type, and time window from prompt
2. Calculates timestamps using bash date commands
3. Makes parallel API calls to gather sensor data for the org
4. Filters results based on check criteria
5. Returns concise findings for this org only (parent skill aggregates)

### dr-replay-tester

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Test D&R rules via historical replay against a **single** LimaCharlie organization. Designed to be spawned in parallel by the `detection-engineering` skill for multi-org testing.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel (one instance per org) by the `detection-engineering` skill when users want to:
- Test a D&R rule across multiple organizations
- Validate detection logic against real historical data
- Compare rule performance across different environments

**Architecture Role**:
- **Parent Skill**: `detection-engineering` (orchestrates parallel execution)
- **This Agent**: Tests rule against ONE organization's historical data
- **Parallelization**: Multiple instances run simultaneously, one per org

**Expected Input**:
Receives a prompt specifying:
- Organization name and ID (UUID)
- Detection rule (YAML/dict)
- Response rule (optional)
- Time window (e.g., "last 1 hour", "last 24 hours")
- Sensor selector (optional, e.g., `plat == "windows"`)

**Output Format**:
Returns **summarized** findings (not all matches):
```markdown
### {Org Name}

**Match Statistics**:
- Events processed: {N}
- Events matched: {M}
- Match rate: {X.X%}

**Sample Matches** (showing 5 of {total}):
1. {hostname}: {process} - {command_line_snippet}
...

**Common Patterns**:
- Top hostname: {hostname} ({N} matches)
- Top process: {process_name} ({N} matches)

**Assessment**: {Brief assessment}
```

**Key Features**:
- **Single-Org Focus**: Only tests against the one organization specified
- **Result Summarization**: Returns stats and top 5 samples, not all hits
- **Pattern Analysis**: Identifies common patterns in matches (hostnames, processes)
- **Fast Execution**: Uses Sonnet model for quick turnaround
- **Designed for Parallelism**: Optimized to run alongside other instances

**Skills Used**:
- Bash (for `limacharlie` CLI)

**How It Works**:
1. Extracts org ID, detection rule, time window, and selector from prompt
2. Converts time window to `last_seconds` parameter
3. Runs `replay_dr_rule` with extracted parameters
4. Analyzes results: calculates stats, extracts top samples, finds patterns
5. Returns concise summary for this org only (parent skill aggregates)

### org-reporter

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Collect comprehensive reporting data for a **single** LimaCharlie organization. Designed to be spawned in parallel by the `reporting` skill for multi-tenant reports.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel (one instance per org) by the `reporting` skill when users want to:
- Generate multi-tenant reports across all organizations
- Create billing and usage summaries (roll-ups and per-tenant)
- Produce security and operational dashboards

**Architecture Role**:
- **Parent Skill**: `reporting` (orchestrates parallel execution)
- **This Agent**: Collects ALL reporting data for ONE organization
- **Parallelization**: Multiple instances run simultaneously, one per org

**Expected Input**:
Receives a prompt specifying:
- Organization name and ID (UUID)
- Time range (start and end Unix timestamps)
- Detection limit (default: 5000)

**Output Format**:
Returns structured JSON with all collected data:
```json
{
  "org_name": "Client ABC",
  "oid": "uuid...",
  "status": "success|partial|failed",
  "time_range": { "start": ..., "end": ..., "days": 30 },
  "data": {
    "org_info": {...},
    "usage": { "total_events": ..., "total_output_gb": ... },
    "billing": { "plan": ..., "status": ... },
    "sensors": { "total": ..., "online": ..., "platforms": {...} },
    "detections": { "retrieved_count": ..., "limit_reached": ..., "top_categories": [...] },
    "rules": { "total_general": ..., "enabled": ... },
    "outputs": { "total": ..., "types": [...] }
  },
  "errors": [...],
  "warnings": [...],
  "metadata": { "apis_called": 9, "apis_succeeded": 8, ... }
}
```

**Key Features**:
- **Single-Org Focus**: Only collects data for the one organization specified
- **Comprehensive Collection**: Gathers usage, billing, sensors, detections, rules, and outputs
- **Error Tolerance**: Continues with partial data on non-critical failures
- **Detection Limit Tracking**: Flags when 5000 detection limit is reached
- **No Cost Calculations**: Reports usage metrics only (guardrail enforced)
- **Structured Output**: Returns JSON for easy aggregation by parent skill

**Skills Used**:
- Bash (for `limacharlie` CLI)

**How It Works**:
1. Extracts org ID, name, time range, and detection limit from prompt
2. Uses `limacharlie` CLI to collect all data (9 API calls)
3. Filters usage stats to requested time range
4. Tracks detection limit and flags if reached
5. Returns structured JSON for aggregation by parent skill

### threat-report-parser

**Model**: Claude Sonnet (requires intelligence for entity extraction)

**Purpose**: Parse threat reports (PDF, HTML, text files) and extract ALL IOCs and behaviors. Returns structured JSON with categorized indicators. Expects reports to already be downloaded to local files by the parent skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned by the `threat-report-evaluation` skill when users want to:
- Analyze threat intelligence reports
- Extract IOCs from breach reports or malware analysis
- Process APT campaign documentation

**Architecture Role**:
- **Parent Skill**: `threat-report-evaluation` (orchestrates the workflow)
- **Phase 0**: Parent skill downloads report to `/tmp/` (keeps content out of main context)
- **This Agent**: Reads local file and extracts structured data
- **Context Savings**: ~200KB PDF → ~10KB JSON (report never enters main context)

**Expected Input**:
- Report source (local file path in `/tmp/`, pre-downloaded by parent)
- Report type (pdf, html, text)

**Output Format**:
Returns structured JSON with:
- Report metadata (title, author, threat name)
- IOCs categorized by type (hashes, domains, IPs, paths, etc.)
- Behaviors with MITRE ATT&CK mappings
- Platform requirements

**Skills Used**:
- `Read` - For reading PDF/HTML/text files (handles PDFs natively)
- `Bash` - For any file operations if needed

### ioc-hunter

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Search for IOCs within a **single** LimaCharlie organization. Designed to be spawned in parallel (one instance per org) by the `threat-report-evaluation` skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel by the `threat-report-evaluation` skill for multi-org IOC hunting.

**Architecture Role**:
- **Parent Skill**: `threat-report-evaluation` (orchestrates parallel execution)
- **This Agent**: Searches ONE organization for IOCs
- **Parallelization**: Multiple instances run simultaneously, one per org

**Expected Input**:
- Organization name and ID (UUID)
- IOC list (hashes, domains, IPs, paths, etc.)
- Time window (default: 30 days)

**Output Format**:
Returns summarized findings classified by severity:
- Critical findings (immediate investigation)
- High/moderate/low priority findings
- Affected sensors with hostnames
- IOCs not found

**Skills Used**:
- Bash (for `limacharlie` CLI)

### behavior-hunter

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Search for malicious behaviors within a **single** LimaCharlie organization using LCQL queries. Designed to be spawned in parallel by the `threat-report-evaluation` skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel by the `threat-report-evaluation` skill for multi-org behavior hunting.

**Architecture Role**:
- **Parent Skill**: `threat-report-evaluation` (orchestrates parallel execution)
- **This Agent**: Generates LCQL queries and searches ONE organization
- **Parallelization**: Multiple instances run simultaneously, one per org

**Expected Input**:
- Organization name and ID (UUID)
- Behavior list with MITRE mappings
- Available platforms
- Time window (default: 7 days)

**Output Format**:
Returns summarized findings with:
- Behaviors found with sample events (max 5 per behavior)
- LCQL queries used
- Classification by event count (NONE/FEW/MODERATE/MANY/EXCESSIVE)

**Skills Used**:
- Bash (for `limacharlie` CLI)

### detection-builder

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Generate and validate D&R rules for a specific detection layer within a **single** LimaCharlie organization. Designed to be spawned in parallel (one per layer) by the `threat-report-evaluation` skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel by the `threat-report-evaluation` skill for building detections across multiple layers.

**Architecture Role**:
- **Parent Skill**: `threat-report-evaluation` (orchestrates parallel execution)
- **This Agent**: Builds rules for ONE detection layer (process, network, file, etc.)
- **Parallelization**: Up to 10 instances run simultaneously, one per layer

**Expected Input**:
- Organization name and ID (UUID)
- Detection layer (process, network, file, persistence, etc.)
- Threat name for rule naming
- Detection requirements list

**Output Format**:
Returns validated rules ready for deployment:
- Rule name, description, MITRE technique
- Detection YAML (validated)
- Response YAML (validated)
- Validation failures with error details

**Skills Used**:
- Bash (for `limacharlie` CLI)

### asset-profiler

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Collect comprehensive asset profile for a **single** sensor. Designed to be spawned in parallel (batched) by the `sensor-coverage` skill in single-org mode.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel (5-10 at a time) by the `sensor-coverage` skill when users want detailed asset profiling for online sensors.

**Architecture Role**:
- **Parent Skill**: `sensor-coverage` (single-org mode with asset profiling enabled)
- **This Agent**: Profiles ONE sensor (OS, packages, users, services, autoruns, connections)
- **Parallelization**: Multiple instances run simultaneously, batched by parent skill

**Expected Input**:
- Organization name and ID (UUID)
- Sensor ID (UUID)
- Hostname
- Profile depth (Basic, Standard, Full)

**Output Format**:
Returns structured JSON with asset details:
```json
{
  "sid": "sensor-uuid",
  "hostname": "WORKSTATION-01",
  "platform": { "os_name": "...", "os_version": "...", ... },
  "software": { "packages_count": N, "services_count": N, ... },
  "users": { "users_count": N, "admin_users": [...] },
  "network": { "connections_count": N, ... },
  "collection_errors": [],
  "profile_complete": true
}
```

**Skills Used**:
- Bash (for `limacharlie` CLI)

### gap-analyzer

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Analyze coverage gaps and calculate risk scores for sensors in a **single** LimaCharlie organization. Receives sensor classification data from the parent skill and returns risk-scored gap analysis with remediation priorities.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned by the `sensor-coverage` skill (single-org mode) after sensor discovery to perform detailed gap analysis.

**Architecture Role**:
- **Parent Skill**: `sensor-coverage` (single-org mode)
- **This Agent**: Performs detailed gap analysis for ONE organization
- **Separate from profiling**: Runs after sensor classification, provides risk scoring

**Expected Input**:
- Organization name and ID (UUID)
- Total sensor count
- Online count
- Offline breakdown by category
- New sensors (24h)
- Optional: Asset profiles from `asset-profiler` agents

**Output Format**:
Returns comprehensive gap analysis:
```json
{
  "org": { "oid": "...", "name": "..." },
  "summary": { "total_sensors": N, "coverage_pct": X, "sla_status": "..." },
  "offline_breakdown": { ... },
  "risk_distribution": { "critical": N, "high": N, ... },
  "gaps": { "stale_sensors": [...], "shadow_it": [...], ... },
  "remediation_priorities": [...]
}
```

**Skills Used**:
- Bash (for `limacharlie` CLI)

### org-coverage-reporter

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Collect comprehensive coverage data for a **single** LimaCharlie organization. Designed to be spawned in parallel (one instance per org) by the `sensor-coverage` skill in multi-org mode. Incorporates gap-analyzer logic internally and supports telemetry health checking.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel (one per org) by the `sensor-coverage` skill when users want fleet-wide coverage assessment across all tenants.

**Architecture Role**:
- **Parent Skill**: `sensor-coverage` (multi-org mode)
- **This Agent**: Collects coverage data for ONE organization
- **Parallelization**: Multiple instances run simultaneously, one per org
- **Incorporates**: Gap-analyzer logic (risk scoring, classification) and telemetry health checking built-in

**Expected Input**:
- Organization name and ID (UUID)
- Timestamps (NOW, 4H, 24H, 7D, 30D as Unix epoch)
- Stale threshold in days
- SLA target percentage
- Telemetry health flag (true/false)
- Asset profiling flag (true/false)

**Output Format**:
Returns structured JSON with complete coverage data:
```json
{
  "org_name": "Client ABC",
  "oid": "uuid",
  "status": "success|partial|failed",
  "coverage": { "total_sensors": N, "online": N, "coverage_pct": X, "sla_status": "..." },
  "offline_breakdown": { "recent_24h": N, "short_1_7d": N, ... },
  "risk_distribution": { "critical": N, "high": N, ... },
  "platforms": { "windows": { "total": N, "offline_pct": X }, ... },
  "tags": { "production": { "total": N, "online": N }, ... },
  "new_sensors_24h": [...],
  "critical_sensors": [...],
  "top_issues": [...],
  "errors": []
}
```

**Key Features**:
- **Incorporates gap-analyzer logic** - No separate agent spawn needed
- **Platform/tag breakdown** - Enables cross-tenant pattern analysis
- **Risk scoring built-in** - Calculates sensor risk scores directly
- **Structured for aggregation** - Output designed for `fleet-pattern-analyzer`

**Skills Used**:
- Bash (for `limacharlie` CLI)

### sensor-tasking-executor

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Execute sensor tasks (live response commands) on a single sensor and return results. Designed for parallel execution by the `sensor-tasking` and `fleet-payload-tasking` skills.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel by parent skills when users want to:
- Execute commands on specific sensors
- Collect data from endpoints (OS version, packages, services, etc.)
- Run live response operations across the fleet
- Perform YARA scans across a fleet

**Architecture Role**:
- **Parent Skills**: `sensor-tasking`, `fleet-payload-tasking`
- **This Agent**: Executes tasks on ONE sensor
- **Parallelization**: Multiple instances run simultaneously, one per sensor

**Expected Input**:
- Organization ID (UUID)
- Sensor ID (UUID)
- Task name (e.g., `get_processes`, `dir_list`, `os_version`)
- Optional task parameters
- Return specification

**Output Format**:
Returns structured JSON with task results:
```json
{
  "success": true,
  "sid": "sensor-uuid",
  "task": "get_processes",
  "online": true,
  "data": { ... },
  "metadata": { "execution_time_ms": 1234 }
}
```

**Key Features**:
- **Online Check**: Verifies sensor is online before tasking
- **Fast Execution**: Uses Sonnet model for quick turnaround
- **Error Handling**: Returns structured errors for offline sensors or task failures
- **Parallel-Friendly**: Optimized to run alongside other instances

**Skills Used**:
- Bash (for `limacharlie` CLI)

---

### fleet-pattern-analyzer

**Model**: Claude Sonnet (requires intelligence for pattern detection)

**Purpose**: Analyze cross-tenant patterns and detect systemic issues from aggregated coverage data. Receives per-org results from `org-coverage-reporter` agents and identifies platform degradation, coordinated enrollments, SLA compliance patterns, risk concentration, silent sensor patterns, and temporal correlations.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned by the `sensor-coverage` skill (multi-org mode) after all `org-coverage-reporter` agents complete, to analyze fleet-wide patterns.

**Architecture Role**:
- **Parent Skill**: `sensor-coverage` (multi-org mode)
- **This Agent**: Analyzes patterns ACROSS all organizations
- **Runs Once**: After parallel per-org collection completes
- **Input**: Aggregated results from all org-coverage-reporter agents

**Expected Input**:
- Configuration (pattern detection thresholds)
- Per-org results (JSON array from org-coverage-reporter agents)

**Output Format**:
Returns comprehensive fleet analysis:
```json
{
  "fleet_summary": { "total_sensors": N, "overall_coverage_pct": X, ... },
  "fleet_health": "HEALTHY|DEGRADED|CRITICAL",
  "systemic_issues": [
    {
      "pattern_id": "platform_degradation_linux",
      "severity": "high",
      "title": "Linux Platform Degradation",
      "description": "...",
      "affected_orgs": [...],
      "possible_causes": [...],
      "recommended_actions": [...]
    }
  ],
  "platform_health": { "windows": { "status": "healthy" }, "linux": { "status": "degraded" } },
  "sla_compliance": { "passing_count": N, "failing_orgs": [...] },
  "recommendations": [...]
}
```

**Pattern Detection**:
1. **Platform Health Degradation** - Platforms with >10% offline rate
2. **Coordinated Enrollment** - Shadow IT spikes across multiple orgs
3. **SLA Compliance Patterns** - Systemic SLA failures
4. **Risk Concentration** - Critical risks clustered in few orgs
5. **Temporal Correlation** - Simultaneous outages
6. **Silent Sensor Patterns** - Online sensors not sending telemetry (concentrated in specific orgs/platforms)

**Skills Used**:
- None (analyzes provided data, no API calls)

---

### fp-pattern-investigator

**Model**: Claude Sonnet (thorough security analysis)

**Purpose**: Conduct a **thorough cybersecurity investigation** of a single FP pattern to determine if it's truly a false positive or might be a real threat. Designed to be spawned in parallel (one instance per pattern) by the `fp-pattern-finder` skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel by the `fp-pattern-finder` skill after deterministic pattern detection, to validate each pattern before presenting to the user.

**Architecture Role**:
- **Parent Skill**: `fp-pattern-finder` (orchestrates parallel execution)
- **This Agent**: Investigates ONE detected FP pattern with full analyst capabilities
- **Parallelization**: Multiple instances run simultaneously, one per pattern

**Expected Input**:
Receives a prompt specifying:
- Organization name and ID (UUID)
- Pattern data (type, category, identifier, count, sample detection IDs)

**Output Format**:
Returns structured JSON with comprehensive investigation findings:
```json
{
  "pattern_id": "single_host_concentration-00313-NIX-penguin",
  "verdict": "likely_fp|needs_review|not_fp",
  "confidence": "high|medium|low",
  "reasoning": "Thorough investigation confirms this is Go build/test activity...",
  "key_findings": [
    "All executions from /tmp/go-build* paths",
    "Host tagged 'chromebook', 'max' - developer workstation",
    "No other detections on host in past 7 days",
    "Process trees show expected go test -> test2json chain"
  ],
  "risk_factors": [],
  "technical_evidence": {
    "samples_analyzed": 3,
    "sensor_info": { "hostname": "penguin", "tags": ["chromebook", "max"] },
    "additional_investigation": {
      "other_detections_on_host": 0,
      "related_events_checked": "LCQL query for network activity...",
      "process_tree_analysis": "Parent chain: go test -> test2json"
    }
  },
  "fp_rule_hints": { ... }
}
```

**Key Features**:
- **Advanced Analyst Mindset**: Investigates like an experienced security analyst, not a checklist
- **Full Investigative Capabilities**: Uses LCQL queries, process trees, IOC searches, timeline analysis
- **Thorough Context Gathering**: Examines related detections, network activity, and process ancestry
- **Evidence-Driven**: Follows investigative leads based on findings
- **Conservative Verdicts**: Uses `needs_review` when uncertain

**Investigation Approach**:
Rather than following a rigid checklist, adapts investigation based on findings:
- Examines sample detections for key attributes
- Builds sensor context (tags, hostname, purpose)
- Follows investigative leads (suspicious hashes → IOC search, unusual parents → process tree)
- Looks for consistency (FP indicator) vs. variance (threat indicator)
- Checks for related activity (other detections, network connections, persistence)

**Skills Used**:
- Bash (for `limacharlie` CLI)

**How It Works**:
1. Extracts pattern data from prompt
2. Examines sample detections in detail
3. Builds comprehensive sensor/host context
4. Conducts additional investigation based on findings (LCQL queries, IOC searches, process trees)
5. Analyzes patterns across samples (consistency vs. variance)
6. Returns detailed verdict with full technical evidence

---

### cloud-discoverer

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Survey a **single** cloud platform (GCP, AWS, Azure, DigitalOcean) to discover projects, VMs, and security-relevant log sources. Designed to be spawned in parallel (one instance per platform) by the `onboard-new-org` skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel by the `onboard-new-org` skill when users want to:
- Discover cloud infrastructure across multiple platforms
- Identify VMs suitable for EDR deployment
- Find security-relevant log sources for ingestion

**Architecture Role**:
- **Parent Skill**: `onboard-new-org` (orchestrates parallel execution)
- **This Agent**: Surveys ONE cloud platform
- **Parallelization**: Multiple instances run simultaneously, one per platform

**Expected Input**:
- Platform to survey (gcp, aws, azure, digitalocean)
- Scope (optional - specific projects/accounts)

**Output Format**:
Returns structured JSON with:
- Projects/accounts discovered
- VMs with OS info, status, and recommended deployment method
- Security-relevant services enabled
- Recommended log sources with priority ratings

**Key Features**:
- **Multi-Project Discovery**: Lists all accessible projects/subscriptions
- **OS Detection**: Determines VM operating system for EDR compatibility
- **Deployment Method Recommendation**: Suggests OS Config, SSM, or Run Command
- **Permission Awareness**: Notes which operations failed due to permissions

**Skills Used**:
- `Bash` - For executing cloud CLI commands

---

### vm-edr-installer

**Model**: Claude Sonnet (fast and cost-effective)

**Purpose**: Deploy LimaCharlie EDR to VMs on a **single** cloud platform using native deployment methods (OS Config for GCP, SSM for AWS, Run Command for Azure). Designed to be spawned in parallel (one instance per platform) by the `onboard-new-org` skill.

**When to Use**:
This agent is **not invoked directly by users**. Instead, it's spawned in parallel by the `onboard-new-org` skill when users want to:
- Deploy EDR agents to cloud VMs fleet-wide
- Use cloud-native deployment methods for reliability
- Track deployment status and sensor registration

**Architecture Role**:
- **Parent Skill**: `onboard-new-org` (orchestrates parallel execution)
- **This Agent**: Deploys EDR to VMs on ONE cloud platform
- **Parallelization**: Multiple instances run simultaneously, one per platform

**Expected Input**:
- Platform (gcp, aws, azure, digitalocean)
- List of VMs with IDs, zones/regions, and OS types
- LimaCharlie organization ID and installation key

**Output Format**:
Returns structured JSON with:
- Deployment status for each VM
- Sensor registration confirmation
- Policy assignments created (for OS Config)
- Errors with remediation steps

**Key Features**:
- **Native Deployment Methods**: Uses OS Config (GCP), SSM (AWS), Run Command (Azure)
- **Sensor Verification**: Confirms sensors appear in LimaCharlie within 2 minutes
- **Error Recovery**: Provides remediation steps for common failures
- **Parallel VM Deployment**: Deploys to multiple VMs in a single command

**Skills Used**:
- Bash (for `limacharlie` CLI and cloud CLI deployment commands)

---

## Agent Architecture

All agents follow Claude Code best practices:
- Single responsibility per agent
- Clear frontmatter with name, description, model, and skills
- Structured system prompts with role, instructions, examples, and constraints
- Optimized model selection (Sonnet for all tasks)
- Efficient tool usage with parallel operations where possible

## Adding New Agents

To add a new agent to this plugin:

1. Create a new `.md` file in this directory
2. Add YAML frontmatter with required fields:
   ```yaml
   ---
   name: agent-name
   description: What it does and when to use it
   model: sonnet|opus
   skills: []
   ---
   ```
3. Write a clear system prompt (2-4 paragraphs minimum)
4. Update this README with the new agent's details
5. Update the main plugin README with usage examples

## Best Practices

- **Model Selection**: Use Sonnet for all tasks, Opus for complex analysis requiring deeper reasoning
- **Skill Access**: Only include skills the agent actually needs
- **Clear Descriptions**: The description field determines when Claude invokes the agent
- **Examples**: Include concrete examples of queries the agent handles
- **Progress Tracking**: Use TodoWrite for multi-step operations
- **Error Handling**: Handle API errors gracefully and continue with partial results
