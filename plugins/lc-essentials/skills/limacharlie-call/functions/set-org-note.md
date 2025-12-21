
# Set Org Note

Creates or updates an organization note in the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Create a new organization note
- Update an existing note's content
- Store organizational documentation
- Save contact information or procedures
- Document policies or runbooks

Common scenarios:
- "Create a note for incident contacts"
- "Update the escalation-policy note"
- "Save our malware response procedures as a note"
- "Store the security team contacts"

## What This Skill Does

Creates or updates an organization note in the LimaCharlie Hive system. The note is automatically enabled and stored with audit metadata.

## Required Information

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use `list_user_orgs` first.

- **oid**: Organization ID (UUID)
- **note_name**: Name for the note
- **text**: The text content of the note (required, cannot be empty)

Optional:
- **description**: Description explaining the note's purpose

## How to Use

### Step 1: Call the API

Use the `lc_call_tool` MCP tool:

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_org_note",
  parameters={
    "oid": "[organization-id]",
    "note_name": "[note-name]",
    "text": "[note content]",
    "description": "[optional description]"
  }
)
```

**API Details:**
- Tool: `set_org_note`
- Required parameters:
  - `oid`: Organization ID
  - `note_name`: Name for the note
  - `text`: The text content of the note
- Optional parameters:
  - `description`: Description of the note

### Step 2: Handle the Response

**Success:**
```json
{
  "success": true,
  "message": "Successfully created/updated org note 'note-name'"
}
```
Note is immediately stored.

**Common Errors:**
- **400 Bad Request**: Invalid note structure or empty text
- **403 Forbidden**: Insufficient permissions - user needs org_notes.set permission
- **500 Server Error**: Backend issue

## Example Usage

### Create a contact information note

User request: "Create a note with our incident response contacts"

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_org_note",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "note_name": "incident-contacts",
    "text": "Primary Contact: security@example.com (555-1234)\nSecondary: ops@example.com (555-5678)\nEscalation: ciso@example.com",
    "description": "Emergency contact list for incident response"
  }
)
```

Result: Note is stored and can be retrieved anytime.

### Update an existing note

User request: "Update the escalation-policy note with new procedures"

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_org_note",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "note_name": "escalation-policy",
    "text": "Level 1: SOC Team (respond within 15 min)\nLevel 2: Security Manager (within 1 hour)\nLevel 3: CISO (within 4 hours)",
    "description": "Incident escalation matrix and SLAs"
  }
)
```

## Related Functions

- `list_org_notes` - List all organization notes
- `get_org_note` - Get a specific note
- `delete_org_note` - Remove a note

## Additional Notes

- Creates if doesn't exist, updates if it does (upsert)
- The `text` field is required and cannot be empty
- Notes can store up to 1MB of text content
- Useful for storing:
  - Contact information
  - Runbooks and procedures
  - Escalation policies
  - Configuration documentation
  - Organizational policies
- All changes are tracked with author and timestamp metadata

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/org_notes.go`
