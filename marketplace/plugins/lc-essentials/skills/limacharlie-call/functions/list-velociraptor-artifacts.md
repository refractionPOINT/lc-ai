# list_velociraptor_artifacts

List all available Velociraptor artifacts for DFIR collection, including both built-in artifacts and external artifacts from triage.velocidex.com.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## Returns

```json
{
  "artifacts": [
    "Windows.System.Drivers",
    "Windows.EventLogs.Security",
    "Linux.Sys.Syslog",
    "Windows.Triage.Targets"
  ],
  "artifacts_details": [
    {"name": "Windows.System.Drivers", "source": "built-in"},
    {"name": "Windows.EventLogs.Security", "source": "built-in"},
    {"name": "Linux.Sys.Syslog", "source": "built-in"},
    {"name": "Windows.Triage.Targets", "source": "external"}
  ]
}
```

## Example

```
lc_call_tool(tool_name="list_velociraptor_artifacts", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
})
```

## Notes

- **Prerequisite**: The `ext-velociraptor` extension must be subscribed in the organization
- **Built-in artifacts**: Standard Velociraptor artifact library (Windows, Linux, macOS system artifacts)
- **External artifacts**: Downloaded from triage.velocidex.com (Windows.Triage.Targets, Linux.Triage.UAC, etc.)
- External artifacts are cached for 24 hours to avoid repeated downloads
- Use `show_velociraptor_artifact` to view the YAML definition of any artifact
- Use `collect_velociraptor_artifact` to initiate collection from endpoints
