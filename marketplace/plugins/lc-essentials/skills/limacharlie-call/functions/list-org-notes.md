
# List Org Notes

Lists all organization notes stored in the Hive for a LimaCharlie organization.

## When to Use

Use this skill when the user needs to:
- List all organization notes
- View notes stored for the organization
- Audit organizational documentation
- Check which notes exist before modifying them
- Review organization-level information

Common scenarios:
- "Show me all my organization notes"
- "What notes do I have stored?"
- "List all org notes"
- "What organizational documentation exists?"

## What This Skill Does

This skill retrieves all organization note records from the LimaCharlie Hive system. It calls the Hive API using the "org_notes" hive name with the organization ID as the partition to list all notes. Each note includes its text content, description, enabled status, tags, comments, and system metadata (creation time, last modification, author, etc.).

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

No other parameters are required.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="list_org_notes",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**API Details:**
- Tool: `list_org_notes`
- Required parameters:
  - `oid`: Organization ID

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "org_notes": {
    "note-name-1": {
      "data": {
        "text": "Note content here",
        "description": "Optional description"
      },
      "enabled": true,
      "tags": ["tag1", "tag2"],
      "comment": "Optional comment",
      "metadata": {
        "created_at": 1234567890,
        "created_by": "user@example.com",
        "last_mod": 1234567899,
        "last_author": "user@example.com",
        "guid": "unique-id"
      }
    }
  },
  "count": 1
}
```

**Success:**
- The response body contains an `org_notes` object where each key is a note name
- Each value contains `data` (text and description), `enabled`, `tags`, `comment`, and `metadata`
- Present the list of notes with their key details
- Count the total number of notes

**Common Errors:**
- **403 Forbidden**: Insufficient permissions - user needs org_notes.get permission
- **404 Not Found**: The hive or partition doesn't exist (unusual, should always exist)
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show a summary count of how many notes exist
- List each note name with its text content
- Show descriptions where available
- Note any tags or comments
- Show creation and last modification timestamps for audit purposes

## Example Usage

### Example 1: List all organization notes

User request: "Show me all my organization notes"

Steps:
1. Get the organization ID from context
2. Call the Hive API to list org notes
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_org_notes",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "org_notes": {
    "incident-contacts": {
      "data": {
        "text": "Primary: security@example.com\nSecondary: ops@example.com",
        "description": "Emergency contact list"
      },
      "enabled": true,
      "tags": ["contacts", "incident-response"],
      "metadata": {
        "created_at": 1700000000,
        "last_mod": 1700001000
      }
    },
    "escalation-policy": {
      "data": {
        "text": "Level 1: SOC\nLevel 2: Security Manager\nLevel 3: CISO",
        "description": "Escalation matrix"
      },
      "enabled": true
    }
  },
  "count": 2
}
```

Format the output showing:
- Total: 2 organization notes
- incident-contacts: Emergency contact list with primary and secondary contacts
- escalation-policy: Escalation matrix for incident handling

## Additional Notes

- Organization notes are general-purpose text storage for organizational information
- Notes can store any text content up to 1MB
- The `enabled` field can be used to mark notes as active/inactive
- Tags can be used for filtering and organizing notes
- The `data` field contains:
  - `text`: The main content of the note (required)
  - `description`: Optional description of what the note contains
- System metadata provides audit trail information
- Empty result (no notes) is valid and means no notes have been created yet
- Use the `get_org_note` skill to retrieve a specific note's full content
- Use the `set_org_note` skill to create or update notes

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (List method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/org_notes.go`
