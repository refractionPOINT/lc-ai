
# Set External Adapter

Create a new external adapter or update an existing external adapter configuration for external data ingestion and processing.

## When to Use

Use this skill when the user needs to:
- Configure a new external adapter for syslog, webhook, or API data ingestion
- Update an existing adapter's configuration or credentials
- Modify parsing rules and field mappings
- Enable or disable an external adapter
- Update connection parameters or credentials
- Change adapter tags for organization
- Reconfigure adapter after data format changes

Common scenarios:
- Initial setup of external data source integrations
- Updating parsing rules when external data format changes
- Configuring syslog receivers for firewall, router, or switch logs
- Setting up webhook receivers for third-party alerts
- Modifying field mappings for better data normalization
- Enabling previously disabled adapters
- Fixing configuration errors in external integrations

## What This Skill Does

This skill creates or updates an external adapter configuration in the organization's Hive storage. External adapters receive and process data from external sources like syslog servers, webhooks, custom APIs, and third-party security tools. Each adapter includes parsing rules that transform external data formats into LimaCharlie's normalized event format. The skill calls the LimaCharlie MCP tool to store the adapter configuration with automatic enablement. If an adapter with the same name exists, it will be updated; otherwise, a new adapter is created.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **adapter_name**: Name for the external adapter (required, alphanumeric with hyphens/underscores)
- **adapter_config**: Complete configuration object (required, structure varies by adapter type - include adapter type within config)

The config typically includes:
- **Connection parameters**: Port, protocol, URL, etc. (varies by type)
- **parsing_rules**: Rules for transforming external data
  - **format**: Data format (syslog, json, cef, leef, custom_regex)
  - **field_mappings**: External field -> LimaCharlie field mappings
  - **filters**: Include/exclude patterns (optional)
  - **transformations**: Data normalization rules (optional)
- **Authentication**: Credentials, tokens, API keys (if required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Unique adapter name (or name of existing adapter to update)
3. Complete adapter configuration with all required fields (including adapter type within config)
4. Valid parsing rules that match the external data format
5. Correct connection parameters and credentials
6. Understanding of the external data source's format and structure

**Pre-Deployment Validation**: Before deploying, use `validate_usp_mapping` to test your parsing rules against sample data. This ensures correct field extraction before production deployment.

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_external_adapter",
  parameters={
    "oid": "[organization-id]",
    "adapter_name": "[adapter-name]",
    "adapter_config": {
      "type": "syslog",
      "listen_port": 514,
      "protocol": "udp",
      "parsing_rules": {
        "format": "syslog_rfc5424",
        "field_mappings": {
          "timestamp": "event.timestamp",
          "hostname": "routing.hostname",
          "message": "event.message"
        }
      }
    }
  }
)
```

**Tool Details:**
- Tool Name: `set_external_adapter`
- Required Parameters:
  - `oid`: Organization ID
  - `adapter_name`: Name for the external adapter
  - `adapter_config`: Configuration object with adapter-specific settings (include adapter type within config)

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "guid": "unique-adapter-guid",
  "hive": {
    "name": "external_adapter",
    "partition": "global"
  },
  "name": "adapter-name"
}
```

**Success:**
- The external adapter has been created or updated successfully
- The response contains the adapter's GUID and hive information
- The adapter is automatically enabled unless specified otherwise
- The adapter will begin processing data based on its configuration

**Common Errors:**
- **Invalid configuration**: Missing required fields, invalid configuration structure, or malformed parsing rules
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions to manage external adapters (requires platform_admin role)
- **Conflict**: ETag mismatch if updating existing adapter with concurrent modifications

### Step 4: Format the Response

Present the result to the user:
- Confirm successful creation or update of the external adapter
- Display the adapter name and type
- Show the enabled status
- List any tags applied
- Provide connection details for sending data
- Suggest testing data ingestion with sample events
- For updates, note what changed

## Example Usage

### Example 1: Create syslog adapter for firewall logs

User request: "Set up a syslog adapter for our Palo Alto firewall logs"

Steps:
1. Extract organization ID from context
2. Prepare adapter name: "firewall-syslog"
3. Gather configuration: port, protocol, parsing rules
4. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="set_external_adapter",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "adapter_name": "firewall-syslog",
    "adapter_config": {
      "type": "syslog",
      "listen_port": 514,
      "protocol": "udp",
      "parsing_rules": {
        "format": "syslog_rfc5424",
        "field_mappings": {
          "timestamp": "event.timestamp",
          "hostname": "routing.hostname",
          "severity": "event.severity",
          "facility": "event.facility",
          "message": "event.message",
          "source_ip": "routing.source_ip"
        },
        "filters": {
          "include_patterns": ["threat", "traffic", "system"]
        }
      }
    }
  }
)
```

Expected response:
```json
{
  "guid": "abc-123-def-456",
  "hive": {
    "name": "external_adapter",
    "partition": "global"
  },
  "name": "firewall-syslog"
}
```

Present to user:
```
Successfully created syslog external adapter!

Adapter Name: firewall-syslog
Type: Syslog
Status: Enabled

Connection Details:
- Protocol: UDP
- Port: 514
- Format: RFC 5424

Parsing Rules:
- timestamp -> event.timestamp
- hostname -> routing.hostname
- severity -> event.severity
- message -> event.message

To send logs from your Palo Alto firewall:
1. Configure syslog forwarding to LimaCharlie's syslog endpoint
2. Use UDP port 514
3. Send logs in RFC 5424 format

The adapter will begin processing logs as soon as they arrive.
Test by sending a sample log and checking the event stream.
```

### Example 2: Create webhook adapter for alerts

User request: "Set up a webhook to receive alerts from our monitoring system"

Steps:
1. Prepare adapter name: "monitoring-webhook"
2. Configure webhook settings
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="set_external_adapter",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "adapter_name": "monitoring-webhook",
    "adapter_config": {
      "type": "webhook",
      "endpoint_url": "/webhook/monitoring",
      "auth_token": "secret-token-123",
      "parsing_rules": {
        "format": "json",
        "field_mappings": {
          "alert_name": "event.alert_name",
          "severity": "event.severity",
          "timestamp": "event.timestamp",
          "description": "event.message",
          "source": "routing.source"
        }
      }
    }
  }
)
```

Expected response:
```json
{
  "guid": "webhook-guid-789",
  "name": "monitoring-webhook"
}
```

Present to user:
```
Successfully created webhook external adapter!

Adapter Name: monitoring-webhook
Type: Webhook
Status: Enabled

Webhook Endpoint:
https://api.limacharlie.io/webhook/monitoring

Authentication:
- Include header: Authorization: Bearer secret-token-123

Expected Format: JSON
Field Mappings:
- alert_name -> event.alert_name
- severity -> event.severity
- timestamp -> event.timestamp
- description -> event.message

Configure your monitoring system to POST alerts to the webhook endpoint.
```

### Example 3: Update parsing rules for existing adapter

User request: "Update the firewall-syslog adapter to parse additional fields"

Steps:
1. Get existing configuration (use get-external-adapter skill)
2. Update parsing rules with new field mappings
3. Call tool with updated configuration
4. Include all existing fields plus new mappings

Present to user:
```
Successfully updated external adapter 'firewall-syslog'!

Updated parsing rules to include:
- New field: action -> event.action
- New field: destination_port -> event.dest_port
- New field: protocol -> event.network_protocol

The adapter will now extract these additional fields from incoming syslog messages.
```

## Additional Notes

- External adapters use the Hive storage system under `external_adapter` hive with `global` partition
- Adapter names must be unique within the organization
- The config structure varies by adapter type (syslog, webhook, api, custom)
- Parsing rules are critical - incorrect rules result in unparsed or malformed events
- **Pre-deployment validation**: Use `validate_usp_mapping` to test parsing rules with sample data before deploying. This validates regex patterns, field mappings, and transformations against real input
- Field mappings should align with LimaCharlie's event schema for proper normalization
- Common LimaCharlie event fields:
  - `event.timestamp`: Event timestamp
  - `event.event_type`: Type of event
  - `event.message`: Event message or description
  - `event.severity`: Event severity level
  - `routing.hostname`: Source hostname
  - `routing.source_ip`: Source IP address
- The adapter is automatically enabled unless explicitly disabled in usr_mtd
- Tags are useful for organizing adapters by source, type, or purpose
- Use meaningful adapter names that indicate the data source and type
- When updating, the entire configuration is replaced - include all fields
- For credential updates, update the adapter configuration with new credentials
- The `etag` field can be used for concurrent update protection
- After creating or updating, test data ingestion with sample events
- Check the adapter's last_error field if data isn't appearing (use get-external-adapter)
- Common adapter types and their key configuration fields:
  - **Syslog**: listen_port, protocol, parsing_rules
  - **Webhook**: endpoint_url, auth_token, parsing_rules
  - **API Polling**: poll_url, poll_interval, auth_headers, parsing_rules
  - **Custom**: custom configuration fields, parsing_rules
- Parsing rule formats:
  - **syslog**: RFC 3164 or RFC 5424
  - **json**: JSON objects
  - **cef**: Common Event Format
  - **leef**: Log Event Extended Format
  - **custom_regex**: Regular expression patterns
- Use list-external-adapters to verify the adapter was created
- Use get-external-adapter to inspect the configuration after creation
- Use delete-external-adapter to remove adapters that are no longer needed
- Consider network security when exposing syslog ports or webhook endpoints
- Document parsing rules and field mappings for maintenance

## Related Functions

- `validate_usp_mapping` - Test parsing configurations before deployment
- `get_external_adapter` - Retrieve existing adapter configuration
- `list_external_adapters` - List all configured adapters
- `delete_external_adapter` - Remove an adapter

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/hive.go`
For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp-server/blob/master/internal/tools/hive/external_adapters.go`
