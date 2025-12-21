# get_process_modules

Retrieve loaded modules (DLLs, shared libraries) for a specific process.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| pid | integer | Yes | Process ID to inspect |

## Returns

```json
{
  "modules": [
    {
      "name": "kernel32.dll",
      "path": "C:\\Windows\\System32\\kernel32.dll",
      "base_address": "0x7FF800000000",
      "size": 1048576,
      "signed": true,
      "signer": "Microsoft Corporation"
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_process_modules", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "pid": 1234
})
```

## Notes

- Live operation (up to 10 min timeout)
- Windows: DLLs; Linux: .so files; macOS: .dylib files
- Unsigned modules on Windows are suspicious
- Modules from temp/user directories warrant investigation
- Detects DLL injection when modules come from unusual paths
