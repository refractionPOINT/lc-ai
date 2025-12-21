# yara_scan_process

Scan a process's memory using YARA rules to detect malware patterns.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |
| pid | integer | Yes | Process ID to scan |
| rule | string | Yes | Full YARA rule content |

## Returns

```json
{
  "matches": [
    {
      "rule_name": "CobaltStrike_Beacon",
      "namespace": "malware",
      "tags": ["apt", "c2"],
      "strings": [
        {
          "identifier": "$beacon_config",
          "offset": "0x1000",
          "data": "6D6573736167652E..."
        }
      ],
      "meta": {
        "description": "Detects Cobalt Strike beacon",
        "author": "Threat Intel Team"
      }
    }
  ]
}
```

Empty `matches` array means no detection (clean).

## Example

```
lc_call_tool(tool_name="yara_scan_process", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456",
  "pid": 1234,
  "rule": "rule CobaltStrike { strings: $a = \"beacon\" condition: $a }"
})
```

## Notes

- Live operation (up to 10 min timeout)
- Scans process virtual memory
- Useful for detecting fileless malware
- Validate YARA syntax before submission
- Related: `yara_scan_file`, `yara_scan_directory`, `yara_scan_memory`
