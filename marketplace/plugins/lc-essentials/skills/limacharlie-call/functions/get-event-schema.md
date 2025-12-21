
# Get Event Schema

Retrieve the detailed schema definition for a specific event type in LimaCharlie, including all available fields and their descriptions.

## When to Use

Use this skill when the user needs to:
- Understand the structure of a specific event type
- See what fields are available for a particular event
- Build queries or D&R rules that reference specific event fields
- Analyze telemetry data and understand field names
- Document event structures for integrations

Common scenarios:
- "Show me the schema for DNS_REQUEST events"
- "What fields are available in PROCESS_START events?"
- "I need to understand the structure of NETWORK_CONNECTIONS"
- "What data is captured in FILE_OPEN events?"

## What This Skill Does

This skill retrieves the complete schema definition for a specific event type. It calls the LimaCharlie API to fetch detailed information about the event structure, including all available field names (elements) and their descriptions. This is essential for understanding what data is captured in each event type and how to reference it in queries and rules.

## Required Information

Before calling this skill, gather:

- **name**: Event type name (e.g., 'DNS_REQUEST', 'PROCESS_START', 'NETWORK_CONNECTIONS')

The event type name should match LimaCharlie's event type naming convention (usually UPPERCASE_WITH_UNDERSCORES).

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Exact event type name (case-sensitive)
2. Event type exists in LimaCharlie's schema system

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_event_schema",
  parameters={
    "name": "[event-type-name]"
  }
)
```

**API Details:**
- Tool: `get_event_schema`
- Required parameters:
  - `name`: Event type name (e.g., "DNS_REQUEST")

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "event_type": "DNS_REQUEST",
  "elements": [
    "event/DNS_REQUEST/DOMAIN_NAME",
    "event/DNS_REQUEST/DNS_TYPE",
    "event/DNS_REQUEST/RESPONSE_IP",
    "event/PROCESS_ID",
    "event/TIMESTAMP"
  ]
}
```

**Success (200-299):**
- Response contains a schema object with:
  - `event_type`: The name of the event type
  - `elements`: Array of field paths that can be used in queries and rules
- Elements use slash notation (e.g., `event/DNS_REQUEST/DOMAIN_NAME`)
- These element paths are used in D&R rules and LCQL queries

**Common Errors:**
- **400 Bad Request**: Event type name format is invalid
- **404 Not Found**: Event type does not exist in the schema system - verify the exact name
- **403 Forbidden**: Insufficient API permissions to read schemas
- **500 Server Error**: Temporary API issue - retry after a short delay

### Step 4: Format the Response

Present the result to the user:
- Display the event type name clearly
- List all available fields (elements) in a readable format
- Explain that these field paths can be used in D&R rules and queries
- Consider grouping related fields or highlighting commonly used ones
- If there are many elements, consider summarizing or showing the most relevant ones first

## Example Usage

### Example 1: Getting DNS_REQUEST schema

User request: "Show me what fields are available in DNS_REQUEST events"

Steps:
1. Event type is 'DNS_REQUEST'
2. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_event_schema",
  parameters={
    "name": "DNS_REQUEST"
  }
)
```

Expected response:
```json
{
  "event_type": "DNS_REQUEST",
  "elements": [
    "event/DNS_REQUEST/DOMAIN_NAME",
    "event/DNS_REQUEST/DNS_TYPE",
    "event/DNS_REQUEST/RESPONSE_IP",
    "event/DNS_REQUEST/RESPONSE_VALUES",
    "event/PROCESS_ID",
    "event/TIMESTAMP"
  ]
}
```

Present to user: "The DNS_REQUEST event type has the following fields: DOMAIN_NAME, DNS_TYPE, RESPONSE_IP, RESPONSE_VALUES, PROCESS_ID, and TIMESTAMP. You can reference these in D&R rules like `event/DNS_REQUEST/DOMAIN_NAME`."

### Example 2: Understanding PROCESS_START for rule creation

User request: "I need to create a D&R rule for new processes - what fields can I use?"

Steps:
1. Determine event type is 'PROCESS_START'
2. Call API to get schema
3. Present fields relevant to process detection (FILE_PATH, COMMAND_LINE, PARENT_PROCESS_ID, etc.)

## Additional Notes

- Event type names are case-sensitive and typically use UPPERCASE_WITH_UNDERSCORES
- Element paths use the format `event/EVENT_TYPE/FIELD_NAME`
- Some fields are common across event types (like TIMESTAMP, PROCESS_ID)
- Platform-specific fields may only appear on certain OS types
- Use `get-event-types-with-schemas` to list all available event types first
- For multiple event types, consider using `get_event_schemas_batch` for better performance

## See Also

- **detection-engineering skill**: For end-to-end detection development workflow (understand → research → build → test → deploy). This function is used in **Phase 2.1 (Schema Research)** of that workflow.

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `/go-limacharlie/limacharlie/schemas.go`
For the MCP tool implementation, check: `/lc-mcp-server/internal/tools/schemas/schemas.go`
