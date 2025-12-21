
# Delete Cloud Sensor

Remove a cloud sensor configuration from the organization, stopping data collection from the specified cloud platform or SaaS service.

## When to Use

Use this skill when the user needs to:
- Delete an unused or obsolete cloud sensor
- Decommission cloud integrations for retired platforms
- Stop collecting data from a specific cloud source
- Clean up cloud sensors after project completion
- Remove misconfigured cloud sensors
- Reduce data ingestion costs by removing unnecessary sources

Common scenarios:
- Project cleanup after environment decommissioning
- Removing test or development cloud sensors
- Stopping data collection from retired cloud platforms
- Cleaning up duplicate or misconfigured sensors
- Consolidating cloud sensors to reduce management overhead
- Cost optimization by removing unnecessary data sources

## What This Skill Does

This skill deletes a cloud sensor configuration from the organization's Hive storage. Once deleted, the sensor stops collecting data from the associated cloud platform or SaaS service immediately. The operation is permanent and cannot be undone. Historical data already collected remains in the organization but no new data will be ingested. The skill calls the LimaCharlie MCP tool to remove the sensor identified by its name from the cloud_sensor hive.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **sensor_name**: Name of the cloud sensor to delete (required)

To find the sensor name:
- Use the list-cloud-sensors skill to see all available cloud sensors
- The sensor name is the unique identifier for each cloud sensor

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Correct cloud sensor name - verify this is the right sensor to delete
3. Confirmation that this sensor should be deleted (operation is permanent)
4. Understanding that data collection will stop immediately
5. Historical data will be retained but no new data will arrive

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_cloud_sensor",
  parameters={
    "oid": "[organization-id]",
    "sensor_name": "[sensor-name]"
  }
)
```

**Tool Details:**
- Tool Name: `delete_cloud_sensor`
- Required Parameters:
  - `oid`: Organization ID
  - `sensor_name`: Name of the cloud sensor to delete

### Step 3: Handle the Response

The tool returns a response with:
```json
{}
```

**Success:**
- The cloud sensor has been successfully deleted
- Data collection from this source has stopped immediately
- The sensor configuration is permanently removed
- Historical data collected remains in the organization
- The deletion cannot be undone

**Common Errors:**
- **Invalid sensor name**: Sensor name format is invalid or malformed
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions to delete cloud sensors (requires fleet_management role)
- **Not Found**: Cloud sensor with the specified name does not exist

### Step 4: Format the Response

Present the result to the user:
- Confirm successful deletion of the cloud sensor
- Specify which sensor was deleted (by name and type if known)
- Note that data collection has stopped
- Remind user that historical data is retained
- Note that the operation is permanent
- Suggest alternative approaches if they need to temporarily stop collection (disable instead)

## Example Usage

### Example 1: Delete obsolete AWS CloudTrail sensor

User request: "Delete the cloud sensor for the old AWS account: old-aws-cloudtrail"

Steps:
1. Extract organization ID from context
2. Verify the sensor name: "old-aws-cloudtrail"
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_cloud_sensor",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sensor_name": "old-aws-cloudtrail"
  }
)
```

Expected response:
```json
{}
```

Present to user:
```
Successfully deleted cloud sensor 'old-aws-cloudtrail'.

Data collection from this AWS CloudTrail source has stopped.
Historical CloudTrail logs already collected remain in your organization.

The sensor configuration is permanently removed.
```

### Example 2: Remove test Office 365 sensor

User request: "Remove the test Office 365 sensor, we're done testing"

Steps:
1. Identify the sensor name (e.g., "test-o365")
2. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_cloud_sensor",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sensor_name": "test-o365"
  }
)
```

Expected response:
```json
{}
```

Present to user:
```
Test Office 365 cloud sensor 'test-o365' has been deleted.

The test integration is now removed and data collection has stopped.
Historical test data remains available for analysis.
```

### Example 3: Handle deletion of non-existent sensor

User request: "Delete the azure-test sensor"

Steps:
1. Call tool with sensor name "azure-test"
2. Tool returns not found error

Present to user:
```
Could not find cloud sensor 'azure-test'.

This sensor may have already been deleted or never existed.
Use the list-cloud-sensors skill to see all available cloud sensors.
```

### Example 4: User wants to temporarily stop collection

User request: "Delete the prod-aws-cloudtrail sensor, we need to stop collecting data"

Steps:
1. Detect that user might want temporary stop instead of permanent deletion
2. Provide guidance

Present to user:
```
Note: Deleting a cloud sensor is permanent. If you want to temporarily stop
data collection, consider disabling the sensor instead:

To disable (temporary):
- Use set-cloud-sensor to update the sensor with enabled=false
- Data collection stops but configuration is preserved
- Can be re-enabled later without reconfiguration

To delete (permanent):
- Configuration is removed completely
- Must reconfigure from scratch to re-enable
- Historical data is retained

Would you like to disable the sensor instead of deleting it?
```

## Additional Notes

- Cloud sensor deletion is permanent and cannot be undone
- Data collection stops immediately upon deletion
- Historical data already collected remains in the organization
- The sensor configuration is completely removed from the Hive
- To temporarily stop collection, use set-cloud-sensor to disable instead
- Verify the sensor name before deletion to avoid accidental removal
- Use list-cloud-sensors to confirm which sensors exist before deletion
- Consider exporting the sensor configuration before deletion for backup
- After deletion, you must fully reconfigure the sensor to restore collection
- Cloud sensor names are case-sensitive - use exact names
- Deletion requires fleet_management permissions
- If you need to recreate the sensor later, use set-cloud-sensor with the same configuration
- Consider cost implications - deleting sensors reduces data ingestion costs
- For AWS sensors, you may also want to remove IAM roles after deletion
- For Azure/GCP sensors, consider removing service principals or service accounts
- Document why sensors are deleted for audit purposes
- Alternative to deletion: Disable the sensor to preserve configuration while stopping collection

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/hive.go`
For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp/blob/master/internal/tools/hive/cloud_sensors.go`
