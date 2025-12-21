
# Set Playbook

Creates or updates an automation playbook in the LimaCharlie Hive.

## When to Use

Use this skill when the user needs to:
- Create a new automation playbook
- Update an existing playbook workflow
- Configure automated incident response
- Set up threat hunting automation
- Define multi-step workflows

Common scenarios:
- "Create a playbook to auto-isolate critical threats"
- "Update the incident-response playbook"
- "Set up a playbook that scans suspicious files with YARA"

## What This Skill Does

Creates or updates an automation playbook in the LimaCharlie Hive system. The playbook is automatically enabled and executes when triggered.

## Recommended Workflow: AI-Assisted Generation

**For Python playbook scripts, use this workflow:**

1. **Gather Documentation** (if needed)
   Use `lookup-lc-doc` skill to search for playbook syntax and available actions.

2. **Generate Python Playbook Code** (optional)
   ```
   mcp__plugin_lc-essentials_limacharlie__generate_python_playbook(
     query="create a playbook that isolates sensors with critical detections and creates cases"
   )
   ```
   Returns Python script using LimaCharlie SDK.

3. **Deploy Playbook** (this API call)

## Required Information

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use `list_user_orgs` first.

- **oid**: Organization ID (UUID)
- **playbook_name**: Name for the playbook
- **playbook_data**: Playbook workflow definition object containing:
  - `steps`: Array of actions to execute
  - `trigger`: What triggers the playbook
  - `filter`: Optional conditional logic
  - `description`: Optional explanation

Optional:
- **tags**: Categorization tags
- **comment**: Description or notes
- **enabled**: Whether playbook is enabled (default: true)

## How to Use

### Step 1: Call the API

Use the `lc_call_tool` MCP tool:

```
mcp__limacharlie__lc_call_tool(
  tool_name="set_playbook",
  parameters={
    "oid": "[organization-id]",
    "playbook_name": "[playbook-name]",
    "playbook_data": {
      "steps": [...],
      "trigger": "detection",
      "filter": "...",
      "description": "..."
    }
  }
)
```

**API Details:**
- Tool: `set_playbook`
- Required parameters:
  - `oid`: Organization ID
  - `playbook_name`: Name for the playbook
  - `playbook_data`: Playbook workflow definition

### Step 2: Handle the Response

**Success:**
```json
{
  "guid": "unique-record-id",
  "name": "playbook-name"
}
```
Playbook is immediately active.

**Common Errors:**
- **400 Bad Request**: Invalid playbook structure
- **403 Forbidden**: Insufficient permissions
- **500 Server Error**: Backend issue

## Example Usage

### Create Playbook with AI Assistance

User request: "Create a playbook to automatically isolate sensors on critical detections"

**Step 1: Generate Python playbook** (optional - for complex automation)
```
mcp__plugin_lc-essentials_limacharlie__generate_python_playbook(
  query="isolate sensors on critical detections and create cases"
)
// Returns Python script with LimaCharlie SDK code
```

**Step 2: Deploy playbook workflow**
```
mcp__limacharlie__lc_call_tool(
  tool_name="set_playbook",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
    "playbook_name": "critical-auto-isolation",
    "playbook_data": {
      "steps": [
        {"action": "isolate_sensor"},
        {"action": "create_case", "params": {"priority": "high"}}
      ],
      "trigger": "detection",
      "filter": "cat == 'CRITICAL'",
      "description": "Auto-isolate critical threats"
    }
  }
)
```

Result: Playbook is active and will automatically isolate sensors on critical detections.

## Related Functions

- `generate_python_playbook` - AI-assisted Python playbook generation
- `list_playbooks` - List all playbooks
- `get_playbook` - Get specific playbook
- `delete_playbook` - Remove a playbook
- Use `lookup-lc-doc` skill for playbook syntax reference

## Additional Notes

- Creates if doesn't exist, updates if it does (upsert)
- Playbooks are enabled by default - be careful with disruptive actions
- Some actions (isolate, delete) are irreversible
- Test in non-production environment first
- Playbooks execute automatically when triggered

## Reference

For the API implementation, see [CALLING_API.md](../../../CALLING_API.md).

For playbook syntax and actions, use the `lookup-lc-doc` skill to search LimaCharlie documentation.
