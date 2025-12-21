
# Get Extension Configuration

Retrieves a specific extension configuration by name from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Get detailed configuration for a specific extension
- View extension settings before modifying them
- Check if an extension configuration exists
- Inspect extension metadata (creation date, last author, etc.)
- Review extension configuration as part of troubleshooting

Common scenarios:
- "Show me the configuration for the artifact-collection extension"
- "What are the settings for my logging extension?"
- "Get the extension config named 'custom-integration'"
- "Is the threat-intel extension configured?"

## What This Skill Does

This skill retrieves a single extension configuration record from the LimaCharlie Hive system by its name. It calls the MCP tool using the "extension_config" hive name with the organization ID as the partition and the specific extension name as the key. The response includes the complete configuration data, user metadata (enabled, tags, comments), and system metadata (audit trail).

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **extension_name**: The name of the extension configuration to retrieve (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Extension name (string, must be exact match)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_extension_config",
  parameters={
    "oid": "[organization-id]",
    "extension_name": "[extension-name]"
  }
)
```

**Tool Details:**
- Tool Name: `get_extension_config`
- Required Parameters:
  - `oid`: Organization ID
  - `extension_name`: The name of the extension configuration to retrieve

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "data": {
    // Extension-specific configuration data
    "setting1": "value1",
    "setting2": 123
  },
  "sys_mtd": {
    "etag": "abc123...",
    "created_by": "user@example.com",
    "created_at": 1234567890,
    "last_author": "user@example.com",
    "last_mod": 1234567899,
    "guid": "unique-id-123",
    "last_error": "",
    "last_error_ts": 0
  },
  "usr_mtd": {
    "enabled": true,
    "expiry": 0,
    "tags": ["production", "critical"],
    "comment": "Extension configuration description"
  }
}
```

**Success:**
- The `data` field contains the extension-specific configuration (structure varies by extension)
- The `usr_mtd` field shows user-controlled metadata (enabled status, tags, comments)
- The `sys_mtd` field shows system metadata including creation and modification history
- Present the configuration details to the user in a readable format

**Common Errors:**
- **Invalid extension name**: Extension name format is invalid
- **Forbidden**: Insufficient permissions - user needs platform_admin or similar role
- **Not Found**: The extension configuration doesn't exist - inform user and suggest creating it

### Step 4: Format the Response

Present the result to the user:
- Show the extension name and enabled status prominently
- Display the configuration data in a structured, readable format
- Include relevant metadata like creation date and last modification
- Note any tags or comments
- If configuration contains sensitive data, warn the user appropriately
- Explain what each configuration setting does if possible

## Example Usage

### Example 1: Get a specific extension configuration

User request: "Show me the artifact-collection extension configuration"

Steps:
1. Get the organization ID from context
2. Use extension name "artifact-collection"
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_extension_config",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "extension_name": "artifact-collection"
  }
)
```

Expected response:
```json
{
  "data": {
    "retention_days": 90,
    "max_size_mb": 100,
    "auto_collect": true
  },
  "sys_mtd": {
    "created_at": 1700000000,
    "last_mod": 1700001000,
    "last_author": "admin@example.com",
    "guid": "ext-config-123"
  },
  "usr_mtd": {
    "enabled": true,
    "tags": ["production"],
    "comment": "Artifact collection with 90-day retention"
  }
}
```

Format the output:
- Extension: artifact-collection (Enabled)
- Retention: 90 days
- Max Size: 100 MB
- Auto-collect: Yes
- Last Modified: [formatted date] by admin@example.com

### Example 2: Check if configuration exists

User request: "Does the threat-intel extension have a configuration?"

Steps:
1. Attempt to get the extension config
2. If not found error: inform user the configuration doesn't exist
3. If success: confirm it exists and show summary

## Additional Notes

- Extension names are case-sensitive - use exact name from list-extension-configs
- The `data` field structure is extension-specific - each extension defines its own schema
- The `enabled` field controls whether the configuration is active
- ETag in sys_mtd is used for optimistic locking in updates
- A configuration can exist even if the extension isn't subscribed (though it won't be used)
- Use `list_extension_configs` first if you don't know the exact extension name
- Extensions with the same name across different partition keys are separate configurations

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Get method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/extension_configs.go`
