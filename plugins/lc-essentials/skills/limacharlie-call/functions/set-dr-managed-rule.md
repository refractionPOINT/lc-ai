# set_dr_managed_rule

Create or update a D&R rule in the managed namespace.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | Rule name (case-sensitive) |
| rule_content | object | Yes | Rule content containing `detect` and optionally `respond` |
| ttl | number | No | Time-to-live in seconds. Rule auto-deletes after this duration. |

## Returns

```json
{}
```

Empty response indicates success. Rule is immediately active.

## Example

```
lc_call_tool(tool_name="set_dr_managed_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "credential_access_detection",
  "rule_content": {
    "detect": {
      "op": "and",
      "rules": [
        {"op": "is", "path": "event/EVENT_TYPE", "value": "CODE_IDENTITY"},
        {"op": "contains", "path": "event/FILE_PATH", "value": "lsass"}
      ]
    },
    "respond": [{"action": "report", "name": "credential_access"}]
  }
})
```

## Notes

- Creates a new rule or replaces an existing rule
- Changes take effect immediately
- Related: `get_dr_managed_rule`, `list_dr_managed_rules`, `delete_dr_managed_rule`
