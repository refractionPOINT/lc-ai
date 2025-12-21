# validate_dr_rule_components

Validate D&R rule components using server-side validation via the Replay service.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| detect | object | Conditional | Detection component (required if `rule_name` not provided) |
| rule_name | string | Conditional | Existing rule name to validate (required if `detect` not provided) |
| respond | array | No | Response actions array |
| namespace | string | No | Rule namespace: general, managed, service (default: general) |

## Returns

**Valid:**
```json
{
  "valid": true,
  "message": "D&R rule components are valid"
}
```

**Invalid:**
```json
{
  "valid": false,
  "error": "Invalid operator 'equals'. Valid operators are: and, or, exists, is, contains, starts with, ends with, matches, is greater than, is less than, length is, lookup"
}
```

## Examples

**Validate detection component:**
```
lc_call_tool(tool_name="validate_dr_rule_components", parameters={
  "oid": "c7e8f940-...",
  "detect": {
    "event": "NEW_PROCESS",
    "op": "contains",
    "path": "event/COMMAND_LINE",
    "value": "powershell"
  }
})
```

**Validate complete rule:**
```
lc_call_tool(tool_name="validate_dr_rule_components", parameters={
  "oid": "c7e8f940-...",
  "detect": {
    "event": "NEW_PROCESS",
    "op": "and",
    "rules": [
      {"op": "contains", "path": "event/FILE_PATH", "value": "powershell"},
      {"op": "contains", "path": "event/COMMAND_LINE", "value": "-enc"}
    ]
  },
  "respond": [
    {"action": "report", "name": "encoded_powershell"},
    {"action": "isolate network"}
  ]
})
```

**Validate existing rule:**
```
lc_call_tool(tool_name="validate_dr_rule_components", parameters={
  "oid": "c7e8f940-...",
  "rule_name": "detect-ransomware",
  "namespace": "general"
})
```

## Valid Operators

`and`, `or`, `exists`, `is`, `contains`, `starts with`, `ends with`, `matches`, `is greater than`, `is less than`, `length is`, `lookup`

## Valid Actions

`report`, `task`, `add tag`, `remove tag`, `isolate network`, `rejoin network`, `service request`

## Notes

- **Server-side validation** via LimaCharlie Replay service
- Validates event types, operators, paths, and actions
- Use before `set_dr_general_rule` to catch errors early
- Related: `generate_dr_rule_detection`, `generate_dr_rule_respond`, `test_dr_rule_events`
