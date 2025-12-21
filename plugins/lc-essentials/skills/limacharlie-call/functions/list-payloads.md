# list_payloads

List all payloads (executables/scripts) available for deployment to sensors.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "payloads": {
    "cleanup-tool.exe": {
      "name": "cleanup-tool.exe",
      "oid": "c7e8f940-...",
      "size": 1048576,
      "by": "admin@company.com",
      "created": 1705000000
    },
    "collect-artifacts.ps1": {
      "name": "collect-artifacts.ps1",
      "oid": "c7e8f940-...",
      "size": 4096,
      "by": "security@company.com",
      "created": 1705100000
    }
  },
  "count": 2
}
```

Empty `{}` in `payloads` means no payloads configured.

## Example

```
lc_call_tool(tool_name="list_payloads", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Payloads are executables or scripts deployed via the `run` command
- File extension in name determines execution type (`.ps1`, `.bat`, `.exe`, `.sh`)
- Use `create_payload` to upload new payloads
- Requires `payload.ctrl` permission
- Related: `create_payload`, `get_payload`, `delete_payload`
