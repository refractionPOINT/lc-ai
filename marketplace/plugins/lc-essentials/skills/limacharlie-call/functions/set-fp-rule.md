
# Set False Positive Rule

Create a new false positive rule or update an existing one to filter unwanted detections.

## When to Use

Use this skill when the user needs to:
- Create a new false positive rule
- Update an existing FP rule
- Filter benign detections
- Reduce detection noise
- Tune detection systems
- Suppress known-safe activity

Common scenarios:
- Rule creation: "Create an FP rule to filter safe process alerts"
- Tuning: "Add a false positive rule for dev environment detections"
- Noise reduction: "Filter out detections from this trusted application"
- Update: "Update the 'known_safe' FP rule to include additional paths"

## What This Skill Does

This skill creates or updates a false positive rule in the organization. FP rules filter detections by matching specific patterns, preventing alerts from being generated for benign activities. The rule uses detection logic (same syntax as D&R detect component) to identify which detections to suppress.

## Required Information

Before calling this skill, gather:

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **rule_name**: Name for the FP rule (unique identifier)
- **rule_content**: Object containing a `detection` (or `detect`) key with the filter logic
- **ttl** (optional): Time-to-live in seconds. Rule auto-deletes after this duration.

### Filter Logic Structure

The filter logic must contain:
- **op**: Operation type (and, or, is, contains, exists, etc.)
- **path**: Detection field path (e.g., "detect/cat", "detect/event/FILE_PATH")
- **value**: Value to match
- **rules**: Array of sub-rules (for and/or operations)

Common detection paths:
- `detect/cat` - Detection category
- `detect/name` - Detection rule name
- `detect/event/*` - Fields from the underlying event
- `routing/hostname` - Sensor hostname
- `routing/tags` - Sensor tags

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. FP rule name (alphanumeric with underscores recommended)
3. Valid filter logic with required fields

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_fp_rule",
  parameters={
    "oid": "[organization-id]",
    "rule_name": "[rule-name]",
    "rule_content": {
      "detection": {
        "op": "and",
        "rules": [
          {"op": "is", "path": "cat", "value": "SUSPICIOUS_EXECUTION"},
          {"op": "contains", "path": "detect/event/FILE_PATH", "value": "/opt/safe_app/"}
        ]
      }
    }
  }
)
```

**API Details:**
- Tool: `set_fp_rule`
- Required parameters:
  - `oid`: Organization ID
  - `rule_name`: Rule name
  - `rule_content`: Object with `detection` (or `detect`) key containing filter logic

### Step 3: Handle the Response

The API returns a response with:
```json
{}
```

**Success (200-299):**
- Rule successfully created or updated
- Rule is now active and filtering detections
- Confirm to user that rule is deployed

**Common Errors:**
- **400 Bad Request**: Invalid filter logic, malformed syntax, or missing required fields
- **403 Forbidden**: Insufficient permissions - user needs detection engineering write permissions
- **409 Conflict**: Rule already exists and is_replace is false
- **500 Server Error**: API service issue - retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Confirm rule was created or updated successfully
- Show rule name
- Summarize what detections the rule will filter
- Note that the rule is now active
- Suggest monitoring detection volume to verify effectiveness

## Example Usage

### Example 1: Create FP rule to filter safe processes

User request: "Create an FP rule to filter SUSPICIOUS_EXECUTION detections for our trusted monitoring tool"

Steps:
1. Design filter logic to match the specific detections
2. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="set_fp_rule",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "rule_name": "filter_monitoring_tool",
    "rule_content": {
      "detection": {
        "op": "and",
        "rules": [
          {"op": "is", "path": "cat", "value": "SUSPICIOUS_EXECUTION"},
          {"op": "contains", "path": "detect/event/FILE_PATH", "value": "C:\\Program Files\\MonitoringTool\\"}
        ]
      }
    }
  }
)
```

Expected response:
```json
{}
```

User message: "Successfully created FP rule 'filter_monitoring_tool'. SUSPICIOUS_EXECUTION detections from the MonitoringTool directory will now be suppressed."

### Example 2: Filter dev environment detections

User request: "Filter all TOOL_USAGE detections on dev servers"

Steps:
1. Prepare filter to match dev hostname pattern
2. Call API with filter logic
3. Confirm rule created

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_fp_rule",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "rule_name": "filter_dev_activity",
    "rule_content": {
      "detection": {
        "op": "and",
        "rules": [
          {"op": "is", "path": "cat", "value": "TOOL_USAGE"},
          {"op": "contains", "path": "routing/hostname", "value": "dev-"}
        ]
      }
    }
  }
)
```

## Additional Notes

- Rule names must be unique within the organization
- Setting is_replace="true" will overwrite existing rules with the same name
- FP rules use the same syntax as D&R detect components
- Empty or invalid filter logic will be rejected
- FP rules are evaluated after D&R rules generate detections
- Suppressed detections are not shown in the timeline
- Suppressed detections still count in statistics
- Be careful with overly broad filters (e.g., filtering entire categories)
- Test FP rules carefully to avoid hiding real threats
- To view the created rule, use get-fp-rule
- To delete the rule, use delete-fp-rule
- Rule changes take effect immediately
- Consider using specific filters rather than broad category filters
- Common use cases:
  - Filter known-safe applications
  - Exclude test/dev environments
  - Suppress detections during maintenance windows
  - Filter specific false positive patterns

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/fp_rule.go`
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/rules/fp_rules.go`
For D&R detection logic syntax, see: https://doc.limacharlie.io/docs/documentation/docs/detection-and-response
