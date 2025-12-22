
# List Extension Subscriptions

Lists all extension subscriptions for a LimaCharlie organization.

## When to Use

Use this skill when the user needs to:
- View which extensions their organization is subscribed to
- Audit current extension subscriptions
- Check if a specific extension is enabled before configuring it
- Review active extensions before making changes
- Verify subscription status after subscribing or unsubscribing

Common scenarios:
- "What extensions am I subscribed to?"
- "List my extension subscriptions"
- "Show me all active extensions"
- "Which extensions are enabled in my organization?"
- "Am I subscribed to the threat-intel extension?"

## What This Skill Does

This skill retrieves all extension subscriptions for a LimaCharlie organization by calling the MCP tool. It returns a list of extension names that the organization is currently subscribed to. This is different from extension configurations - subscriptions indicate which extensions are active, while configurations contain the settings for those extensions.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

No other parameters are required.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="list_extension_subscriptions",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**Tool Details:**
- Tool Name: `list_extension_subscriptions`
- Required Parameters:
  - `oid`: Organization ID

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "subscriptions": [
    "extension-name-1",
    "extension-name-2",
    "extension-name-3"
  ]
}
```

**Success:**
- The response contains a `subscriptions` array with extension names
- Each entry is the name of an extension the organization is subscribed to
- An empty array means no extensions are subscribed
- Present the list to the user with a count

**Common Errors:**
- **Forbidden**: Insufficient permissions - user needs platform_admin role
- **Invalid OID**: Organization ID is not valid or doesn't exist

### Step 4: Format the Response

Present the result to the user:
- Show a count of how many extensions are subscribed
- List each extension name
- If checking for a specific extension, confirm whether it's in the list
- Suggest using `list_extension_configs` to see configuration details
- Note that subscription is required for an extension to be active

## Example Usage

### Example 1: List all subscriptions

User request: "What extensions am I subscribed to?"

Steps:
1. Get the organization ID from context
2. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="list_extension_subscriptions",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "subscriptions": [
    "ext-artifact-collection",
    "ext-reliable-tasking",
    "ext-sensor-cull"
  ]
}
```

Inform user: "Your organization is subscribed to 3 extensions: ext-artifact-collection, ext-reliable-tasking, and ext-sensor-cull. To see the configuration details for any of these, use list-extension-configs."

### Example 2: Check for a specific extension

User request: "Am I subscribed to the threat-intel extension?"

Steps:
1. Get organization ID
2. List all subscriptions
3. Check if "threat-intel" or "ext-threat-intel" is in the list
4. Inform user whether they are subscribed

Response: "Your organization is not currently subscribed to the threat-intel extension. Use subscribe-to-extension to add it."

### Example 3: No subscriptions

User request: "Show my extension subscriptions"

Steps:
1. Call the tool
2. Receive empty array

Response: "Your organization has no extension subscriptions. Extensions provide additional functionality like artifact collection, threat intelligence, and more. Use subscribe-to-extension to add extensions."

## Additional Notes

- **Subscriptions vs Configurations**: These are separate concepts:
  - Subscriptions indicate which extensions are active (this tool)
  - Configurations contain settings for extensions (use list-extension-configs)
  - An extension needs both subscription AND configuration to work properly
- **Extension Names**: Extension names typically follow the pattern `ext-<name>` (e.g., `ext-reliable-tasking`)
- **Immediate**: The list reflects current subscriptions in real-time
- **Organization Level**: Subscriptions are at the organization level, not per-sensor
- **Related Operations**:
  - To subscribe to an extension: use subscribe-to-extension
  - To unsubscribe from an extension: use unsubscribe-from-extension
  - To view extension configurations: use list-extension-configs
  - To configure an extension: use set-extension-config

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/extension.go` (Extensions method)
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/config/extensions.go`
