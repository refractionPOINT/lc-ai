# delete_payload

Delete a payload from the organization, preventing future deployment.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| name | string | Yes | Payload name (case-sensitive) |

## Returns

```json
{
  "success": true,
  "message": "Successfully deleted payload 'cleanup-tool.exe'"
}
```

## Example

```
lc_call_tool(tool_name="delete_payload", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "name": "cleanup-tool.exe"
})
```

## Notes

- **Deletion is permanent** - cannot be undone
- Payload can no longer be deployed to sensors
- **Does not affect sensors** where payload was previously run
- Use `get_payload` to backup before deleting if needed
- Payload name becomes available for reuse
- Requires `payload.ctrl` permission
- Related: `list_payloads`, `create_payload`, `get_payload`
