# get_detection_rules

Retrieve all D&R rules from all namespaces (general, managed, service) for complete detection stack visibility.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "detect-suspicious-cmd": {
    "name": "detect-suspicious-cmd",
    "namespace": "general",
    "detect": {
      "event": "NEW_PROCESS",
      "op": "is",
      "path": "event/FILE_PATH",
      "value": "cmd.exe"
    },
    "respond": [{"action": "report", "name": "suspicious_cmd"}],
    "is_enabled": true
  },
  "ransomware-behavior": {
    "name": "ransomware-behavior",
    "namespace": "managed",
    "detect": {...},
    "respond": [...],
    "is_enabled": true
  }
}
```

Empty `{}` means no rules configured.

## Example

```
lc_call_tool(tool_name="get_detection_rules", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Namespaces

| Namespace | Description |
|-----------|-------------|
| general | Custom user-created rules |
| managed | LC-maintained rules from extensions |
| service | Rules from integrated services |

## Notes

- Returns rules from ALL namespaces in one call
- Rule names can be same across namespaces (namespace + name = unique)
- `is_enabled: false` means rule exists but won't trigger
- For namespace-specific lists, use `list_dr_general_rules` or `list_dr_managed_rules`
- Read-only operation - use namespace-specific functions to modify rules
