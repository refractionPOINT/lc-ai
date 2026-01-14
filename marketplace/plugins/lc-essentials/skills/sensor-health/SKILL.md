---
name: sensor-health
description: Generate comprehensive sensor health and status reports across all LimaCharlie organizations. Use when users ask about sensor connectivity, data availability, offline sensors, sensors not reporting events, or fleet-wide health queries (e.g., "show me sensors online but not sending data", "list sensors offline for 7 days across all orgs").
allowed-tools:
  - Task
  - Read
  - Bash
---

# Sensor Health Reporting Skill

This skill orchestrates parallel sensor health checks across multiple LimaCharlie organizations for fast, comprehensive fleet reporting.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### API Access Pattern

All LimaCharlie API calls go through the `limacharlie-api-executor` sub-agent:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="sonnet",
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

## When to Use

Use this skill when the user asks about:
- **Connectivity Issues**: "Show me sensors online but not sending data"
- **Offline Sensors**: "List sensors that haven't been online for 7 days"
- **Data Availability**: "Which sensors have no events in the last hour?"
- **Fleet Health**: "Find all offline sensors across my organizations"
- **Cross-Org Reports**: "Show me sensor health across all my orgs"

## What This Skill Does

This skill orchestrates sensor health reporting by:
1. Getting the list of user's organizations
2. Spawning parallel `lc-essentials:sensor-health-reporter` agents (one per org)
3. Aggregating results from all agents
4. Presenting a unified report

**Key Advantage**: By running one agent per organization in parallel, this skill can check dozens of organizations simultaneously, dramatically reducing execution time.

## How to Use

### Step 1: Parse User Query

Identify the key parameters:
- **Time window**: Last hour, 7 days, 30 days, etc.
- **Status filter**: Online, offline, all sensors
- **Data availability**: Has events, no events, sparse events
- **Scope**: All orgs (default) or specific orgs

### Step 2: Get Organizations

Use the LimaCharlie API to get the user's organizations:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="sonnet",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW"
)
```

Handle large results with the analyze script if needed.

### Step 3: Spawn Parallel Agents

For each organization, spawn a `lc-essentials:sensor-health-reporter` agent in parallel:

```
Task(
  subagent_type="lc-essentials:sensor-health-reporter",
  model="haiku",
  prompt="Check sensors in organization '{org_name}' (OID: {oid}) that are online but have not sent telemetry in the last {timeframe}."
)
```

**CRITICAL**: Spawn ALL agents in a SINGLE message with multiple Task tool calls to run them in parallel:

```
<message with multiple Task blocks>
  Task 1: Check org 1
  Task 2: Check org 2
  Task 3: Check org 3
  ...
</message>
```

Do NOT spawn them sequentially - that defeats the purpose of parallelization.

### Step 4: Aggregate Results

Once all agents return:
1. Parse each agent's findings
2. Count total problematic sensors across all orgs
3. Group by organization
4. Identify patterns or anomalies

### Step 5: Generate Report

Present a unified report with:
- **Executive Summary**: Total sensors with issues across all orgs
- **Per-Org Breakdown**: Findings from each organization
- **Context**: What the findings mean
- **Recommendations**: Optional suggestions

## Example Workflow

**User Query**: "Show me sensors online but not reporting events in the last hour"

**Step 1**: Get current timestamp and calculate 1 hour ago
```bash
current=$(date +%s)
one_hour_ago=$(date -d '1 hour ago' +%s)
```

**Step 2**: Get org list
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="sonnet",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW"
)
```

**Step 3**: Spawn parallel agents (example with 3 orgs)
```
# Single message with 3 Task calls
Task(subagent_type="lc-essentials:sensor-health-reporter", model="haiku", prompt="Check org1...")
Task(subagent_type="lc-essentials:sensor-health-reporter", model="haiku", prompt="Check org2...")
Task(subagent_type="lc-essentials:sensor-health-reporter", model="haiku", prompt="Check org3...")
```

**Step 4**: Aggregate
```
Org1: 5 sensors with no data
Org2: 12 sensors with no data
Org3: 0 sensors with issues
Total: 17 sensors
```

**Step 5**: Present report
```markdown
## Sensors Online But Without Events (Last Hour)

**Total: 17 sensors across 2 organizations**

### org1 (5 sensors)
- sensor-id-1
- sensor-id-2
...

### org2 (12 sensors)
- sensor-id-6
...

### Analysis
These sensors are connected but not generating events...
```

## Handling Large Result Sets

When `list_user_orgs` returns a `resource_link`, use the analyze script from the plugin root. From this skill's base directory (shown at the top of the skill prompt), the script is at `../../scripts/analyze-lc-result.sh`:

```bash
# Path: {skill_base_directory}/../../scripts/analyze-lc-result.sh
bash "{skill_base_directory}/../../scripts/analyze-lc-result.sh" "<resource_link>"
jq -r '.orgs[] | "\(.oid)|\(.name)"' /tmp/lc-result-*.json
```

## Time Window Calculations

Use bash to calculate timestamps:

```bash
# Current time
date +%s

# X hours ago
date -d 'X hours ago' +%s

# X days ago
date -d 'X days ago' +%s

# X weeks ago
date -d 'X weeks ago' +%s
```

## Performance Tips

1. **Always spawn agents in parallel** - Use a single message with multiple Task calls
2. **Limit scope if needed** - For quick checks, allow user to specify specific orgs
3. **Use Haiku model** - Sensor health checks are straightforward data gathering
4. **Handle errors gracefully** - If one org fails, continue with others
5. **Cache org list** - If doing multiple related queries, reuse the org list

## Error Handling

If an agent fails:
- Log the error for that organization
- Continue processing other organizations
- Include error summary in final report
- Don't let one org failure block the entire report

## Report Format Template

```markdown
## {Query Title}

**Summary**: {Total count} sensors across {N} organizations

### {Org Name 1} ({count} sensors)
- {sensor-id-1}
- {sensor-id-2}
...

### {Org Name 2} ({count} sensors)
- {sensor-id-x}
...

### Organizations with No Issues
- {Org Name 3}
- {Org Name 4}

### Analysis
{Context about findings}

### Recommendations
{Optional suggestions}
```

## Important Constraints

- **Parallel Execution**: ALWAYS spawn agents in parallel (single message, multiple Tasks)
- **OID Format**: Organization ID is a UUID, not the org name
- **Time Limits**: Data availability checks must be <30 days
- **Model**: Always use "haiku" for the sub-agents
- **Error Tolerance**: Continue with partial results if some orgs fail

## Related Skills

- `sensor-tasking` - For sending commands to sensors (live response, data collection)
- `sensor-coverage` - For comprehensive asset inventory and coverage gap analysis

## Related Functions

From `limacharlie-call` skill:
- `list_user_orgs` - Get organizations
- `get_online_sensors` - Get online sensor list (used by agent)
- `get_time_when_sensor_has_data` - Check data timeline (used by agent)
- `list_sensors` - Get all sensors (used by agent for offline checks)
