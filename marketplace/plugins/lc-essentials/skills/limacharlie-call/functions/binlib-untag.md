# binlib_untag

Remove tags from binary hash(es) in the organization's binary library.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| hash | string | One of hash or hashes | Single SHA256 hash to untag |
| hashes | string[] | One of hash or hashes | Array of SHA256 hashes to untag |
| tag | string | One of tag or tags | Single tag to remove |
| tags | string[] | One of tag or tags | Array of tags to remove |

## Returns

```json
{}
```

## Example

```
lc_call_tool(tool_name="binlib_untag", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "tag": "false-positive"
})
```

## Notes

- **Prerequisite**: The `ext-binlib` extension must be subscribed in the organization
- Removing a non-existent tag is idempotent (no error)
- Tags are organization-specific
- Related: `binlib_tag` to add tags
