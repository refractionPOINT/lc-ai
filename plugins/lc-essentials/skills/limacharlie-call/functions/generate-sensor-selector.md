
# Generate Sensor Selector Expression

Generate sensor selector expressions from natural language descriptions using AI-powered assistance.

## When to Use

Use this skill when the user needs to:
- Create sensor selector expressions for D&R rule targeting
- Generate selector syntax from natural language descriptions
- Target specific sensors or sensor groups for rules
- Learn sensor selector syntax through examples
- Filter sensors by platform, tags, or other attributes
- Build complex selector expressions with multiple conditions
- Define sensor scopes for installations, rules, or policies

Common scenarios:
- "Create selector for all Windows servers"
- "Generate selector for production Linux systems"
- "Target sensors with tag 'database' on platform Windows"
- "Select all macOS endpoints except those tagged 'test'"
- "Create selector for sensors in specific geographic region"

## What This Skill Does

This skill uses AI (Gemini) to generate sensor selector expressions from natural language descriptions. Unlike the detection and response generators, this tool makes a single AI call without iterative validation since selectors don't have organization-specific schemas to validate against. The skill returns both the selector expression and an explanation of how it works.

## Required Information

Before calling this skill, gather:

**Note**: This skill does NOT require an Organization ID (OID). Sensor selectors use standard syntax that applies across all organizations.

- **query**: Natural language description of which sensors to select

## How to Use

### Step 1: Validate Parameters

Ensure you have:
1. Clear natural language description of sensor selection criteria
2. Understanding of available selector attributes (platform, tag, hostname, etc.)
3. Knowledge of your organization's sensor tagging strategy (if using tags)

### Step 2: Call the Tool

Use the `generate_sensor_selector` MCP tool from the `limacharlie` server:

```
mcp__limacharlie__generate_sensor_selector(
  query="all Windows servers in production"
)
```

**Tool Details:**
- Tool: `mcp__limacharlie__generate_sensor_selector`
- Parameters:
  - `query` (string, required): Natural language description of sensor selection criteria

**How it works:**
- Sends the natural language query to Gemini AI with sensor selector prompt template
- Generates selector expression using standard syntax
- Returns the selector and an explanation (no validation loop)
- Single-pass generation since selectors don't require organization-specific validation

### Step 3: Handle the Response

The tool returns a response with:
```json
{
  "selector": "plat is windows and tag is production",
  "explanation": "This selector targets all sensors running the Windows platform that have been tagged with 'production'. It uses the 'and' operator to ensure both conditions must be true for a sensor to match."
}
```

**Success:**
- `selector`: The generated selector expression ready to use
- `explanation`: Human-readable explanation of what the selector matches

**Possible Issues:**
- Complex or ambiguous descriptions may produce unexpected selectors - review the explanation
- Tag-based selectors require that sensors actually have those tags configured
- Platform names must match LimaCharlie conventions (windows, linux, macos, chrome)

### Step 4: Format the Response

Present the result to the user:
- Show the generated selector expression
- Display the explanation to help the user understand the logic
- Mention where to use the selector (D&R rules, installation keys, etc.)
- Suggest verifying that sensors have the necessary tags if using tag-based selectors
- Remind them to test the selector to ensure it matches the intended sensors

## Example Usage

### Example 1: Windows Production Servers

User request: "Create selector for all Windows servers in production"

Steps:
1. Call tool:
```
mcp__limacharlie__generate_sensor_selector(
  query="all Windows servers in production"
)
```
2. Present the generated selector and explanation

Expected response:
```json
{
  "selector": "plat is windows and tag is production",
  "explanation": "This selector matches sensors running Windows platform with the 'production' tag."
}
```

### Example 2: Linux Database Servers

User request: "Target only Linux systems tagged as database servers"

Steps:
1. Call tool:
```
mcp__limacharlie__generate_sensor_selector(
  query="Linux systems tagged as database servers"
)
```

Expected response:
```json
{
  "selector": "plat is linux and tag is database",
  "explanation": "This selector targets Linux platform sensors that have been tagged with 'database'."
}
```

### Example 3: Exclude Test Systems

User request: "Select all macOS endpoints except those tagged 'test'"

Steps:
1. Call tool:
```
mcp__limacharlie__generate_sensor_selector(
  query="all macOS endpoints except those tagged test"
)
```

Expected response:
```json
{
  "selector": "plat is macos and not tag is test",
  "explanation": "This selector matches all macOS sensors except those that have the 'test' tag. The 'not' operator excludes test systems."
}
```

### Example 4: Multiple Conditions

User request: "Create selector for Windows or Linux servers in either production or staging environments"

Steps:
1. Call tool:
```
mcp__limacharlie__generate_sensor_selector(
  query="Windows or Linux servers in production or staging environments"
)
```

Expected response:
```json
{
  "selector": "(plat is windows or plat is linux) and (tag is production or tag is staging)",
  "explanation": "This selector matches sensors that are either Windows or Linux platform AND have either 'production' or 'staging' tags. Parentheses ensure proper grouping of conditions."
}
```

## Additional Notes

- **AI-Powered**: Uses Gemini AI with sensor selector-specific prompt templates
- **No Validation**: Single-pass generation without iterative validation
- **No OID Required**: Selector syntax is standard across all organizations
- **Platform Values**: Common platforms include `windows`, `linux`, `macos`, `chrome`
- **Tag-Based**: Relies on sensors being tagged appropriately in your organization
- **Operators**: Supports `is`, `not`, `and`, `or`, `contains`, `starts with`
- **Parentheses**: Use parentheses to group complex conditions
- **Hostname Matching**: Can use hostname patterns for targeting
- **IP-Based**: Can use internal or external IP addresses
- **Case Sensitivity**: Platform values are case-insensitive
- **Multiple Tags**: Can select based on multiple tag conditions
- **Use Cases**:
  - D&R rule targeting via `target` field
  - Installation key pre-tagging
  - Output filtering
  - Artifact collection scoping
  - Add-on deployment targeting
- **Testing**: Use sensor list to verify the selector matches intended sensors
- **Best Practice**: Start with simple selectors and add complexity as needed
- **Tag Strategy**: Effective selectors require a consistent tagging strategy
- **Documentation**: Document your organization's tagging conventions
- **Prompt Template**: Uses `prompts/gen_sensor_selector.txt` from the MCP server

## Reference

For more details on the MCP tool implementation, check: `../lc-mcp-server/internal/tools/ai/ai.go` (generate_sensor_selector function)

For sensor selector syntax and examples, see LimaCharlie's documentation on sensor targeting and selectors.
