# add_tag

Add a tag to a sensor for organization, D&R rule targeting, and investigation tracking.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID to tag |
| tag | string | Yes | Tag name (no spaces recommended) |
| ttl | integer | Yes | Time-to-live in seconds (0=permanent) |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="add_tag", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc12345-6789-0123-4567-890abcdef012",
  "tag": "compromised",
  "ttl": 0
})
```

## Notes

- Tags are case-sensitive
- Common TTLs: 3600 (1hr), 86400 (24hr), 604800 (1wk)
- Use in D&R rules: `target: tag=production`
- Adding existing tag updates its TTL
- Related: `remove_tag`
