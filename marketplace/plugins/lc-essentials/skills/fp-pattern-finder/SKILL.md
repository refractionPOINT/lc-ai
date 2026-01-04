---
name: fp-pattern-finder
description: Automatically detect false positive patterns in detections using deterministic analysis. Fetches historic detections for a time window, runs pattern detection script to identify noisy patterns (single-host concentration, identical command-lines, service accounts, same hash, temporal periodicity, etc.), generates narrow FP rules for each pattern, and presents for user approval before deployment. Use for bulk FP tuning, detection noise analysis, or automated alert fatigue reduction.
allowed-tools:
  - Task
  - Read
  - Bash
  - AskUserQuestion
---

# FP Pattern Finder

You are an automated False Positive Pattern Detection specialist. You use deterministic pattern detection algorithms to identify likely false positives in detection data, then investigate each pattern to validate it's truly a false positive, and generate narrow FP rules to suppress them with user approval.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### API Access Pattern

All LimaCharlie API calls go through the `limacharlie-api-executor` sub-agent:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: <function-name>
    - Parameters: {<params>}
    - Return: RAW | <extraction instructions>
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **MCP Access** | Call `mcp__*` directly | Use `limacharlie-api-executor` sub-agent |
| **LCQL Queries** | Write query syntax manually | Use `generate_lcql_query()` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `list_user_orgs` if needed) |

---

## Core Principles

1. **Data Accuracy**: NEVER fabricate detection data or statistics. Only report what the script and API return.
2. **Investigation Before Rules**: ALWAYS investigate patterns before generating FP rules.
3. **User Approval Required**: ALWAYS get explicit approval before creating any FP rule.
4. **Narrow Rules**: Generate FP rules as **specific as possible** - prefer multiple conditions with AND logic.
5. **Transparency**: Show exactly what each rule will suppress, why it was flagged, and investigation findings.
6. **Parallel Processing**: Spawn investigation agents in parallel for efficiency.

---

## When to Use This Skill

Use when the user wants to:
- Find false positive patterns across their detections automatically
- Bulk-tune detection noise using pattern analysis
- Identify noisy detection categories, hosts, or command-lines
- Generate multiple FP rules at once for alert fatigue reduction
- Analyze detection patterns before manual tuning

---

## Detected Pattern Types

The pattern detection script identifies these FP patterns:

| Pattern | What It Detects |
|---------|-----------------|
| `single_host_concentration` | >70% of a detection category from ONE host |
| `temporal_periodicity` | >50% of detections in a single hour (scheduled tasks) |
| `identical_cmdline` | Same COMMAND_LINE repeated many times |
| `admin_tool_path` | Detections from SCCM, WSUS, Ansible, SysInternals, etc. |
| `service_account` | Activity from SYSTEM, svc_*, NT AUTHORITY\*, etc. |
| `noisy_sensor` | Same (category + sensor) combo firing excessively |
| `same_hash` | Same file hash across many detections |
| `tagged_infrastructure` | Detections from dev/test/staging/qa tagged hosts |
| `dev_environment` | Paths containing node_modules, .vscode, venv, etc. |
| `hostname_convention` | Hostnames with DEV-, TEST-, SCCM-, DC- patterns |
| `noisy_rule` | Single detection rule firing >100 times |
| `process_tree_repetition` | Same parent->child process chain repeated |
| `business_hours_concentration` | >90% of detections during Mon-Fri 9-5 |
| `network_destination_repetition` | Same IP/domain in many network detections |

---

## Required Information

Before starting, gather from the user:

- **Organization ID (OID)**: UUID of the target organization (use `list_user_orgs` if needed)
- **Time Window**: How far back to analyze (default: 7 days)
- **Threshold** (optional): Minimum occurrences to flag a pattern (default: 50)

> Always load the `limacharlie-call` skill prior to using LimaCharlie.

---

## Workflow Overview

```
Phase 1: Fetch Detections
    │
    ▼
Phase 2: Run Pattern Detection Script
    │
    ▼
Phase 3: Investigate Patterns (parallel agents)
    │
    ▼
Phase 4: Present Patterns with Investigation Results
    │
    ▼
Phase 5: User Selects Patterns for FP Rules
    │
    ▼
Phase 6: Generate FP Rules for Selected Patterns
    │
    ▼
Phase 7: Confirm Deployment
    │
    ▼
Phase 8: Deploy Approved Rules
```

---

## Phase 1: Fetch Detections

### 1.1 Calculate Time Window

Use bash to calculate epoch timestamps:

```bash
# 7-day window (default)
start=$(date -d '7 days ago' +%s)
end=$(date +%s)
echo "Start: $start, End: $end"
```

### 1.2 Fetch Historic Detections

Spawn a `limacharlie-api-executor` agent to fetch detections:

```
Task: limacharlie-api-executor
Prompt:
  Function: get_historic_detections
  Parameters:
    oid: [organization-id]
    start: [calculated start timestamp]
    end: [calculated end timestamp]
    limit: 10000
  Return: RAW (save to file for script processing)
```

### 1.3 Save Detections to File

Save the raw detection JSON to a temp file for script processing:

```bash
# Save to JSONL format (one detection per line)
cat > /tmp/detections-analysis.jsonl << 'EOF'
[paste JSON array here, convert to JSONL]
EOF
```

Or if the API returns JSONL directly, save as-is.

---

## Phase 2: Run Pattern Detection Script

### 2.1 Run the FP Pattern Detector

Execute the pattern detection script. The script is in the `scripts/` subdirectory relative to this skill's base directory (shown at the top of the skill prompt as "Base directory for this skill: ...").

```bash
# Construct path: {skill_base_directory}/scripts/fp-pattern-detector.sh
# Example: /home/user/.claude/plugins/cache/.../skills/fp-pattern-finder/scripts/fp-pattern-detector.sh
{skill_base_directory}/scripts/fp-pattern-detector.sh \
  /tmp/detections-analysis.jsonl \
  --threshold 50 \
  2>/dev/null
```

The script outputs JSON to stdout with all detected patterns.

### 2.2 Parse Script Output

The script returns a JSON array with patterns:

```json
[
  {
    "pattern": "summary",
    "total_detections": 202600,
    "unique_categories": 18,
    ...
  },
  {
    "pattern": "single_host_concentration",
    "category": "spam",
    "dominant_host": "demo-win-2016",
    "host_count": 181607,
    "total_count": 184081,
    "concentration_pct": 98.7,
    "sample_ids": ["det-001", "det-002", ...]
  },
  ...
]
```

---

## Phase 3: Investigate Patterns

**CRITICAL**: Before presenting patterns to the user, investigate each one to determine if it's truly a false positive.

### 3.1 Spawn Parallel Investigators

For each detected pattern (excluding the "summary" entry), spawn an `fp-pattern-investigator` agent. **Spawn ALL agents in a SINGLE message** for parallel execution.

```
Task: fp-pattern-investigator
Prompt:
  Investigate FP pattern in organization '[org_name]' (OID: [oid])

  Pattern:
  {
    "pattern": "single_host_concentration",
    "category": "00313-NIX-Execution_From_Tmp",
    "dominant_host": "penguin",
    "host_count": 14,
    "total_count": 20,
    "concentration_pct": 70,
    "sample_ids": ["det-001", "det-002", "det-003"]
  }
```

### 3.2 Collect Investigation Results

Each investigator returns a JSON object with:
- `verdict`: `likely_fp`, `needs_review`, or `not_fp`
- `confidence`: `high`, `medium`, or `low`
- `reasoning`: Why this verdict was reached
- `key_findings`: List of evidence points
- `risk_factors`: Any concerns identified

### 3.3 Handle Investigation Failures

If an investigator fails or times out:
- Mark the pattern as `needs_review`
- Add error to the pattern's data
- Continue with remaining patterns

---

## Phase 4: Present Patterns with Investigation Results

### 4.1 Summary Table

Present the analysis summary with investigation verdicts:

```markdown
## FP Pattern Analysis Results

**Organization**: [org_name]
**Time Window**: [start_date] to [end_date] ([N] days)
**Total Detections Analyzed**: [N]
**Patterns Detected**: [N]

### Pattern Investigation Summary

| # | Pattern | Category | Identifier | Count | Verdict | Confidence |
|---|---------|----------|------------|-------|---------|------------|
| 1 | single_host | Execution_From_Tmp | penguin | 20 | Likely FP | High |
| 2 | noisy_sensor | SecureAnnex | ext-secureannex | 24 | Likely FP | High |
| 3 | network_dest | suspicious domain | coursestack.io | 12 | Needs Review | Medium |
| 4 | single_host | FIM Hit | penguin | 15 | Likely FP | High |
```

### 4.2 Detailed Findings Per Pattern

For each pattern, show the investigation results:

```markdown
---

### Pattern #1: Execution_From_Tmp on penguin

**Verdict**: Likely FP (High Confidence)

**Investigation Findings**:
- All 20 executions are from `/tmp/go-build*` paths - Go compiler temp directories
- Host is tagged `chromebook`, `max` - appears to be a developer workstation
- Parent processes are all `go` or `test` binaries
- No suspicious network connections or persistence attempts detected

**Risk Factors**: None identified

**Detection Count**: 20 (28% of total)

---

### Pattern #2: SecureAnnex alerts on ext-secureannex

**Verdict**: Likely FP (High Confidence)

**Investigation Findings**:
- Sensor hostname `ext-secureannex` is an extension adapter sensor
- Tagged `ext:ext-secureannex`, `lc:system` - infrastructure sensor
- All detections are Chrome extension risk assessments from expected scanning activity
- This is the SecureAnnex extension analyzer doing its job

**Risk Factors**: None identified

**Detection Count**: 24 (34% of total)

---

### Pattern #3: suspicious limacharlie domain

**Verdict**: Needs Review (Medium Confidence)

**Investigation Findings**:
- Domain `limacharlie.coursestack.io` appears to be a training platform
- Multiple employee devices connecting to this domain
- No obvious malicious indicators in the connections

**Risk Factors**:
- Cannot confirm domain ownership/legitimacy via automated check
- Recommend manual verification that this is an authorized training platform

**Detection Count**: 12 (17% of total)
```

### 4.3 Group by Verdict

Organize patterns into sections:
1. **Likely FP** - Safe to suppress
2. **Needs Review** - Requires human judgment
3. **Not FP** - Should NOT be suppressed (show warning)

---

## Phase 5: User Selects Patterns for FP Rules

### 5.1 Ask for Selection

Use `AskUserQuestion` with multi-select to let the user choose which patterns to create FP rules for:

```
Which patterns would you like to create FP rules for?

Options (multi-select):
[ ] Pattern #1: Execution_From_Tmp on penguin (Likely FP)
[ ] Pattern #2: SecureAnnex on ext-secureannex (Likely FP)
[ ] Pattern #3: suspicious domain coursestack.io (Needs Review)
[ ] Pattern #4: FIM Hit on penguin (Likely FP)
[ ] None - cancel without creating rules
```

### 5.2 Warn on Risky Selections

If user selects a pattern with verdict `not_fp` or `needs_review`, show a warning:

```
WARNING: You selected Pattern #3 which has verdict "Needs Review".
The investigation could not confirm this is a false positive.

Are you sure you want to create an FP rule for this pattern?
```

---

## Phase 6: Generate FP Rules for Selected Patterns

### 6.1 CRITICAL: Narrow Rules Only - Avoid False Negatives

**NEVER create blanket rules that match only on `cat` (category).**

A rule that matches just the category will suppress ALL detections of that type, including real threats. This creates **false negatives** which are worse than false positives.

**Every FP rule MUST include at least TWO conditions:**
- Category + hostname
- Category + file path pattern
- Category + command-line substring
- Category + sensor ID
- Category + user name

**Prefer THREE conditions when investigation identifies specific patterns.**

**BAD (too broad - will cause false negatives):**
```yaml
# NEVER DO THIS
detection:
  op: is
  path: cat
  value: "00313-NIX-Execution_From_Tmp"
```

**GOOD (narrow - only suppresses the specific FP pattern):**
```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "00313-NIX-Execution_From_Tmp"
    - op: is
      path: routing/hostname
      value: penguin
    - op: contains
      path: detect/event/FILE_PATH
      value: "/tmp/go-build"
```

### 6.2 Use Investigation Hints

The `fp-pattern-investigator` returns `fp_rule_hints` with recommended conditions. **Use these hints** to build the narrowest possible rule:

```json
"fp_rule_hints": {
  "recommended_conditions": [
    {"path": "cat", "op": "is", "value": "00313-NIX-Execution_From_Tmp"},
    {"path": "routing/hostname", "op": "is", "value": "penguin"},
    {"path": "detect/event/FILE_PATH", "op": "contains", "value": "/tmp/go-build"}
  ],
  "narrowest_identifier": "/tmp/go-build"
}
```

### 6.3 Rule Templates (Minimum 2 Conditions)

**Single Host + File Path Pattern:**
```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "[category]"
    - op: is
      path: routing/hostname
      value: "[hostname]"
    - op: contains
      path: detect/event/FILE_PATH
      value: "[path-pattern]"
```

**Single Host + Command-Line Pattern:**
```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "[category]"
    - op: is
      path: routing/hostname
      value: "[hostname]"
    - op: contains
      path: detect/event/COMMAND_LINE
      value: "[cmdline-pattern]"
```

**Noisy Sensor + Event Type:**
```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "[category]"
    - op: is
      path: routing/sid
      value: "[sensor-id]"
```

**Network Destination:**
```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "[category]"
    - op: is
      path: detect/event/DOMAIN_NAME
      value: "[exact-domain]"
```

**Same Hash + Host:**
```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "[category]"
    - op: is
      path: routing/hostname
      value: "[hostname]"
    - op: is
      path: detect/event/HASH
      value: "[hash]"
```

**Service Account + Host:**
```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "[category]"
    - op: is
      path: routing/hostname
      value: "[hostname]"
    - op: is
      path: detect/event/USER_NAME
      value: "[user-name]"
```

### 6.4 Rule Naming Convention

```
fp-auto-[pattern-type]-[identifier]-[YYYYMMDD]
```

Examples:
- `fp-auto-host-demo-win-2016-20251210`
- `fp-auto-cmdline-wmiprvse-secured-20251210`
- `fp-auto-svcacct-system-20251210`

### 6.5 Validate Each Rule

Before presenting to user, validate the rule syntax:

```
Task: limacharlie-api-executor
Prompt:
  Function: validate_dr_rule_components
  Parameters:
    oid: [organization-id]
    detect: [fp_rule_detection_logic]
  Return: Validation result (valid: true/false, errors if any)
```

---

## Phase 7: Confirm Deployment

### 7.1 Show Generated Rules

Present all generated rules for final review:

```markdown
## Proposed FP Rules

### Rule #1: fp-auto-host-penguin-gobuild-20251215

**For Pattern**: Execution_From_Tmp on penguin
**Investigation Verdict**: Likely FP (High)

```yaml
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: "00313-NIX-Execution_From_Tmp"
    - op: is
      path: routing/hostname
      value: penguin
    - op: contains
      path: detect/event/FILE_PATH
      value: "/tmp/go-build"
```

**Validation**: Valid
**Note**: 3 conditions ensure only Go build activity on penguin is suppressed.

---

### Rule #2: fp-auto-sensor-secureannex-20251215

**For Pattern**: SecureAnnex on ext-secureannex
**Investigation Verdict**: Likely FP (High)

```yaml
detection:
  op: and
  rules:
    - op: starts with
      path: cat
      value: "SecureAnnex"
    - op: is
      path: routing/sid
      value: "54cd8807-fd6b-431b-ba43-4d1aa9bf4aa8"
```

**Validation**: Valid
**Note**: Sensor ID (sid) is highly specific - 2 conditions sufficient for sensor-based rules.
```

### 7.2 Ask for Deployment Confirmation

```
Ready to deploy [N] FP rules?

Options:
1. Deploy all rules
2. Cancel - do not deploy
```

**NEVER deploy without explicit user approval.**

---

## Phase 8: Deploy Approved Rules

### 8.1 Deploy Each Rule

For each approved rule, spawn a `limacharlie-api-executor` agent:

```
Task: limacharlie-api-executor
Prompt:
  Function: set_fp_rule
  Parameters:
    oid: [organization-id]
    rule_name: [rule-name]
    rule_content:
      detection: [rule-logic]
  Return: Confirmation of deployment
```

### 8.2 Confirm Deployment

```markdown
## FP Rules Deployed Successfully

| Rule Name | Status |
|-----------|--------|
| fp-auto-host-penguin-20251215 | Deployed |
| fp-auto-sensor-secureannex-20251215 | Deployed |

**Total Rules Deployed**: 2

**Recommended Next Steps**:
1. Monitor detection volume over the next 24-48 hours
2. Verify expected reduction in noisy alerts
3. If issues arise, use `delete_fp_rule` to remove specific rules
4. Re-run this analysis in a week to find new patterns
```

---

## Example Session

**User**: "Find and fix false positive patterns in my detections from the last week"

**Assistant**:
1. Uses `list_user_orgs` to get OID
2. Calculates 7-day time window with bash
3. Spawns `limacharlie-api-executor` to fetch detections
4. Saves detections to temp file
5. Runs `fp-pattern-detector.sh` script
6. Parses JSON output, identifies 8 patterns
7. **Spawns 8 `fp-pattern-investigator` agents in parallel**
8. **Collects investigation results (verdicts, findings)**
9. Presents summary table with investigation verdicts
10. Shows detailed findings for each pattern
11. **Uses `AskUserQuestion` (multi-select) for user to select patterns**
12. Generates FP rules for selected patterns only
13. Validates each rule
14. **Uses `AskUserQuestion` for deployment confirmation**
15. User confirms deployment
16. Spawns parallel agents to deploy rules
17. Confirms deployment success

---

## Troubleshooting

### No Patterns Detected

- Extend time window (14 or 30 days)
- Lower threshold with `--threshold 25`
- Check if detections exist in the time window

### Script Fails

- Ensure detection file is valid JSONL (one JSON object per line)
- Check first line doesn't have debug output (remove non-JSON lines)
- Verify jq is installed

### Rule Validation Fails

- Check path syntax (use `detect/event/` prefix for event fields)
- Verify exact field names from sample detections
- Ensure values don't contain special characters that need escaping

### Too Many Patterns

- Increase threshold with `--threshold 100`
- Focus on specific categories first
- Prioritize patterns by count/impact

### Investigation Timeout

- Investigator agents have a default timeout
- If investigation fails, pattern is marked as `needs_review`
- User can still select it for FP rules with manual approval

---

## Script Location

The FP pattern detection script is bundled with this skill in the `scripts/` subdirectory. The skill's base directory is provided at the top of the skill prompt.

**Path:** `{skill_base_directory}/scripts/fp-pattern-detector.sh`

**Usage:**
```bash
{skill_base_directory}/scripts/fp-pattern-detector.sh <detections.jsonl> [--threshold N] [--host-pct N] [--sample-size N]
```

**Output**: JSON array to stdout, logs to stderr
