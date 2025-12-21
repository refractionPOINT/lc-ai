# get_org_oid_by_name

Efficiently convert an organization name to its Organization ID (OID) using cached lookups.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | The organization name to look up |
| exact_match | boolean | No | If true (default), exact case-sensitive match. If false, case-insensitive match. |

## Returns

```json
{
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "name": "Production Environment",
  "found": true
}
```

If not found:
```json
{
  "found": false,
  "error": "organization not found: MyOrg"
}
```

## Example

```
lc_call_tool(tool_name="get_org_oid_by_name", parameters={
  "name": "Production Environment"
})
```

Case-insensitive lookup:
```
lc_call_tool(tool_name="get_org_oid_by_name", parameters={
  "name": "production environment",
  "exact_match": false
})
```

## Notes

- **Does not require an organization ID** - user-level operation
- **Preferred for single org lookups** - more efficient than `list_user_orgs` when you only need one OID
- Uses server-side caching for fast repeated lookups (5-minute TTL)
- For listing all orgs or multiple lookups, use `list_user_orgs` instead
- OIDs are permanent unique identifiers (org names can change)
