# yara_scan_memory

Scan multiple processes matching a pattern using YARA rules.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| process_expression | string | Yes | Process name pattern (e.g., "powershell.exe", "*chrome*") |
| rule | string | Yes | Full YARA rule content |

## Returns

```json
{
  "matches": [
    {
      "pid": 1234,
      "process_name": "powershell.exe",
      "rule_name": "Fileless_Malware",
      "strings": [{"identifier": "$shellcode", "offset": "0x1000"}]
    }
  ],
  "scanned_processes": 3,
  "matched_processes": 1
}
```

## Example

```
lc_call_tool(tool_name="yara_scan_memory", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "process_expression": "powershell.exe",
  "rule": "rule PS_Malware { strings: $encoded = \"encodedCommand\" condition: $encoded }"
})
```

## Process Expression

- Exact name: `powershell.exe`
- Wildcard: `*chrome*`, `svchost*`

## Notes

- Live operation (up to 10 min timeout)
- More efficient than scanning processes individually
- Great for hunting across process families (all PowerShell, all svchost)
- Related: `yara_scan_process`, `yara_scan_file`
