
# Validate USP Mapping

Validate USP (Universal Sensor Protocol) adapter mapping configurations by testing them against sample input data to ensure correct parsing before deployment.

## When to Use

Use this skill when the user needs to:
- Test USP adapter mapping configurations before deploying to production
- Verify that parsing rules correctly extract fields from sample data
- Debug parsing issues with external data sources
- Validate field mappings and transformations
- Test regex patterns or format specifications
- Ensure indexing rules work as expected
- Iterate on parsing rules until data is correctly normalized
- Validate multi-mapping selection logic

Common scenarios:
- "Test this USP mapping configuration with sample syslog data"
- "Validate my parsing rules work correctly before deploying"
- "Check if this regex pattern extracts the fields I need"
- "Test my JSON field mappings with sample events"
- "Verify this CEF parsing configuration"
- "Debug why my USP adapter isn't parsing data correctly"

## What This Skill Does

This skill validates USP adapter mapping configurations by sending them to the LimaCharlie API along with sample input data. The API processes the data using the provided parsing rules and returns the parsed events or error messages. This allows you to verify that your parsing configuration correctly transforms raw external data into LimaCharlie's normalized event format before deploying the adapter to production. The validation tests the complete parsing pipeline including format detection, field extraction, mapping application, and optional indexing rules.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.

- **oid**: Organization ID (required for API authentication)
- **platform**: Parser platform type (required: 'text', 'json', 'cef', 'gcp', 'aws')
- **mapping** OR **mappings**: Parsing configuration (at least one required)
  - **mapping**: Single mapping descriptor (use for single-mapping configs)
  - **mappings**: Array of mapping descriptors (use for multi-mapping selection)
- **text_input** OR **json_input**: Sample data to test (at least one required)
  - **text_input**: Newline-separated text string (use for text, syslog, CEF formats)
  - **json_input**: Array of pre-parsed JSON objects (use for JSON, GCP, AWS formats)
- **hostname** (optional): Default hostname for sensors (defaults to 'validation-test')
- **indexing** (optional): Array of indexing rules to test

**Mapping Configuration Structure:**
```
{
  "parsing_re": "regex pattern with named groups",    // for regex parsing
  "parsing_grok": {                                   // for Grok parsing
    "message": "%{PATTERN:field}..."
  },
  "event_type_path": "field/path",                   // field to use as event type
  "event_time_path": "field/path",                   // field to use as timestamp
  "event_time_timezone": "America/New_York",         // timezone for timestamps without TZ info (optional)
  "sensor_hostname_path": "field/path",              // field to use as sensor hostname
  "sensor_key_path": "field/path",                   // field for unique sensor ID
  "transform": {...},                                // optional transform to apply
  "drop_fields": ["field1", "field2"]                // fields to drop
}
```

**Timezone Handling:**
- `event_time_timezone`: Specifies the timezone for parsing timestamps that don't include timezone information
- Uses IANA timezone names (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`, `UTC`)
- If not specified, timestamps without timezone info are treated as UTC
- Unix epoch timestamps are not affected by this setting (they are inherently timezone-agnostic)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Correct platform type for your data source
3. Complete mapping configuration with parsing rules
4. Representative sample data that matches your production format
5. Either single mapping or mappings array (not both)
6. Either text_input or json_input (not both)
7. Sample data that covers typical cases and edge cases

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="validate_usp_mapping",
  parameters={
    "oid": "[organization-id]",
    "platform": "text",
    "mapping": {
      "parsing": {
        "fmt": "regex",
        "re": "(?P<timestamp>\\S+)\\s+(?P<hostname>\\S+)\\s+(?P<message>.*)"
      },
      "mappings": {
        "timestamp": "event.timestamp",
        "hostname": "routing.hostname",
        "message": "event.message"
      }
    },
    "text_input": "2024-01-01T12:00:00Z server01 User login successful"
  }
)
```

**Tool Details:**
- Tool Name: `validate_usp_mapping`
- Required Parameters:
  - `oid`: Organization ID
  - `platform`: Parser platform type
  - `mapping` OR `mappings`: Parsing configuration
  - `text_input` OR `json_input`: Sample data
- Optional Parameters:
  - `hostname`: Default hostname (defaults to 'validation-test')
  - `indexing`: Indexing rules to apply

**Platform Types:**
- **text**: Line-based text parsing with regex or patterns
- **json**: JSON object parsing and field extraction
- **cef**: Common Event Format (CEF) parsing
- **gcp**: Google Cloud Platform log formats
- **aws**: AWS CloudTrail/CloudWatch log formats

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "valid": true,
  "message": "USP mapping is valid",
  "results": [
    {
      "event": {
        "timestamp": "2024-01-01T12:00:00Z",
        "message": "User login successful"
      },
      "routing": {
        "hostname": "server01"
      }
    }
  ],
  "parsed_events_count": 1
}
```

**Success Response:**
- `valid`: true
- `message`: Success message
- `results`: Array of parsed events showing the transformation
- `parsed_events_count`: Number of successfully parsed events
- No `errors` field or empty errors array

**Validation Failure:**
```json
{
  "valid": false,
  "message": "USP mapping validation failed with 2 error(s)",
  "errors": [
    "Failed to parse line 1: regex pattern did not match",
    "Missing required field: timestamp"
  ],
  "results": [],
  "parsed_events_count": 0
}
```

**Common Errors:**
- **Invalid platform**: Platform type not recognized or unsupported
- **Regex pattern errors**: Pattern syntax errors or doesn't match input
- **Missing required fields**: Parsing didn't extract required fields
- **Field mapping errors**: Target field path is invalid
- **Format mismatch**: Input data doesn't match expected format
- **Invalid JSON**: JSON input is malformed
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions for the organization

### Step 4: Format the Response

Present the result to the user:
- Clearly indicate if validation passed or failed
- Show the number of events successfully parsed
- Display parsed events to verify field extraction
- Highlight any errors with specific messages
- Show which input lines failed to parse
- Compare input data with parsed output
- Suggest fixes for common parsing issues
- Recommend next steps (adjust config or deploy)

## Example Usage

### Example 1: Validate Text Parsing with Regex

User request: "Test this syslog parsing configuration with sample data"

Steps:
1. Extract organization ID from context
2. Prepare sample syslog data
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="validate_usp_mapping",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "platform": "text",
    "mapping": {
      "parsing": {
        "fmt": "regex",
        "re": "(?P<timestamp>\\S+)\\s+(?P<hostname>\\S+)\\s+(?P<severity>\\w+):\\s+(?P<message>.*)"
      },
      "mappings": {
        "timestamp": "event.timestamp",
        "hostname": "routing.hostname",
        "severity": "event.severity",
        "message": "event.message"
      }
    },
    "text_input": "2024-01-01T12:00:00Z firewall01 INFO: Connection established from 192.168.1.100\n2024-01-01T12:00:05Z firewall01 WARN: High traffic detected"
  }
)
```

Expected response:
```json
{
  "valid": true,
  "message": "USP mapping is valid",
  "results": [
    {
      "event": {
        "timestamp": "2024-01-01T12:00:00Z",
        "severity": "INFO",
        "message": "Connection established from 192.168.1.100"
      },
      "routing": {
        "hostname": "firewall01"
      }
    },
    {
      "event": {
        "timestamp": "2024-01-01T12:00:05Z",
        "severity": "WARN",
        "message": "High traffic detected"
      },
      "routing": {
        "hostname": "firewall01"
      }
    }
  ],
  "parsed_events_count": 2
}
```

Present to user:
```
✓ USP mapping validation successful!

Parsed 2 events from sample data:

Event 1:
  timestamp: 2024-01-01T12:00:00Z
  severity: INFO
  hostname: firewall01
  message: Connection established from 192.168.1.100

Event 2:
  timestamp: 2024-01-01T12:00:05Z
  severity: WARN
  hostname: firewall01
  message: High traffic detected

The parsing rules correctly extract all fields. Ready to deploy!
Next step: Use set-external-adapter to deploy this configuration.
```

### Example 2: Validate JSON Parsing

User request: "Test my JSON field mappings with sample events"

Steps:
1. Prepare JSON sample data
2. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="validate_usp_mapping",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "platform": "json",
    "mapping": {
      "mappings": {
        "alert_name": "event.alert_name",
        "alert_severity": "event.severity",
        "timestamp": "event.timestamp",
        "source_ip": "event.source_ip",
        "destination_ip": "event.destination_ip",
        "host": "routing.hostname"
      }
    },
    "json_input": [
      {
        "alert_name": "Suspicious Login",
        "alert_severity": "high",
        "timestamp": "2024-01-01T12:00:00Z",
        "source_ip": "203.0.113.45",
        "destination_ip": "10.0.1.100",
        "host": "webserver01"
      },
      {
        "alert_name": "Port Scan Detected",
        "alert_severity": "medium",
        "timestamp": "2024-01-01T12:05:00Z",
        "source_ip": "198.51.100.22",
        "destination_ip": "10.0.1.200",
        "host": "firewall01"
      }
    ]
  }
)
```

Expected response:
```json
{
  "valid": true,
  "message": "USP mapping is valid",
  "results": [
    {
      "event": {
        "alert_name": "Suspicious Login",
        "severity": "high",
        "timestamp": "2024-01-01T12:00:00Z",
        "source_ip": "203.0.113.45",
        "destination_ip": "10.0.1.100"
      },
      "routing": {
        "hostname": "webserver01"
      }
    },
    {
      "event": {
        "alert_name": "Port Scan Detected",
        "severity": "medium",
        "timestamp": "2024-01-01T12:05:00Z",
        "source_ip": "198.51.100.22",
        "destination_ip": "10.0.1.200"
      },
      "routing": {
        "hostname": "firewall01"
      }
    }
  ],
  "parsed_events_count": 2
}
```

Present to user:
```
✓ JSON field mappings validated successfully!

Parsed 2 JSON events:

Event 1:
  alert_name: Suspicious Login
  severity: high (mapped from alert_severity)
  source_ip: 203.0.113.45
  destination_ip: 10.0.1.100
  hostname: webserver01

Event 2:
  alert_name: Port Scan Detected
  severity: medium (mapped from alert_severity)
  source_ip: 198.51.100.22
  destination_ip: 10.0.1.200
  hostname: firewall01

All fields mapped correctly. Configuration is ready for deployment.
```

### Example 3: Catch Parsing Errors

User request: "Why isn't my regex pattern matching the syslog data?"

Steps:
1. Call tool with incorrect regex
2. Get validation errors
3. Help user fix the pattern

Call:
```
mcp__limacharlie__lc_call_tool(
  tool_name="validate_usp_mapping",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "platform": "text",
    "mapping": {
      "parsing": {
        "fmt": "regex",
        "re": "(?P<timestamp>\\d{4}-\\d{2}-\\d{2})\\s+(?P<message>.*)"
      },
      "mappings": {
        "timestamp": "event.timestamp",
        "message": "event.message"
      }
    },
    "text_input": "2024-01-01T12:00:00Z This is a log message"
  }
)
```

Expected response:
```json
{
  "valid": false,
  "message": "USP mapping validation failed with 1 error(s)",
  "errors": [
    "Failed to parse line 1: regex pattern did not match input"
  ],
  "results": [],
  "parsed_events_count": 0
}
```

Present to user:
```
✗ USP mapping validation failed

Errors:
  - Failed to parse line 1: regex pattern did not match input

Issue: Your regex pattern expects date format YYYY-MM-DD but the input
       uses ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)

Your pattern: (?P<timestamp>\\d{4}-\\d{2}-\\d{2})
Input data:   2024-01-01T12:00:00Z

Fix: Update the regex to match ISO 8601 timestamps:
     (?P<timestamp>\\S+)  (matches non-whitespace characters)

Or use a more specific pattern:
     (?P<timestamp>\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z)

Try validating again with the updated pattern.
```

### Example 4: Validate with Indexing Rules

User request: "Test my USP mapping with custom indexing rules"

Steps:
1. Include indexing configuration
2. Validate parsing and indexing together

```
mcp__limacharlie__lc_call_tool(
  tool_name="validate_usp_mapping",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "platform": "text",
    "mapping": {
      "parsing": {
        "fmt": "regex",
        "re": "(?P<timestamp>\\S+)\\s+(?P<level>\\w+)\\s+(?P<message>.*)"
      },
      "mappings": {
        "timestamp": "event.timestamp",
        "level": "event.severity",
        "message": "event.message"
      }
    },
    "indexing": [
      {
        "field": "event.severity",
        "index": true
      },
      {
        "field": "event.timestamp",
        "index": true
      }
    ],
    "text_input": "2024-01-01T12:00:00Z ERROR Database connection failed"
  }
)
```

Present to user:
```
✓ USP mapping with indexing validated successfully!

Parsed 1 event:
  timestamp: 2024-01-01T12:00:00Z (indexed)
  severity: ERROR (indexed)
  message: Database connection failed

Indexing rules applied:
  - event.severity will be indexed for fast searching
  - event.timestamp will be indexed for time-based queries

Configuration is ready. Deploy with set-external-adapter.
```

## Additional Notes

- **API-Based Validation**: Requires organization context and valid credentials
- **Real Parsing Engine**: Uses the actual USP parsing engine, not simulation
- **Representative Data**: Use real sample data from your production source
- **Multiple Events**: Test with multiple sample events to catch edge cases
- **Error Messages**: Specific error messages help debug parsing issues
- **Iterative Testing**: Adjust config, re-validate until parsing is correct
- **Platform Selection**:
  - Use **text** for: syslog, custom text logs, regex-based parsing
  - Use **json** for: JSON APIs, JSON-formatted logs
  - Use **cef** for: ArcSight CEF, McAfee ePO
  - Use **gcp** for: Google Cloud logs, Stackdriver
  - Use **aws** for: CloudTrail, CloudWatch, VPC Flow Logs
- **Parsing Formats** (for text platform):
  - **regex**: Custom regular expressions with named capture groups
  - **syslog**: RFC 3164 or RFC 5424 syslog
  - **csv**: Comma-separated values
  - **tsv**: Tab-separated values
  - **kv**: Key-value pairs (key=value format)
- **Field Mapping Targets**:
  - **event.***: Event-specific fields (timestamp, message, severity, etc.)
  - **routing.***: Routing metadata (hostname, source_ip, etc.)
  - **Custom fields**: Any valid field path
- **Common Patterns**:
  - **ISO 8601 timestamp**: `(?P<timestamp>\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?Z?)`
  - **Syslog timestamp**: `(?P<timestamp>\\w{3}\\s+\\d{1,2}\\s+\\d{2}:\\d{2}:\\d{2})`
  - **IPv4 address**: `(?P<ip>\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})`
  - **Severity level**: `(?P<severity>DEBUG|INFO|WARN|ERROR|CRITICAL)`
- **Testing Strategy**:
  1. Start with simplest parsing rules
  2. Validate with minimal sample data
  3. Gradually add complexity (more fields, transformations)
  4. Test with diverse samples (normal cases, edge cases, malformed data)
  5. Verify all required fields are extracted
  6. Check field mappings produce correct output structure
- **Validation Workflow**:
  1. **Generate** config based on data source documentation
  2. **Validate** with this skill using sample data
  3. **Review** parsed events to verify correctness
  4. **Iterate** on parsing rules if needed
  5. **Deploy** with set-external-adapter once validated
- **Multi-Mapping Selection**: Use `mappings` array when different event types require different parsing rules. The engine selects the appropriate mapping based on event content.
- **Indexing**: Indexing rules improve query performance for frequently searched fields
- **Hostname Default**: If not extracted from data, defaults to 'validation-test' (or custom value)
- **Performance**: Validation is fast (typically <1 second for small samples)
- **Limits**: Validate with reasonable sample sizes (1-100 events)
- **Security**: Sample data is not stored; validation is ephemeral
- **Next Steps After Validation**:
  1. Use **set-external-adapter** to deploy the validated configuration
  2. Configure your external data source to send data
  3. Monitor incoming events to verify production parsing
  4. Adjust and re-validate if production data differs from samples
- **Related Skills**:
  - **set-external-adapter**: Deploy validated USP configuration
  - **get-external-adapter**: Retrieve existing adapter configs
  - **list-external-adapters**: List all configured adapters
  - **delete-external-adapter**: Remove adapters

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/validation.go` (ValidateUSPMapping method, lines 294-376)

For the API implementation, check: `https://github.com/refractionPOINT/lc_api-go/blob/master/service/endpoint_usp_validation.go`

For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp-server/blob/master/internal/tools/rules/usp_validation.go`
