# dir_list

List directory contents with wildcard support and recursive traversal.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| root_dir | string | Yes | Directory path to list |
| file_expression | string | Yes | File pattern with wildcards (`*`, `?`) |
| depth | integer | No | Recursion depth (1=no recursion, default=1) |

## Returns

```json
{
  "files": [
    {
      "path": "C:\\Temp\\file.exe",
      "name": "file.exe",
      "size": 1048576,
      "modified": "2024-01-15T10:30:00Z",
      "is_directory": false
    }
  ],
  "total_files": 15,
  "total_directories": 3
}
```

## Example

```
lc_call_tool(tool_name="dir_list", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "root_dir": "C:\\Temp",
  "file_expression": "*.exe",
  "depth": 2
})
```

## Wildcard Patterns

- `*.*` - All files with extensions
- `*.exe` - All executables
- `file?.txt` - file1.txt, fileA.txt, etc.

## Notes

- Live operation (up to 10 min timeout)
- Large directories with deep recursion may timeout
- Recently created files in temp directories are often suspicious
- Related: `dir_find_hash`
