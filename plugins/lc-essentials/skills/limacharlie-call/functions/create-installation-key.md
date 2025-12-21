# create_installation_key

Create a new installation key for deploying sensors with automatic tag assignment.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| description | string | Yes | Human-readable description |
| tags | array | Yes | Tags to automatically apply to sensors using this key |

## Returns

```json
{
  "iid": "prod-win-server-key",
  "key": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
  "json_key": "{\"oid\":\"...\",\"iid\":\"...\",\"key\":\"...\"}"
}
```

## Example

```
lc_call_tool(tool_name="create_installation_key", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "description": "Production Windows Servers",
  "tags": ["production", "windows", "server"]
})
```

## Notes

- **Save the key securely** - needed for sensor deployment
- Tags are automatically applied to sensors during enrollment
- Use descriptive tags for organization (environment, OS, location, team)
- Consider separate keys for production vs. development
- Related: `list_installation_keys`, `delete_installation_key`
