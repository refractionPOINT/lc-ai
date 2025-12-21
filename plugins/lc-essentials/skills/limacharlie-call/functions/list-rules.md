
# List Rules in Hive

Lists all rules in a specified Hive in a LimaCharlie organization.

## When to Use

Use this skill when the user needs to:
- List all D&R rules in the organization
- View rules in dr-general, fp, or other Hives
- Audit detection and response configurations
- Check which rules are enabled or disabled
- Review rule details before modifying them
- Understand detection coverage

Common scenarios:
- "Show me all D&R rules"
- "List my detection rules"
- "What rules are in the dr-general Hive?"
- "Show me all false positive rules in the fp Hive"
- "Which rules are enabled in my organization?"

## What This Skill Does

This skill retrieves all rule records from a specified Hive in the LimaCharlie Hive system. It calls the Hive API using the provided hive name with the organization ID as the partition to list all rules. Each rule includes its detection/response definition, enabled status, tags, comments, and system metadata (creation time, last modification, author, etc.).

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **hive_name**: The name of the Hive to list rules from (required)
  - Common values: `dr-general`, `fp`

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Hive name (string, determines which Hive to list from)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="list_rules",
  parameters={
    "oid": "[organization-id]",
    "hive_name": "[hive-name]"
  }
)
```

**API Details:**
- Tool: `list_rules`
- Required parameters:
  - `oid`: Organization ID
  - `hive_name`: Name of the Hive (e.g., "dr-general", "fp")

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "rule-name-1": {
    "data": {
      "detect": {
        "event": "PROCESS_CREATE",
        "op": "contains",
        "path": "event/FILE_PATH",
        "value": "suspicious.exe"
      },
      "respond": [
        {"action": "report", "name": "suspicious-process"}
      ]
    },
    "sys_mtd": {
      "etag": "...",
      "created_by": "user@example.com",
      "created_at": 1234567890,
      "last_author": "user@example.com",
      "last_mod": 1234567899,
      "guid": "..."
    },
    "usr_mtd": {
      "enabled": true,
      "expiry": 0,
      "tags": ["detection", "malware"],
      "comment": "Detects suspicious process creation"
    }
  },
  "rule-name-2": {
    // ... another rule
  }
}
```

**Success:**
- The response body is an object where each key is a rule name
- Each value contains `data` (rule definition), `sys_mtd` (system metadata), and `usr_mtd` (user metadata)
- Present the list of rules with their enabled status and key details
- Count the total number of rules

**Common Errors:**
- **403 Forbidden**: Insufficient permissions - user needs platform_admin or similar role to access Hive
- **404 Not Found**: The hive or partition doesn't exist (invalid hive name)
- **500 Server Error**: Rare backend issue - advise user to retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show a summary count of how many rules exist
- List each rule name with its enabled status
- Highlight what each rule detects
- Note any rules with tags or comments
- Show creation and last modification timestamps for audit purposes
- Explain what each rule does in simple terms

## Example Usage

### Example 1: List all D&R rules

User request: "Show me all D&R rules in the general namespace"

Steps:
1. Get the organization ID from context
2. Use hive_name "dr-general"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_rules",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "hive_name": "dr-general"
  }
)
```

Expected response:
```json
{
  "suspicious-dns": {
    "data": {
      "detect": {
        "event": "DNS_REQUEST",
        "op": "contains",
        "path": "event/DOMAIN_NAME",
        "value": "malicious.com"
      },
      "respond": [
        {"action": "report", "name": "suspicious-dns"}
      ]
    },
    "usr_mtd": {
      "enabled": true,
      "tags": ["network", "dns"],
      "comment": "Detect DNS queries to known bad domains"
    }
  },
  "ransomware-behavior": {
    "data": {
      "detect": {...},
      "respond": [
        {"action": "report"},
        {"action": "isolate"}
      ]
    },
    "usr_mtd": {
      "enabled": true,
      "tags": ["malware", "ransomware"]
    }
  }
}
```

Format the output showing:
- Total: 2 rules in dr-general
- suspicious-dns: Enabled - Detects DNS queries to malicious domains
- ransomware-behavior: Enabled - Detects ransomware behavior and isolates sensor

### Example 2: List false positive rules

User request: "Show me all false positive rules"

Steps:
1. Get organization ID
2. Use hive_name "fp"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_rules",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "hive_name": "fp"
  }
)
```

## Additional Notes

- **Hive Types**:
  - `dr-general`: User-created Detection & Response rules
  - `dr-managed`: Managed detection rules (usually read-only)
  - `fp`: False Positive filtering rules
- D&R rules contain `detect` and `respond` sections
- FP rules contain filtering logic to suppress false positives
- The `enabled` field in `usr_mtd` controls whether the rule is active
- Tags can be used for filtering and organizing rules
- System metadata provides audit trail information
- Empty result (no rules) is valid and means no rules have been created in that Hive
- Use the `get_rule` skill to retrieve a specific rule's full definition
- Rules are powerful - ensure enabled rules are tested and validated

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (List method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/generic_hive.go`
