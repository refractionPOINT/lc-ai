# list_api_keys

List all API keys with their metadata and permissions.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "api_keys": {
    "a1b2c3d4e5f6": {
      "created": 1609459200,
      "priv": [],
      "key_name": "Main API Key"
    },
    "f6e5d4c3b2a1": {
      "created": 1640995200,
      "priv": ["sensor.get", "sensor.list"],
      "key_name": "Read-only Key"
    }
  }
}
```

## Example

```
lc_call_tool(tool_name="list_api_keys", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Key Properties

| Field | Description |
|-------|-------------|
| key_hash | Identifier for key management (not the actual key) |
| created | Unix timestamp |
| priv | Permissions array (empty = full access) |
| key_name | Description |

## Notes

- Actual API key values are never returned (security)
- Empty `priv` array means full organization access (high privilege)
- Key hashes are used for `delete_api_key` calls
- Related: `create_api_key`, `delete_api_key`
