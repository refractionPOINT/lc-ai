# list_dr_general_rules

List all custom D&R rules in the general namespace.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "detect-powershell": {
    "name": "detect-powershell",
    "namespace": "general",
    "detect": {
      "event": "NEW_PROCESS",
      "op": "contains",
      "path": "event/COMMAND_LINE",
      "value": "powershell -enc"
    },
    "respond": [{"action": "report", "name": "encoded_powershell"}],
    "is_enabled": true
  }
}
```

Empty `{}` means no custom rules.

## Example

```
lc_call_tool(tool_name="list_dr_general_rules", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Only shows custom user-created rules (general namespace)
- Does NOT include managed rules (from LC) or service rules (from extensions)
- For all namespaces, use `get_detection_rules`
- `is_enabled: false` means rule exists but won't trigger
- Related: `get_dr_general_rule`, `set_dr_general_rule`, `delete_dr_general_rule`
