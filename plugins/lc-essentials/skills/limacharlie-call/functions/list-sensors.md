# list_sensors

List all sensors with powerful server-side filtering using bexpr selector syntax.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| selector | string | No | Bexpr filter expression (see below) |
| online_only | boolean | No | Return only online sensors |

## Returns

```json
{
  "sensors": [
    {
      "sid": "sensor-id-1",
      "hostname": "SERVER01",
      "platform": "windows",
      "last_seen": "2024-01-20T14:22:13Z",
      "internal_ip": "10.0.1.50",
      "external_ip": "203.0.113.45"
    }
  ],
  "count": 1
}
```

## Example

```
lc_call_tool(tool_name="list_sensors", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "selector": "plat == `windows` and hostname matches `^prod-`",
  "online_only": true
})
```

## Selector Syntax (Bexpr)

**Fields:** `sid`, `oid`, `iid`, `plat`, `arch`, `hostname`, `int_ip`, `ext_ip`, `alive`, `tags`

**Operators:**
- `==`, `!=`, `>`, `<`, `>=`, `<=` - comparison
- `matches` - regex pattern (e.g., `hostname matches "^web-"`)
- `contains` - substring
- `in` - membership (e.g., `"critical" in tags`)
- `and`, `or`, `not` - logical

**Common patterns:**
```
plat == `windows`                              # Platform filter
hostname matches `^prod-`                      # Hostname regex
`critical` in tags                             # Tag filter
plat == `linux` and hostname matches `^web-`   # Combined
iid == `a1b2c3d4-e5f6-...`                     # Installation key ID filter
```

Note: String literals use backticks in bexpr.

## Notes

- Both `selector` and `online_only` are server-side filters (efficient for large fleets)
- Pagination handled internally - all matching sensors returned
- For individual sensor details, use `get_sensor_info`
