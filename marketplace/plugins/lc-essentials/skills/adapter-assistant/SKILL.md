---
name: adapter-assistant
description: Complete adapter lifecycle assistant for LimaCharlie. Supports External Adapters (cloud-managed), Cloud Sensors (SaaS/cloud integrations), and On-prem USP adapters. Dynamically researches adapter types from local docs and GitHub usp-adapters repo. Creates, validates, deploys, and troubleshoots adapter configurations. Handles parsing rules (Grok, regex), field mappings, credential setup, and multi-adapter configs. Use when setting up new data sources (Okta, S3, Azure Event Hub, syslog, webhook, etc.), troubleshooting ingestion issues, or managing adapter deployments.
allowed-tools:
  - Task
  - Read
  - Bash
  - Skill
  - AskUserQuestion
  - WebFetch
  - WebSearch
  - Glob
  - Grep
---

# Adapter Assistant

A comprehensive, dynamic assistant for LimaCharlie adapter lifecycle management. This skill researches adapter configurations from multiple sources and helps you create, validate, deploy, and troubleshoot adapters for any data source.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output yaml [flags]
```

For command help and discovery: `limacharlie <command> --ai-help`

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **Output Format** | `--output json` | `--output yaml` (more token-efficient) |
| **Filter Output** | Pipe to jq/yq | Use `--filter JMESPATH` to select fields |
| **LCQL Queries** | Write query syntax manually | Use `limacharlie ai generate-query` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |

---

## When to Use

Use this skill when:

- **Setting up new data sources**: Connect syslog, webhooks, cloud services, or any external data to LimaCharlie
- **Configuring SaaS integrations**: Okta, CrowdStrike, Microsoft Defender, Office 365, AWS, Azure, etc.
- **Troubleshooting adapters**: Data not flowing, parsing issues, credential problems
- **Modifying existing adapters**: Update parsing rules, change credentials, add field mappings
- **Auditing adapters**: List and review adapters across organizations
- **Connecting unknown products**: Research how to integrate any product that sends logs or webhooks

Common scenarios:
- "I want to ingest Okta system logs"
- "Set up a syslog adapter for our firewall"
- "My Azure Event Hub adapter isn't receiving data"
- "How do I connect this product that sends webhooks?"
- "Create a webhook to receive alerts from our monitoring system"
- "List all adapters across my organizations"
- "Help me parse these custom log formats"

## What This Skill Does

This skill is **truly dynamic** - it researches adapter configurations from multiple sources in real-time:

1. **Local LimaCharlie documentation** - Adapter types, configuration options, examples
2. **GitHub usp-adapters repository** - Source code for 50+ adapter implementations
3. **External product documentation** - API docs, webhook formats, authentication requirements

The skill then guides you through creating, validating, and deploying adapter configurations with proper parsing rules and credential management.

### Supported Adapter Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **External Adapter** | Cloud-managed syslog, webhook, or API receivers | syslog, webhook, custom API |
| **Cloud Sensor** | Cloud-to-cloud SaaS integrations | Okta, CrowdStrike, O365, AWS S3, Azure Event Hub |
| **On-prem/USP Adapter** | Binary deployments with local configuration | file, syslog receiver, Kubernetes pods |

## Dynamic Research Strategy

**This is the key capability** - the skill researches ANY data source dynamically, not just predefined ones.

### For ANY Data Source Request:

#### Step 1: Check for Native LimaCharlie Adapter

Search local documentation:
```
Glob("./docs/limacharlie/doc/Sensors/Adapters/Adapter_Types/*{keyword}*.md")
```

Check GitHub usp-adapters repository (use API at root - adapters are NOT in a subdirectory):
```
WebFetch(
  url="https://api.github.com/repos/refractionPOINT/usp-adapters/contents",
  prompt="List all available adapter directories from the JSON response"
)
```

#### Step 2: Read LimaCharlie Adapter Documentation

If a native adapter exists, first list files in the adapter directory, then fetch the main source:
```
# Step 1: List files to find the main config file
WebFetch(
  url="https://api.github.com/repos/refractionPOINT/usp-adapters/contents/{adapter}",
  prompt="List all .go files in this adapter directory"
)

# Step 2: Fetch the config (usually client.go, but some adapters differ - e.g., sentinelone uses s1.go)
WebFetch(
  url="https://raw.githubusercontent.com/refractionPOINT/usp-adapters/master/{adapter}/client.go",
  prompt="Extract all configuration fields from the Config struct"
)
```

#### Step 3: Research the External Product

**ALWAYS** research the external product to understand its capabilities:

```
WebSearch("{product name} API documentation")
WebSearch("{product name} webhook integration")
WebSearch("{product name} audit logs export")
```

Extract:
- Authentication method (API key, OAuth, service account, etc.)
- Available event types or log categories
- Webhook payload format (if applicable)
- Rate limits and API best practices
- Required scopes or permissions

#### Step 4: Build Comprehensive Integration Plan

If NO native adapter exists, determine how to connect:
- Can it send webhooks? → LimaCharlie webhook adapter
- Does it write to S3/GCS/Azure Blob? → Cloud storage adapters
- Does it push to Kafka/Pub/Sub/SQS? → Queue adapters
- Can we pull via API? → May need polling or custom integration

Then map out:
- External product configuration requirements
- Matching LimaCharlie adapter configuration
- Parsing requirements for the data format
- Sample data format for validation

## Workflow Phases

### Phase 0: Requirements Gathering

Use `AskUserQuestion` to understand the user's needs:

1. **Operation type**: Create new adapter, modify existing, troubleshoot, or audit
2. **Data source**: What product/system are they connecting?
3. **Adapter category preference**: Cloud-managed or on-prem deployment

### Phase 1: Dynamic Research

Execute the dynamic research strategy above to gather all relevant information about:
- LimaCharlie adapter capabilities
- External product API/webhook specifications
- Configuration requirements on both sides

### Phase 2: Organization and Configuration Discovery

**Get organizations:**
```bash
limacharlie org list --output yaml
```

**List existing External Adapters:**
```bash
limacharlie external-adapter list --oid <oid> --output yaml
```

**List existing Cloud Sensors:**
```bash
limacharlie cloud-adapter list --oid <oid> --output yaml
```

**Get existing configuration (if modifying):**
```bash
limacharlie external-adapter get --key <adapter-name> --oid <oid> --output yaml
# or for cloud sensors:
limacharlie cloud-adapter get --key <sensor-name> --oid <oid> --output yaml
```

### Phase 3: Configuration Generation

Build the configuration based on research:

#### Core client_options (required for all adapters):

```yaml
client_options:
  identity:
    oid: "<organization-id>"
    installation_key: "<installation-key>"  # or use hive://secret/...
  platform: "text|json|carbon_black|gcp|..."
  sensor_seed_key: "<unique-identifier>"
  hostname: "<adapter-hostname>"
  mapping:
    parsing_grok:
      message: '%{PATTERN:field} ...'  # For text platform
    event_type_path: "field/path"
    event_time_path: "timestamp/path"
    sensor_hostname_path: "host/path"
```

#### Credential references (recommended):

Use Hive secrets for sensitive values:
```yaml
apikey: "hive://secret/okta-api-key"
client_secret: "hive://secret/azure-client-secret"
```

Check existing secrets:
```bash
limacharlie secret list --oid <oid> --output yaml
```

#### Indexing configuration (optional):

```yaml
indexing:
  - events_included: ["*"]
    path: "src_ip"
    index_type: "ip"
  - events_included: ["*"]
    path: "user/email"
    index_type: "user"
```

Supported index types: `file_hash`, `file_path`, `file_name`, `domain`, `ip`, `user`, `service_name`, `package_name`

### Phase 4: Validation and Testing

**Validate parsing rules before deployment:**

```bash
limacharlie usp validate \
  --platform text \
  --mapping '{"parsing_grok": {"message": "%{TIMESTAMP_ISO8601:timestamp} %{WORD:action} ..."}, "event_type_path": "action", "event_time_path": "timestamp"}' \
  --text-input "<sample-log-lines>" \
  --oid <oid> --output yaml
```

**Review validation results:**
- Verify all expected fields are extracted
- Check timestamp parsing
- Confirm event type assignment
- Iterate on pattern if validation fails

**For complex parsing**, invoke the parsing-helper skill:
```
Skill("parsing-helper")
```

**For local testing before production deployment:**
```
Skill("test-limacharlie-adapter")
```

### Phase 5: Deployment

**Deploy External Adapter:**
```bash
# Write configuration to a temp file first
cat > /tmp/adapter-config.yaml << 'EOF'
<full-configuration-yaml>
EOF
limacharlie external-adapter set --key <adapter-name> --input-file /tmp/adapter-config.yaml --oid <oid> --output yaml
```

**Deploy Cloud Adapter:**
```bash
cat > /tmp/cloud-adapter-config.yaml << 'EOF'
<full-configuration-yaml>
EOF
limacharlie cloud-adapter set --key <sensor-name> --input-file /tmp/cloud-adapter-config.yaml --oid <oid> --output yaml
```

**For On-prem Adapters**, generate deployment artifacts:

**YAML Configuration:**
```yaml
syslog:
  client_options:
    identity:
      installation_key: "<IID>"
      oid: "<OID>"
    platform: text
    sensor_seed_key: "<unique-key>"
    hostname: "<hostname>"
    mapping:
      parsing_grok:
        message: '%{PATTERN:field} ...'
      event_type_path: "..."
  port: 514
  is_udp: true
```

**CLI Command:**
```bash
./lc_adapter syslog \
  client_options.identity.installation_key=<IID> \
  client_options.identity.oid=<OID> \
  client_options.platform=text \
  client_options.sensor_seed_key=<key> \
  "client_options.mapping.parsing_grok.message=%{PATTERN:field} ..." \
  port=514 \
  is_udp=true
```

**Docker Command:**
```bash
docker run -d --rm -p 514:514/udp refractionpoint/lc-adapter syslog \
  client_options.identity.installation_key=<IID> \
  client_options.identity.oid=<OID> \
  client_options.platform=text \
  client_options.sensor_seed_key=<key> \
  port=514 \
  is_udp=true
```

**Verify deployment:**
```bash
limacharlie sensor list --selector "iid == \`<installation-key-iid>\`" --oid <oid> --output yaml
```

### Phase 6: Post-Deployment

**Troubleshoot if data not appearing:**

1. Check adapter last_error field:
```bash
limacharlie external-adapter get --key <adapter-name> --oid <oid> --output yaml
```

2. Check organization errors for adapter issues:
```bash
limacharlie org errors --oid <oid> --output yaml
```
Look for errors with component names containing the adapter name.

3. Verify sensor exists in sensor list

4. Query for recent events:
```bash
# First calculate timestamps dynamically
start=$(date -d '1 hour ago' +%s) && end=$(date +%s)

limacharlie event list --sid <sensor-id> --start $start --end $end --oid <oid> --output yaml
```

5. Check for unparsed events (`event_type: "unknown_event"` with only `text` field)

**Offer D&R rule creation:**
```
Skill("detection-engineering")
```

## Multi-Organization Adapter Audit

For auditing adapters across multiple organizations, spawn parallel sub-agents:

```
Task(
  subagent_type="lc-essentials:multi-org-adapter-auditor",
  prompt="Audit adapters for organization: {org_name} ({oid})

    Return:
    - List of external adapters with status
    - List of cloud sensors with status
    - Any adapters with errors
    - Configuration issues detected"
)
```

## Adapter Type Quick Reference

| Adapter Type | Platform | Deployment | Key Configuration |
|-------------|----------|------------|-------------------|
| syslog | text | External/On-prem | port, is_udp, parsing_grok |
| webhook | json | Cloud Sensor | secret, client_options |
| okta | json | Cloud Sensor | apikey, url |
| s3 | varies | Cloud Sensor/On-prem | bucket_name, access_key, secret_key, prefix |
| azure_event_hub | varies | Cloud Sensor/On-prem | connection_string |
| office365 | json | Cloud Sensor | domain, tenant_id, publisher_id, client_id, client_secret, endpoint |
| falconcloud | json | Cloud Sensor/On-prem | client_id, client_secret |
| pubsub | varies | Cloud Sensor/On-prem | project_id, subscription_id, service_account_creds |
| file | varies | On-prem | file_path, backfill |

**IMPORTANT**: Always check the **usp-adapters repo** for authoritative field definitions:
- URL: `https://github.com/refractionPOINT/usp-adapters`
- Each adapter has a `client.go` with a `*Config` struct defining all valid fields
- All Cloud Sensors require a nested structure with `client_options` containing `identity`, `platform`, and `sensor_seed_key`

## Example Usage

### Example 1: Set Up Okta System Log Adapter

**User**: "I want to ingest Okta system logs into LimaCharlie"

**Workflow**:

1. **Research Phase**:
   - Read local docs: `./docs/limacharlie/doc/Sensors/Adapters/Adapter_Types/adapter-types-okta.md`
   - WebSearch: "Okta System Log API documentation 2024"
   - Extract: API key requirements, URL format, event types

2. **Configuration**:
   ```yaml
   sensor_type: "okta"
   okta:
     apikey: "hive://secret/okta-api-key"
     url: "https://your-company.okta.com"
     client_options:
       identity:
         oid: "<oid>"
         installation_key: "<iid>"
       hostname: "okta-system-logs"
       platform: "json"
       sensor_seed_key: "okta-logs-sensor"
       mapping:
         sensor_hostname_path: "client/device"
         event_type_path: "eventType"
         event_time_path: "published"
   ```

3. **External Setup Instructions**:
   - Create API token in Okta Admin Console
   - Store token in LimaCharlie secrets: `limacharlie secret set okta-api-key --oid <oid>`

4. **Deploy**: Use `set_cloud_sensor`

### Example 2: Syslog Adapter with Custom Grok Parsing

**User**: "Set up a syslog adapter for our firewall. Sample log: `<134>Nov 15 12:30:45 fw01 ACCEPT TCP 192.168.1.100:54321 10.0.0.5:443`"

**Workflow**:

1. **Analyze log format**: Priority, syslog timestamp, hostname, action, protocol, src:port dst:port

2. **Generate Grok pattern**:
   ```yaml
   parsing_grok:
     message: '<%{INT:priority}>%{SYSLOGTIMESTAMP:timestamp} %{HOSTNAME:host} %{WORD:action} %{WORD:protocol} %{IP:src_ip}:%{NUMBER:src_port} %{IP:dst_ip}:%{NUMBER:dst_port}'
   ```

3. **Validate** with `validate_usp_mapping` using the sample log

4. **Deploy as External Adapter**:
   ```bash
   cat > /tmp/firewall-adapter.yaml << 'EOF'
   adapter_type: syslog
   port: 514
   is_udp: true
   client_options:
     identity:
       oid: "<oid>"
       installation_key: "<iid>"
     platform: text
     sensor_seed_key: firewall-logs
     hostname: firewall-syslog
     mapping:
       parsing_grok:
         message: "<%{INT:priority}>%{SYSLOGTIMESTAMP:timestamp} %{HOSTNAME:host} %{WORD:action} %{WORD:protocol} %{IP:src_ip}:%{NUMBER:src_port} %{IP:dst_ip}:%{NUMBER:dst_port}"
       event_type_path: action
       event_time_path: timestamp
       sensor_hostname_path: host
   EOF
   limacharlie external-adapter set --key firewall-syslog --input-file /tmp/firewall-adapter.yaml --oid <oid> --output yaml
   ```

### Example 3: Connect Unknown Product via Webhook

**User**: "I want to connect this monitoring tool that sends webhooks, I don't know if LimaCharlie supports it"

**Workflow**:

1. **Ask clarifying questions**:
   - What's the product name?
   - Do you have sample webhook payload?

2. **Research the product**:
   ```
   WebSearch("{product name} webhook documentation")
   WebSearch("{product name} webhook payload format")
   ```

3. **Read LimaCharlie webhook adapter docs**:
   ```
   Read("./docs/limacharlie/doc/Sensors/Adapters/Adapter_Types/adapter-types-webhook.md")
   ```

4. **Build integration plan**:
   - LimaCharlie webhook adapter configuration
   - Grok/JSON parsing for the webhook payload
   - Field mappings for proper event normalization

5. **Deploy and provide webhook URL to user**

### Example 4: Troubleshoot Adapter Not Receiving Data

**User**: "My Azure Event Hub adapter isn't receiving data"

**Workflow**:

1. **Get current configuration**:
   ```bash
   limacharlie cloud-adapter get --key azure-event-hub --oid <oid> --output yaml
   ```

2. **Check for errors** in `last_error` field of `sys_mtd`

3. **Common issues**:
   - Connection string missing EntityPath
   - Consumer group not created
   - Credentials expired
   - Diagnostic settings not configured in Azure

4. **Research Azure-side setup**:
   ```
   WebSearch("Azure Event Hub diagnostic settings configuration")
   ```

5. **Provide fix guidance** based on error analysis

## Common Pitfalls

1. **Installation Key vs IID**: For adapters, use the IID (UUID format like `e9a3bcdf-efa2-47ae-b6df-579a02f3a54d`), not the full base64 installation key

2. **DATESTAMP vs TIMESTAMP_ISO8601**:
   - `YYYY-MM-DD HH:MM:SS` → Use `%{TIMESTAMP_ISO8601}`
   - `MM-DD-YY HH:MM:SS` → Use `%{DATESTAMP}`
   - `Jan 15 12:30:45` → Use `%{SYSLOGTIMESTAMP}`

3. **Grok field name**: Always use `message` as the key in `parsing_grok` for text platform:
   ```yaml
   parsing_grok:
     message: '%{PATTERN:field}'  # Correct
   ```

4. **Azure Event Hub connection string**: Must include `EntityPath=<event-hub-name>` for consumer applications

5. **Credential storage**: Always use `hive://secret/<secret-name>` for sensitive values in production

6. **Unparsed events**: If you see `event_type: "unknown_event"` with only a `text` field, parsing is not configured

7. **Timestamp calculations**: Always use Bash to calculate epoch timestamps dynamically:
   ```bash
   start=$(date -d '1 hour ago' +%s) && end=$(date +%s)
   ```

## Related Skills

- `parsing-helper` - For complex Grok pattern generation and validation
- `test-limacharlie-adapter` - For local testing before production deployment
- `detection-engineering` - For creating D&R rules on adapter data

## Reference

For more details:
- Adapter usage: `./docs/limacharlie/doc/Sensors/Adapters/adapter-usage.md`
- Adapter deployment: `./docs/limacharlie/doc/Sensors/Adapters/adapter-deployment.md`
- Adapter types: `./docs/limacharlie/doc/Sensors/Adapters/Adapter_Types/`
- GitHub source: https://github.com/refractionPOINT/usp-adapters
