# get_artifact

Download or get a signed URL for a specific artifact.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| artifact_id | string | Yes | Artifact ID from `list_artifacts` |
| get_url_only | boolean | No | When true, returns only the signed URL without downloading content (default: false) |

## Returns

```json
{
  "id": "artifact-abc123",
  "url": "https://storage.googleapis.com/lc-artifacts/...",
  "size": 52428800,
  "type": "memory_dump",
  "expires": 1672531200
}
```

## Example

```
lc_call_tool(tool_name="get_artifact", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "artifact_id": "art-mem-123"
})
```

## Notes

- **Signed URLs expire** (typically 1 hour) - download promptly
- For large artifacts (>100MB), use URL download method
- Handle artifacts securely - may contain malicious content
- Verify artifact integrity with checksums
- Analysis tools by type:
  - Memory: Volatility, Rekall, WinDbg
  - PCAP: Wireshark, tcpdump
  - Files: sandboxes, reverse engineering tools
- Related: `list_artifacts`
