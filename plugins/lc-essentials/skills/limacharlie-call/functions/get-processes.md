# get_processes

Retrieve real-time process list from a sensor showing all running processes.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "processes": [
    {
      "pid": 1234,
      "ppid": 1000,
      "name": "chrome.exe",
      "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "cmdline": "chrome.exe --type=renderer",
      "user": "SYSTEM",
      "threads": 15,
      "memory": 204800000
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_processes", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation requiring active sensor connection (30s timeout)
- Point-in-time snapshot - processes may start/stop quickly
- Use `ppid` to understand process relationships
- Command line args often reveal malicious intent
- Related: `get_process_modules`, `get_process_strings`
