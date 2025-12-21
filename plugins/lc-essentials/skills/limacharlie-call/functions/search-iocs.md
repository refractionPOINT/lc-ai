# search_iocs

Search for Indicators of Compromise (IOCs) across your organization's data.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| ioc_type | string | Yes | IOC type (see below) |
| ioc_value | string | Yes | Value to search (supports `%` wildcard) |
| info_type | string | Yes | "summary" for counts, "locations" for sensor details |
| case_sensitive | boolean | No | Default: false |

## IOC Types

`file_hash`, `domain`, `ip`, `file_path`, `file_name`, `user`, `service_name`, `package_name`, `hostname`

## Returns

**Summary:**
```json
{
  "type": "file_hash",
  "name": "abc123...",
  "last_1_days": 5,
  "last_7_days": 23,
  "last_30_days": 45
}
```

**Locations:**
```json
{
  "locations": {
    "sensor-1": {
      "hostname": "SERVER01",
      "first_ts": 1705761234,
      "last_ts": 1705847634
    }
  }
}
```

## Example

```
lc_call_tool(tool_name="search_iocs", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "ioc_type": "file_hash",
  "ioc_value": "abc123def456...",
  "info_type": "summary"
})
```

## Notes

- Use `%` wildcard for partial matches (e.g., `%malware%.exe`)
- Summary is cached for performance
- Use `batch_search_iocs` for multiple IOCs at once
