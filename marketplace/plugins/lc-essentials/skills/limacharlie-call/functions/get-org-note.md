
# Get Org Note

Retrieves a specific organization note by name from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Get the full content of a specific organization note
- View note details before modifying
- Check if a specific note exists
- Inspect note metadata (creation date, last author, etc.)
- Read organizational documentation

Common scenarios:
- "Show me the incident-contacts note"
- "What's in the escalation-policy note?"
- "Get the note named 'runbook-malware'"
- "Read the organizational procedures note"

## What This Skill Does

This skill retrieves a single organization note record from the LimaCharlie Hive system by its name. It calls the Hive API using the "org_notes" hive name with the organization ID as the partition and the specific note name as the key. The response includes the complete note content (text and description), user metadata (enabled, tags, comments), and system metadata (audit trail).

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **note_name**: The name of the organization note to retrieve (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Note name (string, must be exact match)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_org_note",
  parameters={
    "oid": "[organization-id]",
    "note_name": "[note-name]"
  }
)
```

**API Details:**
- Tool: `get_org_note`
- Required parameters:
  - `oid`: Organization ID
  - `note_name`: Name of the organization note to retrieve

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "org_note": {
    "name": "incident-contacts",
    "data": {
      "text": "Primary: security@example.com\nSecondary: ops@example.com",
      "description": "Emergency contact information for incident response"
    },
    "enabled": true,
    "tags": ["contacts", "incident-response"],
    "comment": "Keep updated quarterly",
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
- The `org_note` object contains the complete note record
- The `data` field contains `text` (required) and `description` (optional)
- The `metadata` field shows system metadata including audit trail
- Present the note details to the user in a readable format

**Common Errors:**
- **400 Bad Request**: Invalid note name format
- **403 Forbidden**: Insufficient permissions - user needs org_notes.get permission
- **404 Not Found**: The note doesn't exist - inform user and suggest creating it
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show the note name prominently
- Display the text content
- Show description if present
- Include relevant metadata like creation date and last modification
- Note any tags or comments

## Example Usage

### Example 1: Get a specific organization note

User request: "Show me the incident-contacts note"

Steps:
1. Get the organization ID from context
2. Use note name "incident-contacts"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_org_note",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "note_name": "incident-contacts"
  }
)
```

Expected response contains the note with contact information.

Format the output explaining:
- Note: incident-contacts
- Description: Emergency contact information for incident response
- Content:
  - Primary: security@example.com
  - Secondary: ops@example.com
- Last Modified: [date] by security@example.com

### Example 2: Check if note exists

User request: "Does the runbook-malware note exist?"

Steps:
1. Attempt to get the note
2. If 404 error: inform user the note doesn't exist
3. If 200 success: confirm it exists and show summary

## Additional Notes

- Note names are case-sensitive - use exact name from list-org-notes
- The `data` field structure includes:
  - `text`: The main content of the note (required, cannot be empty)
  - `description`: Optional description explaining the note's purpose
- The `enabled` field can be used to mark notes as active/inactive
- Use `list_org_notes` first if you don't know the exact note name
- Notes can contain any text content up to 1MB
- Common uses include storing:
  - Contact information
  - Escalation procedures
  - Runbooks and playbooks
  - Configuration notes
  - Organizational policies

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Get method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/org_notes.go`
