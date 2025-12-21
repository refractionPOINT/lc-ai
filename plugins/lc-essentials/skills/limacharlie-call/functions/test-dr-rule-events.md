# test_dr_rule_events

Test D&R rules against inline events (unit testing for detections).

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| events | array | Yes | Event objects to test against |
| detect | object | Conditional | Detection component (required if `rule_name` not provided) |
| rule_name | string | Conditional | Existing rule name (required if `detect` not provided) |
| respond | array | No | Response actions (defaults to single report action) |
| namespace | string | No | Rule namespace: general, managed, service (default: general) |
| trace | boolean | No | Enable debug tracing (default: false) |

## Event Format

```json
{
  "routing": {
    "event_type": "NEW_PROCESS",
    "hostname": "test-host"
  },
  "event": {
    "COMMAND_LINE": "powershell.exe -enc SGVsbG8=",
    "FILE_PATH": "C:\\Windows\\System32\\powershell.exe"
  }
}
```

## Returns

```json
{
  "matched": true,
  "stats": {
    "events_processed": 1,
    "events_matched": 1
  },
  "results": [
    {"action": "report", "data": {"name": "encoded_powershell"}}
  ],
  "traces": [...]
}
```

## Example

```
lc_call_tool(tool_name="test_dr_rule_events", parameters={
  "oid": "c7e8f940-...",
  "detect": {
    "event": "NEW_PROCESS",
    "op": "contains",
    "path": "event/COMMAND_LINE",
    "value": "-enc"
  },
  "events": [
    {
      "routing": {"event_type": "NEW_PROCESS"},
      "event": {
        "COMMAND_LINE": "powershell.exe -enc SGVsbG8=",
        "FILE_PATH": "C:\\Windows\\System32\\powershell.exe"
      }
    }
  ],
  "trace": true
})
```

## Notes

- **Unit testing** for detection rules - fast iteration without live events
- Free testing (no cost for inline events)
- Enable `trace` to debug why rules match/don't match
- Events must have `routing.event_type` field
- No side effects - response actions are simulated
- Related: `replay_dr_rule`, `validate_dr_rule_components`
