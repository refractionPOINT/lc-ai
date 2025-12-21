
# List Investigations

List all investigations in a LimaCharlie organization.

## When to Use

Use this skill when the user needs to:
- See all investigations in the organization
- Find a specific investigation by browsing available investigations
- Get an overview of ongoing and completed investigations
- Audit investigation usage across the organization
- Find investigations by tags

Common scenarios:
- "Show me all investigations in this organization"
- "List all investigations"
- "What investigations do we have?"
- "Find investigations tagged with 'ransomware'"
- "Show me all active investigations"

## What This Skill Does

This skill retrieves all investigation records from LimaCharlie's Investigation Hive for the specified organization. It returns investigation names along with their metadata (status, tags, creation info).

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.

- **oid**: Organization ID (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="list_investigations",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

**Tool Details:**
- Tool name: `list_investigations`
- Parameters:
  - `oid`: Organization ID (required)

### Step 3: Handle the Response

The tool returns:
```json
{
  "investigations": {
    "incident-2024-001": {
      "data": {
        "name": "Ransomware Investigation",
        "status": "in_progress",
        "priority": "critical",
        ...
      },
      "enabled": true,
      "tags": ["ransomware", "critical"],
      "comment": "Active investigation",
      "metadata": {
        "created_at": 1700000000,
        "created_by": "user@example.com",
        "last_mod": 1700100000,
        "last_author": "analyst@example.com"
      }
    },
    "phishing-incident-2024": {
      ...
    }
  },
  "count": 2
}
```

**Success:**
- Returns all investigations with their data and metadata
- Count indicates total number of investigations
- Each investigation includes status, priority, tags, and audit info

**Common Errors:**
- **403 Forbidden**: Insufficient permissions
- **500 Server Error**: Service issue

### Step 4: Format the Response

Present the result to the user:
- Show total count of investigations
- List investigations with key info (name, status, priority)
- Group by status if helpful (in_progress, closed, etc.)
- Show tags for filtering

**Example output:**
```
Found 5 investigations in organization:

IN PROGRESS (2):
1. ransomware-server01-2024
   Priority: critical | Tags: ransomware, critical
   Last modified: 2024-01-21 by analyst@example.com

2. phishing-investigation-q1
   Priority: high | Tags: phishing, email
   Last modified: 2024-01-20 by security@example.com

CLOSED (3):
3. malware-desktop05-2024
   Status: closed_true_positive | Priority: medium
   Closed: 2024-01-15

4. false-positive-alert-123
   Status: closed_false_positive | Priority: low
   Closed: 2024-01-10

5. test-investigation
   Status: closed_true_positive | Priority: informational
   Closed: 2024-01-05
```

## Example Usage

### Example 1: List all investigations

User request: "Show me all investigations"

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="list_investigations",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

### Example 2: Find specific investigation

User request: "I'm looking for the ransomware investigation"

Steps:
1. List all investigations
2. Filter results for ransomware-related names or tags
3. Present matching investigations

## Additional Notes

- Returns all investigations regardless of status
- Filter results client-side by status, priority, or tags
- Investigation data in list is the same as stored (not expanded)
- Use `get_investigation` for a single investigation with full data
- Use `expand_investigation` to hydrate with full event/detection data
- Related skills: `get_investigation` to retrieve one, `set_investigation` to create/update, `delete_investigation` to remove

## Related Functions

- `get_investigation` - Get a specific investigation by name
- `set_investigation` - Create or update an investigation
- `delete_investigation` - Delete an investigation
- `expand_investigation` - Hydrate investigation with full event/detection data

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

- **Config Hive Documentation**: [Config Hive: Investigation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Platform_Management/Config_Hive/config-hive-investigation.md)
- **MCP Implementation**: `../lc-mcp-server/internal/tools/hive/investigations.go`
