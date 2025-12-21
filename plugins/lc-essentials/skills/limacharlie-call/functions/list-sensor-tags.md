# list_sensor_tags

List all tags currently in use by sensors in the organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "tags": [
    "production",
    "windows-server",
    "web-tier",
    "pci-scope",
    "dev-team"
  ],
  "count": 5
}
```

Empty `[]` in `tags` means no tags are in use.

## Example

```
lc_call_tool(tool_name="list_sensor_tags", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Returns unique tag names across all sensors
- Tags are assigned to sensors using `add_tag`
- Use with `list_sensors` selector `'\`tagname\` in tags'` to find sensors by tag
- Useful for discovering tag taxonomy before filtering
- Related: `add_tag`, `remove_tag`, `list_sensors`
