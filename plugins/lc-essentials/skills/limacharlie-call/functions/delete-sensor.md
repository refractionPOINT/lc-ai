# delete_sensor

Permanently delete a sensor and all its data from the organization.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | UUID | Yes | Sensor ID to delete |

## Returns

```json
{}
```

Empty response indicates success.

## Example

```
lc_call_tool(tool_name="delete_sensor", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "sid": "abc12345-6789-0123-4567-890abcdef012"
})
```

## Notes

- **PERMANENT and IRREVERSIBLE** - all data, history, and tags are deleted
- Sensor ID becomes invalid and cannot be recovered
- Endpoint would need re-enrollment to be managed again
- Does NOT uninstall sensor software from the endpoint
- Consider `isolate_network` or tags for temporary removal needs
