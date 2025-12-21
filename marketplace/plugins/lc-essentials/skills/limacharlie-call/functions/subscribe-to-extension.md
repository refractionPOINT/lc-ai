
# Subscribe to Extension

Subscribes a LimaCharlie organization to an extension, enabling its functionality.

## When to Use

Use this skill when the user needs to:
- Subscribe to an extension to activate it
- Enable an extension in their organization
- Add a new extension capability
- Activate an extension's functionality
- Start using an extension

Common scenarios:
- "Subscribe to the threat-intel extension"
- "Enable the artifact-collection extension"
- "Add the logging extension to my organization"
- "Activate the custom-integration extension"

## What This Skill Does

This skill subscribes an organization to a LimaCharlie extension by calling the MCP tool. Once subscribed, the extension becomes active in the organization and can process events, provide integrations, or deliver functionality based on its purpose. The subscription is independent of extension configuration - you can subscribe without configuring, or configure without subscribing, but both are typically needed for the extension to work effectively.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)
- **extension_name**: The name of the extension to subscribe to (required)

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Extension name (string, must match available extension name)
3. Verify the extension exists and is available
4. Check if already subscribed to avoid duplicate subscription

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="subscribe_to_extension",
  parameters={
    "oid": "[organization-id]",
    "extension_name": "[extension-name]"
  }
)
```

**Tool Details:**
- Tool Name: `subscribe_to_extension`
- Required Parameters:
  - `oid`: Organization ID
  - `extension_name`: The name of the extension to subscribe to

### Step 3: Handle the Response

The tool returns a response with:
```json
{}
```

**Success:**
- Subscription was successful
- The extension is now active in the organization
- The extension can now process data and provide functionality
- Inform the user that subscription is complete

**Common Errors:**
- **Invalid extension name**: Extension name is invalid or already subscribed
- **Forbidden**: Insufficient permissions - user needs platform_admin role
- **Not Found**: Extension doesn't exist or isn't available
- **Conflict**: Already subscribed to this extension

### Step 4: Format the Response

Present the result to the user:
- Confirm the extension subscription was successful
- Show the extension name
- Note that the extension is now active
- If the extension requires configuration, suggest using set-extension-config
- Mention any setup steps specific to the extension
- Suggest verifying the extension is working as expected

## Example Usage

### Example 1: Subscribe to an extension

User request: "Subscribe to the threat-intel extension"

Steps:
1. Get the organization ID from context
2. Use extension name "threat-intel"
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="subscribe_to_extension",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "extension_name": "threat-intel"
  }
)
```

Expected response:
```json
{}
```

Inform user: "Successfully subscribed to the threat-intel extension. The extension is now active in your organization. You may need to configure it using set-extension-config for it to function fully."

### Example 2: Handle already subscribed

User request: "Subscribe to the logging extension"

Steps:
1. Attempt to subscribe
2. Receive conflict error
3. Inform user: "Your organization is already subscribed to the logging extension. To modify its configuration, use set-extension-config. To deactivate it, use unsubscribe-from-extension."

### Example 3: Subscribe and configure

User request: "Enable the artifact-collection extension with 90-day retention"

Steps:
1. First, subscribe to the extension (this skill)
2. Then, configure it with set-extension-config
3. Confirm both operations completed successfully

## Additional Notes

- **Subscription vs Configuration**: These are separate operations:
  - Subscription activates the extension
  - Configuration provides settings for the extension
  - Both are typically needed for full functionality
- **Extension Availability**: Not all extensions are available in all regions or for all plan types
- **Billing**: Some extensions may incur additional charges - check extension documentation
- **Provisioning Time**: Extension activation may take a few seconds to complete
- **API Keys**: Some extensions generate API keys upon subscription for secure communication
- **No Duplicate**: Cannot subscribe twice to the same extension
- **Immediate Effect**: Once subscribed, the extension begins processing data immediately
- **Dependencies**: Some extensions may depend on other extensions being subscribed
- **Organization Level**: Extensions are subscribed at the organization level, not per-sensor
- **Audit Trail**: Subscription is logged in organization audit logs
- **Related Operations**:
  - After subscribing: use set-extension-config to configure settings
  - To deactivate: use unsubscribe-from-extension
  - To view active subscriptions: use list_user_orgs with subscription details
  - To modify settings: use set-extension-config

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/extension.go` (SubscribeToExtension method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/config/extensions.go`
