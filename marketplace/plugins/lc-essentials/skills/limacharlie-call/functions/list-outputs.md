# list_outputs

Retrieve all configured outputs (data export destinations) for an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "prod-syslog": {
    "name": "prod-syslog",
    "module": "syslog",
    "for": "event",
    "dest_host": "10.0.1.50",
    "dest_port": "514",
    "is_tls": "true"
  },
  "s3-archive": {
    "name": "s3-archive",
    "module": "s3",
    "for": "event",
    "bucket": "lc-events-archive"
  }
}
```

## Example

```
lc_call_tool(tool_name="list_outputs", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Output Modules

`syslog`, `s3`, `webhook`, `slack`, `gcs`, `elastic`, `kafka`, `splunk`

## Data Types (`for` field)

`event`, `detect`, `audit`, `deployment`, `artifact`

## Notes

- Secret values appear as `[secret:name]` in config
- Multiple outputs can send the same data type
- Outputs can filter by tags, sensors, event types
- Related: `add_output`, `delete_output`
