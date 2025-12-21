# remove_tag

Remove a tag from a sensor.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID |
| tag | string | Yes | Tag name to remove (case-sensitive) |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="remove_tag", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc12345-6789-0123-4567-890abcdef012",
  "tag": "compromised"
})
```

## Notes

- Tags are case-sensitive
- Immediate effect on D&R rules using this tag
- No error if tag doesn't exist
- Related: `add_tag`
