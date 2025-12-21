# get_detection

Retrieve details about a single, specific detection by its ID.

**Note:** Use this when you have a specific detection ID. For searching by time range, use `get_historic_detections` instead.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| detection_id | string | Yes | Detection ID (UUID/atom) |

## Returns

```json
{
  "detection": {
    "detect_id": "detect-uuid-123",
    "cat": "suspicious_process",
    "detect": {
      "event": {
        "COMMAND_LINE": "powershell.exe -encodedCommand ...",
        "FILE_PATH": "C:\\Windows\\System32\\..."
      },
      "routing": {
        "sid": "xyz-sensor-123",
        "hostname": "SERVER01"
      }
    },
    "detect_mtd": {
      "rule_name": "Encoded PowerShell",
      "severity": 8,
      "tags": ["mitre:T1059.001"]
    }
  }
}
```

## Example

```
lc_call_tool(tool_name="get_detection", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "detection_id": "detect-uuid-123-456"
})
```

## get_detection vs get_historic_detections

| Feature | get_detection | get_historic_detections |
|---------|---------------|-------------------------|
| Purpose | Get ONE by ID | Search by time range |
| Params | detection_id | start, end (timestamps) |
| Returns | Single object | Array |

## Notes

- Detection IDs also called "detect_id" or "atom"
- `detect_mtd` includes MITRE mappings if configured
- Severity typically ranges 1-10
