# delete_dr_managed_rule

Permanently delete a D&R rule from the managed namespace.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | Rule name (case-sensitive, exact match) |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_dr_managed_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "old_lateral_movement"
})
```

## Notes

- **Deletion is permanent and irreversible**
- Rule immediately stops generating detections
- Historical detections remain in timeline
- Consider disabling first (`is_enabled: false`) to test impact
- For general namespace rules, use `delete_dr_general_rule`
- Related: `list_dr_managed_rules`, `get_dr_managed_rule`, `set_dr_managed_rule`
