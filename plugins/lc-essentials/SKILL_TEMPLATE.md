# SKILL TEMPLATE - DO NOT USE DIRECTLY

This is a template for creating new skills. Copy this structure and fill in the specific details for each MCP tool.

## SKILL.md Structure

```yaml
---
name: tool-name-in-kebab-case
description: Clear, concise description of what this skill does and when Claude should use it. Include key trigger words and use cases. Maximum 1024 characters.
allowed-tools: mcp__limacharlie__lc_call_tool, Read
---

# [Tool Name in Title Case]

Brief overview of what this skill does (1-2 sentences).

## When to Use

Use this skill when the user needs to:
- [Specific use case 1]
- [Specific use case 2]
- [Specific use case 3]

Common scenarios:
- [Scenario 1 with context]
- [Scenario 2 with context]

## What This Skill Does

This skill [detailed explanation of functionality]. It calls the LimaCharlie API to [specific operation].

## Required Information

Before calling this skill, gather:
- **oid**: Organization ID (required for all API calls)
- **[param1]**: [Description and format]
- **[param2]**: [Description and format]

Optional parameters:
- **[optional-param]**: [Description and when to use]

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. [Other required parameters]
3. [Validation checks if needed]

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="[tool_name_in_snake_case]",
  parameters={
    "oid": "[organization-id]",
    "[param1]": "[value1]",
    "[param2]": "[value2]"
  }
)
```

**Tool Details:**
- Tool name: `[tool_name]`
- Required parameters: [List required parameters]
- Optional parameters: [List optional parameters if any]

### Step 3: Handle the Response

The tool returns results directly:
```json
{
  // Response structure specific to this tool
}
```

**Success:**
- [What the response contains]
- [How to interpret the data]
- [What to do with the result]

**Common Errors:**
- **Missing parameter**: [Required parameter not provided]
- **Not found**: [Resource doesn't exist]
- **Permission denied**: [Insufficient permissions]
- **Validation failed**: [Invalid configuration]

### Step 4: Format the Response

Present the result to the user:
- [How to format the output]
- [What information to highlight]
- [Any warnings or notes to include]

## Example Usage

### Example 1: [Common scenario]

User request: "[Example user request]"

Steps:
1. [Step 1]
2. [Step 2]
3. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="example_tool",
  parameters={
    "oid": "abc123...",
    "param": "value"
  }
)
```

Expected response:
```json
{
  // Example response
}
```

### Example 2: [Edge case or complex scenario]

User request: "[Another example]"

[Similar structure as Example 1]

## Additional Notes

- [Any special considerations]
- [Related skills that might be useful]
- [Common gotchas or limitations]
- [Best practices specific to this operation]

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/[relevant-file].go`
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/[category]/[tool-file].go`
```

## Key Points for Skill Creation

1. **Name**: Use kebab-case matching the snake_case MCP tool name
2. **Description**: Rich with keywords, use cases, and trigger words (max 1024 chars)
3. **Allowed Tools**: Always include the lc_call_tool and Read tool
4. **Structure**: Follow the template structure for consistency
5. **Examples**: Include at least 2 concrete examples
6. **Error Handling**: Document common errors and how to handle them
7. **Tool Details**: Be specific about tool name and parameters
8. **Response Handling**: Explain what comes back and how to use it

## Common Patterns by Operation Type

### List Operations
- Tool names like `list_sensors`, `list_outputs`
- Usually requires only `oid` parameter
- Returns array or object of resources

### Get Single Resource
- Tool names like `get_sensor_info`, `get_secret`
- Requires `oid` plus resource identifier
- Returns single resource object

### Create Operations
- Tool names like `add_output`, `create_api_key`
- Requires `oid` plus resource configuration
- Returns created resource

### Update Operations
- Tool names like `set_rule`, `set_secret`
- Requires `oid` plus resource name and new configuration
- Returns updated resource

### Delete Operations
- Tool names like `delete_sensor`, `delete_output`
- Requires `oid` plus resource identifier
- Returns success confirmation

## Discovery Optimization

To make skills easily discoverable:
- Include action verbs in description (list, get, create, delete, update, search, scan, etc.)
- Include domain keywords (sensor, rule, detection, output, secret, etc.)
- Include use case keywords (security, investigation, incident response, compliance, etc.)
- Include related concepts (YARA for malware, LCQL for querying, etc.)
- Mention common user intents (troubleshoot, investigate, monitor, alert, etc.)