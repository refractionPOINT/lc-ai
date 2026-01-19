# get_sensor_info

Retrieve detailed information about a specific sensor including metadata, network info, and status.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID |

## Returns

```json
{
  "info": {
    "sid": "xyz-sensor-id",
    "oid": "c7e8f940-...",
    "hostname": "SERVER01",
    "platform": 268435456,
    "arch": 1,
    "enroll": "2024-01-15T10:30:00Z",
    "alive": "2024-01-20T14:22:13Z",
    "int_ip": "10.0.1.50",
    "ext_ip": "203.0.113.45",
    "iid": "install-key-123",
    "isolated": false,
    "kernel": true
  },
  "is_online": true
}
```

## Example

```
lc_call_tool(tool_name="get_sensor_info", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "xyz-sensor-id"
})
```

## Notes

- Platform codes: See [CONSTANTS.md](../../../CONSTANTS.md) for authoritative values
  - Windows=268435456, Linux=536870912, macOS=805306368
- Architecture codes: x86=1, x64=2, ARM=3, ARM64=4
- `alive` timestamp shows last check-in time
- `iid` is the installation key used to enroll the sensor
