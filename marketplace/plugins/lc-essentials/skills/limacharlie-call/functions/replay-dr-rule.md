# replay_dr_rule

Test a D&R rule against historical sensor data to validate detection logic on real telemetry.

## CRITICAL: Calculating Timestamps

**❌ NEVER calculate epoch values manually** - LLMs produce incorrect timestamps (e.g., 2024 instead of 2025).

**✅ ALWAYS use bash for `start_time`/`end_time`:**
```bash
# Last 7 days
start=$(date -d '7 days ago' +%s)
end=$(date +%s)

# Last 1 hour
start=$(date -d '1 hour ago' +%s)
end=$(date +%s)
```

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| detect | object | Conditional | Detection logic (required if no `rule_name`) |
| rule_name | string | Conditional | Name of existing rule (required if no `detect`) |
| last_seconds | integer | Conditional | Replay last N seconds (required if no start/end) |
| start_time | integer | Conditional | Epoch seconds (required with end_time) |
| end_time | integer | Conditional | Epoch seconds (required with start_time) |
| namespace | string | No | 'general', 'managed', 'service' (default: 'general') |
| respond | array | No | Response actions (default: report) |
| sid | UUID | No | Specific sensor ID |
| selector | string | No | Bexpr sensor selector (e.g., `plat == "windows"`) |
| limit_event | integer | No | Max events (default: 10000) |
| dry_run | boolean | No | Cost estimate only (default: false) |
| trace | boolean | No | Enable debug tracing (default: false) |
| stream | string | No | 'event', 'audit', 'detect' (default: 'event') |

## Returns

```json
{
  "matched": true,
  "stats": {
    "events_processed": 50000,
    "events_matched": 127,
    "billed_events": 50000,
    "wall_time": 3500
  },
  "is_dry_run": false,
  "results": [{"action": "report", "data": {...}}]
}
```

## Example

```
lc_call_tool(tool_name="replay_dr_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "detect": {
    "event": "NEW_PROCESS",
    "op": "contains",
    "path": "event/COMMAND_LINE",
    "value": "-enc"
  },
  "last_seconds": 3600,
  "selector": "plat == \"windows\""
})
```

## Notes

- Tests against real historical data from your environment
- Use `dry_run: true` to estimate cost before full replay
- Response actions are simulated, not executed
- Start with small time windows, expand once rule is tuned
- Related: `validate_dr_rule_components`, `set_dr_general_rule`
