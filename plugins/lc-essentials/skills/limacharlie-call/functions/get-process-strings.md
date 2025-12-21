# get_process_strings

Extract all readable strings from a process's memory space.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| pid | integer | Yes | Process ID to extract strings from |

## Returns

```json
{
  "strings": [
    "http://malicious-c2.com/callback",
    "C:\\Windows\\System32\\cmd.exe",
    "password123",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_process_strings", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "pid": 1234
})
```

## Notes

- Live operation (up to 10 min timeout, slow for large processes)
- Returns ASCII and Unicode strings (4+ chars)
- Can reveal: URLs, IPs, credentials, file paths, C2 addresses
- Output can be very large (thousands of strings)
- For targeted search, use `find_strings` instead
