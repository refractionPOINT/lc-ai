# is_online

Check if a specific sensor is currently online and responsive.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID to check |

## Returns

```json
{
  "sid-value": true
}
```

Returns a map with the sensor ID as key and boolean online status as value.

## Example

```
lc_call_tool(tool_name="is_online", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "xyz-sensor-id"
})
```

## Notes

- Quick lightweight check before sending live commands
- For bulk checking, use `get_online_sensors` instead
- For full sensor details including last seen time, use `get_sensor_info`
