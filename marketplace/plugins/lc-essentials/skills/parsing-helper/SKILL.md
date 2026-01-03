---
name: parsing-helper
description: Customize and test Grok parsing for USP, Cloud Sensor, and External adapters. Helps generate parsing rules from sample logs, validate against test data, and deploy configurations. Use when setting up new log sources, troubleshooting parsing issues, or modifying field extraction for adapters.
allowed-tools: Task, AskUserQuestion, Skill, Read, Bash
---

# Parsing Helper

> **IMPORTANT**: Never call `mcp__plugin_lc-essentials_limacharlie__lc_call_tool` directly.
> Always use the Task tool with `subagent_type="lc-essentials:limacharlie-api-executor"`.

A guided workflow for creating, testing, and deploying Grok parsing configurations for LimaCharlie adapters. This skill helps you customize how log data is parsed and normalized as it's ingested into LimaCharlie.

> ⚠️ **TIMEZONE NOTE**: Patterns like `SYSLOGTIMESTAMP` (`Dec 16 17:50:04`) lack timezone info. LimaCharlie assumes UTC. This skill automatically detects timezone mismatches by comparing parsed times to current UTC.

## When to Use

Use this skill when:

- **Setting up new log parsing**: Configure Grok patterns for a new log source
- **Troubleshooting parsing issues**: Logs aren't being parsed correctly or fields are missing
- **Modifying field extraction**: Need to add, remove, or change extracted fields
- **Testing parsing changes**: Validate new parsing rules before deploying to production
- **Generating adapter configurations**: Create YAML/CLI config for local USP adapters

Common scenarios:
- "Help me parse these firewall logs"
- "The timestamp isn't being extracted correctly from my syslog"
- "I need to add a new field to my adapter parsing"
- "Generate a Grok pattern for these log samples"
- "Test this parsing configuration before I deploy it"

## What This Skill Does

This skill provides a 5-phase workflow:

1. **Organization Selection** - Select the LimaCharlie organization
2. **Adapter Discovery** - Identify the adapter type and get current configuration
3. **Sample Log Collection** - Get sample logs from the adapter's sensor or user input
4. **Grok Pattern Generation** - Analyze logs and generate appropriate Grok patterns
5. **Validation & Deployment** - Test parsing and apply configuration

### Supported Adapter Types

| Type | Description | Configuration Method |
|------|-------------|---------------------|
| **External Adapter** | Cloud-managed adapters (syslog, webhook, API) | Update via `set_external_adapter` API |
| **Cloud Sensor** | Virtual sensors for cloud platforms (AWS, Azure, GCP, SaaS) | Update via `set_cloud_sensor` API |
| **One-off/USP Adapter** | On-prem adapters with local configuration | Output YAML/CLI config for user |

## Required Information

Before starting, gather:

- **Organization**: The LimaCharlie org where the adapter is configured
- **Adapter Type**: External Adapter, Cloud Sensor, or One-off/USP Adapter
- **Adapter Name**: For cloud-managed adapters, the name of the existing adapter
- **Sample Logs**: Either from the adapter's sensor or user-provided samples

## How to Use

### Phase 1: Organization Selection

Get the list of available organizations:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW"
)
```

Use `AskUserQuestion` to let the user select an organization if multiple are available.

### Phase 2: Adapter Discovery & Type Selection

Ask the user which adapter type they're working with using `AskUserQuestion`:

**Option A: External Adapter** (cloud-managed syslog, webhook, API)

1. List available external adapters:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_external_adapters
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\"}
    - Return: RAW"
)
```

2. Get the selected adapter's current configuration:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_external_adapter
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"name\": \"<ADAPTER_NAME>\"}
    - Return: RAW"
)
```

**Option B: Cloud Sensor** (AWS, Azure, GCP, SaaS)

1. List available cloud sensors:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_cloud_sensors
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\"}
    - Return: RAW"
)
```

2. Get the selected cloud sensor's current configuration:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_cloud_sensor
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"name\": \"<SENSOR_NAME>\"}
    - Return: RAW"
)
```

**Option C: One-off/USP Adapter** (local adapter, no cloud config)

No API calls needed. Proceed directly to sample log collection.

### Phase 3: Get Sample Log Data

**Option A: Query from adapter's sensor** (for cloud-managed adapters)

If the adapter is already ingesting data, you can fetch sample events:

1. Find the sensor by IID (Installation ID from the adapter's installation key):
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"selector\": \"iid == `<IID>`\"}
    - Return: RAW"
)
```

2. Get recent events from the sensor:

**IMPORTANT**: Always calculate timestamps dynamically using Bash FIRST:

```bash
# Run this to get current epoch timestamps for the last hour
start=$(date -d '1 hour ago' +%s) && end=$(date +%s) && echo "start=$start end=$end"
```

Then use the actual output values (e.g., `start=1764805928 end=1764809528`) directly in the API call - do NOT use placeholder values:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_historic_events
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"sid\": \"<SENSOR_ID>\", \"start\": 1764805928, \"end\": 1764809528, \"limit\": 10}
    - Return: RAW"
)
```

3. Extract the raw log content from the events for analysis.

**Option B: User provides sample logs**

If no data is available or for one-off adapters, ask the user to paste sample log lines.

Use `AskUserQuestion` or direct text input to collect sample logs.

### Recognizing Unparsed Events

When fetching events from a sensor, **unparsed logs** appear as:
- `event_type: "unknown_event"` in the routing
- Event payload contains only a `text` field with the raw log line

Example of an unparsed event:
```json
{
  "event": {
    "text": "2025-12-03 16:41:19 status installed shared-mime-info:amd64 2.2-1"
  },
  "routing": {
    "event_type": "unknown_event",
    "hostname": "my-adapter"
  }
}
```

This indicates no Grok parsing is configured for the adapter. The raw content in the `text` field is what you need to analyze and create a parsing pattern for.

### Phase 4: Generate Grok Pattern

Analyze the sample logs and generate an appropriate Grok pattern.

**Common Grok Patterns:**

| Pattern | Description | Example Match |
|---------|-------------|---------------|
| `%{TIMESTAMP_ISO8601:timestamp}` | ISO 8601 timestamp (YYYY-MM-DD) | `2024-01-15T12:30:45Z` or `2024-01-15 12:30:45` |
| `%{DATESTAMP:timestamp}` | US/EU date format (MM-DD-YY) | `01-15-24 12:30:45` |
| `%{SYSLOGTIMESTAMP:date}` | Syslog timestamp | `Jan 15 12:30:45` |
| `%{IP:ip_address}` | IPv4/IPv6 address | `192.168.1.100` |
| `%{HOSTNAME:host}` | Hostname | `server01.example.com` |
| `%{NUMBER:value}` | Numeric value | `12345` |
| `%{INT:count}` | Integer | `42` |
| `%{WORD:action}` | Single word | `ACCEPT` |
| `%{DATA:field}` | Non-greedy match (up to delimiter) | `any text` |
| `%{GREEDYDATA:message}` | Greedy match (rest of line) | `everything else` |
| `%{LOGLEVEL:level}` | Log level | `ERROR`, `WARN`, `INFO` |
| `%{POSINT:port}` | Positive integer | `443` |

> **Timestamp Pattern Warning**: Do NOT use `%{DATESTAMP}` for `YYYY-MM-DD` format logs - it will misparse the year (treating `2025-12-03` as day=25, month=12, year=03). Use `%{TIMESTAMP_ISO8601}` instead for any `YYYY-MM-DD` formatted timestamps.

**IMPORTANT - Grok Field Name for Text Platform:**

For text platform adapters, always use `message` as the key in `parsing_grok`:

```yaml
parsing_grok:
  message: '%{PATTERN:field} ...'  # Always use "message" as the key, NOT "text"
```

**Building the Mapping Configuration:**

```yaml
client_options:
  mapping:
    parsing_grok:
      message: '%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{WORD:service}\[%{INT:pid}\]: %{GREEDYDATA:message}'
    event_type_path: "service"
    event_time_path: "date"
    sensor_hostname_path: "host"
```

### Phase 4.5: Automatic Timestamp Timezone Check

> **REQUIRED**: After validation, MUST perform this sanity check for patterns without explicit timezone.

**Applies when Grok pattern uses:**
- `%{SYSLOGTIMESTAMP}` - e.g., `Dec 16 17:50:04`
- `%{DATESTAMP}` - e.g., `12-16-24 17:50:04`
- `%{TIMESTAMP_ISO8601}` without `Z` or offset - e.g., `2024-12-16 17:50:04`

**Automatic Detection Steps:**

1. After `validate_usp_mapping` returns, extract the `event_time` from results (epoch milliseconds)

2. Get current UTC epoch:
```bash
date -u +%s
```

3. Calculate the offset:
```bash
# Example: event_time=1734357004000 (milliseconds)
# current_utc=$(date -u +%s)
# offset_hours=$(( (current_utc - event_time/1000) / 3600 ))
```

4. **If offset is 4-12 hours**: The logs are likely in a local timezone (US timezones are UTC-5 to UTC-8)

   **Automatically warn the user:**
   > ⚠️ **Timezone Warning**: The parsed event_time appears to be ~[X] hours behind current UTC time. This suggests your log timestamps are in local time (e.g., Pacific Time), not UTC.
   >
   > LimaCharlie interprets all timestamps without timezone info as UTC. Your events will appear [X] hours in the past.
   >
   > **Recommendation**: Configure your log source to emit UTC timestamps:
   > - rsyslog: Add `$ActionFileDefaultTemplate RSYSLOG_FileFormat` to rsyslog.conf
   > - systemd-journald: Already uses UTC by default

5. Continue with deployment even if warning is shown (user can address later)

### Phase 5: Validate & Apply

**Step 1: Validate the parsing configuration**

Use `validate_usp_mapping` to test the Grok pattern against sample data:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: validate_usp_mapping
    - Parameters: {
        \"oid\": \"<SELECTED_ORG_ID>\",
        \"platform\": \"text\",
        \"mapping\": {
          \"parsing_grok\": {
            \"message\": \"%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{WORD:service}\\\\[%{INT:pid}\\\\]: %{GREEDYDATA:msg}\"
          },
          \"event_type_path\": \"service\",
          \"event_time_path\": \"date\",
          \"sensor_hostname_path\": \"host\"
        },
        \"text_input\": \"<SAMPLE_LOG_LINES>\"
      }
    - Return: RAW"
)
```

> **Note**: The `mapping` object should have `parsing_grok`, `event_type_path`, `event_time_path`, and `sensor_hostname_path` at the same level - NOT nested under a `parsing` key.

**Step 2: Review parsed results**

Show the parsed events to the user:
- Verify all expected fields are extracted
- Confirm event type assignment

**Automatic Timezone Sanity Check:**

If the Grok pattern uses `SYSLOGTIMESTAMP`, `DATESTAMP`, or `TIMESTAMP_ISO8601` without explicit timezone:

1. Get current UTC: `current_utc=$(date -u +%s)`
2. Extract `event_time` from validation result (milliseconds)
3. Calculate offset: `offset_hours=$(( (current_utc - event_time/1000) / 3600 ))`
4. **If offset is 4-12 hours**, display warning:

   "⚠️ **Timezone Mismatch Detected**: Parsed time is ~[offset] hours behind UTC. Your logs appear to be in local time. Events will be timestamped incorrectly in LimaCharlie. Consider configuring your log source to use UTC."

**Step 3: Iterate if needed**

If validation fails or fields are missing, adjust the Grok pattern and re-validate.

**Step 4: Apply configuration**

**For External Adapters:**
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: set_external_adapter
    - Parameters: {
        \"oid\": \"<SELECTED_ORG_ID>\",
        \"name\": \"<ADAPTER_NAME>\",
        \"adapter_type\": \"<EXISTING_TYPE>\",
        \"config\": {
          // ... existing config ...
          \"parsing_rules\": {
            \"parsing_grok\": {
              \"message\": \"<GROK_PATTERN>\"
            },
            \"event_type_path\": \"<PATH>\",
            \"event_time_path\": \"<PATH>\",
            \"sensor_hostname_path\": \"<PATH>\"
          }
        }
      }
    - Return: RAW"
)
```

**For Cloud Sensors:**
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: set_cloud_sensor
    - Parameters: {
        \"oid\": \"<SELECTED_ORG_ID>\",
        \"name\": \"<SENSOR_NAME>\",
        \"config\": {
          // ... existing config with updated parsing ...
        }
      }
    - Return: RAW"
)
```

**Step 5: Verify no adapter errors**

After applying the configuration for External Adapters or Cloud Sensors, check for any errors:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_org_errors
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\"}
    - Return: Look for errors related to the adapter"
)
```

If errors appear, review the adapter configuration and address the issues.

**For One-off/USP Adapters:**

Provide the configuration for the user to apply locally:

**YAML Config:**
```yaml
file:
  client_options:
    platform: text
    identity:
      installation_key: <IID>
      oid: <OID>
    sensor_seed_key: my-adapter
    mapping:
      parsing_grok:
        message: '%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{WORD:service}\[%{INT:pid}\]: %{GREEDYDATA:message}'
      event_type_path: "service"
      event_time_path: "date"
      event_time_timezone: "America/New_York"  # Required for SYSLOGTIMESTAMP (no timezone in pattern)
      sensor_hostname_path: "host"
  file_path: "/var/log/messages"
```

**CLI Config:**
```bash
./lc_adapter file \
  client_options.identity.installation_key=<IID> \
  client_options.identity.oid=<OID> \
  client_options.platform=text \
  client_options.sensor_seed_key=my-adapter \
  "client_options.mapping.parsing_grok.message=%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{WORD:service}\[%{INT:pid}\]: %{GREEDYDATA:message}" \
  client_options.mapping.event_type_path=service \
  client_options.mapping.event_time_path=date \
  client_options.mapping.event_time_timezone=America/New_York \
  client_options.mapping.sensor_hostname_path=host \
  file_path=/var/log/messages
```

> **IMPORTANT**: The `event_time_timezone` is REQUIRED when using `SYSLOGTIMESTAMP`, `DATESTAMP`, or `TIMESTAMP_ISO8601` without explicit timezone info. Without it, LimaCharlie assumes UTC and timestamps will be incorrect.

**When outputting CLI config for `test-limacharlie-adapter` skill, use this format:**
```
--grok '<PATTERN>'
--event-type <PATH>
--event-time <PATH>
--event-time-tz <TIMEZONE>  # Include when timestamp pattern lacks timezone
--hostname-path <PATH>
```

## Example Usage

### Example 1: Parse Syslog Logs

**User**: "Help me parse syslog logs from my Linux server"

**Sample log:**
```
Jan 15 12:30:45 server01 sshd[12345]: Accepted publickey for admin from 192.168.1.50 port 54321 ssh2
```

**Generated Grok pattern:**
```
%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{WORD:service}\[%{INT:pid}\]: %{GREEDYDATA:message}
```

**Mapping configuration:**
```yaml
mapping:
  parsing_grok:
    message: '%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{WORD:service}\[%{INT:pid}\]: %{GREEDYDATA:message}'
  event_type_path: "service"
  event_time_path: "date"
  event_time_timezone: "America/New_York"  # Required - SYSLOGTIMESTAMP has no timezone
  sensor_hostname_path: "host"
```

**CLI options for test-limacharlie-adapter:**
```
--grok '%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{WORD:service}\[%{INT:pid}\]: %{GREEDYDATA:message}'
--event-type service
--event-time date
--event-time-tz America/New_York
--hostname-path host
```

**Validation result:**
```json
{
  "valid": true,
  "results": [{
    "event": {
      "timestamp": "Jan 15 12:30:45",
      "event_type": "sshd",
      "message": "Accepted publickey for admin from 192.168.1.50 port 54321 ssh2"
    },
    "routing": {
      "hostname": "server01"
    }
  }]
}
```

### Example 2: Parse Firewall Logs

**User**: "I need to parse these firewall logs and extract the source/destination IPs"

**Sample log:**
```
2024-01-15T12:00:00Z ACCEPT TCP 192.168.1.100:54321 10.0.0.5:443 packets=1 bytes=78
```

**Generated Grok pattern:**
```
%{TIMESTAMP_ISO8601:timestamp} %{WORD:action} %{WORD:protocol} %{IP:src_ip}:%{NUMBER:src_port} %{IP:dst_ip}:%{NUMBER:dst_port} packets=%{NUMBER:packets} bytes=%{NUMBER:bytes}
```

**Mapping configuration:**
```yaml
mapping:
  parsing_grok:
    message: '%{TIMESTAMP_ISO8601:timestamp} %{WORD:action} %{WORD:protocol} %{IP:src_ip}:%{NUMBER:src_port} %{IP:dst_ip}:%{NUMBER:dst_port} packets=%{NUMBER:packets} bytes=%{NUMBER:bytes}'
  event_type_path: "action"
  event_time_path: "timestamp"
```

**Validation result:**
```json
{
  "valid": true,
  "results": [{
    "event": {
      "timestamp": "2024-01-15T12:00:00Z",
      "event_type": "ACCEPT",
      "protocol": "TCP",
      "src_ip": "192.168.1.100",
      "src_port": "54321",
      "dst_ip": "10.0.0.5",
      "dst_port": "443",
      "packets": "1",
      "bytes": "78"
    }
  }]
}
```

### Example 3: One-off USP Adapter Configuration

**User**: "I have a local adapter running, just give me the config to parse Apache access logs"

**Sample log:**
```
192.168.1.50 - admin [15/Jan/2024:12:30:45 +0000] "GET /api/users HTTP/1.1" 200 1234
```

**Generated configuration (YAML):**
```yaml
file:
  client_options:
    platform: text
    identity:
      installation_key: <YOUR_IID>
      oid: <YOUR_OID>
    sensor_seed_key: apache-logs
    mapping:
      parsing_grok:
        message: '%{COMMONAPACHELOG}'
      event_type_path: "verb"
      event_time_path: "timestamp"
  file_path: "/var/log/apache2/access.log"
```

**Generated configuration (CLI):**
```bash
./lc_adapter file \
  client_options.identity.installation_key=<YOUR_IID> \
  client_options.identity.oid=<YOUR_OID> \
  client_options.platform=text \
  client_options.sensor_seed_key=apache-logs \
  "client_options.mapping.parsing_grok.message=%{COMMONAPACHELOG}" \
  client_options.mapping.event_type_path=verb \
  client_options.mapping.event_time_path=timestamp \
  file_path=/var/log/apache2/access.log
```

## Additional Notes

### Pre-built Grok Patterns

LimaCharlie supports these pre-built patterns for common log formats:

| Pattern | Use Case |
|---------|----------|
| `%{COMMONAPACHELOG}` | Apache common log format |
| `%{COMBINEDAPACHELOG}` | Apache combined log format |
| `%{NGINXACCESS}` | Nginx access logs |

### Key/Value Parsing (Alternative to Grok)

For logs with `key=value` format (like CEF), use `parsing_re` with key-value extraction:

```yaml
mapping:
  parsing_re: '(?:<\d+>\s*)?(\w+)=(".*?"|\S+)'
```

This regex captures pairs where:
- Submatch 1 = Key name
- Submatch 2 = Value

### Field Path Syntax

Use `/` as separator for nested JSON navigation:
- `a` → access field `a`
- `a/b/c` → access nested field `a.b.c`

### Event Type Path Templates

The `event_type_path` supports template strings for dynamic event type assignment based on event content.

### Timestamp Timezone Handling

LimaCharlie assumes UTC for timestamps that don't include explicit timezone information.

**Formats with explicit timezone (safe):**
- ISO 8601 with `Z`: `2024-01-15T12:30:45Z`
- ISO 8601 with offset: `2024-01-15T12:30:45-08:00`
- RFC 3339: `2024-01-15T12:30:45.000-08:00`

**Formats without timezone (assumed UTC):**
- Syslog: `Jan 15 12:30:45`
- Simple datetime: `2024-01-15 12:30:45`

**Recommendation**: Configure log sources to emit UTC timestamps when possible. For syslog on Linux:
- rsyslog: Use `$ActionFileDefaultTemplate RSYSLOG_FileFormat` in rsyslog.conf
- journald: Timestamps are already in UTC by default

### Common Issues

1. **Pattern not matching**: Ensure special characters are escaped (e.g., `\[` for literal brackets)
2. **Greedy matching**: Use `%{DATA}` for non-greedy matching, `%{GREEDYDATA}` only at end of pattern
3. **Timestamp not parsing**: Verify timestamp format matches the Grok pattern exactly

### Common Pitfalls

1. **Using stale timestamps**: Always calculate epoch timestamps dynamically with Bash before querying `get_historic_events`. Never use placeholder or hardcoded values - the API will return empty results for timestamps outside the data retention window.

2. **Wrong mapping structure**: The `mapping` object should have `parsing_grok`, `event_type_path`, and `event_time_path` at the same level - NOT nested under a `parsing` key.

3. **Wrong Grok field name**: For text platform adapters, always use `message` as the key in `parsing_grok`, not `text`.

4. **DATESTAMP vs TIMESTAMP_ISO8601**:
   - `YYYY-MM-DD HH:MM:SS` → Use `%{TIMESTAMP_ISO8601}`
   - `MM-DD-YY HH:MM:SS` → Use `%{DATESTAMP}`
   - `Jan 15 12:30:45` → Use `%{SYSLOGTIMESTAMP}`

5. **Not recognizing unparsed events**: If you see `event_type: "unknown_event"` with only a `text` field, that means parsing is not configured - the `text` field contains the raw log data that needs a Grok pattern.

6. **Timezone assumptions for timestamps without timezone info**:
   - `SYSLOGTIMESTAMP`, `DATESTAMP`, and `TIMESTAMP_ISO8601` without `Z` or offset don't include timezone
   - LimaCharlie assumes UTC for all such timestamps
   - If logs are in local time (e.g., Pacific Time), events will appear 7-8 hours in the future
   - **Solution**: Configure log source to emit UTC timestamps, or verify with user that times appear correct

### Indexing Support

For searchable fields, configure custom indexing:

```yaml
indexing:
  - events_included: ["*"]
    path: "src_ip"
    index_type: "ip"
  - events_included: ["*"]
    path: "dst_ip"
    index_type: "ip"
```

Supported index types: `file_hash`, `file_path`, `file_name`, `domain`, `ip`, `user`, `service_name`, `package_name`

## Related Skills

- `limacharlie-call`: For other LimaCharlie API operations
- `detection-engineering`: Create D&R rules to detect patterns in parsed logs
- `test-limacharlie-adapter`: Deploy a test adapter to verify parsing
- `lookup-lc-doc`: Search LimaCharlie documentation for more parsing details

## Reference

For more details on parsing configuration:
- Adapter Usage: `./docs/limacharlie/doc/Sensors/Adapters/adapter-usage.md`
- Log Collection Guide: `./docs/limacharlie/doc/Sensors/Reference/logcollectionguide.md`
