# binlib_tag

Add tags to binary hash(es) in the organization's binary library. Tags are useful for categorization, workflow tracking, and searching.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| hash | string | One of hash or hashes | Single SHA256 hash to tag |
| hashes | string[] | One of hash or hashes | Array of SHA256 hashes to tag |
| tag | string | One of tag or tags | Single tag to add |
| tags | string[] | One of tag or tags | Array of tags to add |

## Returns

```json
{}
```

## Examples

### Add single tag to single hash

```
lc_call_tool(tool_name="binlib_tag", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "tag": "malware"
})
```

### Add multiple tags to multiple hashes

```
lc_call_tool(tool_name="binlib_tag", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hashes": ["abc123...", "def456..."],
  "tags": ["malware", "ransomware", "analyzed"]
})
```

## Notes

- **Prerequisite**: The `ext-binlib` extension must be subscribed in the organization
- Tags are organization-specific; other orgs cannot see your tags
- Adding an existing tag to a hash is idempotent (no error)
- Use tags for: malware classification, analysis status, threat campaigns
- Use `binlib_search` with `tag` column to find binaries by tag
- Related: `binlib_untag` to remove tags
