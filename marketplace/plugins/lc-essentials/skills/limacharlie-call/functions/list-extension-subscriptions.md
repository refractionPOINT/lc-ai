
# List Extension Subscriptions

Lists all extensions that a LimaCharlie organization is currently subscribed to.

## When to Use

Use this skill when the user needs to:
- Check which extensions are active in an organization
- Audit extension subscriptions
- Verify if a specific extension is enabled
- Review all subscribed extensions before making changes
- Determine what extensions are available before subscribing

Common scenarios:
- "What extensions do I have enabled?"
- "List my extension subscriptions"
- "Which extensions are active in my organization?"
- "Show me all subscribed extensions"
- "Check if threat-intel extension is enabled"

## What This Skill Does

This skill retrieves a list of all extension names that the organization is currently subscribed to. Extensions provide additional functionality like threat intelligence integrations, artifact collection, logging capabilities, and more. The list returned contains only the names of subscribed extensions - for configuration details, use get-extension-config.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

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
  "subscriptions": ["extension-name-1", "extension-name-2", "extension-name-3"]
}
```

**Success:**
- Returns an array of extension names the organization is subscribed to
- Empty array means no extensions are subscribed
- Each string in the array is an extension name

**Common Errors:**
- **Forbidden**: Insufficient permissions - user needs platform_admin role
- **Not Found**: Organization doesn't exist

### Step 4: Format the Response

Present the result to the user:
- List all subscribed extensions clearly
- If empty, inform the user no extensions are currently subscribed
- Suggest using subscribe-to-extension to add new extensions
- Offer to show configuration details with get-extension-config

## Example Usage

### Example 1: List all subscriptions

User request: "What extensions do I have?"

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
  "subscriptions": ["artifact-collection", "threat-intel", "logging"]
}
```

Inform user: "Your organization has 3 extensions subscribed: artifact-collection, threat-intel, and logging. Would you like to see the configuration for any of these, or subscribe to additional extensions?"

### Example 2: Check for a specific extension

User request: "Is the threat-intel extension enabled?"

Steps:
1. Call list_extension_subscriptions
2. Check if "threat-intel" is in the subscriptions array
3. Inform user: "Yes, the threat-intel extension is enabled in your organization." or "No, the threat-intel extension is not currently subscribed. Would you like to enable it?"

### Example 3: Empty subscriptions

User request: "Show me my extension subscriptions"

Steps:
1. Call list_extension_subscriptions
2. Receive empty array
3. Inform user: "Your organization currently has no extension subscriptions. Extensions provide additional functionality like threat intelligence, artifact collection, and logging. Would you like to subscribe to any extensions?"

## Additional Notes

- **Subscription vs Configuration**: These are separate concepts:
  - Subscriptions determine which extensions are active
  - Configuration provides settings for each extension
  - Use get-extension-config to see settings for a subscribed extension
- **Extension Names**: Names are case-sensitive strings
- **Organization Level**: Extensions are subscribed at the organization level, not per-sensor
- **Related Operations**:
  - To subscribe: use subscribe-to-extension
  - To unsubscribe: use unsubscribe-from-extension
  - To view config: use get-extension-config
  - To modify config: use set-extension-config

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).
