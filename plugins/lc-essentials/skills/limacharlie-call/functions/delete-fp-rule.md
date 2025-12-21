
# Delete False Positive Rule

Delete a specific false positive rule from the organization by name.

## When to Use

Use this skill when the user needs to:
- Delete a false positive rule
- Remove outdated FP filters
- Restore previously filtered detections
- Clean up unused FP rules
- Disable detection filtering

Common scenarios:
- Cleanup: "Delete the 'old_filter' FP rule"
- Restore: "Remove the FP rule that's hiding important detections"
- Correction: "Delete FP rule 'overly_broad' so we can see those alerts again"
- Maintenance: "Clean up unused false positive rules"

## What This Skill Does

This skill permanently deletes a false positive rule from the organization by its name. The rule will no longer suppress detections, and previously filtered detections will start appearing again. This operation cannot be undone.

## Required Information

Before calling this skill, gather:

**⚠️ IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **rule_name**: Name of the FP rule to delete (must be exact match)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Exact FP rule name to delete (case-sensitive)
3. Confirm user wants to delete the rule (permanent operation)

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_fp_rule",
  parameters={
    "oid": "[organization-id]",
    "rule_name": "[rule-name]"
  }
)
```

**API Details:**
- Tool: `delete_fp_rule`
- Required parameters:
  - `oid`: Organization ID
  - `rule_name`: FP rule name to delete

### Step 3: Handle the Response

The API returns a response with:
```json
{}
```

**Success (200-299):**
- Rule successfully deleted
- Detections previously filtered by this rule will now appear
- Confirm to user that rule no longer exists

**Common Errors:**
- **400 Bad Request**: Invalid request format or missing parameters
- **403 Forbidden**: Insufficient permissions - user needs detection engineering write permissions
- **404 Not Found**: Rule with specified name does not exist
- **500 Server Error**: API service issue - retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Confirm rule was successfully deleted
- Show the rule name that was removed
- Note that deletion is permanent and cannot be undone
- Warn that previously suppressed detections will now appear
- If rule not found, suggest checking the name with get-fp-rules

## Example Usage

### Example 1: Delete an FP rule

User request: "Delete the 'filter_dev_activity' FP rule"

Steps:
1. Get organization ID from context
2. Extract rule name: "filter_dev_activity"
3. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_fp_rule",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "rule_name": "filter_dev_activity"
  }
)
```

Expected response:
```json
{}
```

User message: "Successfully deleted FP rule 'filter_dev_activity'. Detections that were previously filtered by this rule will now appear in your timeline."

### Example 2: Rule not found

User request: "Delete FP rule 'nonexistent_rule'"

Steps:
1. Call API to delete rule
2. API returns 404 Not Found
3. Inform user: "FP rule 'nonexistent_rule' not found. The rule may have already been deleted or the name may be incorrect. Use get-fp-rules to see available rules."

### Example 3: Restore accidentally filtered detections

User request: "I think my FP rule 'overly_broad_filter' is hiding real threats. Delete it."

Steps:
1. Optionally review the rule first with get-fp-rule
2. Confirm with user that they want to delete
3. Call API to delete rule
4. Inform user: "Deleted FP rule 'overly_broad_filter'. Detections matching this filter will now be visible. Monitor your timeline for any previously suppressed alerts."

## Additional Notes

- Deletion is permanent and cannot be undone
- Rule names are case-sensitive
- The rule must exist in the organization
- Deletion takes effect immediately
- No confirmation prompt from the API - ensure user intends to delete
- Consider backing up the rule configuration before deletion (use get-fp-rule first)
- After deletion, detections that were being filtered will start appearing
- This does not retroactively show historical suppressed detections
- Suppressed detections from before deletion remain suppressed in history
- New detections matching the deleted filter will now appear
- If you want to temporarily disable filtering without deleting, consider:
  - Updating the rule to be more specific
  - Creating a narrower filter
  - There's no "disable" option - must delete to stop filtering
- To recreate a deleted rule, use set-fp-rule
- Monitor detection volume after deletion to ensure no alert overload

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/fp_rule.go`
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/rules/fp_rules.go`
