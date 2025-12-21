
# Delete Extension Configuration

Permanently deletes an extension configuration from the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Delete an extension configuration permanently
- Remove an obsolete or unused configuration
- Clean up extension configurations
- Decommission an extension's settings
- Fix issues by removing and recreating a configuration

Common scenarios:
- "Delete the artifact-collection extension configuration"
- "Remove the logging extension config"
- "Clean up the old threat-intel configuration"
- "Delete extension config named 'test-integration'"

## What This Skill Does

This skill permanently deletes an extension configuration from the LimaCharlie Hive system. It calls the MCP tool using the "extension_config" hive name with the "global" partition and the specific extension name. Once deleted, the configuration and all its data are permanently removed and cannot be recovered.

**Warning:** This operation is permanent and cannot be undone. Consider getting the configuration first if you might need to restore it later.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **extension_name**: The name of the extension configuration to delete (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Extension name (string, must be exact match)
3. Consider warning the user that this is permanent
4. Optionally, use get-extension-config first to confirm what will be deleted

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_extension_config",
  parameters={
    "oid": "[organization-id]",
    "extension_name": "[extension-name]"
  }
)
```

**Tool Details:**
- Tool Name: `delete_extension_config`
- Required Parameters:
  - `oid`: Organization ID
  - `extension_name`: The name of the extension configuration to delete

### Step 3: Handle the Response

The tool returns a response with:
```json
{}
```

**Success:**
- Configuration has been permanently deleted
- The response may be empty or contain confirmation data
- Inform the user that the deletion was successful
- Note that this action cannot be undone

**Common Errors:**
- **Invalid extension name**: Extension name format is invalid
- **Forbidden**: Insufficient permissions - user needs platform_admin or similar role to delete
- **Not Found**: The extension configuration doesn't exist - inform user it was already deleted or never existed

### Step 4: Format the Response

Present the result to the user:
- Confirm the extension configuration was deleted
- Show the extension name that was removed
- Warn that this action is permanent
- Note that the extension subscription (if any) is separate and still exists
- Suggest using list-extension-configs to verify deletion if needed

## Example Usage

### Example 1: Delete an extension configuration

User request: "Delete the artifact-collection extension configuration"

Steps:
1. Get the organization ID from context
2. Optionally warn user about permanent deletion
3. Use extension name "artifact-collection"
4. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="delete_extension_config",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "extension_name": "artifact-collection"
  }
)
```

Expected response:
```json
{}
```

Inform user: "Successfully deleted the artifact-collection extension configuration. This action is permanent and cannot be undone. Note that the extension subscription (if any) still exists."

### Example 2: Handle non-existent configuration

User request: "Delete the non-existent-extension config"

Steps:
1. Attempt to delete the configuration
2. Receive not found error
3. Inform user: "The configuration 'non-existent-extension' does not exist. It may have already been deleted or was never created."

### Example 3: Confirm before deletion

User request: "Delete the logging extension configuration"

Steps:
1. First, use get-extension-config to retrieve current settings
2. Show user what will be deleted
3. Ask for confirmation
4. If confirmed, proceed with deletion
5. Suggest that user can recreate it later if needed using the retrieved settings

## Additional Notes

- **Permanent Action**: Deleted configurations cannot be recovered - there is no "trash" or "undo"
- **Backup First**: Consider retrieving the configuration with get-extension-config before deleting
- **Extension vs Config**: Deleting the configuration does NOT unsubscribe from the extension
  - The extension subscription remains active but will use default settings
  - Use unsubscribe-from-extension to remove the extension subscription itself
- **No Cascade**: Deleting a configuration doesn't affect related resources
- **Immediate Effect**: The configuration is removed immediately and stops being used
- **Re-creation**: You can create a new configuration with the same name after deletion
- **Name Sensitivity**: Extension names are case-sensitive - use exact name
- **Audit Trail**: The deletion is logged in organization audit logs
- **Related Operations**:
  - To temporarily disable: use set-extension-config with `enabled: false` instead
  - To remove extension entirely: also use unsubscribe-from-extension
  - To clean up multiple: delete each configuration individually (no batch delete)

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/hive.go` (Remove method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/hive/extension_configs.go`
