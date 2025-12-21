# list_yara_rules

List all YARA rules configured for malware detection and file scanning.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "malware_detection": {
    "by": "security@company.com",
    "filters": {
      "tags": ["production"],
      "platforms": ["windows", "linux"]
    },
    "sources": ["malware_sigs"],
    "updated": 1705000000
  },
  "ransomware_signatures": {
    "by": "threat-intel@company.com",
    "filters": {
      "tags": [],
      "platforms": ["windows"]
    },
    "sources": ["ransomware_rules"],
    "updated": 1705000100
  }
}
```

Empty `{}` means no YARA rules configured.

## Example

```
lc_call_tool(tool_name="list_yara_rules", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Each rule source can contain multiple YARA rule definitions
- Platform filters: windows, linux, macos
- Empty filters = rule applies to all sensors
- Tag filters restrict rules to sensors with specific tags
- Related: `get_yara_rule`, `set_yara_rule`, `delete_yara_rule`
