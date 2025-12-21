
# Get Event by Atom

Retrieve a specific event by its atom identifier from LimaCharlie Insight.

## When to Use

Use this skill when the user needs to:
- Jump directly to a known event during investigation
- Reference an event from a detection, timeline, or other source
- Pivot from atom references found in parent/child process relationships
- Retrieve full event details when you have the atom identifier
- Validate event context for timeline building

Common scenarios:
- "Get the event with atom abc123 from sensor xyz-456"
- "Show me the details of this event" (when atom is provided)
- "Retrieve the triggering event from this detection"
- "Get the parent process event" (when you have the parent atom)

## What This Skill Does

This skill retrieves a single event from LimaCharlie Insight using its unique atom identifier. Every event in LimaCharlie has an atom that uniquely identifies it, making this function ideal for direct event lookup without needing time-based queries.

## Required Information

Before calling this skill, gather:

**Important**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.

- **oid**: Organization ID (UUID format, required)
- **sid**: Sensor ID (UUID format) where the event originated (required)
- **atom**: The atom identifier of the event to retrieve (required)

**Where to find atoms:**
- In event data: `routing.this` field contains the event's own atom
- In process events: `routing.parent` contains the parent process atom
- In detection data: The triggering event includes atom references
- In timeline records: Events are referenced by their atoms

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Valid sensor ID (sid) - the sensor where the event originated
3. Valid atom identifier - typically a 32+ character string

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_event_by_atom",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "xyz-sensor-id",
    "atom": "1a2b3c4d5e6f7g8h9i0j..."
  }
)
```

**Tool Details:**
- Tool name: `get_event_by_atom`
- Parameters:
  - `oid`: Organization ID (required)
  - `sid`: Sensor ID (required)
  - `atom`: Event atom identifier (required)

### Step 3: Handle the Response

The tool returns the event:
```json
{
  "event": {
    "TIMESTAMP": 1705761234567,
    "EVENT_TYPE": "NEW_PROCESS",
    "FILE_PATH": "C:\\Windows\\System32\\cmd.exe",
    "COMMAND_LINE": "cmd.exe /c whoami",
    "PARENT_PROCESS_ID": 1234,
    "PROCESS_ID": 5678,
    "USER": "DOMAIN\\administrator"
  },
  "routing": {
    "this": "1a2b3c4d5e6f7g8h9i0j...",
    "parent": "parent-atom-id...",
    "sid": "xyz-sensor-id",
    "hostname": "SERVER01",
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
}
```

**Success:**
- Returns the full event with all fields
- Includes `routing` metadata with atom references
- Use `routing.parent` to navigate to parent event
- Use `get_atom_children` to find child events

**Common Errors:**
- **404 Not Found**: Event or sensor does not exist, atom is invalid
- **403 Forbidden**: Insufficient permissions or data retention expired
- **400 Bad Request**: Invalid parameter format

### Step 4: Format the Response

Present the result to the user:
- Display event type and timestamp
- Show key fields relevant to event type
- Highlight command line, file paths, network info
- Include routing info (hostname, sensor)
- Provide atom references for navigation

**Example formatted output:**
```
Event Details (atom: 1a2b3c4d...)
Sensor: SERVER01 (xyz-sensor-id)
Time: 2024-01-20 14:22:15 UTC

Event Type: NEW_PROCESS
  File: C:\Windows\System32\cmd.exe
  Command: cmd.exe /c whoami
  User: DOMAIN\administrator
  PID: 5678
  Parent PID: 1234

Navigation:
  Parent atom: parent-atom-id... (use get_event_by_atom)
  Children: use get_atom_children to find spawned processes
```

## Example Usage

### Example 1: Direct event lookup

User request: "Get the event with atom abc123xyz from sensor srv-456"

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_event_by_atom",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "srv-456",
    "atom": "abc123xyz..."
  }
)
```

### Example 2: Navigate to parent process

User has an event and wants to see its parent process:

1. Extract parent atom from current event's `routing.parent`
2. Call get_event_by_atom with the parent atom:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_event_by_atom",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "srv-456",
    "atom": "[parent-atom-from-routing]"
  }
)
```

### Example 3: Retrieve event from detection

User has a detection and wants to see the triggering event:

1. Get detection details (provides event atom and sid)
2. Call get_event_by_atom with the event atom

## Additional Notes

- **Atoms are unique**: Each event has a globally unique atom identifier
- **Sensor ID required**: You must know which sensor the event came from
- **Navigation**: Use `routing.parent` to traverse up the process tree
- **Children**: Use `get_atom_children` to get all events spawned from this atom
- **Retention**: Events may not be available if data retention has expired
- **Performance**: Direct atom lookup is faster than time-based queries
- **Investigation workflow**: Combine with `get_atom_children` for full process tree analysis

## Related Functions

- `get_atom_children` - Get all children/descendants of this event
- `get_historic_events` - Query events by time range (when atom unknown)
- `get_historic_detections` - Query detections that may reference events by atom

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/historical/historical.go`
