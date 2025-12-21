# yara_scan_file

Scan a file on disk using YARA rules to detect malware patterns.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| file_path | string | Yes | Full path to file |
| rule | string | Yes | Full YARA rule content |

## Returns

```json
{
  "matches": [
    {
      "rule_name": "Ransomware_Wannacry",
      "tags": ["ransomware"],
      "strings": [
        {
          "identifier": "$ransom_note",
          "offset": "0x2000",
          "data": "596F75722066696C6573..."
        }
      ]
    }
  ],
  "file_path": "C:\\Temp\\suspicious.exe",
  "file_size": 1048576,
  "file_hash": "d41d8cd98f00b204e9800998ecf8427e"
}
```

Empty `matches` array means file is clean.

## Example

```
lc_call_tool(tool_name="yara_scan_file", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "file_path": "C:\\Temp\\suspicious.exe",
  "rule": "rule Malware { strings: $a = \"malicious\" condition: $a }"
})
```

## Notes

- Live operation (up to 10 min timeout)
- File must be readable (not locked)
- Faster than process memory scanning
- File hash provided for threat intel correlation
- Related: `yara_scan_process`, `yara_scan_directory`
