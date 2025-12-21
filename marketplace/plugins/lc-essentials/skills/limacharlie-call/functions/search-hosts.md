# search_hosts

Search for sensors using wildcard hostname patterns.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| hostname_expr | string | Yes | Hostname pattern with wildcards |

## Returns

```json
{
  "sensors": [
    {
      "sid": "sensor-1",
      "hostname": "web-server-01",
      "platform": "linux",
      "last_seen": 1705761234,
      "internal_ip": "10.0.1.10"
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="search_hosts", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hostname_expr": "web-*"
})
```

## Wildcard Patterns

- `*` - matches zero or more characters
- `?` - matches exactly one character

**Examples:**
- `web-*` matches "web-01", "web-server", "web-prod-01"
- `*-prod` matches "app-prod", "web-prod"
- `*database*` matches any hostname containing "database"
- `app-??` matches "app-01", "app-db" (exactly 2 chars)

## Notes

- Pattern matching is case-sensitive
- For more complex filtering, use `list_sensors` with selector
