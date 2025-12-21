# get_yara_rule

Retrieve a specific YARA rule's source content and signatures.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | YARA rule source name (case-sensitive) |

## Returns

```json
{
  "rules": "rule suspicious_pe {\n  meta:\n    author = \"security-team\"\n  strings:\n    $mz = { 4D 5A }\n    $suspicious = \"malware\" nocase\n  condition:\n    $mz at 0 and $suspicious\n}\n"
}
```

## Example

```
lc_call_tool(tool_name="get_yara_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "malware_detection"
})
```

## YARA Rule Structure

```yara
rule rule_name {
  meta:
    author = "..."
    description = "..."
  strings:
    $hex = { 4D 5A 90 }
    $str = "text" nocase
    $regex = /pattern/
  condition:
    $hex or $str
}
```

## Notes

- Rule source can contain multiple YARA rule definitions
- YARA supports hex patterns, text strings, and regular expressions
- Related: `list_yara_rules`, `set_yara_rule`, `delete_yara_rule`, `validate_yara_rule`
