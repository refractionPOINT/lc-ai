# generate_dr_rule_respond

Generate D&R response components from natural language using AI (Gemini).

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| query | string | Yes | Natural language description of response actions |

## Returns

```json
{
  "respond": "- action: report\n  name: threat_detected\n- action: isolate network"
}
```

## Examples

**Report and Isolate:**
```
lc_call_tool(tool_name="generate_dr_rule_respond", parameters={
  "oid": "c7e8f940-...",
  "query": "isolate the sensor and send a report"
})
```

**Kill and Alert:**
```
lc_call_tool(tool_name="generate_dr_rule_respond", parameters={
  "oid": "c7e8f940-...",
  "query": "kill the process tree and send a webhook alert"
})
```

**Comprehensive Response:**
```
lc_call_tool(tool_name="generate_dr_rule_respond", parameters={
  "oid": "c7e8f940-...",
  "query": "kill process, isolate sensor, tag as compromised, create high-priority report"
})
```

## Available Actions

| Action | Description |
|--------|-------------|
| report | Create detection report with metadata |
| task | Execute sensor task (deny_tree, etc.) |
| isolate network | Network isolation |
| rejoin network | Remove network isolation |
| add tag | Tag sensor (with optional TTL) |
| remove tag | Remove sensor tag |
| webhook | HTTP webhook to external systems |
| service request | Trigger service integrations |

## How It Works

1. Sends query to Gemini AI with D&R response prompt
2. Generates YAML response component
3. Validates against org's D&R schema
4. Retries up to 10 times if validation fails
5. Returns clean YAML

## Notes

- **AI-powered** - generates responses from natural language
- **Auto-validated** - checks against your org's schema
- Actions execute in order listed
- **Response only** - use `generate_dr_rule_detection` for detection logic
- Consider operational impact (isolation, process termination)
- **Always test** before deploying
- Related: `generate_dr_rule_detection`, `validate_dr_rule_components`
