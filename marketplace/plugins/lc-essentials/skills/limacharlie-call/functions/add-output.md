# add_output

Create a new output configuration to export data to external systems.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |
| name | string | Yes | Unique output name |
| module | string | Yes | Output module (see Output Modules below) |
| output_type | string | Yes | Data type: event, detect, audit, deployment, artifact, tailored, billing |
| config | object | No | Module-specific configuration parameters (see below) |

## Output Modules

`s3`, `gcs`, `pubsub`, `bigquery`, `scp`, `sftp`, `slack`, `syslog`, `webhook`, `webhook_bulk`, `smtp`, `humio`, `kafka`, `azure_storage_blob`, `azure_event_hub`, `elastic`, `tines`, `torq`, `datadog`, `opensearch`, `websocket`

## Config Object Parameters

The `config` object accepts all module-specific parameters. Common fields:

**Cloud Storage (s3, gcs):**
| Field | Description |
|-------|-------------|
| bucket | Bucket name |
| secret_key | Service account key or AWS credentials |
| region_name | AWS region (S3) |

**BigQuery:**
| Field | Description |
|-------|-------------|
| project | GCP project name |
| dataset | BigQuery dataset name |
| table | BigQuery table name |
| schema | Column definitions (e.g., `event_type:STRING, oid:STRING`) |
| secret_key | Service account JSON key |
| custom_transform | JSON field mapping (e.g., `{"oid":"routing.oid"}`) |
| sec_per_file | Seconds between batch loads |

**Network (syslog, webhook, elastic):**
| Field | Description |
|-------|-------------|
| dest_host | Destination host/URL |
| username | Username for authentication |
| password | Password for authentication |
| is_tls | Enable TLS (`"true"` or `"false"`) |

**Filtering (all modules):**
| Field | Description |
|-------|-------------|
| tag | Filter by sensor tag |
| sid | Filter by sensor ID |
| event_white_list | Comma-separated event types to include |
| event_black_list | Comma-separated event types to exclude |

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
    "dest_host": "10.0.1.50",
    "is_tls": "true"
  }
})
```

**BigQuery output:**
```
lc_call_tool(tool_name="add_output", parameters={
  "oid": "c7e8f940-...",
  "name": "bq-detections",
  "module": "bigquery",
  "output_type": "detect",
  "config": {
    "project": "my-gcp-project",
    "dataset": "limacharlie_data",
    "table": "detections",
    "secret_key": "hive://secret/bq-service-account",
    "schema": "event_type:STRING, oid:STRING, sid:STRING",
    "custom_transform": "{\"oid\":\"routing.oid\",\"sid\":\"routing.sid\",\"event_type\":\"routing.event_type\"}"
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
    "secret_key": "hive://secret/aws-creds",
    "region_name": "us-east-1",
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
- Use `hive://secret/name` for credentials stored in LimaCharlie secrets
- Related: `list_outputs`, `delete_output`
