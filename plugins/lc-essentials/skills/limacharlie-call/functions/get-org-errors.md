
# Get Organization Errors

Retrieve error logs and issues affecting a LimaCharlie organization for troubleshooting and monitoring.

## When to Use

Use this skill when the user needs to:
- Troubleshoot organization configuration issues
- Debug integration or service failures
- Monitor organization health and errors
- Investigate service disruptions
- Review warnings and error messages
- Identify misconfigured components

Common scenarios:
- Troubleshooting output delivery failures
- Debugging D&R rule errors
- Investigating integration issues
- Monitoring for configuration problems
- Responding to service alerts
- Conducting health checks

## What This Skill Does

This skill retrieves error logs for a LimaCharlie organization. It calls the LimaCharlie API to get recent errors, warnings, and issues affecting the organization. This includes configuration errors, integration failures, service issues, and other problems that need attention.

## Required Information

Before calling this skill, gather:

**IMPORTANT**: The Organization ID (OID) is a UUID (like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name. If you don't have the OID, use the `list_user_orgs` skill first to get the OID from the organization name.
- **oid**: Organization ID (required)

No additional parameters are required.

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Valid organization ID (oid)

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="get_org_errors",
  parameters={
    "oid": "[organization-id]"
  }
)
```

**Tool Details:**
- Tool name: `get_org_errors`
- Required parameters:
  - `oid` (string): Organization ID

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "errors": [
    {
      "component": "output:syslog-prod",
      "error": "Connection refused to host 10.0.0.5:514",
      "timestamp": 1640995200,
      "severity": "error"
    },
    {
      "component": "rule:suspicious-process",
      "error": "Invalid selector syntax in detection rule",
      "timestamp": 1640995100,
      "severity": "warning"
    }
  ]
}
```

**Success:**
- Response contains array of error objects
- Each error includes component name, error message, timestamp
- Severity levels may indicate criticality
- Empty errors array means no current issues

**Common Errors:**
- **400 Bad Request**: Invalid organization ID format
- **403 Forbidden**: Insufficient permissions to view org errors
- **404 Not Found**: Organization does not exist
- **500 Server Error**: API service issue - retry or contact support

### Step 4: Format the Response

Present the result to the user:
- Group errors by component or severity
- Show timestamp for each error (most recent first)
- Explain error messages in user-friendly terms
- Suggest remediation steps for each error
- Highlight critical errors requiring immediate attention
- Indicate if no errors are present (healthy state)

## Example Usage

### Example 1: Check for current organization errors

User request: "Are there any errors in my organization?"

Steps:
1. Extract organization ID from context
2. Call tool to get error logs:
```
mcp__limacharlie__lc_call_tool(
  tool_name="get_org_errors",
  parameters={
    "oid": "c7e8f940-1234-5678-abcd-1234567890ab"
  }
)
```

Expected response:
```json
{
  "errors": [
    {
      "component": "output:splunk-integration",
      "error": "Authentication failed: Invalid API token",
      "timestamp": 1672531200,
      "severity": "error"
    }
  ]
}
```

Present to user:
```
Organization Health Check

1 Error Found

Error: Output Delivery Failure
Component: output:splunk-integration
Message: Authentication failed: Invalid API token
Time: January 1, 2023 12:00 AM
Severity: Error

Impact:
- Events are not being forwarded to Splunk
- Data may be queued or dropped

Recommended Action:
1. Verify the API token in the Splunk output configuration
2. Check if the token has expired or been revoked
3. Update the output configuration with a valid token
4. Test the connection after updating

Use dismiss-org-error skill to clear this error after fixing.
```

### Example 2: No errors found (healthy state)

User request: "Check for any issues"

Expected response with no errors:
```json
{
  "errors": []
}
```

Present to user:
```
Organization Health Check

No Errors Detected

All systems are operating normally:
- No configuration errors
- No integration failures
- No service disruptions

Your organization is healthy and all components are functioning properly.
```

### Example 3: Multiple errors requiring attention

User request: "Show me all current errors"

Expected response with multiple errors:
```json
{
  "errors": [
    {
      "component": "output:syslog-prod",
      "error": "Connection timeout to 10.0.0.5:514",
      "timestamp": 1672531300
    },
    {
      "component": "rule:malware-detection",
      "error": "YARA rule compilation failed",
      "timestamp": 1672531250
    },
    {
      "component": "extension:threat-intel",
      "error": "API rate limit exceeded",
      "timestamp": 1672531200
    }
  ]
}
```

Present to user:
```
Organization Error Report

3 Errors Requiring Attention

1. Output Connection Issue (5 minutes ago)
   Component: output:syslog-prod
   Issue: Connection timeout to 10.0.0.5:514
   Action: Verify syslog server is running and accessible

2. Rule Configuration Error (5 minutes ago)
   Component: rule:malware-detection
   Issue: YARA rule compilation failed
   Action: Review and fix YARA rule syntax

3. Extension Rate Limit (5 minutes ago)
   Component: extension:threat-intel
   Issue: API rate limit exceeded
   Action: Check threat intel query volume or upgrade plan

Priority: Address these issues to restore full functionality
```

## Additional Notes

- Errors persist until resolved and dismissed
- Some errors auto-dismiss when underlying issue is fixed
- Use dismiss-org-error skill to manually clear resolved errors
- Regular error monitoring helps maintain org health
- Critical errors may affect data collection or detection
- Error logs help troubleshoot integration issues
- Component names identify the source of each error
- Timestamps show when errors first occurred
- Some errors may indicate needed configuration updates
- Contact support for persistent or unclear errors

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `go-limacharlie/limacharlie/organization_ext.go` (GetOrgErrors function)
For the MCP tool implementation, check: `lc-mcp-server/internal/tools/admin/admin.go` (RegisterGetOrgErrors)
