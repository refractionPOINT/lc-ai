
# Get Rule from Hive

Retrieves a specific rule by name from a Hive in a LimaCharlie organization.

## When to Use

Use this skill when the user needs to:
- Get detailed detection/response logic for a specific rule
- View rule definition before modifying it
- Check if a rule exists
- Inspect rule metadata (creation date, last author, etc.)
- Review rule logic as part of troubleshooting
- Understand what a rule detects and how it responds

Common scenarios:
- "Show me the suspicious-dns rule"
- "What does the ransomware-detection rule do?"
- "Get the rule named 'malware-behavior' from dr-general"
- "Is the chrome-fp rule configured in the fp Hive?"

## What This Skill Does

This skill retrieves a single rule record from a specified Hive in the LimaCharlie Hive system by its name. It calls the Hive API using the provided hive name with the organization ID as the partition and the specific rule name as the key. The response includes the complete rule definition (detect and respond sections), user metadata (enabled, tags, comments), and system metadata (audit trail).

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **hive_name**: The name of the Hive containing the rule (required)
  - Common values: `dr-general`, `fp`
- **rule_name**: The name of the rule to retrieve (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Hive name (string, determines which Hive to retrieve from)
3. Rule name (string, must be exact match)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_rule",
  parameters={
    "oid": "[organization-id]",
    "hive_name": "[hive-name]",
    "rule_name": "[rule-name]"
  }
)
```

**API Details:**
- Tool: `get_rule`
- Required parameters:
  - `oid`: Organization ID
  - `hive_name`: Name of the Hive (e.g., "dr-general", "fp")
  - `rule_name`: Name of the rule to retrieve

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "data": {
    "detect": {
      "event": "DNS_REQUEST",
      "op": "contains",
      "path": "event/DOMAIN_NAME",
      "value": "malicious.com"
    },
    "respond": [
      {"action": "report", "name": "suspicious-dns"},
      {"action": "add_tag", "tag": "suspicious", "ttl": 900}
    ]
  },
  "sys_mtd": {
    "etag": "abc123...",
    "created_by": "user@example.com",
    "created_at": 1234567890,
    "last_author": "admin@example.com",
    "last_mod": 1234567899,
    "guid": "unique-id-123"
  },
  "usr_mtd": {
    "enabled": true,
    "expiry": 0,
    "tags": ["network", "dns"],
    "comment": "Detects DNS queries to known malicious domains"
  }
}
```

**Success:**
- The `data` field contains the complete rule definition
- The `usr_mtd` field shows user-controlled metadata
- The `sys_mtd` field shows system metadata including audit trail
- Present the rule details to the user in a readable format

**Common Errors:**
- **400 Bad Request**: Invalid rule name format
- **403 Forbidden**: Insufficient permissions - user needs platform_admin or similar role
- **404 Not Found**: The rule doesn't exist - inform user and suggest creating it
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show the rule name, Hive, and enabled status prominently
- Explain what the rule detects (event type, conditions)
- List the response actions in order
- Include comment if present
- Display relevant metadata like creation date and last modification
- Note any tags
- Explain what the rule does in simple terms

## Example Usage

### Example 1: Get a specific D&R rule

User request: "Show me the suspicious-dns rule from dr-general"

Steps:
1. Get the organization ID from context
2. Use hive_name "dr-general" and rule name "suspicious-dns"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_rule",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "hive_name": "dr-general",
    "rule_name": "suspicious-dns"
  }
)
```

Expected response contains the rule definition showing it detects DNS queries to malicious domains.

Format the output explaining:
- Rule: suspicious-dns (Enabled)
- Hive: dr-general
- Detects: DNS_REQUEST events containing "malicious.com" in the domain name
- Responds:
  1. Report detection as "suspicious-dns"
  2. Add tag "suspicious" for 15 minutes
- Last Modified: [date] by admin@example.com

### Example 2: Get a false positive rule

User request: "What's the chrome-update-fp rule?"

Steps:
1. Get organization ID
2. Use hive_name "fp" and rule name "chrome-update-fp"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_rule",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "hive_name": "fp",
    "rule_name": "chrome-update-fp"
  }
)
```

### Example 3: Rule not found

User request: "Show me the nonexistent-rule"

Steps:
1. Attempt to get the rule
2. Receive 404 error
3. Inform user: "The rule 'nonexistent-rule' does not exist in dr-general. Would you like me to list all available rules?"

## Additional Notes

- Rule names are case-sensitive - use exact name from list-rules
- The `data` field structure for D&R rules includes:
  - `detect`: Detection logic (event type, operators, conditions)
  - `respond`: Array of response actions to execute
- FP rules have different structure for filtering logic
- The `enabled` field controls whether the rule is active
- Use `list_rules` first if you don't know the exact rule name
- Rules can contain complex nested detection logic
- Common response actions:
  - `report`: Generate a detection
  - `add_tag`: Tag the sensor
  - `isolate`: Isolate the sensor from network
  - `task`: Send a command to the sensor
- Review rule logic carefully before enabling in production

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Get method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/generic_hive.go`
