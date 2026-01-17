# remove_org_user

Remove a user from an organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| email | string | Yes | User's email address to remove |

## Returns

```json
{
  "success": true
}
```

## Example

```
lc_call_tool(tool_name="remove_org_user", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "email": "former.employee@example.com"
})
```

## Notes

- Only Owners and Administrators can remove users
- Cannot remove the last Owner from an organization
- Users with access via groups will retain access through those groups
- Related: `list_org_users`, `add_org_user`
