# get_registry_keys

Retrieve Windows registry keys and values from a specific path. Windows-only.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (Windows, must be online) |
| path | string | Yes | Registry path (e.g., "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run") |

## Returns

```json
{
  "keys": [
    {
      "name": "Run",
      "values": [
        {
          "name": "SecurityHealth",
          "type": "REG_EXPAND_SZ",
          "data": "%windir%\\system32\\SecurityHealthSystray.exe"
        }
      ]
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_registry_keys", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "path": "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
})
```

## Registry Path Format

- `HKLM` = HKEY_LOCAL_MACHINE
- `HKCU` = HKEY_CURRENT_USER
- `HKCR` = HKEY_CLASSES_ROOT
- `HKU` = HKEY_USERS

## Notes

- Windows-only operation
- Live operation (up to 10 min timeout)
- Some keys require elevated privileges (SAM, SECURITY may be inaccessible)
- Common persistence locations: Run keys, Services, Scheduled Tasks
