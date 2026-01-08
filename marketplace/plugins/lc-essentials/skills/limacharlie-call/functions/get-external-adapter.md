
# Get External Adapter

Retrieve detailed configuration and metadata for a specific external adapter integration.

## When to Use

Use this skill when the user needs to:
- View the complete configuration of a specific external adapter
- Inspect parsing rules and field mappings
- Troubleshoot an adapter that isn't receiving data properly
- Review connection details and credentials
- Check the enabled status and tags of an adapter
- Examine error messages or last modification timestamps
- Verify parsing rules for external data normalization

Common scenarios:
- Troubleshooting external data ingestion issues
- Verifying adapter configuration before making changes
- Documenting external integration settings
- Checking parsing rules and field mappings
- Reviewing adapter metadata for audit purposes
- Investigating why an adapter stopped working
- Validating data transformation rules

## What This Skill Does

This skill retrieves the complete configuration and metadata for a specific external adapter by name. External adapters receive and process data from external sources like syslog servers, webhooks, custom APIs, and third-party security tools. Each adapter includes parsing rules that transform external data into LimaCharlie's normalized event format. The skill calls the LimaCharlie MCP tool to fetch the adapter's data configuration, user metadata (enabled status, tags, comments), and system metadata (creation info, modification history, errors).

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **adapter_name**: Name of the external adapter to retrieve (required)

To find the adapter name:
- Use the list-external-adapters skill to see all available adapters
- The adapter name is the unique identifier for each external adapter

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Correct external adapter name
3. The adapter name matches exactly (case-sensitive)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_external_adapter",
  parameters={
    "oid": "[organization-id]",
    "adapter_name": "[adapter-name]"
  }
)
```

**Tool Details:**
- Tool Name: `get_external_adapter`
- Required Parameters:
  - `oid`: Organization ID
  - `adapter_name`: Name of the external adapter to retrieve

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "data": {
    "adapter_type": "syslog",
    "listen_port": 514,
    "protocol": "udp",
    "parsing_rules": {
      "format": "syslog_rfc5424",
      "field_mappings": {
        "timestamp": "event.timestamp",
        "hostname": "routing.hostname",
        "message": "event.message"
      },
      "filters": [ ... ]
    }
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["syslog", "firewall"],
    "comment": "Palo Alto firewall syslog adapter",
    "expiry": 0
  },
  "sys_mtd": {
    "etag": "abc123def456",
    "created_by": "user@example.com",
    "created_at": 1704067200,
    "last_author": "admin@example.com",
    "last_mod": 1704153600,
    "guid": "unique-guid-123-456",
    "last_error": "",
    "last_error_ts": 0
  }
}
```

**Success:**
- The response contains the complete external adapter configuration
- `data`: The adapter configuration
  - `adapter_type`: Type of adapter (syslog, webhook, api, custom)
  - Connection details specific to adapter type
  - `parsing_rules`: Rules for transforming external data
    - Format specification
    - Field mappings for normalization
    - Filters and transformations
- `usr_mtd`: User-controlled metadata (enabled, tags, comment, expiry)
- `sys_mtd`: System-managed metadata (creation, modification, GUID, errors)

**Common Errors:**
- **Invalid adapter name**: Adapter name format is invalid or malformed
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions to view external adapters (requires platform_admin role)
- **Not Found**: External adapter with the specified name does not exist

### Step 4: Format the Response

Present the result to the user:
- Display the adapter name prominently
- Show the adapter type (syslog, webhook, etc.)
- Present connection details in a readable format
- Display parsing rules and field mappings clearly
- Show enabled status and tags
- Display creation and modification information
- Highlight any errors in the last_error field with timestamps
- Format sensitive fields (credentials, tokens) appropriately
- Provide context-specific guidance based on adapter type

## Example Usage

### Example 1: Get syslog adapter configuration

User request: "Show me the configuration for firewall-syslog"

Steps:
1. Extract organization ID from context
2. Use adapter name: "firewall-syslog"
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_external_adapter",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "adapter_name": "firewall-syslog"
  }
)
```

Expected response:
```json
{
  "data": {
    "adapter_type": "syslog",
    "listen_port": 514,
    "protocol": "udp",
    "parsing_rules": {
      "format": "syslog_rfc5424",
      "field_mappings": {
        "timestamp": "event.timestamp",
        "hostname": "routing.hostname",
        "severity": "event.severity",
        "message": "event.message"
      }
    }
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["syslog", "firewall", "palo-alto"],
    "comment": "Palo Alto firewall syslog adapter",
    "expiry": 0
  },
  "sys_mtd": {
    "created_by": "user@example.com",
    "created_at": 1704067200,
    "last_author": "admin@example.com",
    "last_mod": 1704153600,
    "guid": "guid-123-456",
    "last_error": "",
    "last_error_ts": 0
  }
}
```

Present to user:
```
External Adapter: firewall-syslog

Type: Syslog
Status: Enabled
Tags: syslog, firewall, palo-alto

Connection Details:
- Port: 514
- Protocol: UDP
- Format: RFC 5424

Parsing Rules:
- timestamp -> event.timestamp
- hostname -> routing.hostname
- severity -> event.severity
- message -> event.message

Metadata:
- Created by: user@example.com on January 1, 2024
- Last modified by: admin@example.com on January 2, 2024
- Comment: Palo Alto firewall syslog adapter
- Status: No errors

To send syslog data, configure your firewall to send logs to:
  - LimaCharlie syslog endpoint on port 514 (UDP)
```

### Example 2: Troubleshoot webhook adapter with errors

User request: "Why isn't the webhook-alerts adapter working?"

Steps:
1. Call tool to get adapter details
2. Check last_error field

Expected response with error:
```json
{
  "data": {
    "adapter_type": "webhook",
    "endpoint_url": "/webhook/alerts",
    "auth_token": "***"
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["webhook", "alerts"],
    "comment": "",
    "expiry": 0
  },
  "sys_mtd": {
    "last_error": "Failed to parse incoming webhook data: invalid JSON",
    "last_error_ts": 1704240000
  }
}
```

Present to user:
```
External Adapter: webhook-alerts

Type: Webhook
Status: Enabled (but experiencing errors)

ERROR DETECTED:
- Error: Failed to parse incoming webhook data: invalid JSON
- Occurred: January 3, 2024 at 12:00 PM

The adapter is enabled but cannot process incoming data due to parsing errors.

Troubleshooting steps:
1. Verify the webhook sender is sending valid JSON
2. Check the parsing rules match the incoming data format
3. Review recent webhook payloads for formatting issues
4. Update parsing rules if the data format has changed
5. Test with a sample webhook payload
```

### Example 3: Adapter not found

User request: "Get the api-integration adapter"

Steps:
1. Call tool with adapter name "api-integration"
2. Tool returns not found error

Present to user:
```
External adapter 'api-integration' not found.

This adapter may have been deleted or never existed.
Use the list-external-adapters skill to see all available adapters.
```

## Additional Notes

- External adapters are stored in the Hive under `external_adapter` hive name with `{oid}` partition
- Adapter names are case-sensitive - use exact names from list-external-adapters
- The `data` field structure varies by adapter type:
  - **Syslog**: listen_port, protocol, parsing_rules
  - **Webhook**: endpoint_url, auth_token, parsing_rules
  - **API**: poll_url, poll_interval, auth_headers, parsing_rules
  - **Custom**: varies by custom implementation
- Parsing rules are critical for proper data normalization
- Field mappings transform external field names to LimaCharlie's event schema
- The `last_error` field is critical for troubleshooting - check it first
- External adapter configurations may contain sensitive credentials - handle securely
- The `enabled` field controls active data reception - disabled adapters don't process data
- Tags help organize adapters by source, type, or purpose
- The `etag` in sys_mtd is used for optimistic concurrency control during updates
- Use the set-external-adapter skill to update configurations
- Use the delete-external-adapter skill to remove adapters
- Parsing rules include:
  - Format specification (syslog, JSON, CEF, LEEF, custom regex)
  - Field mappings (external field -> LimaCharlie field)
  - Filters (include/exclude patterns)
  - Transformations (data normalization, enrichment)
- Common adapter types:
  - **Syslog**: Receives syslog messages (RFC 3164, RFC 5424)
  - **Webhook**: Receives HTTP POST requests
  - **API Polling**: Fetches data from external APIs periodically
  - **Custom**: Custom protocol implementations

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/hive.go`
For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp-server/blob/master/internal/tools/hive/external_adapters.go`
