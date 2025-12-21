# rejoin_network

Remove network isolation from a sensor, restoring normal network connectivity.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID to rejoin |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="rejoin_network", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc12345-6789-0123-4567-890abcdef012"
})
```

## Notes

- Restores full network connectivity immediately
- Use after investigation/remediation is complete
- Verify threat is contained before rejoining
- Related: `isolate_network`, `is_isolated`
