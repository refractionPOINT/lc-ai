# get_org_info

Retrieve organization information including configuration, limits, and metadata.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "name": "My Organization",
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "location": "usa",
  "plan": "enterprise",
  "limits": {
    "max_sensors": 1000,
    "max_rules": 500
  },
  "features": ["advanced_detection", "threat_intel"],
  "created": 1609459200
}
```

## Example

```
lc_call_tool(tool_name="get_org_info", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Read-only operation
- Location affects data residency and compliance
- Some features are plan-dependent
- Contact LimaCharlie support to modify plan limits
