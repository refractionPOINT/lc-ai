
# Set SOP

Creates or updates a Standard Operating Procedure in the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Create a new SOP
- Update an existing procedure
- Document security workflows
- Save incident response procedures
- Store compliance runbooks

Common scenarios:
- "Create an SOP for malware response"
- "Update the phishing-response procedure"
- "Save our incident escalation workflow as an SOP"
- "Document the threat hunting procedure"

## What This Skill Does

Creates or updates a Standard Operating Procedure in the LimaCharlie Hive system. The SOP is automatically enabled and stored with audit metadata.

## Required Information

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use `list_user_orgs` first.

- **oid**: Organization ID (UUID)
- **sop_name**: Name for the SOP
- **text**: The procedural content (required, cannot be empty)

Optional:
- **description**: Description explaining the SOP's purpose

## How to Use

### Step 1: Call the API

Use the `lc_call_tool` MCP tool:

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_sop",
  parameters={
    "oid": "[organization-id]",
    "sop_name": "[sop-name]",
    "text": "[procedure content]",
    "description": "[optional description]"
  }
)
```

**API Details:**
- Tool: `set_sop`
- Required parameters:
  - `oid`: Organization ID
  - `sop_name`: Name for the SOP
  - `text`: The procedural content
- Optional parameters:
  - `description`: Description of the SOP

### Step 2: Handle the Response

**Success:**
```json
{
  "success": true,
  "message": "Successfully created/updated SOP 'sop-name'"
}
```
SOP is immediately stored.

**Common Errors:**
- **400 Bad Request**: Invalid SOP structure or empty text
- **403 Forbidden**: Insufficient permissions - user needs sop.set permission
- **500 Server Error**: Backend issue

## Example Usage

### Create a malware response SOP

User request: "Create an SOP for malware incident response"

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_sop",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sop_name": "malware-response",
    "text": "## Malware Response Procedure\n\n### 1. Isolation\n- Immediately isolate the affected system\n- Document isolation time and method\n- Notify SOC lead\n\n### 2. Evidence Collection\n- Capture memory dump using LimaCharlie\n- Export process list and network connections\n- Collect relevant log files\n\n### 3. Analysis\n- Submit sample to sandbox\n- Check YARA rule matches\n- Query threat intelligence\n\n### 4. Remediation\n- Remove malware artifacts\n- Restore from clean backup if needed\n- Verify system integrity\n- Reconnect to network\n\n### 5. Documentation\n- Complete incident report\n- Update detection rules\n- Schedule lessons learned",
    "description": "Standard procedure for malware incident response - Tier 1 analysts"
  }
)
```

Result: SOP is stored and can be retrieved anytime.

### Update an existing SOP

User request: "Update the phishing-response procedure with new steps"

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_sop",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sop_name": "phishing-response",
    "text": "## Phishing Response Procedure\n\n1. Identify all affected users\n2. Reset compromised credentials immediately\n3. Block malicious URLs in proxy\n4. Quarantine related emails\n5. Notify affected users\n6. Update email filters\n7. Document incident",
    "description": "Phishing incident handling procedure - updated 2024"
  }
)
```

## Related Functions

- `list_sops` - List all SOPs
- `get_sop` - Get a specific SOP
- `delete_sop` - Remove an SOP

## Additional Notes

- Creates if doesn't exist, updates if it does (upsert)
- The `text` field is required and cannot be empty
- SOPs can store up to 1MB of text content
- Text supports markdown formatting for better readability
- Useful for documenting:
  - Incident response procedures
  - Threat hunting playbooks
  - Escalation workflows
  - Compliance procedures
  - Security operations runbooks
- All changes are tracked with author and timestamp metadata
- Consider using a consistent structure across SOPs:
  - Purpose/Scope
  - Prerequisites
  - Numbered steps
  - Roles and responsibilities
  - Escalation criteria

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/sop.go`
