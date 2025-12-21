# add_output

Create a new output configuration to export data to external systems.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| name | string | Yes | Unique output name |
| module | string | Yes | Output type (syslog, s3, webhook, slack, gcs, elastic, kafka) |
| output_type | string | Yes | Data type: event, detect, audit, deployment, artifact |
| config | object | No | Module-specific configuration parameters (see below) |

### Config Object Parameters

The `config` object contains module-specific and filtering parameters:

**Module-Specific:**
| Field | Description |
|-------|-------------|
| dest_host | Destination host/URL (syslog, webhook, elastic) |
| bucket | S3/GCS bucket name |
| username | Username for authentication (elastic) |
| password | Password for authentication (elastic) |

**Filtering:**
| Field | Description |
|-------|-------------|
| tag | Filter by sensor tag |
| sid | Filter by sensor ID |

## Returns

```json
{
  "name": "prod-syslog",
  "module": "syslog",
  "for": "event",
  "dest_host": "10.0.1.50"
}
```

## Examples

**Syslog output:**
```
lc_call_tool(tool_name="add_output", parameters={
  "oid": "c7e8f940-...",
  "name": "prod-syslog",
  "module": "syslog",
  "output_type": "event",
  "config": {
    "dest_host": "10.0.1.50"
  }
})
```

**S3 archive:**
```
lc_call_tool(tool_name="add_output", parameters={
  "oid": "c7e8f940-...",
  "name": "detection-archive",
  "module": "s3",
  "output_type": "detect",
  "config": {
    "bucket": "lc-detections",
    "tag": "production"
  }
})
```

**Webhook with filtering:**
```
lc_call_tool(tool_name="add_output", parameters={
  "oid": "c7e8f940-...",
  "name": "alert-webhook",
  "module": "webhook",
  "output_type": "detect",
  "config": {
    "dest_host": "https://api.example.com/alerts",
    "tag": "critical-systems"
  }
})
```

## Notes

- Outputs become active immediately
- Cannot modify outputs - delete and recreate to change
- Boolean fields must be strings: `"true"` or `"false"`
- Use `[secret:name]` for credentials
- Related: `list_outputs`, `delete_output`
