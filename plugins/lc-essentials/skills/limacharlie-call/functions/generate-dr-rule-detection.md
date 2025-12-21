# generate_dr_rule_detection

Generate D&R detection components from natural language using AI (Gemini).

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | Natural language description of threat/behavior to detect |

## Returns

```json
{
  "detection": "event: NEW_PROCESS\nop: and\nrules:\n  - op: contains\n    path: event/FILE_PATH\n    value: powershell\n  - op: contains\n    path: event/COMMAND_LINE\n    value: ' -enc'"
}
```

## Examples

**Encoded PowerShell:**
```
lc_call_tool(tool_name="generate_dr_rule_detection", parameters={
  "oid": "c7e8f940-...",
  "query": "detect encoded PowerShell commands"
})
```

**Lateral Movement:**
```
lc_call_tool(tool_name="generate_dr_rule_detection", parameters={
  "oid": "c7e8f940-...",
  "query": "detect PsExec execution for lateral movement"
})
```

**Suspicious DNS:**
```
lc_call_tool(tool_name="generate_dr_rule_detection", parameters={
  "oid": "c7e8f940-...",
  "query": "DNS requests to .xyz or .top TLDs"
})
```

## How It Works

1. Sends query to Gemini AI with D&R detection prompt
2. Generates YAML detection component
3. Validates against org's D&R schema
4. Retries up to 10 times if validation fails
5. Returns clean YAML

## Notes

- **AI-powered** - generates detection from natural language
- **Auto-validated** - checks against your org's schema
- **Detection only** - use `generate_dr_rule_respond` for response actions
- Supports all event types (NEW_PROCESS, DNS_REQUEST, NETWORK_CONNECTIONS, etc.)
- Valid operators: `is`, `contains`, `starts with`, `ends with`, `matches`, `and`, `or`
- **Always test** generated detections before deploying
- Related: `generate_dr_rule_respond`, `validate_dr_rule_components`
