
# Get Event Types With Schemas

Retrieve a complete list of all event types that have schema definitions available in the organization.

## When to Use

Use this skill when the user needs to:
- Discover what event types are available
- List all telemetry types supported
- Find the correct name for a specific event type
- Browse available data sources for detection
- Understand the organization's telemetry coverage

Common scenarios:
- "What event types are available?"
- "Show me all the events LimaCharlie can collect"
- "What's the event type for DNS queries?"
- "List all network-related events"

## What This Skill Does

This skill retrieves the complete list of event type names that have schema definitions in LimaCharlie. It returns a comprehensive array of event type names, allowing users to discover what telemetry is available before diving into specific schemas.

## Required Information

Before calling this skill, gather:

- **oid**: Organization ID (UUID) - the organization to query schemas for

| Name | Type | Required | Description |
|------|------|----------|-------------|
| oid | UUID | Yes | Organization ID ([Core Concepts](../../../CALLING_API.md#core-concepts)) |

## How to Use

### Step 1: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_event_types_with_schemas",
  parameters={
    "oid": "[organization-uuid]"
  }
)
```

**API Details:**
- Tool: `get_event_types_with_schemas`
- Required parameters:
  - `oid`: Organization ID (UUID)

### Step 2: Handle the Response

The API returns a response with:
```json
{
  "event_types": [
    "DNS_REQUEST",
    "HTTP_REQUEST",
    "NETWORK_CONNECTIONS",
    "PROCESS_START",
    "FILE_CREATE",
    "FILE_DELETE",
    "REGISTRY_CREATE",
    ...
  ],
  "count": 85
}
```

**Success (200-299):**
- Response contains `event_types` array with all available event type names
- Names use LimaCharlie's standard naming convention (UPPERCASE_WITH_UNDERSCORES)
- Array typically contains 50-100+ event types depending on platform support
- These names can be used with `get_event_schema` to get detailed field information

**Common Errors:**
- **403 Forbidden**: Insufficient API permissions to read schemas
- **404 Not Found**: Invalid or missing OID parameter
- **500 Server Error**: Temporary API issue - retry after a short delay

### Step 3: Format the Response

Present the result to the user:
- List event types in logical groups (network, process, file, registry, etc.)
- Include a count of total event types available
- Highlight commonly used event types
- Provide brief descriptions of event type categories
- If user asked for specific type, filter and highlight matches

## Example Usage

### Example 1: Listing all available event types

User request: "What event types are available in LimaCharlie?"

Steps:
1. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_event_types_with_schemas",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "event_types": [
    "DNS_REQUEST",
    "HTTP_REQUEST",
    "NETWORK_CONNECTIONS",
    "PROCESS_START",
    "FILE_CREATE",
    "FILE_DELETE",
    "REGISTRY_CREATE",
    ...
  ],
  "count": 85
}
```

Present to user grouped by category:
- Network Events: DNS_REQUEST, HTTP_REQUEST, NETWORK_CONNECTIONS...
- Process Events: PROCESS_START, PROCESS_TERMINATE...
- File Events: FILE_CREATE, FILE_DELETE, FILE_OPEN...
- Registry Events: REGISTRY_CREATE, REGISTRY_DELETE...

### Example 2: Finding DNS-related events

User request: "What events are available for DNS monitoring?"

Steps:
1. Get all event types with OID
2. Filter for DNS-related names
3. Present matching event types with brief descriptions

## Additional Notes

- Event type names are platform-agnostic at the schema level
- Not all event types are available on all platforms (Windows, Linux, macOS)
- Use `get-event-types-with-schemas-for-platform` to filter by OS
- The list includes both endpoint and cloud/SaaS event types
- Event types with schemas are those that have been indexed and are queryable
- Use this as a discovery tool before requesting specific schemas
- Names returned here can be directly used with other schema-related skills

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `/go-limacharlie/limacharlie/schemas.go`
For the MCP tool implementation, check: `/lc-mcp-server/internal/tools/schemas/schemas.go`
