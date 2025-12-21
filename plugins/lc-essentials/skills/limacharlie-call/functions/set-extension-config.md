
# Set Extension Configuration

Creates or updates an extension configuration in the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Create a new extension configuration
- Update an existing extension configuration
- Modify extension settings
- Configure an extension for the first time
- Change extension parameters

Common scenarios:
- "Configure the artifact-collection extension with 90-day retention"
- "Update the logging extension to use S3 bucket xyz"
- "Set up the threat-intel extension with these API keys"
- "Create extension config named 'custom-integration' with these settings"

## What This Skill Does

This skill creates or updates an extension configuration in the LimaCharlie Hive system. It calls the MCP tool using the "extension_config" hive name with the "global" partition. The configuration is automatically enabled and includes the provided data. If a configuration with the same name already exists, it will be updated. The operation uses gzip compression and base64 encoding for efficient transfer of potentially large configuration data.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **extension_name**: The name for the extension configuration (required)
- **config_data**: The configuration data object (required, must be valid JSON object)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Extension name (string, will become the configuration key)
3. Configuration data (object/dict with extension-specific settings)
4. Validate that config structure matches extension requirements

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_extension_config",
  parameters={
    "oid": "[organization-id]",
    "extension_name": "[extension-name]",
    "config_data": {
      "setting1": "value1",
      "setting2": 123
    }
  }
)
```

**Tool Details:**
- Tool Name: `set_extension_config`
- Required Parameters:
  - `oid`: Organization ID
  - `extension_name`: The name for the extension configuration
  - `config_data`: Configuration data object with extension-specific settings

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "guid": "unique-record-id",
  "hive": {
    "name": "extension_config",
    "partition": "global"
  },
  "name": "extension-name"
}
```

**Success:**
- Configuration has been created or updated successfully
- The response includes a unique GUID for the record
- The `name` field confirms which configuration was set
- Inform the user that the configuration is now active

**Common Errors:**
- **Invalid configuration**: Invalid configuration data format or structure - check the config object
- **Forbidden**: Insufficient permissions - user needs platform_admin or similar role
- **Conflict**: ETag mismatch if using optimistic locking (advanced use case)
- **Payload Too Large**: Configuration data exceeds size limits

### Step 4: Format the Response

Present the result to the user:
- Confirm the extension configuration was created/updated
- Show the extension name
- Summarize key configuration settings
- Note that it's enabled and ready to use
- If updating, mention what changed from the previous version
- Suggest verifying with get-extension-config if needed

## Example Usage

### Example 1: Create a new extension configuration

User request: "Configure the artifact-collection extension with 90-day retention and 100MB max size"

Steps:
1. Get the organization ID from context
2. Prepare configuration data:
   ```json
   {
     "retention_days": 90,
     "max_size_mb": 100,
     "auto_collect": true
   }
   ```
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="set_extension_config",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "extension_name": "artifact-collection",
    "config_data": {
      "retention_days": 90,
      "max_size_mb": 100,
      "auto_collect": true
    }
  }
)
```

Expected response:
```json
{
  "guid": "ext-config-abc123",
  "name": "artifact-collection"
}
```

Inform user: "Successfully configured artifact-collection extension with 90-day retention and 100MB max size. Configuration is enabled and active."

### Example 2: Update existing configuration

User request: "Update the logging extension to use S3 bucket 'my-logs-bucket'"

Steps:
1. Optionally get existing config first to see current settings
2. Prepare updated configuration data
3. Call tool with the new configuration (it will replace the existing one)
4. Confirm the update was successful

## Additional Notes

- **Creating vs Updating**: This operation performs an "upsert" - creates if doesn't exist, updates if it does
- **Data Structure**: Each extension type has its own expected configuration schema - consult extension documentation
- **Enabled by Default**: New configurations are enabled by default
- **ETag for Safety**: For advanced use cases, you can use ETags to prevent concurrent modification conflicts
- **Size Limits**: Very large configurations may hit payload size limits - keep configs reasonable
- **Validation**: The API may validate configuration structure against extension schema
- **No Partial Updates**: POST replaces the entire configuration - include all fields you want to keep
- **Subscription Required**: For the configuration to take effect, the extension must also be subscribed
- Use `get_extension_config` to verify the configuration was set correctly
- Use `subscribe_to_extension` to activate the extension if not already subscribed

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Add method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/extension_configs.go`
