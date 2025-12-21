
# List SOPs

Lists all Standard Operating Procedures stored in the Hive for a LimaCharlie organization.

## When to Use

Use this skill when the user needs to:
- List all SOPs in their organization
- View available standard operating procedures
- Audit security procedures and runbooks
- Check which SOPs exist before modifying them
- Review procedural documentation

Common scenarios:
- "Show me all my SOPs"
- "What standard operating procedures do I have?"
- "List all SOPs in the organization"
- "What security procedures are documented?"

## What This Skill Does

This skill retrieves all Standard Operating Procedure records from the LimaCharlie Hive system. It calls the Hive API using the "sop" hive name with the organization ID as the partition to list all SOPs. Each SOP includes its text content, description, enabled status, tags, comments, and system metadata (creation time, last modification, author, etc.).

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
  tool_name="list_sops",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**API Details:**
- Tool: `list_sops`
- Required parameters:
  - `oid`: Organization ID

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "sops": {
    "sop-name-1": {
      "data": {
        "text": "SOP content here",
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
- The response body contains a `sops` object where each key is an SOP name
- Each value contains `data` (text and description), `enabled`, `tags`, `comment`, and `metadata`
- Present the list of SOPs with their key details
- Count the total number of SOPs

**Common Errors:**
- **403 Forbidden**: Insufficient permissions - user needs sop.get permission
- **404 Not Found**: The hive or partition doesn't exist (unusual, should always exist)
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show a summary count of how many SOPs exist
- List each SOP name with a brief description
- Show descriptions where available
- Note any tags that categorize the SOPs
- Show creation and last modification timestamps for audit purposes

## Example Usage

### Example 1: List all SOPs

User request: "Show me all my standard operating procedures"

Steps:
1. Get the organization ID from context
2. Call the Hive API to list SOPs
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_sops",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "sops": {
    "malware-response": {
      "data": {
        "text": "1. Isolate affected system\n2. Collect forensic artifacts\n3. Analyze malware sample\n4. Remediate and restore",
        "description": "Standard procedure for malware incidents"
      },
      "enabled": true,
      "tags": ["incident-response", "malware"],
      "metadata": {
        "created_at": 1700000000,
        "last_mod": 1700001000
      }
    },
    "phishing-response": {
      "data": {
        "text": "1. Identify affected users\n2. Reset credentials\n3. Block malicious URLs\n4. User notification",
        "description": "Phishing incident handling procedure"
      },
      "enabled": true,
      "tags": ["incident-response", "phishing"]
    }
  },
  "count": 2
}
```

Format the output showing:
- Total: 2 SOPs
- malware-response: Standard procedure for malware incidents
- phishing-response: Phishing incident handling procedure

## Additional Notes

- SOPs are designed for documenting standard security procedures
- SOPs can store any text content up to 1MB
- The `enabled` field can be used to mark SOPs as active/inactive
- Tags can be used for filtering and organizing SOPs by category
- The `data` field contains:
  - `text`: The main procedural content (required)
  - `description`: Optional description explaining the SOP's purpose
- System metadata provides audit trail information
- Empty result (no SOPs) is valid and means no SOPs have been created yet
- Use the `get_sop` skill to retrieve a specific SOP's full content
- Use the `set_sop` skill to create or update SOPs
- Common SOP categories include:
  - Incident response procedures
  - Threat hunting playbooks
  - Escalation workflows
  - Compliance procedures

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (List method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/sop.go`
