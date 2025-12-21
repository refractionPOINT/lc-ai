# isolate_network

Isolate a sensor from the network, blocking all traffic except LimaCharlie communication.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID to isolate |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="isolate_network", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc12345-6789-0123-4567-890abcdef012"
})
```

## Notes

- Critical incident response action for threat containment
- Blocks all network except LimaCharlie C2 traffic
- Sensor remains manageable for investigation
- Persists until explicitly removed with `rejoin_network`
- Check status with `is_isolated`
