
# Get False Positive Rule

Retrieve a specific false positive rule by name, including its filter logic and configuration.

## When to Use

Use this skill when the user needs to:
- View a specific false positive rule's configuration
- Inspect FP rule filter logic
- Review what detections a rule filters
- Analyze FP rule structure
- Export a specific FP rule configuration

Common scenarios:
- Rule inspection: "Show me the 'filter_safe_processes' FP rule"
- Analysis: "What detections does my 'dev_filter' FP rule suppress?"
- Review: "Display the configuration for FP rule 'noisy_alerts'"
- Documentation: "Get the filter logic for 'known_false_positives'"

## What This Skill Does

This skill retrieves a specific false positive rule by name. It fetches the complete rule configuration including the detection filter logic.

## Required Information

Before calling this skill, gather:

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **rule_name**: Name of the FP rule to retrieve (must be exact match)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. FP rule name (must be exact match, case-sensitive)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_fp_rule",
  parameters={
    "oid": "[organization-id]",
    "rule_name": "[rule-name]"
  }
)
```

**API Details:**
- Tool: `get_fp_rule`
- Required parameters:
  - `oid`: Organization ID
  - `rule_name`: FP rule name

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "name": "filter_safe_processes",
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "data": {
    "op": "and",
    "rules": [
      {"op": "is", "path": "detect/cat", "value": "SUSPICIOUS_EXECUTION"},
      {"op": "contains", "path": "detect/event/FILE_PATH", "value": "C:\\Program Files\\TrustedApp\\"}
    ]
  }
}
```

**Success (200-299):**
- Response contains the complete rule configuration
- Extract the complete rule configuration
- Present filter logic and metadata
- If rule name not found, return "Rule not found" error

**Common Errors:**
- **400 Bad Request**: Invalid organization ID format
- **403 Forbidden**: Insufficient permissions to view FP rules
- **404 Not Found**: Organization ID does not exist or rule name not found
- **500 Server Error**: API service issue - retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show rule name clearly
- Display the filter logic (detection component)
- Explain in plain language what the rule filters
- Highlight the detection paths and values being matched
- If rule not found, suggest checking the name or using get-fp-rules

## Example Usage

### Example 1: Get specific FP rule

User request: "Show me the 'filter_safe_processes' FP rule"

Steps:
1. Get organization ID from context
2. Extract rule name: "filter_safe_processes"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_fp_rule",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "rule_name": "filter_safe_processes"
  }
)
```

Expected response:
```json
{
  "name": "filter_safe_processes",
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "data": {
    "op": "and",
    "rules": [
      {"op": "is", "path": "detect/cat", "value": "SUSPICIOUS_EXECUTION"},
      {"op": "contains", "path": "detect/event/FILE_PATH", "value": "C:\\Program Files\\TrustedApp\\"}
    ]
  }
}
```

User message: "FP Rule: filter_safe_processes

This rule filters SUSPICIOUS_EXECUTION detections where the file path contains 'C:\\Program Files\\TrustedApp\\'. It suppresses alerts for processes running from the trusted application directory."

### Example 2: Rule not found

User request: "Get FP rule 'nonexistent_rule'"

Steps:
1. Call API
2. API returns 404 Not Found
3. Inform user: "FP rule 'nonexistent_rule' not found. Use get-fp-rules to see available rules."

## Additional Notes

- Rule names are case-sensitive and must match exactly
- FP rules use the same detection logic syntax as D&R rules
- The `data` field contains the filter logic (detection component)
- Common filter patterns:
  - Match detection category: `{"op": "is", "path": "detect/cat", "value": "CATEGORY_NAME"}`
  - Match detection name: `{"op": "is", "path": "detect/name", "value": "rule_name"}`
  - Match event fields: `{"op": "contains", "path": "detect/event/FIELD", "value": "pattern"}`
  - Match sensor properties: `{"op": "is", "path": "routing/hostname", "value": "hostname"}`
- FP rules can use complex logic with 'and'/'or' operators
- The rule filters detections after D&R rules have fired
- To modify this rule, use set-fp-rule
- To delete this rule, use delete-fp-rule
- Understanding FP rules helps tune detection systems and reduce alert noise

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/fp_rule.go`
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/rules/fp_rules.go`
