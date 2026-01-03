# get_dr_general_rule

Retrieve a specific custom D&R rule by name from the general namespace.

**⚠️ PARAMETER NAME**: Use `rule_name`, NOT `name`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | Rule name (case-sensitive, exact match) |

## Returns

```json
{
  "rule-name": {
    "name": "rule-name",
    "namespace": "general",
    "detect": {
      "event": "NEW_PROCESS",
      "op": "contains",
      "path": "event/COMMAND_LINE",
      "value": "powershell -enc"
    },
    "respond": [
      {"action": "report", "name": "encoded_powershell"},
      {"action": "add tag", "tag": "suspicious", "ttl": 86400}
    ],
    "is_enabled": true,
    "target": "platform=windows"
  }
}
```

## Example

```
lc_call_tool(tool_name="get_dr_general_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "detect-suspicious-powershell"
})
```

## Notes

- Only searches general namespace (custom rules)
- For managed/service rules, use `get_detection_rules` and filter
- `is_enabled: false` means rule exists but won't trigger
- `target` field limits which sensors the rule applies to
- Related: `list_dr_general_rules`, `set_dr_general_rule`, `delete_dr_general_rule`
