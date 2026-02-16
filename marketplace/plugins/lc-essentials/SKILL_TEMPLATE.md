# SKILL TEMPLATE - DO NOT USE DIRECTLY

This is a template for creating new skills. Copy this structure and fill in the specific details for each operation.

## SKILL.md Structure

```yaml
---
name: tool-name-in-kebab-case
description: Clear, concise description of what this skill does and when Claude should use it. Include key trigger words and use cases. Maximum 1024 characters.
allowed-tools:
  - Task
  - Read
  - Bash
---

# [Tool Name in Title Case]

Brief overview of what this skill does (1-2 sentences).

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output yaml [flags]
```

For command help: `limacharlie <command> --ai-help`
For command discovery: `limacharlie discover`

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **Output Format** | `--output json` | `--output yaml` (more token-efficient) |
| **Filter Output** | Pipe to jq/yq | Use `--filter JMESPATH` to select fields |
| **LCQL Queries** | Write query syntax manually | Use `limacharlie ai generate-query` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |

---

## When to Use

Use this skill when the user needs to:
- [Specific use case 1]
- [Specific use case 2]
- [Specific use case 3]

Common scenarios:
- [Scenario 1 with context]
- [Scenario 2 with context]

## What This Skill Does

This skill [detailed explanation of functionality]. It calls the LimaCharlie CLI to [specific operation].

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

### Step 2: Execute the Command

Use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output yaml [--flag value]
```

**Command Details:**
- Command: `limacharlie <noun> <verb>`
- Required flags: [List required flags]
- Optional flags: [List optional flags if any]

### Step 3: Handle the Response

The command returns YAML output:
```yaml
# Response structure specific to this command
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
3. Run command:
```bash
limacharlie sensor list --oid abc123... --output yaml
```

Expected response:
```yaml
# Example response
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

For more details on using the `limacharlie` CLI, see [CALLING_API.md](../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/[relevant-file].go`
```

## Key Points for Skill Creation

1. **Name**: Use kebab-case matching the operation name
2. **Description**: Rich with keywords, use cases, and trigger words (max 1024 chars)
3. **Allowed Tools**: Include Task, Read, Bash as needed - never include `mcp__*` tools
4. **Structure**: Follow the template structure for consistency
5. **Examples**: Include at least 2 concrete examples
6. **Error Handling**: Document common errors and how to handle them
7. **Command Details**: Be specific about CLI commands and flags
8. **Response Handling**: Explain what comes back and how to use it

## Common Patterns by Operation Type

### List Operations
- Commands like `limacharlie sensor list`, `limacharlie output list`
- Usually requires only `--oid` flag
- Returns array or object of resources

### Get Single Resource
- Commands like `limacharlie sensor get`, `limacharlie secret get`
- Requires `--oid` plus resource identifier
- Returns single resource object

### Create Operations
- Commands like `limacharlie output add`, `limacharlie api-key create`
- Requires `--oid` plus resource configuration
- Returns created resource

### Update Operations
- Commands like `limacharlie rule set`, `limacharlie secret set`
- Requires `--oid` plus resource name and new configuration
- Returns updated resource

### Delete Operations
- Commands like `limacharlie sensor delete`, `limacharlie output delete`
- Requires `--oid` plus resource identifier
- Returns success confirmation

## Discovery Optimization

To make skills easily discoverable:
- Include action verbs in description (list, get, create, delete, update, search, scan, etc.)
- Include domain keywords (sensor, rule, detection, output, secret, etc.)
- Include use case keywords (security, investigation, incident response, compliance, etc.)
- Include related concepts (YARA for malware, LCQL for querying, etc.)
- Mention common user intents (troubleshoot, investigate, monitor, alert, etc.)
