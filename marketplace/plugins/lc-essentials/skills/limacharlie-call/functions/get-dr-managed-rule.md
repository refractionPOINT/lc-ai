# get_dr_managed_rule

Retrieve a specific D&R rule from the managed namespace by name.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | Rule name (case-sensitive, exact match) |

## Returns

```json
{
  "credential_access_detection": {
    "name": "credential_access_detection",
    "namespace": "managed",
    "detect": {
      "op": "and",
      "rules": [
        {"op": "is", "path": "event/EVENT_TYPE", "value": "CODE_IDENTITY"},
        {"op": "contains", "path": "event/FILE_PATH", "value": "lsass"}
      ]
    },
    "respond": [
      {"action": "report", "name": "credential_access", "metadata": {"severity": "high"}}
    ],
    "is_enabled": true
  }
}
```

## Example

```
lc_call_tool(tool_name="get_dr_managed_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "credential_access_detection"
})
```

## Notes

- Only searches managed namespace
- For general namespace rules, use `get_dr_general_rule`
- Detection logic uses D&R syntax with operators: `and`, `or`, `is`, `contains`, etc.
- Related: `list_dr_managed_rules`, `set_dr_managed_rule`, `delete_dr_managed_rule`
