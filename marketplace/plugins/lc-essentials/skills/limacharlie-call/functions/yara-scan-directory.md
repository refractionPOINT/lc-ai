# yara_scan_directory

Recursively scan a directory using YARA rules to detect malware across multiple files.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| directory | string | Yes | Directory path to scan |
| rule | string | Yes | Full YARA rule content |
| file_pattern | string | No | File pattern (e.g., "*.exe") |
| depth | integer | No | Recursion depth (default=5) |

## Returns

```json
{
  "matches": [
    {
      "file_path": "C:\\Temp\\malware.exe",
      "rule_name": "Ransomware_Generic",
      "strings": [{"identifier": "$ransom", "offset": "0x1000"}]
    }
  ],
  "scanned_files": 156,
  "matched_files": 1
}
```

## Example

```
lc_call_tool(tool_name="yara_scan_directory", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "directory": "C:\\Users\\Downloads",
  "rule": "rule Malware { strings: $a = \"malicious\" condition: $a }",
  "file_pattern": "*.exe",
  "depth": 3
})
```

## Notes

- Live operation (up to 10 min timeout, may be longer for large directories)
- Use file_pattern to focus on specific types (*.exe, *.dll, *.ps1)
- Large directories with deep recursion may timeout
- Related: `yara_scan_file`, `yara_scan_process`
