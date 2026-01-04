
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

**CRITICAL - Config Structure**: All cloud sensor configs MUST follow this nested structure:
```json
{
  "sensor_type": "<adapter-type>",
  "<adapter-type>": {
    "client_options": {
      "identity": { "oid": "<org-id>", "installation_key": "<iid>" },
      "platform": "json",
      "sensor_seed_key": "<unique-key>"
    },
    // adapter-specific fields here
  }
}
```

**IMPORTANT - Finding Adapter Fields**: The authoritative source for each adapter's configuration fields is the **usp-adapters GitHub repository**:
- URL: `https://github.com/refractionPOINT/usp-adapters`
- Each adapter has a `client.go` file with a `*Config` struct defining all valid fields
- Example: For `okta`, check `usp-adapters/okta/client.go` → `OktaConfig` struct

Common sensor types (always verify in usp-adapters for complete field list):
- **s3**: AWS S3 buckets (including CloudTrail logs)
- **azure_event_hub**: Azure Event Hub
- **gcs**: Google Cloud Storage
- **pubsub**: GCP Pub/Sub
- **office365**: Microsoft 365 audit logs
- **okta**: Okta system logs
- **webhook**: Generic webhook receiver
- **falconcloud**: CrowdStrike Falcon
- And 30+ more adapters...

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
      "sensor_type": "okta",
      "okta": {
        "client_options": {
          "identity": {
            "oid": "[organization-id]",
            "installation_key": "[installation-key]"
          },
          "platform": "json",
          "sensor_seed_key": "okta-system-logs"
        },
        "apikey": "hive://secret/okta-api-key",
        "url": "https://company.okta.com"
      }
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

### Example 1: Create S3 cloud sensor for AWS CloudTrail logs

User request: "Set up a cloud sensor for our AWS CloudTrail logs in the production environment"

**Note**: For AWS CloudTrail logs stored in S3, use the `s3` sensor type (not `aws_cloudtrail` which doesn't exist).

Steps:
1. Extract organization ID and installation key from context
2. Prepare sensor name: "prod-aws-cloudtrail"
3. Store AWS credentials as secrets first
4. Call tool with properly nested config:
```
mcp__limacharlie__lc_call_tool(
  tool_name="set_cloud_sensor",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sensor_name": "prod-aws-cloudtrail",
    "sensor_config": {
      "sensor_type": "s3",
      "s3": {
        "client_options": {
          "identity": {
            "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
            "installation_key": "your-installation-key"
          },
          "platform": "json",
          "sensor_seed_key": "prod-cloudtrail-logs"
        },
        "bucket_name": "my-cloudtrail-logs",
        "access_key": "hive://secret/aws-access-key",
        "secret_key": "hive://secret/aws-secret-key",
        "region": "us-east-1",
        "prefix": "AWSLogs/"
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
    "name": "cloud_sensor",
    "partition": "global"
  },
  "name": "prod-aws-cloudtrail"
}
```

Present to user:
```
Successfully created S3 cloud sensor for AWS CloudTrail logs!

Sensor Name: prod-aws-cloudtrail
Type: S3
Status: Enabled

Configuration:
- S3 Bucket: my-cloudtrail-logs
- Region: us-east-1
- Prefix: AWSLogs/

The sensor will begin collecting CloudTrail logs from your S3 bucket.
Check back in a few minutes to verify data is flowing.
```

### Example 2: Create Office 365 sensor with secret reference

User request: "Set up an Office 365 audit log sensor"

Steps:
1. First, store the client secret in LimaCharlie's secret manager
2. Create the sensor config referencing the secret with proper nested structure
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

# Step 2: Create sensor with properly nested config
mcp__limacharlie__lc_call_tool(
  tool_name="set_cloud_sensor",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sensor_name": "office365-audit",
    "sensor_config": {
      "sensor_type": "office365",
      "office365": {
        "client_options": {
          "identity": {
            "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
            "installation_key": "your-installation-key"
          },
          "platform": "json",
          "sensor_seed_key": "o365-audit-logs"
        },
        "domain": "company.onmicrosoft.com",
        "tenant_id": "abc-123-def",
        "publisher_id": "abc-123-def",
        "client_id": "client-id-456",
        "client_secret": "hive://secret/o365-client-secret",
        "endpoint": "enterprise",
        "content_types": "Audit.AzureActiveDirectory,Audit.Exchange,Audit.SharePoint,Audit.General"
      }
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

2. **Then reference it in the sensor config** (note the nested structure):
```json
{
  "sensor_type": "pubsub",
  "pubsub": {
    "client_options": {
      "identity": { "oid": "<org-id>", "installation_key": "<iid>" },
      "platform": "json",
      "sensor_seed_key": "my-pubsub-sensor"
    },
    "service_account_creds": "hive://secret/gcp-sa-key",
    "project_id": "my-project",
    "subscription_id": "my-subscription"
  }
}
```

**Common credential fields that support `hive://secret/`**:
- `service_account_creds` (GCP Pub/Sub, GCS)
- `client_secret` (Azure, Office 365)
- `apikey` (Okta)
- `secret_key` (AWS S3, SQS)

**Wrong** - Flat structure without nesting:
```json
{
  "sensor_type": "pubsub",
  "service_account_creds": "hive://secret/my-secret",
  "project_id": "my-project"
}
```

**Right** - Properly nested with matching type key:
```json
{
  "sensor_type": "pubsub",
  "pubsub": {
    "client_options": { ... },
    "service_account_creds": "hive://secret/my-secret",
    "project_id": "my-project",
    "subscription_id": "my-subscription"
  }
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
- **Always consult the usp-adapters repo** (`https://github.com/refractionPOINT/usp-adapters`) for the authoritative list of fields for each adapter type. Look for the `*Config` struct in each adapter's `client.go` file.
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
