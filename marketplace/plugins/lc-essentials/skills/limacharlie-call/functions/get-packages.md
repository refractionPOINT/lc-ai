# get_packages

Retrieve installed software packages from a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "packages": [
    {
      "name": "openssh-server",
      "version": "8.9p1-3ubuntu0.1",
      "architecture": "amd64"
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_packages", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation (up to 10 min timeout)
- Linux: RPM/DEB packages; Windows: installed programs; macOS: applications
- Cross-reference with vulnerability databases
- Useful for software inventory and patch assessment
