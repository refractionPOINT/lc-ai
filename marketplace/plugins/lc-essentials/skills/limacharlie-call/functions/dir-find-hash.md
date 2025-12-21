# dir_find_hash

Search for files matching specific SHA256 hashes within a directory tree.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| root_dir | string | Yes | Directory to search |
| file_expression | string | Yes | File pattern with wildcards |
| hashes | array | Yes | SHA256 hashes to find (64 hex chars each) |
| depth | integer | No | Recursion depth (default=1) |

## Returns

```json
{
  "matches": [
    {
      "path": "C:\\Temp\\malware.exe",
      "hash": "d41d8cd98f00b204e9800998ecf8427e...",
      "size": 1048576,
      "modified": "2024-01-15T10:30:00Z"
    }
  ],
  "scanned_files": 450,
  "matched_files": 1
}
```

## Example

```
lc_call_tool(tool_name="dir_find_hash", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "root_dir": "C:\\Users",
  "file_expression": "*.*",
  "hashes": ["d41d8cd98f00b204e9800998ecf8427e..."],
  "depth": 5
})
```

## Notes

- Live operation (up to 10 min timeout)
- Ideal for IOC hunting from threat intelligence
- SHA256 hashes only (64 hex characters)
- Empty result means system clean for those hashes
- Focus on high-risk directories: Downloads, Temp, AppData
