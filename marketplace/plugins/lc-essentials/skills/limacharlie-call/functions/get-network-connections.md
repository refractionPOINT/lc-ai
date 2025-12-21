# get_network_connections

Retrieve real-time network connections from a sensor showing all active and listening connections.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID (must be online) |

## Returns

```json
{
  "connections": [
    {
      "state": "ESTABLISHED",
      "local_address": "192.168.1.100",
      "local_port": 54321,
      "remote_address": "203.0.113.50",
      "remote_port": 443,
      "pid": 1234,
      "process_name": "chrome.exe",
      "protocol": "TCP"
    }
  ]
}
```

## Example

```
lc_call_tool(tool_name="get_network_connections", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc-123-def-456"
})
```

## Notes

- Live operation requiring active sensor connection (30s timeout)
- States: ESTABLISHED, LISTENING, TIME_WAIT, etc.
- Listening on 0.0.0.0 means all interfaces
- Correlate PIDs with `get_processes` for full context
- Unusual high ports or foreign IPs warrant investigation
