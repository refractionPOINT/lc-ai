# get_payload

Download a payload to a local file path.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| name | string | Yes | Payload name (case-sensitive) |
| file_path | string | Yes | Absolute destination path for download |

## Returns

```json
{
  "success": true,
  "message": "Successfully downloaded payload 'cleanup-tool.exe' to '/tmp/cleanup-tool.exe'",
  "payload_name": "cleanup-tool.exe",
  "file_path": "/tmp/cleanup-tool.exe",
  "size": 1048576
}
```

## Example

```
lc_call_tool(tool_name="get_payload", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "name": "cleanup-tool.exe",
  "file_path": "/tmp/cleanup-tool.exe"
})
```

## Notes

- **Handle payloads securely** - may contain sensitive or executable code
- File is downloaded directly to specified path
- Creates parent directories if they don't exist
- Overwrites destination file if it exists
- Requires `payload.ctrl` permission
- Use for backup before deletion or for local inspection
- Related: `list_payloads`, `create_payload`, `delete_payload`
