# binlib_get_hash_metadata

Get detailed binary metadata for SHA256 hash(es) including PE information, code signing certificates, import hash, TLSH fuzzy hash, and organization-specific tags.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| hash | string | One of hash or hashes | Single SHA256 hash to get metadata for |
| hashes | string[] | One of hash or hashes | Array of SHA256 hashes to get metadata for |

## Returns

```json
{
  "results": {
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": {
      "found": true,
      "tags": ["trusted", "microsoft"],
      "metadata": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "size": 1048576,
        "type": "pe",
        "imp_hash": "d4c8e739a0e5d3b5c9f2e1a4b3c2d1e0",
        "tlsh_hash": "T1E3D1234567890ABCDEF...",
        "res_company_name": "Microsoft Corporation",
        "res_file_description": "Windows System File",
        "res_product_name": "Microsoft Windows",
        "res_product_version": "10.0.19041.1",
        "sig_authentihash": "abc123...",
        "signatures": [
          {
            "sig_issuer": "Microsoft Code Signing PCA 2011",
            "sig_subject": "Microsoft Corporation",
            "sig_serial": "330000012345..."
          }
        ]
      }
    }
  }
}
```

## Example

```
lc_call_tool(tool_name="binlib_get_hash_metadata", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
})
```

## Notes

- **Prerequisite**: The `ext-binlib` extension must be subscribed in the organization
- Metadata is extracted when binaries are first acquired from endpoints
- **File types**: `pe` (Windows), `elf` (Linux), `macho` (macOS)
- **PE-specific fields**: `imp_hash` (import hash), `res_*` (version resources), `signatures` (code signing)
- **TLSH**: Fuzzy hash useful for finding similar binaries
- Use `binlib_search` to find binaries by metadata fields
- Use `binlib_check_hash` for a lightweight existence check without full metadata
