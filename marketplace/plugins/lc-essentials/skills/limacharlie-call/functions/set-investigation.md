
# Set Investigation

Create or update an investigation in LimaCharlie's Investigation Hive. Investigations are records used during cybersecurity incident response to organize events, detections, and entities of interest.

## When to Use

Use this skill when the user needs to:
- Create a new investigation
- Save findings from an incident investigation
- Document events, detections, and IOCs in a structured format
- Update an existing investigation with new findings
- Record investigation notes and action items
- Build a forensic investigation for incident response

Common scenarios:
- "Create an investigation for this ransomware incident"
- "Save these findings to an investigation called 'phishing-incident-2024'"
- "Update the investigation with these new IOCs"
- "Document this investigation"
- "Add these events to the incident investigation"

## What This Skill Does

This skill creates or updates an investigation record in LimaCharlie's Investigation Hive. Investigations store references to events (by atom), detections (by ID), entities (IOCs), and investigation notes. If an investigation with the same name exists, it will be replaced with the new data.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.

- **oid**: Organization ID (required)
- **investigation_name**: Name for the investigation (alphanumeric, hyphens, underscores, max 256 chars)
- **investigation_data**: Investigation data object (see structure below)

## Investigation Data Structure

For the complete schema reference, see [Config Hive: Investigation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Platform_Management/Config_Hive/config-hive-investigation.md).

### Root Fields

| Field | Type | Required | Max Length | Description |
|-------|------|----------|-----------|-------------|
| `name` | string | Yes | 256 | Human-readable investigation name |
| `description` | string | No | 4096 | Detailed description of the investigation |
| `status` | string | No | - | Investigation status (see enum below) |
| `priority` | string | No | - | Priority level (see enum below) |
| `events` | array | No | - | Event references with annotations |
| `detections` | array | No | - | Detection references with annotations |
| `entities` | array | No | - | Entities of interest (IOCs) |
| `notes` | array | No | - | Investigation notes and findings |
| `summary` | string | No | 16384 | Executive summary |
| `conclusion` | string | No | 16384 | Final investigation conclusion |

### Event Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `atom` | string | Yes | LimaCharlie event atom identifier |
| `sid` | string | Yes | Sensor ID the event originated from |
| `tags` | array | No | Tags for categorizing the event |
| `relevance` | string | No | Why this event matters (max 1024) |
| `verdict` | string | No | Analyst verdict (unknown, benign, suspicious, malicious) |

### Detection Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detection_id` | string | Yes | Detection identifier |
| `tags` | array | No | Tags for categorizing the detection |

### Entity Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Entity type (ip, domain, hash, user, host, email, file_path, process, url, other) |
| `value` | string | Yes | Entity value (max 2048) |
| `name` | string | No | Human-readable name (max 256) |
| `first_seen` | int64 | No | First observation timestamp (Unix epoch ms) |
| `last_seen` | int64 | No | Last observation timestamp (Unix epoch ms) |
| `context` | string | No | Why this entity is of interest (max 2048) |
| `verdict` | string | No | Analyst verdict |

### Note Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | No | Note type (observation, hypothesis, finding, conclusion, action_item, question) |
| `content` | string | Yes | Note content (max 16384) |
| `timestamp` | int64 | No | Creation timestamp (Unix epoch ms) |
| `resolved` | boolean | No | For action_items/questions: whether resolved |

### Enum Values

- **Status**: `new`, `in_progress`, `pending_review`, `escalated`, `closed_false_positive`, `closed_true_positive`
- **Priority**: `critical`, `high`, `medium`, `low`, `informational`
- **Verdict**: `unknown`, `benign`, `suspicious`, `malicious`

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Descriptive investigation name
3. Valid investigation data structure

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="set_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "incident-2024-001",
    "investigation_data": {
      "name": "Ransomware Investigation 2024-001",
      "description": "Investigating ransomware activity on DESKTOP-001",
      "status": "in_progress",
      "priority": "critical",
      "events": [...],
      "detections": [...],
      "entities": [...],
      "notes": [...],
      "summary": "..."
    }
  }
)
```

**Tool Details:**
- Tool name: `set_investigation`
- Parameters:
  - `oid`: Organization ID (required)
  - `investigation_name`: Name for the investigation (required)
  - `investigation_data`: Investigation data object (required)

### Step 3: Handle the Response

The tool returns:
```json
{
  "success": true,
  "message": "Successfully created/updated investigation 'incident-2024-001'"
}
```

**Success:**
- Investigation is created/updated and immediately available
- Can be retrieved with `get_investigation` or `expand_investigation`
- If updating, old data is completely replaced

**Common Errors:**
- **400 Bad Request**: Invalid parameters or malformed data
- **403 Forbidden**: Insufficient permissions
- **500 Server Error**: Service issue, retry

### Step 4: Format the Response

Present the result to the user:
- Confirm investigation creation/update
- Summarize what was saved (event count, detection count, entity count)
- Provide next steps (expand, review, share)

## Example Usage

### Example 1: Create incident investigation

User request: "Create an investigation for this incident"

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="set_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "cobalt-strike-incident-2024",
    "investigation_data": {
      "name": "Cobalt Strike C2 Incident",
      "description": "Active Cobalt Strike beacon detected communicating with C2 server",
      "status": "in_progress",
      "priority": "critical",
      "events": [
        {
          "atom": "abc123def456",
          "sid": "sensor-001-uuid",
          "tags": ["phase:execution", "mitre:T1218.011"],
          "relevance": "Rundll32 beacon process with C2 communication",
          "verdict": "malicious"
        }
      ],
      "detections": [
        {
          "detection_id": "det-789",
          "tags": ["cobalt-strike", "high-severity"]
        }
      ],
      "entities": [
        {
          "type": "ip",
          "value": "203.0.113.50",
          "name": "C2 Server",
          "context": "Command and control infrastructure",
          "verdict": "malicious"
        }
      ],
      "notes": [
        {
          "type": "finding",
          "content": "Active C2 communication confirmed to 203.0.113.50:80",
          "timestamp": 1700000000000
        },
        {
          "type": "action_item",
          "content": "Isolate affected host immediately",
          "resolved": false
        }
      ],
      "summary": "Cobalt Strike beacon detected on DESKTOP-001 with active C2 to 203.0.113.50"
    }
  }
)
```

Expected response:
```json
{
  "success": true,
  "message": "Successfully created/updated investigation 'cobalt-strike-incident-2024'"
}
```

### Example 2: Update existing investigation

User request: "Add these new findings to the incident investigation"

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="set_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "existing-incident",
    "investigation_data": {
      "name": "Updated Investigation",
      "status": "pending_review",
      "priority": "high",
      "events": [...previous events plus new ones...],
      "entities": [...previous entities plus new ones...],
      "notes": [
        ...previous notes...,
        {
          "type": "conclusion",
          "content": "Investigation complete. Threat contained.",
          "timestamp": 1700100000000
        }
      ],
      "conclusion": "Attack contained. No data exfiltration observed."
    }
  }
)
```

**Note**: Setting an investigation completely replaces the existing data. To add to an existing investigation, first retrieve it with `get_investigation`, merge with new data, then set the combined result.

## Additional Notes

- Setting an investigation completely replaces any existing data with that name
- To add entries without replacing: get existing with `get_investigation` -> merge -> set combined
- Maximum record size is 5MB
- Investigation names should be descriptive (e.g., `ransomware-server01-2024-01-20`)
- Use tags on events and detections for categorization (MITRE ATT&CK, attack phase, etc.)
- Notes support different types for structured documentation
- Use `expand_investigation` to hydrate a saved investigation with full event/detection data
- Related skills: `list_investigations` to see all, `get_investigation` to retrieve, `delete_investigation` to remove, `expand_investigation` to hydrate

## Related Functions

- `list_investigations` - List all investigations in the organization
- `get_investigation` - Get a specific investigation by name
- `delete_investigation` - Delete an investigation
- `expand_investigation` - Hydrate investigation with full event/detection data

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

- **Config Hive Documentation**: [Config Hive: Investigation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Platform_Management/Config_Hive/config-hive-investigation.md)
- **Investigation Guide**: [Best Practices](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Getting_Started/Use_Cases/investigation-guide.md)
- **MCP Implementation**: `../lc-mcp-server/internal/tools/hive/investigations.go`
