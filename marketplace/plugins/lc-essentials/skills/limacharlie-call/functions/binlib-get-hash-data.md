# binlib_get_hash_data

Get signed URLs to download binary files by SHA256 hash(es). Used for malware analysis, reverse engineering, or forensic examination.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| hash | string | One of hash or hashes | Single SHA256 hash to get download URL for |
| hashes | string[] | One of hash or hashes | Array of SHA256 hashes to get download URLs for |

## Returns

```json
{
  "results": {
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": {
      "found": true,
      "download_url": "https://storage.googleapis.com/lc-library-bin/b_e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855?X-Goog-Signature=..."
    },
    "a1b2c3d4e5f6...": {
      "found": false
    }
  }
}
```

## Example

```
lc_call_tool(tool_name="binlib_get_hash_data", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
})
```

## Notes

- **Prerequisite**: The `ext-binlib` extension must be subscribed in the organization
- **Access restriction**: Only users with approved email domains can download binary files
- Signed URLs are valid for a limited time (typically 10 minutes)
- Downloaded files are gzip-compressed; decompress after download
- Maximum stored file size is 100 MB
- Use for malware analysis, reverse engineering, or forensic examination
