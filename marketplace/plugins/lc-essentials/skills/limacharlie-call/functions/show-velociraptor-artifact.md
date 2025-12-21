# show_velociraptor_artifact

Display the YAML definition of a specific Velociraptor artifact. Use this to understand artifact parameters, data sources, and collection behavior before running a collection.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| artifact_name | string | Yes | Name of the artifact (e.g., "Windows.System.Drivers") |

## Returns

```json
{
  "definition": "name: Windows.System.Drivers\ndescription: |\n  Enumerate loaded kernel drivers...\nparameters:\n  - name: DriverPathRegex\n    default: .\n    description: Filter by driver path\nsources:\n  - query: |\n      SELECT * FROM Artifact.Windows.Sys.Drivers()\n      WHERE Path =~ DriverPathRegex\n"
}
```

## Example

```
lc_call_tool(tool_name="show_velociraptor_artifact", parameters={
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "artifact_name": "Windows.System.Drivers"
})
```

## Notes

- **Prerequisite**: The `ext-velociraptor` extension must be subscribed in the organization
- Use `list_velociraptor_artifacts` first to see available artifact names
- The `definition` field contains the complete Velociraptor artifact YAML
- Review the artifact's `parameters` section to understand optional arguments for `collect_velociraptor_artifact`
- External artifacts (from triage.velocidex.com) are downloaded on-demand if not cached
- Works for both built-in and external artifacts
