
# Get Event Types With Schemas For Platform

Retrieve a list of event types that have schema definitions available for a specific platform (e.g., Windows, Linux, macOS).

## When to Use

Use this skill when the user needs to:
- Discover event types available on a specific platform
- Build detections for a particular operating system
- Understand platform-specific telemetry capabilities
- Filter event types by OS for focused analysis
- Compare telemetry across different platforms

Common scenarios:
- "What event types are available on Windows?"
- "Show me Linux-specific events"
- "What telemetry can I get from macOS sensors?"
- "Which events work on Chrome OS?"

## What This Skill Does

This skill retrieves the list of event type names that have schema definitions for a specific platform. It filters the complete event type list to show only those relevant to the specified operating system or platform, helping users focus on platform-appropriate detections and queries.

## Required Information

Before calling this skill, gather:

- **platform**: Platform name (e.g., 'windows', 'linux', 'macos', 'chrome')

Platform names should match LimaCharlie's platform naming (typically lowercase). Use `get_platform_names` to get the exact list of valid platform names.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid platform name (get from `get_platform_names` if unsure)
2. Platform name is lowercase and exactly matches LimaCharlie's naming

### Step 2: Call the API

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_event_types_with_schemas_for_platform",
  parameters={
    "platform": "[platform-name]"
  }
)
```

**API Details:**
- Tool: `get_event_types_with_schemas_for_platform`
- Required parameters:
  - `platform`: Platform name (e.g., "windows", "linux", "macos")

### Step 3: Handle the Response

The API returns a response with:
```json
{
  "event_types": [
    "DNS_REQUEST",
    "PROCESS_START",
    "NETWORK_CONNECTIONS",
    "REGISTRY_CREATE",
    ...
  ]
}
```

**Success (200-299):**
- Response contains `event_types` array filtered by platform
- Windows includes registry events not available on Linux/macOS
- Linux includes package manager events not on Windows
- macOS has its own platform-specific events
- Common events (DNS, HTTP, network) appear across platforms

**Common Errors:**
- **400 Bad Request**: Invalid platform name format
- **404 Not Found**: Platform name doesn't exist - use `get_platform_names` to get valid names
- **403 Forbidden**: Insufficient API permissions to read schemas
- **500 Server Error**: Temporary API issue - retry after a short delay

### Step 4: Format the Response

Present the result to the user:
- List event types grouped by category (network, process, file, etc.)
- Include count of event types for this platform
- Note any platform-specific events (e.g., registry events for Windows)
- Compare with other platforms if relevant
- Highlight commonly used events for detection on this platform

## Example Usage

### Example 1: Getting Windows event types

User request: "What event types are available on Windows?"

Steps:
1. Platform is 'windows'
2. Call API:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_event_types_with_schemas_for_platform",
  parameters={
    "platform": "windows"
  }
)
```

Expected response:
```json
{
  "event_types": [
    "DNS_REQUEST",
    "PROCESS_START",
    "NETWORK_CONNECTIONS",
    "REGISTRY_CREATE",
    "REGISTRY_DELETE",
    "WMI_ACTIVITY",
    "SERVICE_CHANGE",
    ...
  ]
}
```

Present to user: "Windows sensors support X event types including Windows-specific events like registry operations (REGISTRY_CREATE, REGISTRY_DELETE), WMI activity, and service changes, plus standard cross-platform events."

### Example 2: Comparing Linux event types

User request: "What telemetry is different between Windows and Linux?"

Steps:
1. Get event types for 'windows'
2. Get event types for 'linux'
3. Compare and highlight differences
4. Note Linux-specific events (package operations, systemd events)
5. Note Windows-specific events (registry, WMI)

## Additional Notes

- Platform names are typically lowercase (windows, linux, macos, chrome)
- Some event types are cross-platform (DNS_REQUEST, HTTP_REQUEST, NETWORK_CONNECTIONS)
- Platform-specific events include:
  - Windows: REGISTRY_*, WMI_*, SERVICE_*
  - Linux: PACKAGE_*, SYSTEMD_*
  - macOS: AUTHORIZATION_*, KEYCHAIN_*
- Chrome OS has its own set of browser-focused events
- Use `get_platform_names` first if unsure of exact platform name
- Not all platforms have equal telemetry breadth
- The organization must have sensors on the platform for the events to actually generate

## See Also

- **detection-engineering skill**: For end-to-end detection development workflow (understand → research → build → test → deploy). This function is used in **Phase 2.1 (Schema Research)** of that workflow.

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `/go-limacharlie/limacharlie/schemas.go`
For the MCP tool implementation, check: `/lc-mcp-server/internal/tools/schemas/schemas.go`
