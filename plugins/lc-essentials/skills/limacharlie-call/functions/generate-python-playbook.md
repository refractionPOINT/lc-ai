
# Generate Python Playbook

Generate Python playbook scripts for LimaCharlie automation from natural language descriptions using AI-powered assistance.

## When to Use

Use this skill when the user needs to:
- Create Python automation scripts for LimaCharlie tasks
- Generate playbooks for incident response workflows
- Automate security operations using the LimaCharlie Python SDK
- Build custom integrations with LimaCharlie
- Learn LimaCharlie SDK usage through examples
- Create scripts for bulk operations or batch tasks
- Develop automated response workflows
- Implement custom security orchestration

Common scenarios:
- "Create a playbook to isolate all sensors with a specific tag"
- "Generate Python script to export detections from the last 24 hours"
- "Build a playbook that queries sensors and generates a report"
- "Create automation to update D&R rules across multiple organizations"
- "Generate script to bulk tag sensors based on criteria"

## What This Skill Does

This skill uses AI (Gemini) to generate Python playbook scripts from natural language descriptions. The generated scripts use the LimaCharlie Python SDK (limacharlie-io library) to interact with the LimaCharlie API. Unlike validation-based generators, this tool makes a single AI call without validation since playbook code cannot be automatically validated without execution. The skill returns Python code ready to run or adapt.

## Required Information

Before calling this skill, gather:

**Note**: This skill does NOT require an Organization ID (OID). The generated playbook will typically include code to retrieve the OID from credentials or accept it as a parameter.

- **query**: Natural language description of the automation or task to perform

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Clear natural language description of the automation task
2. Understanding of what the playbook should accomplish
3. Knowledge of LimaCharlie concepts relevant to the task (sensors, rules, outputs, etc.)
4. API credentials available for the generated playbook to use

### Step 2: Call the Tool

Use the `generate_python_playbook` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__generate_python_playbook(
  query="create a playbook to list all sensors and export their details to a CSV file"
)
```

**Tool Details:**
- Tool: `mcp__limacharlie__generate_python_playbook`
- Parameters:
  - `query` (string, required): Natural language description of the automation task

**How it works:**
- Sends the natural language query to Gemini AI with Python playbook prompt template
- Generates Python code using the LimaCharlie SDK
- Removes markdown code fences if present
- Returns Python code as a string (no validation - code is not executed)
- Single-pass generation

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "playbook": "import limacharlie\nimport csv\nimport os\n\n# Initialize LimaCharlie SDK\napi_key = os.environ.get('LC_API_KEY')\norg_id = os.environ.get('LC_OID')\nlc = limacharlie.Manager(api_key=api_key, oid=org_id)\n\n# Get all sensors\nsensors = lc.sensors()\n\n# Export to CSV\nwith open('sensors.csv', 'w', newline='') as csvfile:\n    writer = csv.DictWriter(csvfile, fieldnames=['sid', 'hostname', 'platform', 'last_seen'])\n    writer.writeheader()\n    for sensor in sensors:\n        writer.writerow({\n            'sid': sensor.sid,\n            'hostname': sensor.hostname,\n            'platform': sensor.platform,\n            'last_seen': sensor.last_seen\n        })\n\nprint('Sensors exported to sensors.csv')"
}
```

**Success:**
- `playbook`: Python code string ready to save and execute

**Possible Issues:**
- Generated code may need customization for your specific environment
- Code is not validated or executed - syntax errors are possible
- API credentials and dependencies must be configured before running
- Complex automation may require manual refinement

### Step 4: Format the Response

Present the result to the user:
- Show the generated Python code in a code block
- Explain what the playbook does
- Mention required dependencies (limacharlie-io package)
- List any environment variables or configuration needed
- Suggest testing in a safe environment first
- Provide instructions for saving and running the script

## Example Usage

### Example 1: Export Sensors to CSV

User request: "Create a playbook to list all sensors and export their details to CSV"

Steps:
1. Call tool:
```
mcp__limacharlie__generate_python_playbook(
  query="create a playbook to list all sensors and export their details to a CSV file"
)
```
2. Present the generated playbook code

### Example 2: Bulk Sensor Isolation

User request: "Generate a playbook to isolate all sensors with tag 'compromised'"

Steps:
1. Call tool:
```
mcp__limacharlie__generate_python_playbook(
  query="isolate all sensors that have the tag 'compromised'"
)
```

### Example 3: Detection Export

User request: "Create a playbook that exports all detections from the last 24 hours to a JSON file"

Steps:
1. Call tool:
```
mcp__limacharlie__generate_python_playbook(
  query="export all detections from the last 24 hours to a JSON file"
)
```

## Additional Notes

- **AI-Powered**: Uses Gemini AI with Python playbook-specific prompt templates
- **No Validation**: Code is not validated or executed during generation
- **No OID Required**: Generated code typically handles OID via credentials or parameters
- **SDK-Based**: Generated code uses the official limacharlie-io Python library
- **Dependencies**: Requires `limacharlie` package: `pip install limacharlie`
- **Credentials**: Playbooks typically use environment variables or config files for API keys
- **Error Handling**: Generated code may include basic error handling
- **Comments**: Code includes comments explaining key sections
- **Customization**: Generated code is a starting point - customize for your needs
- **Testing**: Always test playbooks in a safe environment before production use
- **Best Practices**: Review and understand the code before running
- **API Limits**: Be aware of rate limits when performing bulk operations
- **Permissions**: Ensure API credentials have appropriate permissions for the task
- **Organization Context**: Multi-org playbooks should handle organization selection
- **Use Cases**:
  - Bulk sensor operations (tagging, isolation, task execution)
  - Detection and alert exports
  - Rule management automation
  - Report generation
  - Integration with external systems
  - Incident response workflows
  - Compliance reporting
- **Security**: Store API credentials securely (environment variables, secrets manager)
- **Logging**: Consider adding logging for audit trails
- **Idempotency**: Design playbooks to be safely re-runnable
- **Prompt Template**: Uses `prompts/gen_playbook.txt` from the MCP server

## Reference

For more details on the MCP tool implementation, check: `../lc-mcp-server/internal/tools/ai/ai.go` (generate_python_playbook function)

For LimaCharlie Python SDK documentation, see: https://doc.limacharlie.io/docs/sdk/python
