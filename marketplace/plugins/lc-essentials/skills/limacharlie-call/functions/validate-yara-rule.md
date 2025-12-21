# validate_yara_rule

Validate YARA rule syntax using basic client-side checks.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| rule_content | string | Yes | YARA rule source code to validate |

**Note:** No OID required - validation is performed locally.

## Returns

**Valid rule:**
```json
{
  "valid": true,
  "message": "YARA rule passes basic syntax validation"
}
```

**Invalid rule:**
```json
{
  "valid": false,
  "message": "YARA rule missing 'condition:' section"
}
```

## Example

```
lc_call_tool(tool_name="validate_yara_rule", parameters={
  "rule_content": "rule SuspiciousPowerShell {\n  strings:\n    $ps = \"powershell\" nocase\n  condition:\n    $ps\n}"
})
```

## Checks Performed

- Non-empty content
- Contains `rule` keyword
- Balanced braces `{ }`
- Contains `condition:` section

## Not Checked (requires full YARA compiler)

- String pattern syntax
- Condition expression logic
- Regex validity
- Import statements
- Module usage

## Notes

- **Basic validation only** - not a full YARA compiler
- No API calls made - instant local validation
- Use before `set_yara_rule` to catch obvious errors
- YARA syntax: https://yara.readthedocs.io/
