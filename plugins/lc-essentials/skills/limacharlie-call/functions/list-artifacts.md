# list_artifacts

List collected artifacts and forensic data from sensors.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| sid | string | No | Filter by sensor ID |
| artifact_type | string | No | Filter by artifact type (memory_dump, pcap, file, registry) |
| start | integer | No | Start timestamp (Unix seconds) |
| end | integer | No | End timestamp (Unix seconds) |

## Returns

```json
{
  "artifacts": [
    {
      "id": "artifact-123abc",
      "sid": "sensor-456def",
      "type": "memory_dump",
      "size": 52428800,
      "timestamp": 1640995200,
      "source": "manual_collection"
    },
    {
      "id": "artifact-789ghi",
      "sid": "sensor-456def",
      "type": "pcap",
      "size": 10485760,
      "timestamp": 1640995300
    }
  ],
  "total": 2
}
```

## Example

```
lc_call_tool(tool_name="list_artifacts", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "artifact_type": "memory_dump",
  "start": 1672444800
})
```

## Common Artifact Types

| Type | Description |
|------|-------------|
| memory_dump | Full memory dumps for forensics |
| pcap | Network packet captures |
| file | Collected files/executables |
| registry | Registry hive exports |
| event_log | Windows event log exports |
| velociraptor | Velociraptor forensic collections (ZIP files) |

## Notes

- Size in bytes, timestamps in Unix seconds
- Use `get_artifact` with artifact ID to download
- Artifacts expire based on retention settings
- Related: `get_artifact`
