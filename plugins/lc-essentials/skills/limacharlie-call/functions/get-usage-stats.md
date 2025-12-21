# get_usage_stats

Retrieve usage statistics and metrics for an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "sensors": {
    "total": 1500,
    "online": 1420,
    "by_platform": {
      "windows": 800,
      "linux": 500,
      "macos": 200
    }
  },
  "data_ingestion": {
    "events_per_day": 50000000,
    "bytes_per_day": 15000000000
  },
  "api_requests": {
    "per_day": 100000
  },
  "retention_days": 30
}
```

## Example

```
lc_call_tool(tool_name="get_usage_stats", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Metrics typically updated hourly/daily
- Useful for capacity planning and cost optimization
- High data volumes may indicate need for event filtering
- Sudden usage spikes may indicate issues or attacks
