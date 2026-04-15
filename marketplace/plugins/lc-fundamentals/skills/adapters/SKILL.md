---
name: adapters
description: Working with LimaCharlie adapters — cloud sensors (SaaS integrations), external adapters (cloud-managed), and on-prem/USP adapters. Covers configuration, credential setup, parsing rules, validation, deployment, and troubleshooting. Use when setting up data sources, configuring adapters, or troubleshooting ingestion.
allowed-tools:
  - Bash
  - Read
  - WebFetch
  - WebSearch
  - Glob
  - Grep
---

# Adapters

How to work with LimaCharlie adapters — the telemetry ingestion layer for third-party data sources.

## Adapter Categories

| Category | Description | Management |
|----------|-------------|-----------|
| **Cloud Sensor** | Cloud-to-cloud SaaS integrations (Okta, O365, AWS S3, Azure Event Hub) | `limacharlie cloud-adapter` |
| **External Adapter** | Cloud-managed syslog, webhook, or API receivers | `limacharlie external-adapter` |
| **On-prem/USP** | Binary deployed locally with config file or CLI args | `lc_adapter` binary or Docker |

## CLI Commands

### Cloud Sensors

```bash
# List
limacharlie cloud-adapter list --oid <oid> --output yaml

# Get configuration
limacharlie cloud-adapter get --key <name> --oid <oid> --output yaml

# Create/Update
cat > /tmp/config.yaml << 'EOF'
<configuration>
EOF
limacharlie cloud-adapter set --key <name> --input-file /tmp/config.yaml --oid <oid> --output yaml

# Delete
limacharlie cloud-adapter delete --key <name> --confirm --oid <oid>
```

### External Adapters

```bash
# List
limacharlie external-adapter list --oid <oid> --output yaml

# Get configuration
limacharlie external-adapter get --key <name> --oid <oid> --output yaml

# Create/Update
limacharlie external-adapter set --key <name> --input-file /tmp/config.yaml --oid <oid> --output yaml

# Delete
limacharlie external-adapter delete --key <name> --confirm --oid <oid>
```

## Configuration Structure

All adapters share a common `client_options` structure:

```yaml
client_options:
  identity:
    oid: "<organization-id>"
    installation_key: "<iid>"  # UUID format, or hive://secret/...
  platform: "text|json|gcp|aws|..."
  sensor_seed_key: "<unique-identifier>"
  hostname: "<adapter-hostname>"
  mapping:
    parsing_grok:
      message: '%{PATTERN:field} ...'
    event_type_path: "field/path"
    event_time_path: "timestamp/path"
    sensor_hostname_path: "host/path"
```

### Key Config Fields

| Field | Description |
|-------|-------------|
| `identity.oid` | Organization ID |
| `identity.installation_key` | Installation key IID (UUID), or `hive://secret/...` |
| `platform` | Data format: `text` (syslog/logs), `json` (structured), or specific platforms |
| `sensor_seed_key` | Unique identifier for this adapter's sensor (determines SID) |
| `hostname` | Display name in sensor list |
| `mapping.parsing_grok` | Grok pattern for text parsing |
| `mapping.event_type_path` | JSON path to event type field |
| `mapping.event_time_path` | JSON path to timestamp field |
| `mapping.sensor_hostname_path` | JSON path to source hostname |

### Credential References

Use Hive secrets for sensitive values:

```yaml
apikey: "hive://secret/okta-api-key"
client_secret: "hive://secret/azure-client-secret"
```

### Indexing Configuration

Enable IOC searching on adapter data:

```yaml
indexing:
  - events_included: ["*"]
    path: "src_ip"
    index_type: "ip"
  - events_included: ["*"]
    path: "user/email"
    index_type: "user"
```

Supported index types: `file_hash`, `file_path`, `file_name`, `domain`, `ip`, `user`, `service_name`, `package_name`.

## Parsing Validation

Validate parsing rules before deployment:

```bash
cat > /tmp/usp-test.yaml << 'EOF'
parsing_grok:
  message: "%{TIMESTAMP_ISO8601:timestamp} %{WORD:action} ..."
event_type_path: action
event_time_path: timestamp
sample_data:
  - "2025-01-15T10:30:00Z LOGIN user@example.com"
EOF
limacharlie usp validate --platform text --input-file /tmp/usp-test.yaml --oid <oid> --output yaml
```

## Common Adapter Types

| Type | Platform | Config Key |
|------|----------|-----------|
| Syslog | `text` | `port`, `is_udp`, `parsing_grok` |
| Webhook | `json` | `secret` |
| Okta | `json` | `apikey`, `url` |
| AWS S3 | varies | `bucket_name`, `access_key`, `secret_key` |
| Azure Event Hub | varies | `connection_string` |
| Office 365 | `json` | `domain`, `tenant_id`, `client_id`, `client_secret` |
| CrowdStrike | `json` | `client_id`, `client_secret` |
| GCP Pub/Sub | varies | `project_id`, `subscription_id`, `service_account_creds` |

## On-Prem Deployment

### Docker

```bash
docker run -d --rm -p 514:514/udp refractionpoint/lc-adapter syslog \
  client_options.identity.installation_key=<IID> \
  client_options.identity.oid=<OID> \
  client_options.platform=text \
  client_options.sensor_seed_key=<key> \
  port=514 is_udp=true
```

### Binary

```bash
./lc_adapter syslog \
  client_options.identity.installation_key=<IID> \
  client_options.identity.oid=<OID> \
  client_options.platform=text \
  client_options.sensor_seed_key=<key> \
  port=514 is_udp=true
```

## Researching Adapter Types

For unknown or undocumented adapters, check the usp-adapters repository:

```bash
# List available adapter implementations
WebFetch(url="https://api.github.com/repos/refractionPOINT/usp-adapters/contents")

# Read adapter config struct (usually client.go)
WebFetch(url="https://raw.githubusercontent.com/refractionPOINT/usp-adapters/master/<adapter>/client.go")
```

## Post-Deployment Verification

### Check Sensor Appeared

```bash
limacharlie sensor list --selector "iid == \`<iid>\`" --oid <oid> --output yaml
```

### Check for Errors

```bash
# Adapter-specific errors
limacharlie external-adapter get --key <name> --oid <oid> --output yaml
# Look for last_error in sys_mtd

# Organization-wide errors
limacharlie org errors --oid <oid> --output yaml
```

### Verify Data Flow

```bash
start=$(date -d '1 hour ago' +%s) && end=$(date +%s)
limacharlie event list --sid <sensor-id> --start $start --end $end --oid <oid> --output yaml
```

## Common Pitfalls

1. **IID vs Installation Key**: Use the IID (UUID format), not the full base64 installation key
2. **Grok field name**: Always use `message` as the key in `parsing_grok` for text platform
3. **DATESTAMP formats**: `TIMESTAMP_ISO8601` for ISO dates, `SYSLOGTIMESTAMP` for syslog, `DATESTAMP` for MM-DD-YY
4. **Azure Event Hub**: Connection string must include `EntityPath=<event-hub-name>`
5. **Unparsed events**: `event_type: "unknown_event"` with only `text` field means parsing is misconfigured
6. **Credential storage**: Always use `hive://secret/<name>` for production credentials
