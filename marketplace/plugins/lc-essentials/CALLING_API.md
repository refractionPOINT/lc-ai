# LimaCharlie Tool Access

The `lc_call_tool` provides unified access to all LimaCharlie MCP tools. This document explains the architecture and how it works.

## Execution Architecture

**All LimaCharlie API operations are executed through the `limacharlie-api-executor` sub-agent** for optimal performance, cost efficiency, and parallel execution capability.

### Why Use a Sub-Agent?

- **Reliability**: Sonnet model provides better reasoning for API operations
- **Accuracy**: More reliable handling of complex parameters and responses
- **Parallel Execution**: Multiple API calls can run concurrently
- **Separation of Concerns**: Main thread focuses on orchestration, sub-agent handles API details
- **Autonomous Result Processing**: Sub-agent handles large result downloads, schema analysis, and data extraction

### Execution Flow

```
Main Thread/Skill
    ↓ (delegates via Task tool)
limacharlie-api-executor Agent (Sonnet)
    ↓ (calls MCP tool)
lc_call_tool
    ↓ (API request)
LimaCharlie Platform
```

## Core Concepts

### Organization ID (OID)

The OID is a **UUID** (e.g., `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name.

- Use `get_org_oid_by_name` to convert a single org name to OID (cached, efficient)
- Use `list_user_orgs` to get all accessible orgs with their OIDs
- All functions require OID except: `list_user_orgs`, `get_org_oid_by_name`, `create_org`, `get_platform_names`

### LCQL Query Generation

**Never write LCQL queries manually.** LCQL uses unique pipe-based syntax validated against org-specific schemas. Manual queries will fail or produce incorrect results.

Always use this workflow:
1. `generate_lcql_query` - Convert natural language to LCQL
2. `run_lcql_query` - Execute with the generated query string

### Timestamp Formats

| API | Format | Example |
|-----|--------|---------|
| `get_historic_events`, `get_historic_detections` | **Seconds** (10 digits) | `1699574400` |
| Detection/event data | Milliseconds (13 digits) | `1699574400000` |

**Always divide by 1000** when using timestamps from detection data in historic queries.

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `missing required parameter` | Required field not provided | Check function docs for required params |
| `no such entity` | Resource doesn't exist | Verify OID/SID/resource name |
| `permission denied` | Insufficient API permissions | Check API key scopes |
| `validation failed` | Invalid config/syntax | Use validation tools first |

## Basic Parameters

The sub-agent receives:
- **Function**: Name of the LimaCharlie API function (e.g., `get_sensor_info`, `run_lcql_query`)
- **Parameters**: Object containing the parameters for the specific function
- **Return** (required): Specifies what data the caller wants back

### Return Field Options

The **Return** field is required and tells the agent exactly what data to return:

| Return Value | Meaning |
|-------------|---------|
| `RAW` | Return the complete API response as-is, no processing |
| `<extraction instructions>` | Extract/summarize specific data (e.g., "Count of online sensors", "Only hostnames") |

**Examples**:
- `Return: RAW` - Full API response
- `Return: Count of total sensors and count of online sensors` - Summarized counts
- `Return: Only sensors that are online with hostname and SID` - Filtered data
- `Return: Summary with total count, breakdown by platform` - Aggregated report

## How It Works

The `lc_call_tool` is a meta-tool that invokes other registered LimaCharlie MCP tools. The sub-agent calls it with specific function names and parameters:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_sensor_info",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "xyz-sensor-id"
  }
)
```

The sub-agent handles the call, processes results, and returns structured data to the main thread.

## Authentication

Authentication is handled automatically using the MCP server's auth context. You don't need to provide API keys or JWT tokens.

## Direct MCP Calls (Fast Path)

For simple functions with small responses, call MCP directly to bypass executor overhead (0.5-2s vs 5-15s). See AUTOINIT.md section 1a for the whitelist. If response contains `resource_link`, spawn executor to handle download.

## Response Structure

Tools return their results directly without HTTP wrapper:

```json
{
  "sensor": {
    "sid": "xyz-sensor-id",
    "hostname": "SERVER01",
    "platform": "windows",
    ...
  }
}
```

Errors are returned with an `error` field:

```json
{
  "error": "sensor not found"
}
```

## Available Tools

### Core Profile
- `get_sensor_info` - Get detailed sensor information
- `list_sensors` - List all sensors (supports filtering)
- `get_online_sensors` - List online sensors
- `is_online` - Check if sensor is online
- `search_hosts` - Search sensors by hostname pattern

### Historical Data Profile
- `run_lcql_query` - Run LCQL query
- `get_historic_events` - Get historical events
- `get_historic_detections` - Get historical detections
- `search_iocs` - Search for IOCs
- `batch_search_iocs` - Batch search IOCs
- `get_time_when_sensor_has_data` - Get sensor data time range
- `list_saved_queries` - List saved queries
- `get_saved_query` - Get saved query
- `run_saved_query` - Execute saved query
- `set_saved_query` - Create/update saved query
- `delete_saved_query` - Delete saved query
- `get_event_schema` - Get event schema
- `get_event_schemas_batch` - Get multiple event schemas
- `get_event_types_with_schemas` - List event types with schemas
- `get_event_types_with_schemas_for_platform` - List event types by platform
- `get_platform_names` - Get platform names
- `list_with_platform` - List sensors by platform

### Live Investigation Profile
- `get_processes` - Get running processes
- `get_process_modules` - Get process modules
- `get_process_strings` - Extract process strings
- `yara_scan_process` - YARA scan process
- `yara_scan_file` - YARA scan file
- `yara_scan_directory` - YARA scan directory
- `yara_scan_memory` - YARA scan memory
- `get_network_connections` - Get network connections
- `get_os_version` - Get OS version
- `get_users` - Get system users
- `get_services` - Get services
- `get_drivers` - Get drivers
- `get_autoruns` - Get autoruns
- `get_packages` - Get packages
- `get_registry_keys` - Get registry keys
- `find_strings` - Find strings in memory
- `dir_list` - List directory
- `dir_find_hash` - Find files by hash
- `list_artifacts` - List artifacts
- `get_artifact` - Get artifact

### Threat Response Profile
- `isolate_network` - Isolate sensor
- `rejoin_network` - Rejoin sensor to network
- `is_isolated` - Check isolation status
- `add_tag` - Add tag to sensor
- `remove_tag` - Remove tag from sensor
- `delete_sensor` - Delete sensor
- `reliable_tasking` - Execute reliable task
- `list_reliable_tasks` - List reliable tasks

### Fleet Management Profile
- `list_installation_keys` - List installation keys
- `create_installation_key` - Create installation key
- `delete_installation_key` - Delete installation key
- `list_cloud_sensors` - List cloud sensor configs
- `get_cloud_sensor` - Get cloud sensor config
- `set_cloud_sensor` - Create/update cloud sensor
- `delete_cloud_sensor` - Delete cloud sensor
- `upgrade_sensors` - Upgrade sensors to specific version

### Detection Engineering Profile
- `get_detection_rules` - Get all D&R rules
- `list_dr_general_rules` - List general D&R rules
- `get_dr_general_rule` - Get general D&R rule
- `set_dr_general_rule` - Create/update general D&R rule
- `delete_dr_general_rule` - Delete general D&R rule
- `list_dr_managed_rules` - List managed D&R rules
- `get_dr_managed_rule` - Get managed D&R rule
- `set_dr_managed_rule` - Update managed D&R rule
- `delete_dr_managed_rule` - Delete managed D&R rule
- `validate_dr_rule_components` - Validate D&R rule
- `list_yara_rules` - List YARA rules
- `get_yara_rule` - Get YARA rule
- `set_yara_rule` - Create/update YARA rule
- `delete_yara_rule` - Delete YARA rule
- `validate_yara_rule` - Validate YARA rule syntax
- `get_fp_rules` - Get all FP rules
- `get_fp_rule` - Get FP rule
- `set_fp_rule` - Create/update FP rule
- `delete_fp_rule` - Delete FP rule
- `get_mitre_report` - Get MITRE ATT&CK report

### Platform Admin Profile
- `get_org_oid_by_name` - Convert org name to OID
- `get_org_info` - Get organization info
- `get_usage_stats` - Get usage statistics
- `get_billing_details` - Get billing details
- `get_org_errors` - Get organization errors
- `dismiss_org_error` - Dismiss organization error
- `get_org_invoice_url` - Get invoice URL
- `create_org` - Create organization
- `list_user_orgs` - List user organizations
- `list_outputs` - List outputs
- `add_output` - Create output
- `delete_output` - Delete output
- `list_secrets` - List secrets
- `get_secret` - Get secret value
- `set_secret` - Create/update secret
- `delete_secret` - Delete secret
- `list_lookups` - List lookups
- `get_lookup` - Get lookup
- `set_lookup` - Create/update lookup
- `delete_lookup` - Delete lookup
- `query_lookup` - Query lookup
- `list_playbooks` - List playbooks
- `get_playbook` - Get playbook
- `set_playbook` - Create/update playbook
- `delete_playbook` - Delete playbook
- `list_external_adapters` - List external adapters
- `get_external_adapter` - Get external adapter
- `set_external_adapter` - Create/update external adapter
- `delete_external_adapter` - Delete external adapter
- `list_extension_configs` - List extension configs
- `get_extension_config` - Get extension config
- `set_extension_config` - Update extension config
- `delete_extension_config` - Delete extension config
- `subscribe_to_extension` - Subscribe to extension
- `unsubscribe_from_extension` - Unsubscribe from extension
- `list_rules` - List Hive rules
- `get_rule` - Get Hive rule
- `set_rule` - Create/update Hive rule
- `delete_rule` - Delete Hive rule
- `list_api_keys` - List API keys
- `create_api_key` - Create API key
- `delete_api_key` - Delete API key

### AI-Powered Tools
- `generate_lcql_query` - Generate LCQL from natural language
- `generate_dr_rule_detection` - Generate D&R detection component
- `generate_dr_rule_respond` - Generate D&R response component
- `generate_sensor_selector` - Generate sensor selector
- `generate_python_playbook` - Generate Python playbook
- `generate_detection_summary` - Generate detection summary

## Common Patterns

### Pattern 1: Get Single Resource

```
lc_call_tool(
  tool_name="get_sensor_info",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "xyz-sensor-id"
  }
)
```

### Pattern 2: List Resources

```
lc_call_tool(
  tool_name="list_sensors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

### Pattern 3: Server-Side Filtering with Selector

**Best practice for sensor filtering**: Use the `selector` parameter with bexpr syntax for powerful server-side filtering.

```
# Filter by platform
lc_call_tool(
  tool_name="list_sensors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "plat == `windows`"
  }
)

# Filter by hostname pattern
lc_call_tool(
  tool_name="list_sensors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "hostname matches `^web-`"
  }
)

# Filter by IP address
lc_call_tool(
  tool_name="list_sensors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "int_ip == `10.0.1.50` or ext_ip == `10.0.1.50`"
  }
)

# Complex filters (combine multiple conditions)
lc_call_tool(
  tool_name="list_sensors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "plat == `windows` and hostname matches `^prod-`"
  }
)
```

### Pattern 3b: Efficient Multi-Filter (Selector + Online)

**Best practice for large sensor fleets**: Combine `selector` and `online_only` for maximum efficiency - both are evaluated server-side.

```
# Online Windows sensors only
lc_call_tool(
  tool_name="list_sensors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "plat == `windows`",
    "online_only": true  # Server-side: efficient for large fleets
  }
)

# Online production Linux servers
lc_call_tool(
  tool_name="list_sensors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "selector": "plat == `linux` and hostname matches `^prod-`",
    "online_only": true
  }
)
```

**Why this approach?**
- Both `selector` and `online_only` are evaluated **server-side** before results are returned
- Example: If you have 1000 sensors (600 Windows, 400 Linux) and 200 are offline, requesting online Windows sensors returns only 480 results
- Minimal data transfer and no client-side processing needed

**Filtering performance tips:**
- **Server-side filters** (most efficient): `selector` (bexpr syntax) and `online_only`
- **Selector capabilities**: Filter by platform, hostname (regex), IP (regex), tags, architecture, and more
- **Best practice**: All filtering is now server-side with the new API - use `selector` for complex queries

### Pattern 4: Create Resource

```
lc_call_tool(
  tool_name="add_output",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "name": "my-syslog",
    "module": "syslog",
    "type": "event",
    "dest_host": "10.0.0.5",
    "dest_port": 514
  }
)
```

### Pattern 5: Delete Resource

```
lc_call_tool(
  tool_name="delete_output",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "name": "my-syslog"
  }
)
```

### Pattern 6: Run Query

```
lc_call_tool(
  tool_name="run_lcql_query",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "query": "-24h | * | DNS_REQUEST | event.DOMAIN_NAME contains 'example.com'",
    "limit": 1000,
    "stream": "event"
  }
)
```

### Pattern 7: Search IOCs

```
lc_call_tool(
  tool_name="search_iocs",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "ioc_type": "domain",
    "ioc_value": "malicious.com",
    "info_type": "locations"
  }
)
```

### Pattern 8: Live Sensor Command

```
lc_call_tool(
  tool_name="get_processes",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "xyz-sensor-id"
  }
)
```

## User-Level and Global Operations

Some operations don't require a specific organization ID:

**User-level operations** (omit `oid`):
- `list_user_orgs` - List organizations accessible to the user

**Global operations** (omit `oid`):
- `create_org` - Create new organization
- `get_platform_names` - Get platform names from global ontology

**All other operations require a valid organization ID.**

## Handling Large Results

**The `limacharlie-api-executor` sub-agent handles large results automatically.** This section documents the underlying mechanism for reference.

When tool calls return large result sets (>100KB), the `lc_call_tool` returns a special response format instead of the full data:

```json
{
  "is_temp_file": false,
  "reason": "results too large, see resource_link for content",
  "resource_link": "https://storage.googleapis.com/lc-tmp-mcp-export/lc_call_tool_20251114_142154_73e57517.json.gz?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=...",
  "resource_size": 34329,
  "success": true
}
```

### Understanding the Response

- **is_temp_file**: `false` indicates data is at a remote URL
- **reason**: Explains why the full data wasn't returned inline
- **resource_link**: Signed Google Cloud Storage URL containing the data
- **resource_size**: Size of the compressed file in bytes
- **success**: `true` indicates the tool call succeeded

### Resource Link Details

The `resource_link` URL:
- Contains gzip-compressed JSON data (`.json.gz` extension)
- Is time-limited (typically expires in 24 hours)
- Includes GCP authentication tokens in the URL parameters
- Can be downloaded directly with tools like `curl` or `WebFetch`

**IMPORTANT: curl auto-decompresses gzip**

Although the URL ends in `.json.gz`, `curl` with `-L` flag automatically decompresses the content. Do NOT pipe through `gunzip`:

```bash
# CORRECT - curl handles decompression automatically
curl -sL "[resource_link_url]" | jq '.'

# WRONG - will fail with "not in gzip format" error
curl -sL "[resource_link_url]" | gunzip | jq '.'
```

### Autonomous Handling by Sub-Agent

When you delegate to the `limacharlie-api-executor` agent with a Return specification, the agent:

1. **Parses** the Return field to understand what data is needed
2. **Detects** the `resource_link` in the API response (for large results)
3. **Downloads** the data from the signed URL
4. **Analyzes** the JSON schema using `analyze-lc-result.sh`
5. **Processes** data according to Return specification:
   - If `Return: RAW` → Returns complete data as-is
   - If extraction instructions → Extracts/summarizes using jq
6. **Cleans up** temporary files
7. **Returns** processed results to the main thread

You don't need to handle this manually. See the `limacharlie-call` skill documentation for usage examples.

### Manual Processing (Advanced)

If you need to manually process large results (not recommended), follow this workflow:

**CRITICAL REQUIREMENT**: DO NOT attempt to guess the JSON structure or write jq queries before analyzing the schema.

**Why this is mandatory**: Skipping the analysis step results in incorrect queries, wasted tokens, and frustration. The schema reveals the actual structure, which may differ from what you expect.

**Step 1: Download and Analyze (REQUIRED)**

**You MUST run the analyze script first. DO NOT skip this step.**

Run the analyze script with the `resource_link` URL directly. The script is at `scripts/analyze-lc-result.sh` in the plugin root directory.

**Finding the script path**: The skill's base directory is shown at the top of the skill prompt. From any skill directory (`{plugin_root}/skills/{skill-name}/`), the plugin root is `../..`. So the script path is: `{skill_base_directory}/../../scripts/analyze-lc-result.sh`

```bash
# Example: if skill base directory is /path/to/plugin/skills/limacharlie-call
# Then the script is at /path/to/plugin/scripts/analyze-lc-result.sh
bash "{skill_base_directory}/../../scripts/analyze-lc-result.sh" "https://storage.googleapis.com/lc-tmp-mcp-export/..."
```

Replace the URL with the actual `resource_link` value from the tool response.

**What this script does:**
1. Downloads the file to `/tmp/lc-result-{timestamp}.json`
2. Outputs the JSON schema to stdout showing object keys, array patterns, and data types
3. Prints the file path to stderr (after `---FILE_PATH---`)

**Example output:**
```
(stdout) {"sensors": [{"sid": "string", "hostname": "string", "platform": "string"}]}
(stderr) ---FILE_PATH---
(stderr) /tmp/lc-result-1731633216789456123.json
```

**Before proceeding to Step 2**, you MUST review the schema output to understand:
- Is the top-level structure an object or array?
- What are the available keys/fields?
- How is the data nested?

**Step 2: Extract Specific Data with jq**

**Only after reviewing the schema**, use jq to extract the specific information requested. Use the file path shown in the script output.

Common patterns based on schema:

```bash
# If schema shows top-level array
jq '.[] | select(.hostname == "web-01")' /tmp/lc-result-{timestamp}.json

# If schema shows top-level object with named keys
jq '.sensors[] | {id: .sid, name: .hostname}' /tmp/lc-result-{timestamp}.json

# Count items
jq '. | length' /tmp/lc-result-{timestamp}.json
```

**Step 3: Clean Up**

Remove the temporary file when done:

```bash
rm /tmp/lc-result-{timestamp}.json
```

Replace `{timestamp}` with the actual timestamp from Step 1's output.

**When to use this workflow:**
- `lc_call_tool` returns a `resource_link` response
- You're asking for specific information (e.g., "find sensors with hostname X", "count enabled rules", "get OID for lc_demo")
- You don't need the complete result set

**When NOT to use this workflow:**
- You explicitly want the full/complete dataset
- Results are small enough to fit in context (no `resource_link`)
- You only need summary metadata (count, structure overview)

### Common Scenarios

**Scenario 1: Large Sensor Lists**
- Tool: `list_sensors` for organizations with 1000+ sensors
- Returns: `resource_link` with full sensor inventory
- Use jq to: Find specific sensors, filter by platform, check online status

**Scenario 2: Bulk Historical Events**
- Tool: `run_lcql_query` with broad time range
- Returns: `resource_link` with thousands of events
- Use jq to: Extract specific event types, count occurrences, find patterns

**Scenario 3: Extensive Rule Lists**
- Tool: `list_dr_general_rules` for organizations with many D&R rules
- Returns: `resource_link` with complete rule set
- Use jq to: Find rules by name, check which are enabled, analyze detection logic

### Best Practices

1. **Request specific data**: Be clear about what information you need from large results
2. **Use the analyze script**: The analyze-lc-result.sh script helps you understand the data structure before querying
3. **Be patient**: Large files may take time to download and process
4. **Re-run if expired**: If the signed URL expires (403/404), re-run the original tool call for a fresh link
5. **Avoid full dumps**: Don't request the complete dataset unless truly necessary

## Error Handling

Tools return errors in the response:

```json
{
  "error": "missing required parameter: sid"
}
```

Common errors:
- **Missing parameter**: Required parameter not provided
- **Invalid parameter**: Wrong type or format
- **Not found**: Resource doesn't exist
- **Permission denied**: Insufficient permissions
- **Validation failed**: Invalid configuration

## Best Practices

1. **Always validate OID**: Ensure you have a valid organization ID
2. **Check required parameters**: Review which fields are required for each tool
3. **Use appropriate tools**: Choose the right tool for the operation
4. **Handle errors gracefully**: Provide clear error messages to users
5. **Reference function docs**: Check the function markdown files for detailed usage

## MCP Server Configuration

The `lc_call_tool` is provided by the LimaCharlie MCP server configured in this plugin:
- **Server name**: `limacharlie`
- **Profile**: `api_access` (provides the `lc_call_tool` tool)
- **Tool reference**: `mcp__limacharlie__lc_call_tool`
- **Server URL**: https://mcp.limacharlie.io/mcp/api_access

This MCP server is configured in `.claude-plugin/servers.json` and provides access to all LimaCharlie tools through the unified `lc_call_tool` interface.

## Additional Resources

- Go SDK source: ../go-limacharlie/limacharlie/
- MCP tool implementations: ../lc-mcp-server/internal/tools/
- LimaCharlie API documentation: https://doc.limacharlie.io/
