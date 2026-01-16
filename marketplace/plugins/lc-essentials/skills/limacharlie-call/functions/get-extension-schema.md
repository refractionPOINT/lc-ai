
# Get Extension Schema

Retrieves the configuration schema for a LimaCharlie extension, showing what configuration fields are available, their types, and constraints.

## When to Use

Use this skill when the user needs to:
- Understand what configuration options an extension supports
- View the schema before configuring an extension
- Check required vs optional fields for extension configuration
- Inspect field types and validation constraints
- Generate or validate extension configuration programmatically

Common scenarios:
- "What configuration options does the ext-exfil extension support?"
- "Show me the schema for the artifact-collection extension"
- "What fields can I set when configuring the threat-intel extension?"
- "What are the required parameters for the logging extension?"

## What This Skill Does

This skill retrieves the configuration schema definition for an extension from the LimaCharlie platform. Unlike `get_extension_config` which retrieves the actual configuration values stored in Hive, this skill returns the schema that defines what configuration fields are available for the extension.

The schema typically includes a `config_schema` field that describes:
- Available configuration fields
- Field types (string, number, boolean, object, array)
- Required vs optional fields
- Default values
- Validation constraints

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **extension_name**: The name of the extension to retrieve the schema for (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Extension name (string, must be exact match)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_extension_schema",
  parameters={
    "oid": "[organization-id]",
    "extension_name": "[extension-name]"
  }
)
```

**Tool Details:**
- Tool Name: `get_extension_schema`
- Required Parameters:
  - `oid`: Organization ID
  - `extension_name`: The name of the extension to retrieve the schema for

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "extension_name": "ext-exfil",
  "schema": {
    "config_schema": {
      "type": "object",
      "properties": {
        "setting1": {
          "type": "string",
          "description": "Description of setting1"
        },
        "setting2": {
          "type": "integer",
          "default": 100
        }
      },
      "required": ["setting1"]
    }
  }
}
```

**Success:**
- The `extension_name` field confirms which extension schema was retrieved
- The `schema` field contains the schema definition, typically with a `config_schema` sub-field
- Present the schema to the user in a readable format, highlighting required fields

**Common Errors:**
- **Invalid extension name**: Extension name doesn't exist or is misspelled
- **Forbidden**: Insufficient permissions - user needs appropriate extension permissions
- **Not Found**: The extension doesn't exist in the LimaCharlie marketplace

### Step 4: Format the Response

Present the result to the user:
- Show the extension name prominently
- List all available configuration fields with their types
- Highlight which fields are required vs optional
- Include default values where applicable
- Explain the purpose of each field if descriptions are available

## Example Usage

### Example 1: Get schema for an extension

User request: "What configuration options does the ext-exfil extension support?"

Steps:
1. Get the organization ID from context
2. Use extension name "ext-exfil"
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_extension_schema",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "extension_name": "ext-exfil"
  }
)
```

Expected response:
```json
{
  "extension_name": "ext-exfil",
  "schema": {
    "config_schema": {
      "type": "object",
      "properties": {
        "destination": {
          "type": "string",
          "description": "S3 bucket or GCS path for exfiltrated data"
        },
        "retention_days": {
          "type": "integer",
          "default": 30
        }
      },
      "required": ["destination"]
    }
  }
}
```

Format the output:
- Extension: ext-exfil
- Configuration Fields:
  - `destination` (string, REQUIRED): S3 bucket or GCS path for exfiltrated data
  - `retention_days` (integer, optional, default: 30): Retention period in days

### Example 2: Check schema before configuring

User request: "I want to configure the artifact-collection extension. What fields do I need to set?"

Steps:
1. Get the extension schema first
2. Show required vs optional fields
3. User can then use `set_extension_config` with the correct fields

## Additional Notes

- Extension names are case-sensitive - use exact names from the LimaCharlie marketplace
- This retrieves the schema definition, NOT the actual configuration values
- Use `get_extension_config` to retrieve the current configuration values
- Use `set_extension_config` to create or update configuration values based on the schema
- The schema format follows JSON Schema conventions
- An extension can be subscribed to (`subscribe_to_extension`) even without configuration if no required fields exist
- Some extensions may have an empty or minimal schema if they don't require configuration

## Related Functions

- `get_extension_config` - Get current configuration values (from Hive)
- `set_extension_config` - Create or update configuration
- `list_extension_configs` - List all configured extensions
- `subscribe_to_extension` - Subscribe to an extension
- `list_extension_subscriptions` - List subscribed extensions

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/extension.go` (GetExtensionSchema method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/config/extensions.go`
