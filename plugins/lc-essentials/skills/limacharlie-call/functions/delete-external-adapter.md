
# Delete External Adapter

Remove an external adapter configuration from the organization, stopping data ingestion from the specified external source.

## When to Use

Use this skill when the user needs to:
- Delete an unused or obsolete external adapter
- Decommission external integrations for retired systems
- Stop receiving data from a specific external source
- Clean up adapters after project completion
- Remove misconfigured external adapters
- Reduce data ingestion costs by removing unnecessary sources

Common scenarios:
- Project cleanup after environment decommissioning
- Removing test or development adapters
- Stopping data collection from retired external systems
- Cleaning up duplicate or misconfigured adapters
- Consolidating adapters to reduce management overhead
- Cost optimization by removing unnecessary data sources
- Security cleanup after removing third-party integrations

## What This Skill Does

This skill deletes an external adapter configuration from the organization's Hive storage. Once deleted, the adapter stops receiving and processing data from the associated external source immediately. The operation is permanent and cannot be undone. Historical data already ingested remains in the organization but no new data will be processed. The skill calls the LimaCharlie MCP tool to remove the adapter identified by its name from the external_adapter hive.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **adapter_name**: Name of the external adapter to delete (required)

To find the adapter name:
- Use the list-external-adapters skill to see all available adapters
- The adapter name is the unique identifier for each external adapter

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Correct external adapter name - verify this is the right adapter to delete
3. Confirmation that this adapter should be deleted (operation is permanent)
4. Understanding that data ingestion will stop immediately
5. Historical data will be retained but no new data will arrive

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_external_adapter",
  parameters={
    "oid": "[organization-id]",
    "adapter_name": "[adapter-name]"
  }
)
```

**Tool Details:**
- Tool Name: `delete_external_adapter`
- Required Parameters:
  - `oid`: Organization ID
  - `adapter_name`: Name of the external adapter to delete

### Step 3: Handle the Response

The tool returns a response with:
```json
{}
```

**Success:**
- The external adapter has been successfully deleted
- Data ingestion from this source has stopped immediately
- The adapter configuration is permanently removed
- Historical data collected remains in the organization
- The deletion cannot be undone

**Common Errors:**
- **Invalid adapter name**: Adapter name format is invalid or malformed
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions to delete external adapters (requires platform_admin role)
- **Not Found**: External adapter with the specified name does not exist

### Step 4: Format the Response

Present the result to the user:
- Confirm successful deletion of the external adapter
- Specify which adapter was deleted (by name and type if known)
- Note that data ingestion has stopped
- Remind user that historical data is retained
- Note that the operation is permanent
- Suggest alternative approaches if they need to temporarily stop ingestion (disable instead)

## Example Usage

### Example 1: Delete obsolete syslog adapter

User request: "Delete the syslog adapter for the old firewall: old-firewall-syslog"

Steps:
1. Extract organization ID from context
2. Verify the adapter name: "old-firewall-syslog"
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_external_adapter",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "adapter_name": "old-firewall-syslog"
  }
)
```

Expected response:
```json
{}
```

Present to user:
```
Successfully deleted external adapter 'old-firewall-syslog'.

Data ingestion from this syslog source has stopped.
Historical firewall logs already collected remain in your organization.

The adapter configuration is permanently removed.
If logs are still being sent, they will be dropped.
```

### Example 2: Remove test webhook adapter

User request: "Remove the test webhook adapter, we're done testing"

Steps:
1. Identify the adapter name (e.g., "test-webhook")
2. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_external_adapter",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "adapter_name": "test-webhook"
  }
)
```

Expected response:
```json
{}
```

Present to user:
```
Test webhook adapter 'test-webhook' has been deleted.

The test webhook endpoint is now removed and will no longer accept data.
Historical test data remains available for analysis.

Any requests to the webhook endpoint will now return 404 Not Found.
```

### Example 3: Handle deletion of non-existent adapter

User request: "Delete the api-test adapter"

Steps:
1. Call tool with adapter name "api-test"
2. Tool returns not found error

Present to user:
```
Could not find external adapter 'api-test'.

This adapter may have already been deleted or never existed.
Use the list-external-adapters skill to see all available adapters.
```

### Example 4: User wants to temporarily stop ingestion

User request: "Delete the firewall-syslog adapter, we need to stop receiving logs"

Steps:
1. Detect that user might want temporary stop instead of permanent deletion
2. Provide guidance

Present to user:
```
Note: Deleting an external adapter is permanent. If you want to temporarily
stop data ingestion, consider disabling the adapter instead:

To disable (temporary):
- Use set-external-adapter to update the adapter with enabled=false
- Data ingestion stops but configuration is preserved
- Parsing rules and settings are retained
- Can be re-enabled later without reconfiguration

To delete (permanent):
- Configuration is removed completely
- Parsing rules are lost
- Must reconfigure from scratch to re-enable
- Historical data is retained

Would you like to disable the adapter instead of deleting it?
```

## Additional Notes

- External adapter deletion is permanent and cannot be undone
- Data ingestion stops immediately upon deletion
- Historical data already ingested remains in the organization
- The adapter configuration is completely removed from the Hive
- Parsing rules and field mappings are lost - backup before deletion if needed
- To temporarily stop ingestion, use set-external-adapter to disable instead
- Verify the adapter name before deletion to avoid accidental removal
- Use list-external-adapters to confirm which adapters exist before deletion
- Consider exporting the adapter configuration before deletion for backup
- After deletion, you must fully reconfigure the adapter to restore ingestion
- Adapter names are case-sensitive - use exact names
- Deletion requires platform_admin permissions
- If you need to recreate the adapter later, use set-external-adapter with the same configuration
- Consider cost implications - deleting adapters reduces data ingestion costs
- For syslog adapters, external systems may still send data (it will be dropped)
- For webhook adapters, the endpoint becomes unavailable after deletion
- For API polling adapters, polling stops immediately
- Document why adapters are deleted for audit purposes
- Alternative to deletion: Disable the adapter to preserve configuration while stopping ingestion
- If an external system is decommissioned, delete its adapters to clean up
- Consider related configurations (outputs, D&R rules) that may reference the adapter's data
- Review detections and dashboards that may depend on data from the deleted adapter

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/hive.go`
For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp/blob/master/internal/tools/hive/external_adapters.go`
