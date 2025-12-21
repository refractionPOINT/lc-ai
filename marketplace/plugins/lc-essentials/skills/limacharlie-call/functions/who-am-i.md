# who_am_i

Get the current API identity and permissions for the authenticated user or API key.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "ident": "user@example.com",
  "orgs": ["c7e8f940-1234-5678-abcd-1234567890ab", "d8f9a041-2345-6789-bcde-2345678901bc"],
  "perms": ["sensor.list", "sensor.task", "dr.list"],
  "user_perms": {
    "c7e8f940-1234-5678-abcd-1234567890ab": ["org.get", "sensor.list"]
  }
}
```

## Example

```
lc_call_tool(tool_name="who_am_i", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Returns the identity (`ident`) of the authenticated API key or user
- The `ident` field is useful for identifying which API key/user is making requests
- `orgs` lists all organizations the identity has access to
- `perms` lists global permissions
- `user_perms` lists per-organization permissions (if applicable)
- Read-only operation
