
# Generate Detection Summary

Generate human-readable summaries of detection data from raw event JSON using AI-powered analysis.

## When to Use

Use this skill when the user needs to:
- Create human-readable summaries of complex detection events
- Translate technical telemetry data into plain language
- Generate executive summaries for security incidents
- Explain detections to non-technical stakeholders
- Create incident reports from detection data
- Analyze and interpret detection event data
- Document security findings in readable format
- Triage detections with AI-assisted context

Common scenarios:
- "Summarize this detection event for the security team"
- "Explain what this detection means in simple terms"
- "Create an incident summary from this detection data"
- "Generate a readable report from these detection events"
- "Help me understand what this alert is telling us"

## What This Skill Does

This skill uses AI (Gemini) to generate human-readable summaries of detection data. It takes raw JSON event data from detections and produces a markdown-formatted summary that explains what happened, why it's significant, and what actions might be needed. Unlike validation-based generators, this tool makes a single AI call without validation, focusing on interpretation and explanation rather than syntax validation.

## Required Information

Before calling this skill, gather:

**Note**: This skill does NOT require an Organization ID (OID). It operates purely on the detection data provided.

- **query**: JSON string containing the detection data to summarize

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Detection data in JSON format (from LimaCharlie detections API or web interface)
2. Complete event data including telemetry, metadata, and detection context
3. Understanding that more complete data produces better summaries

### Step 2: Call the Tool

Use the `generate_detection_summary` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__generate_detection_summary(
  query='{"detect": {"event": "NEW_PROCESS", "routing": {"hostname": "LAPTOP-01", ...}}, "cat": "suspicious_powershell", ...}'
)
```

**Tool Details:**
- Tool: `mcp__limacharlie__generate_detection_summary`
- Parameters:
  - `query` (string, required): JSON string of detection data to summarize

**How it works:**
- Sends the detection JSON to Gemini AI with detection summary prompt template
- AI analyzes the event data, context, and detection logic
- Generates a structured markdown summary
- Returns human-readable explanation (no validation loop)
- Single-pass generation

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "summary": "# Detection Summary: Suspicious PowerShell Execution\n\n## Overview\nA suspicious PowerShell command was detected on LAPTOP-01 at 2024-01-20 14:35:22 UTC.\n\n## Details\n- **Host**: LAPTOP-01\n- **User**: john.doe\n- **Process**: powershell.exe\n- **Command Line**: `powershell.exe -enc SGVsbG8gV29ybGQ=`\n\n## Analysis\nThis detection triggered because PowerShell was executed with the `-enc` parameter...\n\n## Recommended Actions\n1. Investigate the user's recent activity\n2. Check for other suspicious PowerShell executions on this host\n..."
}
```

**Success:**
- `summary`: Markdown-formatted human-readable summary of the detection

**Possible Issues:**
- Incomplete or malformed JSON may produce less accurate summaries
- Very complex detections may require additional context for full understanding
- AI interpretation may occasionally miss nuances - always verify critical details

### Step 4: Format the Response

Present the result to the user:
- Display the markdown summary (it's already formatted)
- Mention that this is an AI-generated interpretation
- Suggest using it as a starting point for investigation
- Remind them to verify critical details from the raw event data
- Highlight recommended actions if included in the summary

## Example Usage

### Example 1: Summarize PowerShell Detection

User request: "Summarize this detection event for the security team"

Steps:
1. Get detection JSON data from LimaCharlie
2. Call tool:
```
mcp__limacharlie__generate_detection_summary(
  query='{"detect": {"event": "NEW_PROCESS", "routing": {"hostname": "LAPTOP-01", "event_time": 1705759522000, "sid": "abc123"}}, "cat": "suspicious_powershell", "detect": {"op": "contains", "path": "event/COMMAND_LINE", "value": "-enc"}}'
)
```
3. Present the generated summary

### Example 2: Network Connection Summary

User request: "Explain what this network connection detection means"

Steps:
1. Get detection JSON for network event
2. Call tool:
```
mcp__limacharlie__generate_detection_summary(
  query='{"detect": {"event": "NETWORK_CONNECTIONS", "routing": {"dst_ip": "192.0.2.100", "dst_port": 4444}}, "cat": "suspicious_network", ...}'
)
```

### Example 3: Multiple Event Summary

User request: "Create an incident summary from these related detection events"

Steps:
1. Combine multiple detection events into a single JSON structure
2. Call tool:
```
mcp__limacharlie__generate_detection_summary(
  query='{"events": [{"detect": {...}, "cat": "lateral_movement"}, {"detect": {...}, "cat": "credential_access"}], "timeline": "..."}'
)
```

## Additional Notes

- **AI-Powered**: Uses Gemini AI with detection summary-specific prompt templates
- **No Validation**: Single-pass generation focused on interpretation, not validation
- **No OID Required**: Operates only on the detection data provided
- **Markdown Output**: Returns formatted markdown for easy reading and sharing
- **Context-Aware**: AI considers event type, detection logic, and metadata
- **Interpretation**: Provides analysis of why the detection is significant
- **Actionable**: Often includes recommended investigation or response steps
- **Flexible Input**: Can handle various detection event structures
- **Aggregation**: Can summarize single events or multiple related events
- **Executive Summary**: Good for communicating to non-technical stakeholders
- **Triage Assistance**: Helps analysts quickly understand detection significance
- **Use Cases**:
  - Incident response documentation
  - Security reports and briefings
  - Triage and prioritization
  - Training and education
  - Communication with management
  - SOC ticket creation
  - Post-incident analysis
- **Limitations**: AI interpretation may not catch all nuances
- **Verification**: Always verify critical details from raw event data
- **Enrichment**: More complete input data produces better summaries
- **Custom Context**: Can include additional context in the JSON for better summaries
- **Privacy**: Ensure sensitive data is redacted if sharing summaries externally
- **Prompt Template**: Uses `prompts/gen_det_summary.txt` from the MCP server

## Reference

For more details on the MCP tool implementation, check: `../lc-mcp-server/internal/tools/ai/ai.go` (generate_detection_summary function)

For detection event structure and format, see LimaCharlie's documentation on detections and telemetry.
