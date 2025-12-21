# is_isolated

Check if a sensor is currently network isolated.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID to check |

## Returns

```json
{
  "is_isolated": true
}
```

## Example

```
lc_call_tool(tool_name="is_isolated", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc12345-6789-0123-4567-890abcdef012"
})
```

## Notes

- Read-only check, does not modify sensor state
- Can check even if sensor is offline
- Related: `isolate_network`, `rejoin_network`
