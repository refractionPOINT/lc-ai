
# List External Adapters

Retrieve all external adapter configurations from a LimaCharlie organization, showing which external data sources are being ingested.

## When to Use

Use this skill when the user needs to:
- View all configured external adapter integrations
- Check which external systems are sending data to LimaCharlie
- Audit existing external data source configurations
- Find a specific adapter by name or tags
- Review adapter enablement status and metadata
- Troubleshoot external data ingestion issues

Common scenarios:
- Initial setup verification after configuring external adapters
- Security audits of external data source coverage
- Compliance reporting on data ingestion sources
- Troubleshooting missing external telemetry
- Planning new external adapter deployments
- Documenting current external data ingestion setup

## What This Skill Does

This skill retrieves all external adapter configurations from the organization's Hive storage. External adapters are integrations that receive and process data from external sources such as syslog servers, webhooks, custom APIs, third-party security tools (firewalls, EDR, SIEM), and other log sources. Each adapter typically includes parsing rules to normalize the external data into LimaCharlie's event format. The skill calls the LimaCharlie MCP tool to list all entries in the "external_adapter" hive with the organization ID as the partition key, returning each adapter's configuration, enablement status, tags, and metadata.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

No additional parameters are needed.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="list_external_adapters",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**Tool Details:**
- Tool Name: `list_external_adapters`
- Required Parameters:
  - `oid`: Organization ID

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "adapter-name-1": {
    "data": {
      "adapter_type": "syslog",
      "listen_port": 514,
      "parsing_rules": { ... }
    },
    "usr_mtd": {
      "enabled": true,
      "tags": ["syslog", "firewall"],
      "comment": "Firewall syslog adapter",
      "expiry": 0
    },
    "sys_mtd": {
      "etag": "abc123",
      "created_by": "user@example.com",
      "created_at": 1704067200,
      "last_author": "user@example.com",
      "last_mod": 1704153600,
      "guid": "unique-guid-123",
      "last_error": "",
      "last_error_ts": 0
    }
  },
  "adapter-name-2": { ... }
}
```

**Success:**
- The response contains a map of external adapter configurations
- Each key is the adapter name
- Each value contains:
  - `data`: The adapter configuration including type, connection details, and parsing rules
  - `usr_mtd`: User metadata (enabled status, tags, comment, expiry)
  - `sys_mtd`: System metadata (creation info, modification info, GUID, errors)
- If no external adapters exist, the response will be an empty object `{}`

**Common Errors:**
- **Invalid organization ID**: Organization ID format is invalid or malformed
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions to view external adapters (requires platform_admin role)
- **Not Found**: Organization does not exist or hive partition not found

### Step 4: Format the Response

Present the result to the user:
- Display each external adapter with its name and key properties
- Show the adapter type (syslog, webhook, API, etc.)
- Indicate whether each adapter is enabled or disabled
- List any tags associated with the adapter
- Show creation and last modification dates
- Highlight any errors in the last_error field
- Provide a count of total external adapters configured
- If filtering, apply filters by name, tags, or adapter type

## Example Usage

### Example 1: List all external adapters

User request: "Show me all external adapter configurations"

Steps:
1. Extract the organization ID from context
2. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_external_adapters",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "firewall-syslog": {
    "data": {
      "adapter_type": "syslog",
      "listen_port": 514,
      "protocol": "udp",
      "parsing_rules": {
        "format": "syslog_rfc5424",
        "field_mappings": { ... }
      }
    },
    "usr_mtd": {
      "enabled": true,
      "tags": ["syslog", "firewall", "network"],
      "comment": "Palo Alto firewall syslog adapter",
      "expiry": 0
    },
    "sys_mtd": {
      "created_at": 1704067200,
      "last_mod": 1704153600,
      "last_error": ""
    }
  },
  "webhook-alerts": {
    "data": {
      "adapter_type": "webhook",
      "endpoint_url": "/webhook/alerts",
      "auth_token": "***",
      "parsing_rules": {
        "format": "json",
        "event_type_field": "alert_type"
      }
    },
    "usr_mtd": {
      "enabled": true,
      "tags": ["webhook", "alerts"],
      "comment": "Custom alert webhook integration",
      "expiry": 0
    },
    "sys_mtd": {
      "created_at": 1704240000,
      "last_mod": 1704240000,
      "last_error": ""
    }
  }
}
```

Present to user:
```
Found 2 external adapters:

1. firewall-syslog
   - Type: Syslog
   - Status: Enabled
   - Port: 514 (UDP)
   - Tags: syslog, firewall, network
   - Comment: Palo Alto firewall syslog adapter
   - Created: January 1, 2024
   - Last Modified: January 2, 2024

2. webhook-alerts
   - Type: Webhook
   - Status: Enabled
   - Endpoint: /webhook/alerts
   - Tags: webhook, alerts
   - Comment: Custom alert webhook integration
   - Created: January 3, 2024
```

### Example 2: Check for syslog adapters

User request: "Which syslog adapters do we have configured?"

Steps:
1. Call tool to get all external adapters
2. Filter results for syslog adapters (check adapter_type or tags)
3. Present filtered results:
```
Found 1 syslog adapter:

firewall-syslog
- Type: Syslog
- Status: Enabled
- Port: 514 (UDP)
- Format: RFC 5424
- Comment: Palo Alto firewall syslog adapter
```

### Example 3: No external adapters configured

User request: "List external adapters"

Steps:
1. Call tool
2. Receive empty response: `{}`

Present to user:
```
No external adapters are currently configured in this organization.

External adapters allow you to ingest data from external sources like:
- Syslog servers (firewalls, routers, switches)
- Webhooks from third-party services
- Custom API integrations
- Third-party security tools (SIEM, EDR, firewall logs)
- Network devices and appliances

Use the set-external-adapter skill to create external adapter configurations.
```

## Additional Notes

- External adapters are stored in the Hive under the `external_adapter` hive name with `{oid}` partition
- Each adapter has a unique name within the organization
- The `enabled` field controls whether the adapter is actively receiving data
- Tags can be used to organize and filter external adapters
- The `last_error` field in sys_mtd shows the most recent error, if any
- External adapters typically include parsing rules to normalize external data
- Common adapter types include:
  - **Syslog**: Receives syslog messages over UDP/TCP/TLS
  - **Webhook**: Receives HTTP POST requests with event data
  - **API**: Polls external APIs for data
  - **Custom**: Custom integrations with specific protocols
- Parsing rules transform external data formats into LimaCharlie event format
- Use the get-external-adapter skill to retrieve detailed configuration for a specific adapter
- Use the set-external-adapter skill to create or update adapter configurations
- Use the delete-external-adapter skill to remove adapters
- External adapter configurations may contain sensitive credentials - handle with care
- The `comment` field is useful for documenting the purpose or source of each adapter
- Adapters may listen on network ports or expose webhook endpoints
- Consider firewall rules and network security when configuring adapters
- Parsing rules are critical for proper data normalization and searchability

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/hive.go`
For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp-server/blob/master/internal/tools/hive/external_adapters.go`
