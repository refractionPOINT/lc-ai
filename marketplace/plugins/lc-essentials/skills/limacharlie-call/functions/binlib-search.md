# binlib_search

Search binaries in the organization's library by metadata criteria. Supports multiple search columns and operators for finding binaries by size, type, signatures, resources, and tags.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| criteria | string | Yes | JSON array of search criteria (see format below) |
| limit | number | No | Maximum results to return (default: 1000) |

### Criteria Format

JSON array where each object has:
- `column`: Field to search (see Searchable Columns)
- `operator`: Comparison operator (see Operators)
- `value`: Value to match

### Searchable Columns

| Column | Type | Description |
|--------|------|-------------|
| sha256 | string | SHA256 hash |
| size | integer | File size in bytes |
| type | string | File type: `pe`, `elf`, `macho` |
| imp_hash | string | Import hash (PE files) |
| tlsh_hash | string | TLSH fuzzy hash |
| res_company_name | string | PE version resource: CompanyName |
| res_file_description | string | PE version resource: FileDescription |
| res_product_version | string | PE version resource: ProductVersion |
| sig_issuer | string | Code signing certificate issuer |
| sig_subject | string | Code signing certificate subject |
| sig_serial | string | Code signing certificate serial number |
| sig_authentihash | string | PE Authenticode hash |
| tag | string | Organization tag |

### Operators

`=`, `!=`, `LIKE`, `>`, `<`, `>=`, `<=`

**Note**: `LIKE` uses SQL-style wildcards: `%` for any characters, `_` for single character.

## Returns

```json
{
  "results": [
    {
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 1048576,
      "type": "pe",
      "imp_hash": "d4c8e739...",
      "tlsh_hash": "T1E3D123...",
      "res_company_name": "Microsoft Corporation",
      "res_file_description": "Windows System File",
      "res_product_version": "10.0.19041.1",
      "sig_authentihash": "xyz789...",
      "signatures": [
        {
          "sig_issuer": "Microsoft Code Signing PCA 2011",
          "sig_subject": "Microsoft Corporation",
          "sig_serial": "330000012345..."
        }
      ]
    }
  ]
}
```

## Examples

### Find binaries signed by specific issuer

```
lc_call_tool(tool_name="binlib_search", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "criteria": "[{\"column\": \"sig_issuer\", \"operator\": \"LIKE\", \"value\": \"%DigiCert%\"}]"
})
```

### Find large PE files

```
lc_call_tool(tool_name="binlib_search", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "criteria": "[{\"column\": \"type\", \"operator\": \"=\", \"value\": \"pe\"}, {\"column\": \"size\", \"operator\": \">\", \"value\": \"10000000\"}]",
  "limit": 100
})
```

### Find binaries with specific tag

```
lc_call_tool(tool_name="binlib_search", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "criteria": "[{\"column\": \"tag\", \"operator\": \"=\", \"value\": \"malware\"}]"
})
```

### Find binaries by company name

```
lc_call_tool(tool_name="binlib_search", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "criteria": "[{\"column\": \"res_company_name\", \"operator\": \"LIKE\", \"value\": \"%Microsoft%\"}]"
})
```

## Notes

- **Prerequisite**: The `ext-binlib` extension must be subscribed in the organization
- **IMPORTANT**: The `criteria` parameter must be a JSON string, not a raw array
- Multiple criteria are combined with AND logic
- Results are capped at `limit` (default 1000)
- Use `binlib_yara_scan` to scan search results with YARA rules
