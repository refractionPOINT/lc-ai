
# Get False Positive Rules

Retrieve all false positive (FP) rules configured in the organization for filtering unwanted detections.

## When to Use

Use this skill when the user needs to:
- List all false positive rules
- View FP rule inventory
- Audit detection noise reduction filters
- Review false positive configurations
- Check what detections are being filtered

Common scenarios:
- Inventory: "Show me all my false positive rules"
- Audit: "What FP rules are configured?"
- Review: "List all detection filters"
- Management: "Display false positive rule configurations"

## What This Skill Does

This skill retrieves all false positive rules from the organization. FP rules are filters that suppress specific detections to reduce alert noise from benign activities. They work by matching detection patterns and preventing alerts from being generated. This is useful for tuning detection systems and reducing false positives.

## Required Information

Before calling this skill, gather:

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

No additional parameters are required.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_fp_rules",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**API Details:**
- Tool: `get_fp_rules`
- Required parameters:
  - `oid`: Organization ID

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "fp-rule-1": {
    "name": "fp-rule-1",
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "data": {
      "op": "and",
      "rules": [
        {"op": "is", "path": "detect/cat", "value": "PROCESS_ANOMALY"},
        {"op": "contains", "path": "detect/event/FILE_PATH", "value": "/opt/known_safe/"}
      ]
    }
  },
  "fp-rule-2": {
    "name": "fp-rule-2",
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "data": {
      "op": "is",
      "path": "detect/cat",
      "value": "NOISY_DETECTION"
    }
  }
}
```

**Success (200-299):**
- The response contains a map of FP rules indexed by rule name
- Each rule includes:
  - `name`: FP rule name
  - `oid`: Organization ID
  - `data`: Detection filter logic (same format as D&R detect component)
- Count the number of rules and present to user
- Display rule names and summarize what they filter

**Common Errors:**
- **400 Bad Request**: Invalid organization ID format
- **403 Forbidden**: Insufficient permissions to view FP rules
- **404 Not Found**: Organization ID does not exist
- **500 Server Error**: API service issue - retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show total count of false positive rules
- List rule names with their filter logic summary
- Explain what each rule is filtering (which detection categories or patterns)
- Note if no FP rules are configured (empty list is valid)
- Highlight rules that might be too broad (filtering entire categories)

## Example Usage

### Example 1: List all FP rules

User request: "Show me all my false positive rules"

Steps:
1. Get organization ID from context
2. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_fp_rules",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "filter_safe_processes": {
    "name": "filter_safe_processes",
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "data": {
      "op": "and",
      "rules": [
        {"op": "is", "path": "detect/cat", "value": "SUSPICIOUS_EXECUTION"},
        {"op": "contains", "path": "detect/event/FILE_PATH", "value": "C:\\Program Files\\TrustedApp\\"}
      ]
    }
  },
  "filter_dev_activity": {
    "name": "filter_dev_activity",
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "data": {
      "op": "and",
      "rules": [
        {"op": "is", "path": "detect/cat", "value": "TOOL_USAGE"},
        {"op": "contains", "path": "routing/hostname", "value": "dev-"}
      ]
    }
  }
}
```

User message: "You have 2 false positive rules configured:
1. filter_safe_processes - Filters SUSPICIOUS_EXECUTION detections for TrustedApp
2. filter_dev_activity - Filters TOOL_USAGE detections on dev hosts"

### Example 2: No FP rules configured

User request: "List my false positive rules"

Steps:
1. Call API
2. Response body is empty object: {}
3. Inform user: "You have no false positive rules configured. FP rules can be added using set-fp-rule to filter out benign detections."

## Additional Notes

- FP rules use the same detection logic syntax as D&R rules
- They match against detections, not raw events
- Common paths in FP rules:
  - `detect/cat` - Detection category
  - `detect/name` - Detection rule name
  - `detect/event/*` - Fields from the underlying event
  - `routing/hostname` - Sensor hostname
  - `routing/tags` - Sensor tags
- FP rules are evaluated after D&R rules generate detections
- Matched detections are suppressed (not shown in timeline)
- Suppressed detections still count in statistics but don't generate alerts
- Be careful with overly broad FP rules that filter entire categories
- To view a specific FP rule, use get-fp-rule
- To add or update FP rules, use set-fp-rule
- To remove FP rules, use delete-fp-rule
- FP rules are useful for:
  - Filtering known-safe applications
  - Excluding test/dev environments
  - Suppressing noisy detections
  - Tuning detection sensitivity

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/fp_rule.go`
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/rules/fp_rules.go`
