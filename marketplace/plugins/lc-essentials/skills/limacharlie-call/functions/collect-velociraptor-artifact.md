# collect_velociraptor_artifact

Initiate Velociraptor artifact collection from one or more endpoints. Deploys Velociraptor to the target sensor(s), executes the specified artifacts, and ingests the results back into LimaCharlie.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| artifact_list | string[] | One of artifact_list or custom_artifact | List of artifact names to collect |
| custom_artifact | string | One of artifact_list or custom_artifact | Custom artifact YAML definition |
| sid | string | One of sid or sensor_selector | Single sensor ID |
| sensor_selector | string | One of sid or sensor_selector | bexpr selector for multiple sensors (e.g., `plat == windows`) |
| args | string | No | Comma-separated arguments for artifact (e.g., `DriverPathRegex=.*sys$`) |
| collection_ttl | int | No | Seconds to keep attempting collection (default: 604800 = 7 days) |
| retention_ttl | int | No | Days to retain collected artifacts (default: 7) |
| ignore_cert | bool | No | Ignore SSL certificate errors during collection |

## Returns

```json
{
  "job_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "n_sensors": 5
}
```

## Examples

### Collect single artifact from one sensor

```
lc_call_tool(tool_name="collect_velociraptor_artifact", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "artifact_list": ["Windows.System.Drivers"],
  "sid": "sensor-uuid-here"
})
```

### Collect multiple artifacts from all Windows sensors

```
lc_call_tool(tool_name="collect_velociraptor_artifact", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "artifact_list": ["Windows.System.Drivers", "Windows.EventLogs.Security"],
  "sensor_selector": "plat == windows"
})
```

### Collect with custom arguments

```
lc_call_tool(tool_name="collect_velociraptor_artifact", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "artifact_list": ["Windows.System.Drivers"],
  "sid": "sensor-uuid-here",
  "args": "DriverPathRegex=.*malware.*"
})
```

### Collect with custom artifact definition

```
lc_call_tool(tool_name="collect_velociraptor_artifact", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "custom_artifact": "name: Custom.Investigation\ndescription: Custom artifact\nsources:\n  - query: SELECT * FROM info()",
  "sid": "sensor-uuid-here"
})
```

## Notes

- **Prerequisite**: The `ext-velociraptor` extension must be subscribed in the organization
- **Async operation**: Returns immediately with `job_id`; results are ingested asynchronously
- **Offline sensors**: Uses reliable-tasking for persistent delivery; collection attempts continue until `collection_ttl` expires
- **Platform support**: Windows (x86/x64), Linux (386/amd64/arm64), macOS (amd64/arm64)
- **External artifacts**: Automatically downloaded from triage.velocidex.com if needed
- **Result processing**: Collection results are automatically parsed and sent as `velociraptor_collection` events
- **Batch limit**: Up to 100 sensors can be tasked in parallel
- **Max artifact size**: Results larger than 100 MB (configurable) are skipped
- Use `show_velociraptor_artifact` to see available parameters for the `args` field
- Track job progress via LimaCharlie detections/events with the `job_id`

## Common Use Cases

- **Incident Response**: Collect forensic artifacts from compromised endpoints
- **Threat Hunting**: Search for IOCs across your fleet using Velociraptor's VQL queries
- **Compliance**: Gather system configuration data for audit purposes
- **Triage**: Quickly assess endpoint state during security investigations
