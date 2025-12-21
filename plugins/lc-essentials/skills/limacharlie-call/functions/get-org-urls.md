# get_org_urls

Get organization URLs including geo-dependent domains for webhooks, DNS, and API endpoints.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "hooks": "9157798c50af372c.hook.limacharlie.io",
  "dns": "9157798c50af372c.dns.limacharlie.io",
  "api": "api.limacharlie.io",
  "ingestion": "lc.limacharlie.io"
}
```

## Example

```
lc_call_tool(tool_name="get_org_urls", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- Read-only operation
- The `hooks` domain is geo-dependent and required for constructing webhook URLs
- Webhook URL format: `https://{hooks}/{oid}/{webhook_name}/{secret}`
- URLs vary by organization location (USA, Canada, Europe, etc.)
- Related: `set_cloud_sensor` (for creating webhook cloud sensors)
