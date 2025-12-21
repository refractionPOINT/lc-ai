
# Create Organization

Create a new LimaCharlie organization with specified configuration and optional Infrastructure-as-Code template.

## When to Use

Use this skill when the user needs to:
- Create a new LimaCharlie organization
- Set up multi-tenant deployments for customers
- Provision isolated environments for testing or development
- Create separate organizations for business units or teams
- Deploy pre-configured organizations using IaC templates
- Set up organization with specific data residency requirements

Common scenarios:
- MSP onboarding new customers
- Creating dev/staging/prod environments
- Setting up customer-specific tenants
- Provisioning demo or trial organizations
- Deploying standardized configurations via templates
- Implementing data sovereignty requirements

## What This Skill Does

This skill creates a new LimaCharlie organization with specified name and data residency location. It calls the LimaCharlie API at the user level (not organization level) to provision a new org. Optionally, an Infrastructure-as-Code YAML template can be provided to automatically configure the new organization with rules, outputs, and other settings.

## Required Information

Before calling this skill, gather:

**NOTE**: This is a **user-level operation** that does not require a specific organization ID.

**name**: Organization name (required)
  - Human-readable name for the organization
  - Used for identification in UI and billing
- **location**: Data residency location (required)
  - Valid values: "usa", "europe", "canada", "india", "uk"
  - Determines where data is stored (compliance/sovereignty)

Optional parameters:
- **template**: YAML Infrastructure-as-Code template (optional)
  - Automatically configures rules, outputs, secrets, etc.
  - Applied immediately after org creation
  - Format: YAML string with LimaCharlie IaC syntax

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Unique, descriptive organization name
2. Valid location matching data residency requirements
3. Optional: Prepared IaC template for configuration
4. User has permissions to create organizations

### Step 2: Call the Tool

Use the `lc_call_tool` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__lc_call_tool(
  tool_name="create_org",
  parameters={
    "name": "[org-name]",
    "location": "[location]",
    "template": "[yaml-template]"  // Optional
  }
)
```

**Tool Details:**
- Tool name: `create_org`
- Required parameters:
  - `name` (string): Organization name
  - `location` (string): Data residency location
- Optional parameters:
  - `template` (string): YAML IaC template

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "oid": "c7e8f940-1234-5678-abcd-1234567890ab",
  "name": "New Organization",
  "location": "usa"
}
```

**Success:**
- Response contains the new organization ID (oid)
- Organization is immediately created and active
- If template provided, it's applied automatically
- User has owner-level access to new organization
- Organization appears in user's org list

**Common Errors:**
- **400 Bad Request**: Invalid parameters (name missing, invalid location, malformed template)
- **403 Forbidden**: User lacks permission to create organizations
- **409 Conflict**: Organization name already exists (though usually allowed)
- **500 Server Error**: Org creation failed - contact support

### Step 4: Format the Response

Present the result to the user:
- Confirm successful creation with org name and ID
- Display the organization's data location
- Provide next steps (install sensors, configure rules)
- If template was used, confirm configuration applied
- Show how to access the new organization
- Note any initial setup recommendations

## Example Usage

### Example 1: Create a basic organization

User request: "Create a new organization called 'Acme Production' in the US"

Steps:
1. Prepare parameters
2. Call tool to create organization:
```
mcp__limacharlie__lc_call_tool(
  tool_name="create_org",
  parameters={
    "name": "Acme Production",
    "location": "usa"
  }
)
```

Expected response:
```json
{
  "oid": "c7e8f940-9876-5432-abcd-1234567890ab",
  "name": "Acme Production",
  "location": "usa"
}
```

Present to user:
```
Organization Created Successfully

Name: Acme Production
Organization ID: c7e8f940-9876-5432-abcd-1234567890ab
Location: USA (United States)
Status: Active

Your new organization is ready to use!

Next steps:
1. Generate installation keys for sensor deployment
2. Configure detection rules and outputs
3. Set up integrations and automations
4. Deploy sensors to endpoints

You have owner-level access to this organization.
```

### Example 2: Create organization with IaC template

User request: "Create a new customer org with our standard security configuration"

Steps:
1. Load standard IaC template
2. Create org with template:
```
mcp__limacharlie__lc_call_tool(
  tool_name="create_org",
  parameters={
    "name": "Customer XYZ Security",
    "location": "usa",
    "template": "---\nrules:\n  - name: suspicious-process\n    detect: {...}\n    respond: [...]\noutputs:\n  - name: siem-output\n    module: syslog\n    ..."
  }
)
```

Present to user:
```
Organization Created and Configured

Name: Customer XYZ Security
Organization ID: c7e8f940-5555-6666-7777-888899990000
Location: USA
Status: Active and configured

Applied standard template:
- Detection rules deployed (15 rules)
- SIEM output configured
- Response actions enabled
- Secrets configured
- Extensions subscribed

The organization is fully configured and ready for sensor deployment.

Installation keys have been created:
- Production: iid-prod-12345
- Development: iid-dev-67890
```

### Example 3: Create EU organization for compliance

User request: "We need a European organization for GDPR compliance"

Steps:
1. Specify Europe location for data residency
2. Create organization:
```
mcp__limacharlie__lc_call_tool(
  tool_name="create_org",
  parameters={
    "name": "Acme Europe GDPR",
    "location": "europe"
  }
)
```

Present to user:
```
European Organization Created

Name: Acme Europe GDPR
Organization ID: c7e8f940-aaaa-bbbb-cccc-ddddeeeeefff
Location: Europe (EU data residency)
Status: Active

Data Residency:
- All data stored in European data centers
- GDPR compliant data processing
- EU-based infrastructure

This organization meets European data sovereignty requirements.
All telemetry, detections, and configurations remain in the EU.

Next steps:
1. Deploy sensors to European endpoints
2. Configure EU-compliant data retention policies
3. Set up European SIEM integrations
```

## Additional Notes

- **This is a user-level operation that does not require a specific organization ID**
- Organization creation is a user-level operation (not org-scoped)
- Newly created orgs inherit user's access level (owner)
- Location determines data residency and cannot be changed later
- Choose location based on compliance requirements (GDPR, data sovereignty)
- IaC templates can dramatically speed up org provisioning
- Templates support rules, outputs, secrets, extensions, and more
- Organization names can be changed later through UI
- Multiple orgs with same name are allowed (use descriptive names)
- New orgs start with default/free plan (may need upgrade)
- Consider creating installation keys immediately after org creation
- For MSPs: Use templates to ensure consistent customer configurations

## Reference

For more details on using `lc_call_tool`, see [CALLING_API.md](../../../CALLING_API.md).

For the Go SDK implementation, check: `go-limacharlie/limacharlie/organization.go` (CreateOrganization function)
For the MCP tool implementation, check: `lc-mcp-server/internal/tools/admin/admin.go` (RegisterCreateOrg)
