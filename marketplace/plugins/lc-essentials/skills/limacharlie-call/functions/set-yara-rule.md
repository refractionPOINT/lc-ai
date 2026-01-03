# set_yara_rule

Create or update a YARA rule for malware detection and file scanning.

**⚠️ PARAMETER NAMES**: Use `rule_name` and `rule_content`, NOT `name` and `content`.

## Recommended Workflow

1. `validate_yara_rule` - Validate syntax first
2. `set_yara_rule` - Deploy validated rule

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | Rule source name |
| rule_content | string | Yes | Valid YARA rule source code |

## Returns

```json
{}
```

Empty response indicates success. Rule is immediately active.

## Example

```
lc_call_tool(tool_name="set_yara_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "ransomware_detection",
  "rule_content": "rule ransomware_behavior {\n  meta:\n    author = \"security-team\"\n  strings:\n    $encrypt = \"CryptEncrypt\" nocase\n    $ransom = \"YOUR FILES HAVE BEEN ENCRYPTED\" nocase\n  condition:\n    $encrypt and $ransom\n}"
})
```

## Notes

- **Always validate syntax first** with `validate_yara_rule`
- Setting replaces existing rule with same name
- Rules are distributed to sensors based on platform/tag filters
- Related: `validate_yara_rule`, `list_yara_rules`, `get_yara_rule`, `delete_yara_rule`
- YARA syntax: https://yara.readthedocs.io/
