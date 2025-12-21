# get_online_sensors

Retrieve all sensors currently online and connected to the LimaCharlie platform.

**⚠️ IMPORTANT:** This function returns only sensor IDs with **no filtering capability**. To find sensors by platform, hostname, tags, or other attributes, use `list_sensors` with a `selector` instead.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "sensors": ["sensor-id-1", "sensor-id-2", "sensor-id-3"],
  "count": 3
}
```

Returns an object with:
- `sensors`: Array of online sensor IDs (no metadata, no filtering)
- `count`: Number of online sensors

## Example

```
lc_call_tool(tool_name="get_online_sensors", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## When to Use This vs list_sensors

| Use Case | Recommended Function |
|----------|---------------------|
| Quick count of online sensors | `get_online_sensors` |
| Find online Windows sensors | `list_sensors` with `selector: "plat == windows"`, `online_only: true` |
| Find online sensors by hostname | `list_sensors` with `selector: "hostname contains \"web\""`, `online_only: true` |
| Find online sensors with a tag | `list_sensors` with `selector: "\"prod\" in tags"`, `online_only: true` |
| Get sensor details (hostname, IP, etc.) | `list_sensors` with `online_only: true` |

**Anti-pattern:** Do NOT call `get_online_sensors` and then loop through with `get_sensor_info` to find sensors by platform. Use `list_sensors` with a selector instead—it's a single API call.

## Notes

- Returns only SIDs—no hostnames, platforms, or other metadata
- Cannot filter by platform, tags, or other attributes
- For individual sensor status check, use `is_online`
- For filtered/detailed results, use `list_sensors` with `selector` and `online_only: true`
