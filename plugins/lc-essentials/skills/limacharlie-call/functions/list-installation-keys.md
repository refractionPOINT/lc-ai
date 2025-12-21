# list_installation_keys

List all installation keys for sensor deployment.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "c7e8f940-...": {
    "prod-windows-key": {
      "iid": "prod-windows-key",
      "desc": "Production Windows Servers",
      "tags": "production,windows,server",
      "key": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
      "created": 1704067200,
      "use_public_root_ca": false
    },
    "dev-linux-key": {
      "iid": "dev-linux-key",
      "desc": "Development Linux Workstations",
      "tags": "development,linux,workstation",
      "key": "wxyz9876-5432-10ab-cdef-ghijklmnopqr",
      "created": 1704153600
    }
  }
}
```

## Example

```
lc_call_tool(tool_name="list_installation_keys", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Key Properties

| Field | Description |
|-------|-------------|
| iid | Installation key ID |
| desc | Human-readable description |
| tags | Comma-separated tags applied to enrolled sensors |
| key | Actual key value for deployment |
| created | Unix timestamp |

## Notes

- Installation keys are sensitive credentials
- Tags in a key are automatically applied to sensors during enrollment
- Multiple sensors can use the same key
- Related: `create_installation_key`, `delete_installation_key`
