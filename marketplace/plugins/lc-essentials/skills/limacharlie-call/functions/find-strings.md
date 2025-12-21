# find_strings

Search for specific strings across all process memory on a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| strings | string | Yes | Comma-separated strings to find |

## Returns

```json
{
  "matches": [
    {
      "pid": 1234,
      "process_name": "malware.exe",
      "found_strings": ["password123", "api-key-secret"],
      "count": 2
    }
  ],
  "searched_processes": 45,
  "matching_processes": 1
}
```

## Example

```
lc_call_tool(tool_name="find_strings", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "strings": "password,credential,secret"
})
```

## Notes

- Live operation (up to 10 min timeout)
- More efficient than `get_process_strings` for targeted searches
- Case-sensitive, searches for substrings
- Great for hunting IOCs, credentials, C2 domains in memory
- Related: `get_process_strings` for full string extraction
