# delete_yara_rule

Permanently delete a YARA rule source from the organization.

**⚠️ PARAMETER NAME**: Use `rule_name`, NOT `name`.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| rule_name | string | Yes | YARA rule source name (case-sensitive) |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_yara_rule", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "rule_name": "old_malware_signatures"
})
```

## Notes

- **Deletion is permanent and irreversible**
- Rule immediately stops scanning files/processes
- Deletes all YARA rule definitions within the source
- Historical detections remain in timeline
- Consider backing up with `get_yara_rule` before deleting
- Related: `list_yara_rules`, `get_yara_rule`, `set_yara_rule`
