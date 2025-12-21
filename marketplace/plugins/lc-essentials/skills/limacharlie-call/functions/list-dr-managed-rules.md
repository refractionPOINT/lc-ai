# list_dr_managed_rules

List all D&R rules in the managed namespace (automation, imports, extensions).

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "credential_access_detection": {
    "name": "credential_access_detection",
    "namespace": "managed",
    "detect": {"op": "and", "rules": [...]},
    "respond": [{"action": "report", "name": "credential_access"}],
    "is_enabled": true
  },
  "lateral_movement_smb": {
    "name": "lateral_movement_smb",
    "namespace": "managed",
    "detect": {...},
    "respond": [...],
    "is_enabled": true
  }
}
```

Empty `{}` means no managed rules configured.

## Example

```
lc_call_tool(tool_name="list_dr_managed_rules", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Managed rules are created by extensions, automation, or rule imports
- For all namespaces, use `get_detection_rules`
- For custom rules, use `list_dr_general_rules`
- Related: `get_dr_managed_rule`, `set_dr_managed_rule`, `delete_dr_managed_rule`
