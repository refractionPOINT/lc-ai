# list_user_orgs

Retrieve all LimaCharlie organizations accessible to the authenticated user.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| (none) | - | - | User-level operation, no org ID required |

## Returns

```json
{
  "orgs": [
    {
      "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
      "name": "Production Environment",
      "role": "owner"
    },
    {
      "oid": "c7e8f940-5678-1234-dcba-0987654321ab",
      "name": "Development Environment",
      "role": "admin"
    }
  ],
  "total": 2
}
```

## Example

```
lc_call_tool(tool_name="list_user_orgs", parameters={})
```

## Notes

- **Does not require an organization ID** - user-level operation
- Use this to discover OIDs before calling other functions
- Role levels: owner, admin, user
- OIDs are permanent unique identifiers (org names can change)
- For MSPs: lists all customer organizations
