# set_dr_general_rule

Create or update a custom D&R rule in the general namespace.

## Recommended Workflow: AI-Assisted Generation

**For reliable rule creation:**
1. `generate_dr_rule_detection` - Generate detection component
2. `generate_dr_rule_respond` - Generate response actions
3. `validate_dr_rule_components` - Validate syntax
4. `set_dr_general_rule` - Deploy

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | Rule name (alphanumeric, hyphens, underscores) |
| rule_content | object | Yes | Rule content containing `detect` and optionally `respond` |
| ttl | number | No | Time-to-live in seconds. Rule auto-deletes after this duration. |

## Returns

```json
{}
```

Empty response indicates success. Rule is immediately active.

## Example

```
lc_call_tool(tool_name="set_dr_general_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "detect-encoded-powershell",
  "rule_content": {
    "detect": {
      "event": "NEW_PROCESS",
      "op": "contains",
      "path": "event/COMMAND_LINE",
      "value": "powershell -enc"
    },
    "respond": [{"action": "report", "name": "encoded_powershell"}]
  }
})
```

## Lookup-Based Detection

For IOC-based rules using lookups:

```json
{
  "detect": {
    "op": "lookup",
    "path": "event/DOMAIN_NAME",
    "resource": "hive://lookup/threat-intel-domains"
  }
}
```

**Important:** Always use `hive://lookup/name` format, NOT `lookup://name`.

## Notes

- Validate with `validate_dr_rule_components` before deployment
- Rules become active immediately unless `is_enabled: false`
- Related: `generate_dr_rule_detection`, `generate_dr_rule_respond`
