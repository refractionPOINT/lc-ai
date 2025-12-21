# delete_output

Delete an output configuration, immediately stopping data export.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| name | string | Yes | Output name (case-sensitive) |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_output", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "name": "prod-syslog"
})
```

## Notes

- **Deletion is immediate** - data export stops instantly
- Cannot be undone - configuration must be recreated
- Buffered/pending data may be lost
- Output name becomes available for reuse
- To modify an output: delete, then recreate with new settings
- Related: `list_outputs`, `add_output`
