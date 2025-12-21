
# Get Investigation

Retrieve a specific investigation from LimaCharlie's Investigation Hive by name.

## When to Use

Use this skill when the user needs to:
- Retrieve a saved investigation
- Review investigation data before updating
- Check the current state of an investigation
- Export investigation data for reporting
- Merge new findings with existing investigation data

Common scenarios:
- "Get the investigation for incident-2024-001"
- "Show me the ransomware investigation"
- "Retrieve the current state of this investigation"
- "What's in the investigation named 'phishing-attack'?"

## What This Skill Does

This skill retrieves an investigation record from LimaCharlie's Investigation Hive by its name. It returns the complete investigation data including events, detections, entities, notes, and metadata.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.

- **oid**: Organization ID (required)
- **investigation_name**: Name of the investigation to retrieve (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Exact investigation name

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "incident-2024-001"
  }
)
```

**Tool Details:**
- Tool name: `get_investigation`
- Parameters:
  - `oid`: Organization ID (required)
  - `investigation_name`: Name of the investigation to retrieve (required)

### Step 3: Handle the Response

The tool returns:
```json
{
  "investigation": {
    "name": "incident-2024-001",
    "data": {
      "name": "Ransomware Investigation",
      "description": "...",
      "status": "in_progress",
      "priority": "critical",
      "events": [...],
      "detections": [...],
      "entities": [...],
      "notes": [...],
      "summary": "..."
    },
    "enabled": true,
    "tags": ["ransomware", "critical"],
    "comment": "Active investigation",
    "metadata": {
      "created_at": 1700000000,
      "created_by": "user@example.com",
      "last_mod": 1700100000,
      "last_author": "analyst@example.com",
      "guid": "abc-123-def"
    }
  }
}
```

**Success:**
- Returns complete investigation with data and metadata
- Includes creation and modification timestamps
- Shows who created and last modified the investigation

**Common Errors:**
- **404 Not Found**: Investigation with the specified name does not exist
- **403 Forbidden**: Insufficient permissions
- **400 Bad Request**: Invalid parameters

### Step 4: Format the Response

Present the result to the user:
- Display investigation name and status
- Show summary if available
- List event, detection, and entity counts
- Show investigation notes
- Display metadata (created/modified timestamps)

**Example output:**
```
Investigation: incident-2024-001
Status: in_progress | Priority: critical

Summary: Ransomware attack detected on DESKTOP-001. Initial access via phishing.

Contents:
- Events: 5
- Detections: 3
- Entities: 4
- Notes: 7

Created: 2024-01-20 by user@example.com
Last Modified: 2024-01-21 by analyst@example.com
```

## Example Usage

### Example 1: Retrieve investigation

User request: "Get the investigation for the ransomware incident"

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "ransomware-investigation-2024"
  }
)
```

### Example 2: Get investigation before updating

User request: "I need to add new findings to the existing investigation"

Steps:
1. Get the existing investigation
2. Merge new data with existing
3. Use `set_investigation` to save combined data

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_investigation",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "investigation_name": "existing-incident"
  }
)
```

Then merge the returned data with new findings and call `set_investigation`.

## Additional Notes

- Investigation names are case-sensitive
- Use `list_investigations` first if you don't know the exact name
- The returned data contains references (atoms, detection IDs), not full event data
- Use `expand_investigation` to get full event and detection data hydrated
- Metadata shows audit trail (who created/modified and when)
- Related skills: `list_investigations` to find investigations, `set_investigation` to update, `expand_investigation` to hydrate

## Related Functions

- `list_investigations` - List all investigations in the organization
- `set_investigation` - Create or update an investigation
- `delete_investigation` - Delete an investigation
- `expand_investigation` - Hydrate investigation with full event/detection data

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

- **Config Hive Documentation**: [Config Hive: Investigation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Platform_Management/Config_Hive/config-hive-investigation.md)
- **MCP Implementation**: `../lc-mcp-server/internal/tools/hive/investigations.go`
