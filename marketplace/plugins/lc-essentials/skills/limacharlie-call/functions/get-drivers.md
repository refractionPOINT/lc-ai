# get_drivers

Retrieve installed kernel drivers/modules from a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "drivers": [
    {
      "name": "ntfs",
      "path": "C:\\Windows\\system32\\drivers\\ntfs.sys",
      "signed": true,
      "signer": "Microsoft Windows"
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_drivers", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation (up to 10 min timeout)
- Kernel modules on Linux, drivers on Windows
- Unsigned drivers may indicate rootkits
- Check for drivers from non-system locations
