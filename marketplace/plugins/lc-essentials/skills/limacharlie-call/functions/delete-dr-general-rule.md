# delete_dr_general_rule

Permanently delete a custom D&R rule from the general namespace.

**⚠️ PARAMETER NAME**: Use `rule_name`, NOT `name`.

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
lc_call_tool(tool_name="delete_dr_general_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "test-powershell-detection"
})
```

## Notes

- **Deletion is permanent and irreversible**
- Rule immediately stops evaluating events
- Historical detections remain in logs
- Consider disabling first (`is_enabled: false`) to test impact
- Only affects general namespace (cannot delete managed/service rules)
- Related: `list_dr_general_rules`, `get_dr_general_rule`, `set_dr_general_rule`
