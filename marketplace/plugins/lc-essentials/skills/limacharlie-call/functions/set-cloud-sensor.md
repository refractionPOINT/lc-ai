
# Set Cloud Sensor

Create a new cloud sensor or update an existing cloud sensor configuration for cloud platform and SaaS integrations.

## When to Use

Use this skill when the user needs to:
- Configure a new cloud sensor for AWS, Azure, GCP, or SaaS platforms
- Update an existing cloud sensor's configuration or credentials
- Enable or disable a cloud sensor
- Modify cloud sensor tags for organization
- Update connection parameters for cloud integrations
- Reconfigure cloud sensor after credential rotation

Common scenarios:
- Initial setup of cloud data source integrations
- Updating expired or rotated credentials
- Changing cloud sensor regions or scopes
- Enabling previously disabled cloud sensors
- Adding tags to organize cloud sensors
- Fixing configuration errors in cloud integrations

## What This Skill Does

This skill creates or updates a cloud sensor configuration in the organization's Hive storage. Cloud sensors are virtual sensors that collect telemetry from cloud platforms and SaaS services without requiring endpoint agents. The configuration includes the sensor type, connection parameters (credentials, regions, tenants), and metadata. The skill calls the LimaCharlie MCP tool to store the sensor configuration with automatic enablement. If a sensor with the same name exists, it will be updated; otherwise, a new sensor is created.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **sensor_name**: Name for the cloud sensor (required, alphanumeric with hyphens/underscores)
- **sensor_config**: Complete configuration object (required, structure varies by sensor type)

The config structure depends on the cloud platform or service:
- **AWS CloudTrail**: aws_region, s3_bucket, role_arn, external_id
- **Azure Activity Logs**: subscription_id, tenant_id, client_id, client_secret
- **GCP Audit Logs**: project_id, service_account_json
- **Office 365**: tenant_id, client_id, client_secret, content_types
- **Okta**: domain, api_token
- Other platforms have their own specific requirements

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Unique sensor name (or name of existing sensor to update)
3. Complete sensor configuration with all required fields for the sensor type
4. Valid credentials and connection parameters
5. Understanding of the cloud platform's authentication requirements

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_cloud_sensor",
  parameters={
    "oid": "[organization-id]",
    "sensor_name": "[sensor-name]",
    "sensor_config": {
      "sensor_type": "aws_cloudtrail",
      "aws_region": "us-east-1",
      "s3_bucket": "my-cloudtrail-logs",
      "role_arn": "arn:aws:iam::123456789012:role/LCCloudTrail",
      "external_id": "lc-ext-id-12345"
    }
  }
)
```

**Tool Details:**
- Tool Name: `set_cloud_sensor`
- Required Parameters:
  - `oid`: Organization ID
  - `sensor_name`: Name for the cloud sensor
  - `sensor_config`: Configuration object with sensor-specific settings

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "guid": "unique-sensor-guid",
  "hive": {
    "name": "cloud_sensor",
    "partition": "global"
  },
  "name": "sensor-name"
}
```

**Success:**
- The cloud sensor has been created or updated successfully
- The response contains the sensor's GUID and hive information
- The sensor is automatically enabled unless specified otherwise
- The sensor will begin collecting data based on its configuration

**Common Errors:**
- **Invalid configuration**: Missing required fields, invalid configuration structure, or malformed config
- **Unauthorized**: Authentication token is invalid or expired
- **Forbidden**: Insufficient permissions to manage cloud sensors (requires fleet_management role)
- **Conflict**: ETag mismatch if updating existing sensor with concurrent modifications

### Step 4: Format the Response

Present the result to the user:
- Confirm successful creation or update of the cloud sensor
- Display the sensor name and type
- Show the enabled status
- List any tags applied
- Provide guidance on verifying data collection
- Suggest checking the sensor after a few minutes to confirm data ingestion
- For updates, note what changed

## Example Usage

### Example 1: Create AWS CloudTrail cloud sensor

User request: "Set up a cloud sensor for our AWS CloudTrail logs in the production environment"

Steps:
1. Extract organization ID from context
2. Prepare sensor name: "prod-aws-cloudtrail"
3. Gather AWS configuration: region, S3 bucket, role ARN, external ID
4. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="set_cloud_sensor",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sensor_name": "prod-aws-cloudtrail",
    "sensor_config": {
      "sensor_type": "aws_cloudtrail",
      "aws_region": "us-east-1",
      "s3_bucket": "my-cloudtrail-logs",
      "role_arn": "arn:aws:iam::123456789012:role/LCCloudTrail",
      "external_id": "lc-ext-id-12345"
    }
  }
)
```

Expected response:
```json
{
  "guid": "abc-123-def-456",
  "hive": {
    "name": "cloud_sensor",
    "partition": "global"
  },
  "name": "prod-aws-cloudtrail"
}
```

Present to user:
```
Successfully created AWS CloudTrail cloud sensor!

Sensor Name: prod-aws-cloudtrail
Type: AWS CloudTrail
Status: Enabled

Configuration:
- AWS Region: us-east-1
- S3 Bucket: my-cloudtrail-logs
- Role ARN: arn:aws:iam::123456789012:role/LCCloudTrail

The sensor will begin collecting CloudTrail logs from your S3 bucket.
Check back in a few minutes to verify data is flowing.
```

### Example 2: Create Office 365 sensor with secret reference

User request: "Set up an Office 365 audit log sensor"

Steps:
1. First, store the client secret in LimaCharlie's secret manager
2. Create the sensor config referencing the secret
3. Call tool with configuration:
```
# Step 1: Store the secret first
mcp__limacharlie__lc_call_tool(
  tool_name="set_secret",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "secret_name": "o365-client-secret",
    "secret_value": "actual-secret-value-here"
  }
)

# Step 2: Create sensor referencing the secret
mcp__limacharlie__lc_call_tool(
  tool_name="set_cloud_sensor",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sensor_name": "office365-audit",
    "sensor_config": {
      "sensor_type": "office365",
      "tenant_id": "abc-123-def",
      "client_id": "client-id-456",
      "client_secret": "hive://secret/o365-client-secret",
      "content_types": ["Audit.General", "Audit.Exchange"]
    }
  }
)
```

Expected response:
```json
{
  "guid": "existing-guid",
  "name": "office365-audit"
}
```

Present to user:
```
Successfully created Office 365 cloud sensor!

Sensor Name: office365-audit
Status: Enabled
Credentials: Using secret 'o365-client-secret'

The sensor will begin collecting Office 365 audit logs.
Monitor the sensor for the next few minutes to confirm data is flowing.
```

### Example 3: Enable a disabled cloud sensor

User request: "Enable the azure-activity-logs sensor"

Steps:
1. Get existing configuration
2. Update with enabled=true in usr_mtd
3. Call tool

Present to user:
```
Successfully enabled cloud sensor 'azure-activity-logs'.

The sensor is now active and will resume collecting Azure Activity Logs.
```

## Credential Handling

**IMPORTANT**: Never hardcode credentials directly in sensor configurations. Use LimaCharlie's secret manager with the `hive://secret/<secret-name>` pattern:

1. **First, store the secret**:
```
set_secret(oid, secret_name="gcp-sa-key", secret_value="<json-credentials>")
```

2. **Then reference it in the sensor config**:
```json
{
  "sensor_type": "pubsub",
  "service_account_creds": "hive://secret/gcp-sa-key",
  "project_name": "my-project",
  "sub_name": "my-subscription"
}
```

**Common credential fields that support `hive://secret/`**:
- `service_account_creds` / `service_account_json` (GCP)
- `client_secret` (Azure, Office 365)
- `api_token` / `apikey` (Okta, various APIs)
- `secret_key` (AWS)

**Wrong** - Do NOT use a `secret_name` field:
```json
{
  "sensor_type": "pubsub",
  "secret_name": "my-secret"  // ERROR: unknown field
}
```

**Right** - Reference secret in the credential field itself:
```json
{
  "sensor_type": "pubsub",
  "service_account_creds": "hive://secret/my-secret"
}
```

## Additional Notes

- Cloud sensors use the Hive storage system under `cloud_sensor` hive with `global` partition
- Sensor names must be unique within the organization
- The config structure is specific to each cloud platform or SaaS service
- Required fields vary by sensor type - consult platform-specific documentation
- **Always use `hive://secret/<name>` for credentials** - never hardcode secrets in configs
- The sensor is automatically enabled unless explicitly disabled in usr_mtd
- Tags are useful for organizing sensors by environment, platform, or team
- Use meaningful sensor names that indicate the platform and purpose
- When updating, the entire configuration is replaced - include all fields
- For credential rotation, update the sensor configuration with new credentials
- The `etag` field can be used for concurrent update protection
- After creating or updating, allow a few minutes for data collection to begin
- Check the sensor's last_error field if data isn't appearing (use get-cloud-sensor)
- Common sensor types and their key configuration fields:
  - **AWS CloudTrail**: sensor_type, aws_region, s3_bucket, role_arn, external_id
  - **AWS GuardDuty**: sensor_type, aws_region, role_arn, external_id
  - **Azure Activity Logs**: sensor_type, subscription_id, tenant_id, client_id, client_secret
  - **GCP Audit Logs**: sensor_type, project_id, service_account_json
  - **Office 365**: sensor_type, tenant_id, client_id, client_secret, content_types
  - **Okta**: sensor_type, domain, api_token
- Use list-cloud-sensors to verify the sensor was created
- Use get-cloud-sensor to inspect the configuration after creation
- Use delete-cloud-sensor to remove sensors that are no longer needed
- **Pre-deployment validation**: For cloud sensors using USP parsing configurations, use `validate_usp_mapping` to test parsing rules before deployment

## Related Functions

- `validate_usp_mapping` - Test USP parsing configurations before deployment
- `get_cloud_sensor` - Retrieve existing sensor configuration
- `list_cloud_sensors` - List all configured cloud sensors
- `delete_cloud_sensor` - Remove a cloud sensor

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `https://github.com/refractionPOINT/go-limacharlie/blob/master/limacharlie/hive.go`
For the MCP tool implementation, check: `https://github.com/refractionPOINT/lc-mcp/blob/master/internal/tools/hive/cloud_sensors.go`
