
# Get Cloud Sensor

Retrieve detailed configuration and metadata for a specific cloud sensor integration.

## When to Use

Use this skill when the user needs to:
- View the complete configuration of a specific cloud sensor
- Inspect cloud integration settings and credentials
- Troubleshoot a cloud sensor that isn't collecting data properly
- Review connection details for AWS, Azure, GCP, or SaaS integrations
- Check the enabled status and tags of a cloud sensor
- Examine error messages or last modification timestamps

Common scenarios:
- Troubleshooting cloud data ingestion issues
- Verifying cloud sensor configuration before making changes
- Documenting cloud integration settings
- Checking credentials or connection parameters
- Reviewing sensor metadata for audit purposes
- Investigating why a cloud sensor stopped working

## What This Skill Does

This skill retrieves the complete configuration and metadata for a specific cloud sensor by name. Cloud sensors are virtual sensors that collect telemetry from cloud platforms (AWS, Azure, GCP) and SaaS services (Office 365, Okta, GitHub, etc.) without requiring endpoint agents. The skill calls the LimaCharlie MCP tool to fetch the sensor's data configuration, user metadata (enabled status, tags, comments), and system metadata (creation info, modification history, errors).

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **sensor_name**: Name of the cloud sensor to retrieve (required)

To find the sensor name:
- Use the list-cloud-sensors skill to see all available cloud sensors
- The sensor name is the unique identifier for each cloud sensor

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Correct cloud sensor name
3. The sensor name matches exactly (case-sensitive)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_cloud_sensor",
  parameters={
    "oid": "[organization-id]",
    "sensor_name": "[sensor-name]"
  }
)
```

**Tool Details:**
- Tool Name: `get_cloud_sensor`
- Required Parameters:
  - `oid`: Organization ID
  - `sensor_name`: Name of the cloud sensor to retrieve

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "data": {
    "sensor_type": "aws_cloudtrail",
    "aws_region": "us-east-1",
    "s3_bucket": "my-cloudtrail-logs",
    "role_arn": "arn:aws:iam::123456789012:role/LCCloudTrail",
    "additional_config": { ... }
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["aws", "production", "cloudtrail"],
    "comment": "Production AWS CloudTrail integration",
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
- The response contains the complete cloud sensor configuration
- `data`: The sensor configuration specific to the cloud platform or service
  - Varies by sensor type (AWS, Azure, GCP, Office 365, etc.)
  - Contains connection details, credentials, regions, etc.
- `usr_mtd`: User-controlled metadata
  - `enabled`: Whether the sensor is active
  - `tags`: Array of tags for organization
  - `comment`: Description or notes
  - `expiry`: Expiration timestamp (0 = no expiry)
- `sys_mtd`: System-managed metadata
  - `created_by`: User who created the sensor
  - `created_at`: Creation timestamp
  - `last_author`: User who last modified the sensor
  - `last_mod`: Last modification timestamp
  - `guid`: Unique identifier
  - `last_error`: Most recent error message (empty if no errors)
  - `last_error_ts`: Timestamp of last error

**Common Errors:**
- **Invalid sensor name**: Sensor name format is invalid or malformed
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions to view cloud sensors (requires fleet_management role)
- **Not Found**: Cloud sensor with the specified name does not exist

### Step 4: Format the Response

Present the result to the user:
- Display the sensor name prominently
- Show the sensor type (AWS CloudTrail, Azure Activity Logs, etc.)
- Present key configuration details in a readable format
- Show enabled status and tags
- Display creation and modification information
- Highlight any errors in the last_error field with timestamps
- Format sensitive fields (credentials) appropriately - consider masking
- Provide context-specific guidance based on sensor type

## Example Usage

### Example 1: Get AWS CloudTrail sensor configuration

User request: "Show me the configuration for prod-aws-cloudtrail"

Steps:
1. Extract organization ID from context
2. Use sensor name: "prod-aws-cloudtrail"
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_cloud_sensor",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sensor_name": "prod-aws-cloudtrail"
  }
)
```

Expected response:
```json
{
  "data": {
    "sensor_type": "aws_cloudtrail",
    "aws_region": "us-east-1",
    "s3_bucket": "my-cloudtrail-logs",
    "role_arn": "arn:aws:iam::123456789012:role/LCCloudTrail",
    "external_id": "lc-ext-id-123"
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["aws", "production", "cloudtrail"],
    "comment": "Production AWS CloudTrail integration",
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
Cloud Sensor: prod-aws-cloudtrail

Type: AWS CloudTrail
Status: Enabled
Tags: aws, production, cloudtrail

Configuration:
- AWS Region: us-east-1
- S3 Bucket: my-cloudtrail-logs
- Role ARN: arn:aws:iam::123456789012:role/LCCloudTrail
- External ID: lc-ext-id-123

Metadata:
- Created by: user@example.com on January 1, 2024
- Last modified by: admin@example.com on January 2, 2024
- Comment: Production AWS CloudTrail integration
- Status: No errors
```

### Example 2: Troubleshoot sensor with errors

User request: "Why isn't the office365-audit sensor working?"

Steps:
1. Call tool to get sensor details
2. Check last_error field

Expected response with error:
```json
{
  "data": {
    "sensor_type": "office365",
    "tenant_id": "abc-123-def"
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["office365"],
    "comment": "",
    "expiry": 0
  },
  "sys_mtd": {
    "last_error": "Authentication failed: Invalid client secret",
    "last_error_ts": 1704240000
  }
}
```

Present to user:
```
Cloud Sensor: office365-audit

Type: Office 365
Status: Enabled (but experiencing errors)

ERROR DETECTED:
- Error: Authentication failed: Invalid client secret
- Occurred: January 3, 2024 at 12:00 PM

The sensor is enabled but cannot collect data due to authentication failure.

Troubleshooting steps:
1. Verify the client secret is correct in Azure AD
2. Check if the secret has expired
3. Ensure the application has the required permissions
4. Update the sensor configuration with the correct credentials
```

### Example 3: Sensor not found

User request: "Get the azure-logs sensor"

Steps:
1. Call tool with sensor name "azure-logs"
2. Tool returns not found error

Present to user:
```
Cloud sensor 'azure-logs' not found.

This sensor may have been deleted or never existed.
Use the list-cloud-sensors skill to see all available cloud sensors.
```

## Additional Notes

- Cloud sensors are stored in the Hive under `cloud_sensor` hive name with `{oid}` partition
- Sensor names are case-sensitive - use exact names from list-cloud-sensors
- The `data` field structure varies by sensor type:
  - AWS sensors contain region, bucket, role ARN, etc.
  - Azure sensors contain subscription ID, tenant ID, etc.
  - Office 365 sensors contain tenant ID, client credentials, etc.
- The `last_error` field is critical for troubleshooting - check it first when investigating issues
- Cloud sensor configurations may contain sensitive credentials - handle securely
- The `enabled` field controls active data collection - disabled sensors don't fetch data
- Tags help organize sensors by environment, platform, or purpose
- The `etag` in sys_mtd is used for optimistic concurrency control during updates
- Use the set-cloud-sensor skill to update configurations
- Use the delete-cloud-sensor skill to remove sensors
- Common sensor types include:
  - AWS: cloudtrail, guardduty, vpc_flow_logs, config, securityhub
  - Azure: activity_logs, signin_logs, security_center
  - GCP: audit_logs, cloud_logging
  - SaaS: office365, okta, github, salesforce

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/hive.go`
For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp-server/blob/master/internal/tools/hive/cloud_sensors.go`
