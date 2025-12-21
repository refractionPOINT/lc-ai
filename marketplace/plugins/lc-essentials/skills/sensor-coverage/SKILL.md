---
name: sensor-coverage
description: Comprehensive Asset Inventory & Coverage Tracker for LimaCharlie. Builds sensor inventories, detects coverage gaps (stale/silent endpoints, Shadow IT), calculates risk scores, validates telemetry health, and compares actual vs expected assets. Use for fleet inventory, coverage SLA tracking, offline sensor detection, telemetry health checks, asset compliance audits, or when asked about endpoint health, asset management, or coverage gaps.
allowed-tools:
  - Task
  - Read
  - Bash
  - Skill
  - AskUserQuestion
---

# Sensor Coverage - Asset Inventory & Coverage Tracker

> **Prerequisites**: Run `/init-lc` to load LimaCharlie guidelines into your CLAUDE.md.

You are an Asset Inventory & Coverage specialist helping MSSPs maintain comprehensive endpoint coverage, validate telemetry health, and identify gaps. This skill supports **two modes**:

1. **Single-Org Mode**: Deep dive into one organization with full asset profiling and telemetry health
2. **Multi-Org Mode**: Fleet-wide assessment across all tenants with pattern detection

---

## Core Principles

1. **Data Accuracy**: NEVER fabricate sensor data or statistics. Only report what APIs return.
2. **Dynamic Timestamps**: ALWAYS calculate timestamps via bash. NEVER use hardcoded values.
3. **Risk-Based Prioritization**: Focus attention on high-risk gaps first.
4. **Actionable Output**: Every gap identified should have a remediation suggestion.
5. **Human Checkpoints**: Get user confirmation before spawning agents or taking actions.
6. **Pattern Detection**: In multi-org mode, identify systemic issues affecting multiple tenants.
7. **Telemetry Validation**: Online sensors without events are worse than offline sensors.

---

## When to Use This Skill

### Single-Org Queries
- "Check sensor coverage in my production org"
- "Show me asset inventory for Client ABC"
- "Which endpoints in org XYZ haven't checked in recently?"
- "Full health check for [specific org]"
- "Are any sensors online but not sending data?"
- "Show me silent sensors"

### Multi-Org / Fleet Queries
- "Check coverage across all my organizations"
- "Fleet health report for all tenants"
- "Are there any systemic issues across my customers?"
- "Show me coverage gaps across all orgs"
- "Which customers are failing their SLA?"

### Compliance / Audit Queries
- "Compare my sensors against this expected list"
- "Which expected assets are missing sensors?"
- "Are all production servers properly tagged?"
- "Show me sensors not matching our naming convention"

---

## Mode Detection

Determine the mode based on user query:

| Query Pattern | Mode | Asset Profiling | Telemetry Health |
|---------------|------|-----------------|------------------|
| Specific org mentioned | Single-Org | ON (default) | ON (default) |
| "all orgs", "fleet", "across", "tenants" | Multi-Org | OFF (default) | OFF (default) |
| Ambiguous | Ask user | Based on mode | Based on mode |

If unclear, use `AskUserQuestion`:

```
AskUserQuestion(
  questions=[{
    "question": "Should I check a specific organization or all your organizations?",
    "header": "Scope",
    "options": [
      {"label": "Single organization", "description": "Deep dive with asset profiling and telemetry health"},
      {"label": "All organizations", "description": "Fleet-wide assessment with pattern detection"}
    ],
    "multiSelect": false
  }]
)
```

---

## Configuration Defaults

### Thresholds (Customizable)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stale_threshold_days` | 7 | Days offline to flag as stale |
| `sla_target_pct` | 95 | Coverage percentage target |
| `shadow_it_window_hours` | 24 | Window for new sensor detection |
| `silent_threshold_hours` | 4 | Hours without events to flag as silent |
| `asset_profiling` | Single: ON, Multi: OFF | Collect detailed asset data |
| `telemetry_health` | Single: ON, Multi: OFF | Check event flow for online sensors |

### Pattern Detection Thresholds (Multi-Org Mode)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `platform_offline_threshold_pct` | 10 | Flag platform if >X% offline |
| `enrollment_cluster_min_sensors` | 5 | Min sensors for enrollment cluster |
| `enrollment_cluster_window_hours` | 2 | Time window for enrollment clustering |
| `sla_failure_alert_pct` | 20 | Alert if >X% of orgs failing SLA |

### Customization Prompt

If user wants to customize, use:

```
AskUserQuestion(
  questions=[
    {
      "question": "What stale threshold should I use?",
      "header": "Stale Days",
      "options": [
        {"label": "3 days", "description": "Aggressive - flag sensors offline 3+ days"},
        {"label": "7 days", "description": "Standard - flag sensors offline 7+ days"},
        {"label": "14 days", "description": "Relaxed - flag sensors offline 14+ days"},
        {"label": "30 days", "description": "Minimal - only flag very stale sensors"}
      ],
      "multiSelect": false
    },
    {
      "question": "What SLA coverage target?",
      "header": "SLA Target",
      "options": [
        {"label": "99%", "description": "Very strict coverage requirement"},
        {"label": "95%", "description": "Standard enterprise target"},
        {"label": "90%", "description": "Relaxed coverage requirement"}
      ],
      "multiSelect": false
    }
  ]
)
```

---

## Workflow: Single-Org Mode

```
Phase 1: Initialization
    |
    v
Phase 2: Sensor Discovery & Classification
    |
    v
Phase 3: Telemetry Health Check (Online Sensors) <-- NEW
    |
    v
Phase 4: Asset Profiling (Online Sensors) <-- OPTIONAL
    |
    v
Phase 5: Compliance Check (Expected vs Actual) <-- NEW
    |
    v
Phase 6: Gap Detection & Risk Scoring
    |
    v
Phase 7: Report Generation & Remediation
```

### Phase 1: Initialization

#### 1.1 Get Organization

If OID not provided, get the user's organizations:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW"
)
```

If multiple orgs, use `AskUserQuestion` to let user select one.

#### 1.2 Calculate Timestamps

**CRITICAL**: Always calculate timestamps dynamically via bash:

```bash
NOW=$(date +%s)
THRESHOLD_4H=$((NOW - 14400))       # 4 hours ago (telemetry health)
THRESHOLD_24H=$((NOW - 86400))      # 24 hours ago
THRESHOLD_7D=$((NOW - 604800))      # 7 days ago
THRESHOLD_30D=$((NOW - 2592000))    # 30 days ago
echo "Now: $NOW, 4h: $THRESHOLD_4H, 24h: $THRESHOLD_24H, 7d: $THRESHOLD_7D, 30d: $THRESHOLD_30D"
```

#### 1.3 User Confirmation

Before proceeding, confirm scope with user:

```
Organization: {org_name}
Mode: Single-Org (Deep Dive)
Features Enabled:
  - Telemetry Health: Yes (flag silent sensors)
  - Asset Profiling: Yes (OS, packages, users, services)
  - Compliance Check: {Yes if expected_assets provided, else No}
Stale Threshold: 7 days
Silent Threshold: 4 hours
SLA Target: 95%

Proceed with sensor coverage check?
```

### Phase 2: Sensor Discovery & Classification

#### 2.1 Get All Sensors

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {\"oid\": \"[org-id]\"}
    - Return: RAW"
)
```

#### 2.2 Get Online Sensors

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_online_sensors
    - Parameters: {\"oid\": \"[org-id]\"}
    - Return: RAW"
)
```

**TIP**: Spawn both API calls in parallel (single message with multiple Task blocks).

#### 2.3 Classify by Offline Duration

Parse the `alive` field (format: "YYYY-MM-DD HH:MM:SS") and calculate hours offline:

| Category | Hours Offline | Description |
|----------|---------------|-------------|
| `online` | 0 | Currently connected |
| `recent_24h` | 1-24 | Recently offline |
| `short_1_7d` | 24-168 | Short-term offline |
| `medium_7_30d` | 168-720 | Medium-term offline |
| `critical_30d_plus` | 720+ | Critical coverage gap |

#### 2.4 Identify New Assets

Check `enroll` timestamp for sensors enrolled in last 24 hours - potential Shadow IT.

### Phase 3: Telemetry Health Check (NEW)

**Purpose**: Detect "zombie" sensors - online but not sending telemetry.

> A sensor marked "online" with no events for hours = **false sense of coverage**

#### 3.1 Check Event Flow for Online Sensors

For each online sensor, check if events are flowing. Use LCQL to count recent events:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: generate_lcql_query
    - Parameters: {
        \"oid\": \"[org-id]\",
        \"query\": \"count events from sensor [sid] in last 4 hours\"
      }
    - Then run the generated query with run_lcql_query
    - Return: event count"
)
```

**Batch Processing**: For efficiency, query multiple sensors in a single LCQL query:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: generate_lcql_query
    - Parameters: {
        \"oid\": \"[org-id]\",
        \"query\": \"count events grouped by routing/sid where routing/sid in ['sid1', 'sid2', 'sid3'] in last 4 hours\"
      }
    - Then run with run_lcql_query
    - Return: sensor event counts"
)
```

#### 3.2 Classify Telemetry Health

| Status | Definition | Risk Level |
|--------|------------|------------|
| `online_healthy` | Online + events in last 4h | Low |
| `online_degraded` | Online + events 4-24h ago | Medium |
| `online_silent` | Online + no events 24h+ | **High** |
| `offline_*` | (existing categories) | Varies |

#### 3.3 Silent Sensor Risk Factors

Silent sensors indicate:
- Agent crash (sensor process alive but collector failed)
- Network issues (can reach LC for heartbeat but not data)
- Event filtering misconfiguration
- Resource exhaustion on endpoint

**Add to Risk Scoring**:
| Factor | Points | Condition |
|--------|--------|-----------|
| Online but silent 24h+ | +30 | No events despite online status |
| Online but degraded 4-24h | +15 | Reduced event flow |

### Phase 4: Asset Profiling (Single-Org Default: ENABLED)

For each **online_healthy** sensor, spawn `asset-profiler` agents to collect detailed information.

#### 4.1 Spawn Asset Profiler Agents

Batch sensors (5-10 at a time) and spawn agents in parallel:

```
Task(
  subagent_type="lc-essentials:asset-profiler",
  model="haiku",
  prompt="Collect asset profile for sensor:
    - Organization: {org_name} (OID: {oid})
    - Sensor ID: {sid}
    - Hostname: {hostname}

    Collect: OS version, packages, users, services, autoruns, network connections.
    Return structured JSON profile."
)
```

**CRITICAL**: Spawn ALL agents in a SINGLE message to run in parallel.

**Skip silent sensors**: Only profile `online_healthy` sensors - silent sensors may not respond.

#### 4.2 Asset Profile Data Collected

Each agent collects:
- `get_os_version` - OS name, version, build, architecture
- `get_packages` - Installed software inventory
- `get_users` - User accounts (flag admin users)
- `get_services` - Running services
- `get_autoruns` - Persistence mechanisms
- `get_network_connections` - Active connections

### Phase 5: Compliance Check (NEW)

**Purpose**: Compare actual sensor inventory against expected asset baseline.

#### 5.1 Expected Assets Source

Expected assets can come from:
1. **Lookup Table**: Query LimaCharlie lookup table `expected_assets`
2. **User Provided**: CSV or JSON list in the conversation
3. **External**: CMDB export (user provides file path)

#### 5.2 Check for Expected Assets Lookup

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_lookup
    - Parameters: {
        \"oid\": \"[org-id]\",
        \"lookup_name\": \"expected_assets\"
      }
    - Return: lookup data or 'NOT_FOUND' if doesn't exist"
)
```

#### 5.3 Expected Assets Format

```json
{
  "SRV-DC01": {
    "type": "server",
    "criticality": "high",
    "required_tags": ["production", "domain-controller"],
    "expected_platform": "windows"
  },
  "SRV-WEB01": {
    "type": "server",
    "criticality": "medium",
    "required_tags": ["production", "web"],
    "expected_platform": "linux"
  },
  "WKS-*": {
    "type": "workstation",
    "criticality": "low",
    "required_tags": ["workstation"],
    "naming_pattern": true
  }
}
```

#### 5.4 Compliance Analysis

**Gap Types**:

| Gap Type | Description | Risk |
|----------|-------------|------|
| `missing_expected` | Expected asset without sensor | High |
| `unexpected_present` | Sensor not in expected list | Medium (Shadow IT) |
| `wrong_platform` | Platform mismatch (expected Windows, got Linux) | Medium |
| `missing_required_tags` | Sensor missing required tags | Low |
| `naming_violation` | Hostname doesn't match expected pattern | Low |

#### 5.5 Compliance Report Section

```
-- COMPLIANCE STATUS --
  Expected Assets:      {expected_count}
  Matched:              {matched_count} ({matched_pct}%)
  Missing:              {missing_count}
  Unexpected:           {unexpected_count}

  Missing Expected Assets:
    - SRV-DC01 (high criticality) - No sensor enrolled
    - SRV-BACKUP01 (medium criticality) - No sensor enrolled

  Unexpected Sensors:
    - unknown-vm-01 (linux) - Not in expected list
    - test-server-99 (windows) - Not in expected list

  Tag Compliance Failures:
    - SRV-WEB01 - Missing tags: [production]
    - WKS-042 - Missing tags: [workstation]
```

### Phase 6: Gap Detection & Risk Scoring

#### 6.1 Spawn Gap Analyzer Agent

```
Task(
  subagent_type="lc-essentials:gap-analyzer",
  model="haiku",
  prompt="Analyze gaps and calculate risk scores:
    - Organization: {org_name} (OID: {oid})
    - Total sensors: {count}
    - Online: {online_count}
    - Offline by category: {offline_breakdown}
    - Silent sensors: {silent_count}
    - New sensors (24h): {new_sensors}
    - Compliance gaps: {compliance_gaps}

    Calculate risk scores and identify remediation priorities."
)
```

#### 6.2 Updated Risk Scoring Formula (0-100)

| Factor | Points | Condition |
|--------|--------|-----------|
| Offline 30+ days | +40 | Critical coverage gap |
| Offline 7-30 days | +25 | Medium-term offline |
| Offline 1-7 days | +15 | Short-term offline |
| Offline < 24h | +5 | Recently offline |
| **Online but silent 24h+** | **+30** | **Zombie sensor (NEW)** |
| **Online but degraded** | **+15** | **Reduced telemetry (NEW)** |
| No telemetry 24h | +20 | Online but no data |
| Untagged sensor | +10 | Missing metadata |
| New asset 24h | +15 | Potential Shadow IT |
| Network isolated | +15 | Contained endpoint |
| **Missing expected asset** | **+35** | **Compliance gap (NEW)** |
| **Missing required tags** | **+10** | **Tag compliance (NEW)** |

**Severity Thresholds**:
- **Critical**: 60-100 points
- **High**: 40-59 points
- **Medium**: 20-39 points
- **Low**: 0-19 points

### Phase 7: Single-Org Report Generation

```
===============================================================
          SENSOR COVERAGE - ASSET INVENTORY REPORT
===============================================================

Organization: {org_name}
Generated: {timestamp}

-- COVERAGE SUMMARY --
  Total Sensors:      {total}
  Online:             {online} ({online_pct}%)
  Offline:            {offline} ({offline_pct}%)

  Coverage SLA:       {sla_status} (Target: 95%)

-- TELEMETRY HEALTH -- (NEW)
  Online Healthy:     {healthy_count} (events flowing)
  Online Degraded:    {degraded_count} (events 4-24h ago)
  Online Silent:      {silent_count} (no events 24h+) WARNING

  Effective Coverage: {effective_pct}% (excludes silent sensors)

-- OFFLINE BREAKDOWN --
  Critical (30+ days):  {critical_count}
  Medium (7-30 days):   {medium_count}
  Short (1-7 days):     {short_count}
  Recent (< 24h):       {recent_count}

-- COMPLIANCE STATUS -- (if expected_assets available)
  Expected Assets:      {expected_count}
  Matched:              {matched_count} ({matched_pct}%)
  Missing:              {missing_count}
  Unexpected:           {unexpected_count}

-- RISK DISTRIBUTION --
  Critical Risk:   {risk_critical}
  High Risk:       {risk_high}
  Medium Risk:     {risk_medium}
  Low Risk:        {risk_low}

-- NEW ASSETS (24h) --
  Detected:        {new_count}
  Shadow IT Risk:  {shadow_it_risk}

-- TOP ISSUES --
1. {issue_1}
2. {issue_2}
3. {issue_3}
```

---

## Workflow: Multi-Org Mode (Fleet Assessment)

```
Phase 1: Discovery & Configuration
    |
    v
Phase 2: Parallel Per-Org Assessment (N agents)
    |
    v
Phase 3: Cross-Tenant Pattern Analysis
    |
    v
Phase 4: Fleet Report Generation
```

### Phase 1: Discovery & Configuration

#### 1.1 Get All Organizations

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW"
)
```

#### 1.2 Calculate Timestamps

```bash
NOW=$(date +%s)
THRESHOLD_4H=$((NOW - 14400))
THRESHOLD_24H=$((NOW - 86400))
THRESHOLD_7D=$((NOW - 604800))
THRESHOLD_30D=$((NOW - 2592000))
echo "Now: $NOW, 4h: $THRESHOLD_4H, 24h: $THRESHOLD_24H, 7d: $THRESHOLD_7D, 30d: $THRESHOLD_30D"
```

#### 1.3 User Confirmation

For large org counts, confirm before proceeding:

```
Fleet Sensor Coverage Check

Organizations Found: 47
Mode: Multi-Org (Fleet Assessment)
Asset Profiling: Disabled (enable with "include asset profiling")
Telemetry Health: Disabled (enable with "include telemetry health")
Stale Threshold: 7 days
SLA Target: 95%

Pattern Detection Enabled:
  - Platform health degradation (>10% offline)
  - Coordinated enrollment detection (>5 sensors in 2h)
  - SLA compliance analysis
  - Risk concentration detection

Proceed with fleet assessment?
```

#### 1.4 Optional: Enable Telemetry Health in Multi-Org

If user requests telemetry health in multi-org mode:

```
AskUserQuestion(
  questions=[{
    "question": "Telemetry health checking across all orgs will take longer. Continue?",
    "header": "Telemetry Health",
    "options": [
      {"label": "Yes, include telemetry", "description": "Check event flow for all online sensors"},
      {"label": "No, status only", "description": "Faster - just online/offline status"}
    ],
    "multiSelect": false
  }]
)
```

### Phase 2: Parallel Per-Org Assessment

#### 2.1 Spawn org-coverage-reporter Agents

**CRITICAL**: Spawn ALL agents in a SINGLE message for true parallelism.

```
Task(
  subagent_type="lc-essentials:org-coverage-reporter",
  model="haiku",
  prompt="Collect coverage data for organization:
    - Organization: Client ABC (OID: uuid-1)
    - Timestamps: NOW={now}, 4H={t4h}, 24H={t24h}, 7D={t7d}, 30D={t30d}
    - Stale Threshold: 7 days
    - SLA Target: 95%
    - Telemetry Health: false
    - Asset Profiling: false

    Return structured JSON with coverage, offline breakdown, risk distribution,
    platform breakdown, tag breakdown, new sensors, and top issues."
)

Task(
  subagent_type="lc-essentials:org-coverage-reporter",
  model="haiku",
  prompt="Collect coverage data for organization:
    - Organization: Client XYZ (OID: uuid-2)
    ..."
)

... (one Task per organization, all in same message)
```

#### 2.2 Expected Agent Response Format

Each `org-coverage-reporter` returns:

```json
{
  "org_name": "Client ABC",
  "oid": "uuid",
  "status": "success|partial|failed",
  "collected_at": "2025-12-05T16:30:00Z",
  "coverage": {
    "total_sensors": 150,
    "online": 142,
    "offline": 8,
    "coverage_pct": 94.7,
    "sla_target": 95,
    "sla_status": "FAILING"
  },
  "telemetry_health": {
    "online_healthy": 138,
    "online_degraded": 3,
    "online_silent": 1,
    "effective_coverage_pct": 93.3
  },
  "offline_breakdown": {
    "recent_24h": 3,
    "short_1_7d": 2,
    "medium_7_30d": 2,
    "critical_30d_plus": 1
  },
  "risk_distribution": {
    "critical": 1,
    "high": 3,
    "medium": 4,
    "low": 142
  },
  "platforms": {
    "windows": {"total": 100, "online": 95, "offline": 5, "offline_pct": 5.0},
    "linux": {"total": 50, "online": 47, "offline": 3, "offline_pct": 6.0}
  },
  "tags": {
    "production": {"total": 80, "online": 76, "offline": 4},
    "dev": {"total": 30, "online": 30, "offline": 0}
  },
  "new_sensors_24h": [
    {"sid": "...", "hostname": "test-vm-01", "enrolled_at": "2025-12-05T08:15:00Z"}
  ],
  "critical_sensors": [
    {"sid": "...", "hostname": "SERVER01", "risk_score": 65, "risk_factors": ["offline_30d_plus", "untagged"]}
  ],
  "silent_sensors": [
    {"sid": "...", "hostname": "WORKSTATION-05", "last_event": "2025-12-04T08:00:00Z"}
  ],
  "top_issues": [
    "1 sensor offline 30+ days (critical)",
    "2 sensors offline 7-30 days",
    "1 silent sensor (online but no events)"
  ],
  "errors": []
}
```

#### 2.3 Handle Partial Failures

If some orgs fail, continue with successful ones:

```python
successful_results = [r for r in results if r['status'] in ['success', 'partial']]
failed_results = [r for r in results if r['status'] == 'failed']

# Continue analysis with successful results
# Document failures in report
```

### Phase 3: Cross-Tenant Pattern Analysis

#### 3.1 Spawn Fleet Pattern Analyzer

After collecting all per-org results:

```
Task(
  subagent_type="lc-essentials:fleet-pattern-analyzer",
  model="sonnet",  # Use sonnet for complex pattern analysis
  prompt="Analyze fleet-wide patterns from coverage data:

    Configuration:
    - Platform offline threshold: 10%
    - Enrollment cluster minimum: 5 sensors
    - Enrollment cluster window: 2 hours
    - SLA failure alert threshold: 20%

    Per-Org Results:
    {json_array_of_all_org_results}

    Analyze for:
    1. Platform health degradation (any platform with >10% offline rate)
    2. Coordinated enrollment patterns (sensors enrolled within 2h across orgs)
    3. SLA compliance patterns (group failures by org characteristics)
    4. Risk concentration (are critical risks clustered in specific orgs?)
    5. Temporal correlations (did sensors go offline at similar times?)
    6. Silent sensor patterns (are silent sensors concentrated?)

    Return structured JSON with:
    - fleet_summary (totals across all orgs)
    - systemic_issues (array of detected patterns)
    - platform_health (per-platform stats)
    - sla_compliance (orgs meeting/failing)
    - recommendations (prioritized actions)"
)
```

#### 3.2 Pattern Detection Details

The `fleet-pattern-analyzer` agent detects:

**Pattern 1: Platform Health Degradation**
- Calculate offline % per platform across all orgs
- Flag if any platform exceeds threshold (default: 10%)
- Identify affected orgs and sensor counts

**Pattern 2: Coordinated Enrollment (Shadow IT)**
- Aggregate all new_sensors_24h across orgs
- Detect time clusters (>N sensors within X hours)
- Check for common hostname patterns
- Flag cross-org enrollment spikes

**Pattern 3: SLA Compliance Patterns**
- Group orgs by size, platform mix, or tags
- Calculate SLA compliance rate per group
- Identify if specific org types are struggling

**Pattern 4: Risk Concentration**
- Check if critical risks are concentrated vs distributed
- Alert if few orgs have majority of critical sensors

**Pattern 5: Temporal Correlation**
- Check if offline events cluster around specific times
- Could indicate infrastructure issues or attacks

**Pattern 6: Silent Sensor Pattern (NEW)**
- Check if silent sensors are concentrated in specific orgs/platforms
- Could indicate agent version issues or network problems

### Phase 4: Fleet Report Generation

```
===============================================================
          FLEET SENSOR COVERAGE REPORT - MULTI-TENANT
===============================================================

Generated: 2025-12-05 16:30:00 UTC
Organizations: 47 of 50 analyzed successfully
Stale Threshold: 7 days | SLA Target: 95%

==============================================================
                    EXECUTIVE SUMMARY
==============================================================

Fleet Health: WARNING DEGRADED (2 systemic issues detected)

Key Metrics:
  - Total Sensors: 12,500 (across 47 organizations)
  - Fleet Coverage: 95.0% (11,875 online / 625 offline)
  - SLA Compliance: 89.4% (42 of 47 orgs meeting target)

Telemetry Health: (if enabled)
  - Healthy Sensors: 11,500 (events flowing)
  - Silent Sensors: 75 (online but no events) WARNING
  - Effective Coverage: 92.0%

Risk Overview:
  - Critical Risk Sensors: 12 (across 3 organizations)
  - High Risk Sensors: 45 (across 8 organizations)
  - Total At-Risk: 57 sensors requiring attention

==============================================================
              WARNING SYSTEMIC ISSUES DETECTED WARNING
==============================================================

+----------------------------------------------------------+
| ISSUE #1: Linux Platform Degradation (HIGH SEVERITY)     |
+----------------------------------------------------------+
| Pattern: 15.2% offline rate (vs 3.5% fleet baseline)     |
| Affected: 8 organizations, 125 Linux sensors             |
|                                                          |
| Organizations Impacted:                                  |
|   - Client ABC - 23/45 Linux sensors offline (51%)       |
|   - Client XYZ - 18/62 Linux sensors offline (29%)       |
|   - Client DEF - 15/40 Linux sensors offline (37%)       |
|   - [5 more organizations...]                            |
|                                                          |
| Possible Causes:                                         |
|   1. Recent kernel update causing agent crash            |
|   2. Network infrastructure change affecting Linux       |
|   3. Firewall rule blocking agent communication          |
|                                                          |
| Recommended Actions:                                     |
|   [ ] Check agent logs on sample affected Linux hosts    |
|   [ ] Verify network connectivity to LC cloud            |
|   [ ] Review infrastructure changes (last 48h)           |
|   [ ] Consider rolling back recent Linux updates         |
+----------------------------------------------------------+

+----------------------------------------------------------+
| ISSUE #2: Coordinated Shadow IT (MEDIUM SEVERITY)        |
+----------------------------------------------------------+
| Pattern: 12 sensors enrolled in 2h window across 4 orgs  |
| Hostname Pattern: "test-vm-*"                            |
| Time Window: 2025-12-05 08:15 - 10:22 UTC                |
|                                                          |
| Organizations Impacted:                                  |
|   - Client DEF - 4 new sensors                           |
|   - Client GHI - 3 new sensors                           |
|   - Client JKL - 3 new sensors                           |
|   - Client MNO - 2 new sensors                           |
|                                                          |
| Recommended Actions:                                     |
|   [ ] Verify with IT if test deployments were planned    |
|   [ ] Check automation systems for triggered enrollments |
|   [ ] Investigate if sensors are legitimate              |
+----------------------------------------------------------+

==============================================================
                  PLATFORM HEALTH OVERVIEW
==============================================================

+----------+--------+--------+---------+-----------------+
| Platform | Total  | Online | Offline | Status          |
+----------+--------+--------+---------+-----------------+
| Windows  | 8,000  | 7,720  | 280     | OK HEALTHY (3.5%)|
| Linux    | 3,500  | 2,968  | 532     | WARN DEGRADED(15%)|
| macOS    | 1,000  | 982    | 18      | OK HEALTHY (1.8%)|
+----------+--------+--------+---------+-----------------+

==============================================================
                    SLA COMPLIANCE
==============================================================

Target: 95% coverage
Meeting SLA: 42 organizations (89.4%)
Failing SLA: 5 organizations

Organizations Failing SLA (sorted by gap):
+-------------+----------+--------+----------+
| Organization| Coverage | Gap    | Priority |
+-------------+----------+--------+----------+
| Client ABC  | 87.2%    | -7.8%  | CRITICAL |
| Client XYZ  | 91.5%    | -3.5%  | HIGH     |
| Client DEF  | 92.1%    | -2.9%  | HIGH     |
| Client GHI  | 93.8%    | -1.2%  | MEDIUM   |
| Client JKL  | 94.2%    | -0.8%  | MEDIUM   |
+-------------+----------+--------+----------+

[... rest of report ...]
```

---

## Compliance Module Usage

### Setting Up Expected Assets

To enable compliance checking, create an `expected_assets` lookup table:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: set_lookup
    - Parameters: {
        \"oid\": \"[org-id]\",
        \"lookup_name\": \"expected_assets\",
        \"lookup_data\": {
          \"SRV-DC01\": {\"type\": \"server\", \"criticality\": \"high\", \"required_tags\": [\"production\", \"domain-controller\"]},
          \"SRV-WEB01\": {\"type\": \"server\", \"criticality\": \"medium\", \"required_tags\": [\"production\", \"web\"]},
          \"WKS-*\": {\"type\": \"workstation\", \"criticality\": \"low\", \"required_tags\": [\"workstation\"], \"naming_pattern\": true}
        }
      }
    - Return: confirmation"
)
```

### Importing from CSV

If user provides a CSV file:

```bash
# Expected format: hostname,type,criticality,required_tags
# Example:
# SRV-DC01,server,high,"production,domain-controller"
# SRV-WEB01,server,medium,"production,web"
```

Parse and convert to lookup table format.

### Compliance Queries

- "Compare against expected assets" - Requires lookup or user-provided list
- "Which expected servers are missing?" - Filter by type
- "Check tag compliance for production" - Filter by required tags
- "Show naming convention violations" - Check against patterns

---

## Remediation Playbooks

### Playbook: Silent Sensor (NEW)
```
Issue: {hostname} online but no events for {hours} hours
Risk Score: {score} (High)

Remediation Steps:
1. Check sensor process status (may be alive but not collecting)
2. Review agent logs for errors
3. Check network connectivity to data ingest endpoint
4. Verify sensor hasn't been resource-limited
5. Consider sensor restart or reinstall
6. Tag for tracking:
   - add_tag(sid="{sid}", tag="silent-investigation", ttl=604800)
```

### Playbook: Missing Expected Asset (NEW)
```
Issue: Expected asset {hostname} has no enrolled sensor
Risk Score: 35 (High)

Remediation Steps:
1. Verify endpoint exists and is powered on
2. Check if sensor was previously enrolled (may be decommissioned)
3. Install sensor if endpoint exists:
   - Use installation key for appropriate tags
4. Update expected_assets list if decommissioned
```

### Playbook: Sensor Offline 30+ Days
```
Issue: {hostname} offline for {days} days
Risk Score: {score} (Critical)

Remediation Steps:
1. Verify endpoint status with IT Operations
2. Check if device decommissioned in CMDB
3. If active but offline:
   - Check network connectivity
   - Verify sensor service status
   - Consider sensor reinstallation
4. If decommissioned:
   - Remove sensor: delete_sensor(sid="{sid}")
5. Tag for tracking:
   - add_tag(sid="{sid}", tag="stale-30d-review", ttl=604800)
```

### Playbook: New Asset Detected (Shadow IT)
```
Issue: New sensor {hostname} enrolled {hours}h ago
Risk Score: {score} (High)

Remediation Steps:
1. Cross-reference with IT deployment tickets
2. Verify hostname matches naming convention
3. Check installation key used
4. If legitimate:
   - Apply department tags: add_tag(sid, "{dept}")
5. If unauthorized:
   - Investigate device ownership
   - Consider isolation: isolate_network(sid)
```

### Playbook: Platform Degradation (Multi-Org)
```
Issue: {platform} showing {pct}% offline rate across {org_count} orgs

Remediation Steps:
1. Identify common factors:
   - OS version distribution
   - Network segments
   - Recent changes (patches, configs)
2. Check sample hosts:
   - Agent service status
   - Network connectivity to LC cloud
   - System logs for errors
3. Coordinate fix across affected orgs
4. Consider staggered remediation to track effectiveness
```

---

## Export Options

After generating report, offer export:

```
AskUserQuestion(
  questions=[{
    "question": "How would you like to export this report?",
    "header": "Export",
    "options": [
      {"label": "Markdown", "description": "Human-readable text format"},
      {"label": "JSON", "description": "Structured data for automation"}
    ],
    "multiSelect": false
  }]
)
```

---

## Integration with Other Skills

### sensor-health
**Use when**: Already exists for detailed telemetry queries (event-level analysis).

```
Skill(skill="lc-essentials:sensor-health")
```

### reporting
**Use when**: Billing, usage, and detection summaries across orgs.

```
Skill(skill="lc-essentials:reporting")
```

### investigation-creation
**Use when**: Investigating specific problematic sensors.

```
Skill(skill="lc-essentials:investigation-creation")
```

### detection-engineering
**Use when**: Creating D&R rules for Shadow IT detection.

```
Skill(skill="lc-essentials:detection-engineering")
```

---

## Troubleshooting

### No Sensors Found
- Verify OID is correct
- Check user has permissions for the organization

### Asset Profiling Fails
- Sensor may have gone offline since discovery
- Live commands require online sensors
- Check for permission errors

### Telemetry Health Check Slow
- LCQL queries can take time for large sensor counts
- Consider disabling telemetry health for >500 sensors
- Use sampling for very large fleets

### Pattern Detection Issues
- Ensure sufficient orgs for meaningful patterns
- Check if thresholds are too aggressive/relaxed
- Review org result quality (partial failures may skew patterns)

### Compliance Check Fails
- Verify `expected_assets` lookup exists
- Check lookup data format
- Wildcard patterns (WKS-*) require `naming_pattern: true`

### High False Positive Shadow IT
- Review installation key assignments
- Check expected enrollment patterns
- Adjust new asset threshold if needed

## Related Skills

- `sensor-tasking` - For sending commands to sensors identified with coverage issues
- `sensor-health` - For checking sensor connectivity and data availability
- `detection-engineering` - For creating D&R rules for Shadow IT detection
