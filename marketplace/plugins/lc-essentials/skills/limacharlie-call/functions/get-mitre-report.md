
# Get MITRE ATT&CK Coverage Report

Retrieve the MITRE ATT&CK coverage report showing which tactics and techniques are covered by detection rules.

## When to Use

Use this skill when the user needs to:
- View MITRE ATT&CK detection coverage
- Assess security detection posture
- Identify detection gaps in threat coverage
- Report on detection rule coverage
- Analyze coverage by tactics and techniques
- Demonstrate security framework compliance

Common scenarios:
- Coverage assessment: "Show me my MITRE ATT&CK coverage"
- Gap analysis: "What MITRE techniques am I not detecting?"
- Reporting: "Generate a MITRE coverage report for the security team"
- Audit: "What's our detection coverage percentage?"

## What This Skill Does

This skill retrieves a comprehensive MITRE ATT&CK coverage report from the organization. The report shows which MITRE ATT&CK techniques and tactics are covered by your detection rules (D&R rules, YARA rules, etc.). It provides coverage percentages and lists which rules cover each technique, helping identify detection gaps.

## Required Information

Before calling this skill, gather:

**WARNING**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required for all API calls)

No additional parameters are required.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_mitre_report",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**Tool Details:**
- Tool name: `get_mitre_report`
- Required parameters:
  - `oid`: Organization ID (UUID)

### Step 3: Handle the Response

The tool returns data directly:
```json
{
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "coverage_percentage": 45.5,
  "techniques": [
    {
      "technique_id": "T1003",
      "technique_name": "OS Credential Dumping",
      "tactic": "Credential Access",
      "covered": true,
      "rules": ["credential_access_detection", "lsass_access"]
    },
    {
      "technique_id": "T1059",
      "technique_name": "Command and Scripting Interpreter",
      "tactic": "Execution",
      "covered": true,
      "rules": ["suspicious_powershell", "cmd_execution"]
    },
    {
      "technique_id": "T1055",
      "technique_name": "Process Injection",
      "tactic": "Defense Evasion",
      "covered": false,
      "rules": []
    }
  ],
  "tactics": {
    "Credential Access": {
      "covered_techniques": 5,
      "total_techniques": 10,
      "coverage_percentage": 50.0
    },
    "Execution": {
      "covered_techniques": 8,
      "total_techniques": 12,
      "coverage_percentage": 66.7
    },
    "Defense Evasion": {
      "covered_techniques": 3,
      "total_techniques": 20,
      "coverage_percentage": 15.0
    }
  },
  "last_updated": 1705000000
}
```

**Success:**
- The response contains comprehensive coverage data:
  - `oid`: Organization ID
  - `coverage_percentage`: Overall coverage percentage
  - `techniques`: Array of MITRE techniques with coverage status
  - `tactics`: Map of tactics with coverage statistics
  - `last_updated`: Unix timestamp of report generation
- Display overall coverage percentage prominently
- Show coverage breakdown by tactic
- Highlight gaps (uncovered techniques)
- List which rules cover each technique

**Common Errors:**
- **400 Bad Request**: Invalid organization ID format
- **403 Forbidden**: Insufficient permissions to view MITRE report
- **404 Not Found**: Organization ID does not exist
- **500 Server Error**: API service issue - retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Show overall coverage percentage (e.g., "45.5% MITRE ATT&CK coverage")
- Break down coverage by tactic (e.g., "Credential Access: 50%, Execution: 66.7%")
- Highlight low-coverage tactics that need attention
- List uncovered techniques as gaps to address
- Show which rules provide coverage for covered techniques
- Suggest creating detection rules for high-priority gaps
- Provide context on what good coverage looks like (typically 40-60% is reasonable)

## Example Usage

### Example 1: View MITRE coverage report

User request: "Show me my MITRE ATT&CK coverage"

Steps:
1. Get organization ID from context
2. Call tool:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_mitre_report",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "coverage_percentage": 48.2,
  "techniques": [...],
  "tactics": {
    "Initial Access": {"covered_techniques": 4, "total_techniques": 9, "coverage_percentage": 44.4},
    "Execution": {"covered_techniques": 7, "total_techniques": 12, "coverage_percentage": 58.3},
    "Persistence": {"covered_techniques": 3, "total_techniques": 19, "coverage_percentage": 15.8},
    "Credential Access": {"covered_techniques": 6, "total_techniques": 10, "coverage_percentage": 60.0}
  }
}
```

User message: "Your organization has 48.2% MITRE ATT&CK coverage.

Coverage by Tactic:
- Credential Access: 60.0% (6/10 techniques)
- Execution: 58.3% (7/12 techniques)
- Initial Access: 44.4% (4/9 techniques)
- Persistence: 15.8% (3/19 techniques) - LOW

Priority gaps to address:
- Persistence tactic needs more detection rules
- Focus on high-value techniques like lateral movement and privilege escalation"

### Example 2: Identify detection gaps

User request: "What MITRE techniques am I not detecting?"

Steps:
1. Call tool to get MITRE report
2. Filter techniques where covered=false
3. List uncovered techniques with their tactics
4. Prioritize by common attack techniques

User message: "You have detection gaps for these MITRE techniques:
- T1055 (Process Injection) - Defense Evasion
- T1021 (Remote Services) - Lateral Movement
- T1548 (Abuse Elevation Control) - Privilege Escalation

Consider creating detection rules for these high-priority techniques."

## Additional Notes

- Coverage is calculated based on D&R rules, YARA rules, and other detection mechanisms
- MITRE ATT&CK techniques are mapped through rule metadata or tags
- Coverage percentage varies by organization size and security maturity
- Typical coverage ranges:
  - 20-30%: Basic detection coverage
  - 40-50%: Good detection coverage
  - 60%+: Excellent detection coverage
  - 100% coverage is neither practical nor necessary
- Focus on covering high-priority techniques relevant to your threat model
- Some techniques are difficult or impossible to detect reliably
- Coverage report is generated based on current detection rules
- Adding or modifying rules updates the coverage dynamically
- The report includes all rule types: general, managed, YARA, etc.
- Tactics are MITRE ATT&CK tactics (Initial Access, Execution, Persistence, etc.)
- Techniques are specific attack methods within each tactic
- Use this report to:
  - Justify security investments
  - Prioritize detection engineering efforts
  - Demonstrate compliance with frameworks
  - Track detection improvement over time
  - Identify blind spots in threat coverage

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `../go-limacharlie/limacharlie/organization_ext.go`
For the MCP tool implementation, check: `../lc-mcp-server/internal/tools/admin/admin.go`
For MITRE ATT&CK framework, see: https://attack.mitre.org/
