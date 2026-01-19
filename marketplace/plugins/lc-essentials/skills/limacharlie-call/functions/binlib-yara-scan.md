# binlib_yara_scan

Scan binaries in the library against YARA rules. Target binaries using search criteria or specific hashes. Provide YARA rules from the organization's yara hive or inline.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| criteria | string | One of criteria or hash/hashes | JSON search criteria to select binaries (same format as `binlib_search`) |
| hash | string | One of criteria or hash/hashes | Single SHA256 hash to scan |
| hashes | string[] | One of criteria or hash/hashes | Array of SHA256 hashes to scan |
| rule_names | string[] | One of rule_names or rules | Array of YARA rule names from org's yara hive |
| rules | string | One of rule_names or rules | Inline YARA rule content |
| tags_on_match | string[] | No | Tags to automatically add to matching binaries |
| limit | number | No | Maximum binaries to scan (default: 1000) |

## Returns

```json
{
  "matches": [
    {
      "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "matching_rules": ["Ransomware_Wannacry", "Packed_Binary"]
    }
  ],
  "num_scanned": 150,
  "num_not_found": 2
}
```

## Examples

### Scan specific hash with inline rule

```
lc_call_tool(tool_name="binlib_yara_scan", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "rules": "rule MalwareDetection { strings: $a = \"malicious\" condition: $a }"
})
```

### Scan with rules from yara hive

```
lc_call_tool(tool_name="binlib_yara_scan", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "hashes": ["abc123...", "def456..."],
  "rule_names": ["ransomware_detection", "packed_binary"]
})
```

### Scan search results and auto-tag matches

```
lc_call_tool(tool_name="binlib_yara_scan", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "criteria": "[{\"column\": \"type\", \"operator\": \"=\", \"value\": \"pe\"}]",
  "rule_names": ["malware_signatures"],
  "tags_on_match": ["yara-match", "needs-review"],
  "limit": 500
})
```

### Scan binaries from specific company

```
lc_call_tool(tool_name="binlib_yara_scan", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "criteria": "[{\"column\": \"res_company_name\", \"operator\": \"LIKE\", \"value\": \"%SuspiciousVendor%\"}]",
  "rules": "rule SuspiciousPattern { strings: $a = { 90 90 90 90 } condition: $a }"
})
```

## Notes

- **Prerequisite**: The `ext-binlib` extension must be subscribed in the organization
- **Rule sources**:
  - `rule_names`: References rules in your org's yara hive (managed via `set_yara_rule`)
  - `rules`: Inline YARA rule content (useful for ad-hoc hunting)
- `tags_on_match` automatically tags matching binaries for follow-up
- Use `binlib_search` first to estimate the number of binaries that will be scanned
- Maximum binary file size for scanning is 100 MB
- Related: `list_yara_rules`, `set_yara_rule` for managing YARA rules in the hive
