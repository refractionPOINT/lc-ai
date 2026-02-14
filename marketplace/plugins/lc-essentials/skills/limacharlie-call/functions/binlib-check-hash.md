# binlib_check_hash

Check if SHA256 hash(es) have been seen in the organization's binary library.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| hash | string | One of hash or hashes | Single SHA256 hash to check |
| hashes | string[] | One of hash or hashes | Array of SHA256 hashes to check |

## Returns

```json
{
  "results": {
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": {
      "found": true,
      "tags": ["analyzed", "trusted"]
    },
    "a1b2c3d4e5f6...": {
      "found": false
    }
  }
}
```

## Examples

### Check single hash

```
lc_call_tool(tool_name="binlib_check_hash", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
})
```

### Check multiple hashes

```
lc_call_tool(tool_name="binlib_check_hash", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hashes": [
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890"
  ]
})
```

## Notes

- **Prerequisite**: The `ext-binlib` extension must be subscribed in the organization
- Returns `found: true` only if the binary has been seen by this organization
- Tags attached to binaries are included in the response
- Use `binlib_get_hash_metadata` for detailed binary analysis (PE info, signatures)
- Related: `binlib_search` to find binaries by metadata criteria
