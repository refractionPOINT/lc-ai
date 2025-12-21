
# Get SOP

Retrieves a specific Standard Operating Procedure by name from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Get the full content of a specific SOP
- View procedure details before executing or modifying
- Check if a specific SOP exists
- Inspect SOP metadata (creation date, last author, etc.)
- Read a security procedure or runbook

Common scenarios:
- "Show me the malware-response SOP"
- "What's in the phishing-response procedure?"
- "Get the SOP named 'incident-escalation'"
- "Read the threat hunting procedure"

## What This Skill Does

This skill retrieves a single Standard Operating Procedure record from the LimaCharlie Hive system by its name. It calls the Hive API using the "sop" hive name with the organization ID as the partition and the specific SOP name as the key. The response includes the complete procedure content (text and description), user metadata (enabled, tags, comments), and system metadata (audit trail).

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **sop_name**: The name of the SOP to retrieve (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. SOP name (string, must be exact match)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_sop",
  parameters={
    "oid": "[organization-id]",
    "sop_name": "[sop-name]"
  }
)
```

**API Details:**
- Tool: `get_sop`
- Required parameters:
  - `oid`: Organization ID
  - `sop_name`: Name of the SOP to retrieve

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "sop": {
    "name": "malware-response",
    "data": {
      "text": "## Malware Response Procedure\n\n1. **Isolation**\n   - Immediately isolate the affected system from the network\n   - Document the isolation time\n\n2. **Evidence Collection**\n   - Capture memory dump\n   - Collect running processes\n   - Export relevant logs\n\n3. **Analysis**\n   - Submit sample to sandbox\n   - Review YARA matches\n   - Check IOC databases\n\n4. **Remediation**\n   - Remove malware artifacts\n   - Restore from backup if needed\n   - Verify system integrity",
      "description": "Standard procedure for malware incident response"
    },
    "enabled": true,
    "tags": ["incident-response", "malware", "tier-1"],
    "comment": "Approved by Security Team - v2.1",
    "metadata": {
      "created_at": 1234567890,
      "created_by": "admin@example.com",
      "last_mod": 1234567899,
      "last_author": "security@example.com",
      "guid": "unique-id-123"
    }
  }
}
```

**Success:**
- The `sop` object contains the complete SOP record
- The `data` field contains `text` (required) and `description` (optional)
- The `metadata` field shows system metadata including audit trail
- Present the SOP details to the user in a readable format

**Common Errors:**
- **400 Bad Request**: Invalid SOP name format
- **403 Forbidden**: Insufficient permissions - user needs sop.get permission
- **404 Not Found**: The SOP doesn't exist - inform user and suggest creating it
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show the SOP name prominently
- Display the procedure text content (may include markdown formatting)
- Show description if present
- Include relevant metadata like creation date and last modification
- Note any tags that categorize the SOP

## Example Usage

### Example 1: Get a specific SOP

User request: "Show me the malware-response SOP"

Steps:
1. Get the organization ID from context
2. Use SOP name "malware-response"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_sop",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sop_name": "malware-response"
  }
)
```

Expected response contains the SOP with the full procedure.

Format the output showing the procedure steps clearly.

### Example 2: Check if SOP exists

User request: "Does the incident-escalation SOP exist?"

Steps:
1. Attempt to get the SOP
2. If 404 error: inform user the SOP doesn't exist
3. If 200 success: confirm it exists and show summary

## Additional Notes

- SOP names are case-sensitive - use exact name from list-sops
- The `data` field structure includes:
  - `text`: The main procedural content (required, cannot be empty)
  - `description`: Optional description explaining the SOP's purpose
- The `enabled` field can be used to mark SOPs as active/inactive
- Use `list_sops` first if you don't know the exact SOP name
- SOPs can contain any text content up to 1MB
- SOP text often includes markdown formatting for better readability
- Common SOP structures include:
  - Numbered steps
  - Checklists
  - Decision trees
  - Role responsibilities

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Get method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/sop.go`
