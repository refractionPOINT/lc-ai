# Using LimaCharlie

## Constants Reference

See [CONSTANTS.md](./CONSTANTS.md) for the authoritative source of all LimaCharlie constants including platform codes, architecture codes, IOC types, timestamps, and billing amounts.

## Raw REST API Calls (`limacharlie api`)

**`limacharlie api` is an escape hatch** for endpoints that have no dedicated CLI command. Do NOT use it for operations that already have a CLI noun/verb.

- **WRONG**: `limacharlie api orgs/{oid}/sensors --oid <oid>` (use `limacharlie sensor list --oid <oid>`)
- **WRONG**: `limacharlie api orgs/{oid}/extensions --oid <oid>` (use `limacharlie extension list --oid <oid>`)

**Always try `limacharlie <noun> --ai-help` first.** Only fall back to `limacharlie api` when no CLI command exists.

```bash
limacharlie api <endpoint> --oid <oid> --output yaml
```
`{oid}` in the path is replaced with the resolved org ID. Supports `-f` (string fields), `-F` (typed fields, `@file`), `--input <file>`, `--target` (`api`|`billing`|`jwt`|`stream`|`downloads`). The CLI handles all authentication automatically.

### Cases CLI

The Cases extension (`ext-cases`) has first-class CLI support via `limacharlie case`:
```bash
limacharlie case list --oid <oid> --output yaml
limacharlie case get --case-number <case_number> --oid <oid> --output yaml
limacharlie case update --case-number <case_number> --status in_progress --oid <oid> --output yaml
limacharlie case update --case-number <case_number> --severity high --oid <oid> --output yaml
limacharlie case add-note --case-number <case_number> --content "Note" --type analysis --oid <oid> --output yaml
limacharlie case entity add --case <case_number> --type ip --value "10.0.0.1" --verdict malicious --oid <oid> --output yaml
limacharlie case telemetry add --case <case_number> --event '<full LC event JSON>' --verdict suspicious --oid <oid> --output yaml
limacharlie case export --case-number <case_number> --oid <oid> --output yaml
limacharlie case export --case-number <case_number> --with-data ./case-export --oid <oid>
```

The cases extension creates cases from detections via D&R rules and extension requests. Cases can also be created without detections for ad-hoc investigations. Use `limacharlie case --ai-help` for full command reference. See the `case-investigation` skill for the full investigation workflow.

## Required Tool

**ALWAYS use the `limacharlie` CLI via Bash** for all LimaCharlie API operations. Never call MCP tools directly.

## CLI Bootstrap

The `limacharlie` CLI is **automatically installed** on session start via the SessionStart hook.
If auto-install fails (shown as a yellow warning), guide the user to install manually:
```bash
pipx install limacharlie   # preferred (isolated environment)
uv tool install limacharlie # alternative (fast, isolated)
pip install --user limacharlie # fallback
```

On first use, verify authentication:
1. Check auth: `limacharlie auth whoami --output yaml` (permissions are omitted by default for compact output)
2. If no auth: guide user through `limacharlie auth login`
3. List orgs: `limacharlie org list --output yaml`
4. Require user to specify target org(s)
5. Check SOPs: `limacharlie sop list --oid <oid> --output yaml`

To verify a specific permission without fetching the full permission set, use `--check-perm`.
**IMPORTANT**: Always include `--oid <oid>` — without it, the check runs against a null org context and will always return `has_perm: false`:
```bash
limacharlie auth whoami --oid <oid> --check-perm ai_agent.operate --output yaml
# Returns: {perm: ai_agent.operate, has_perm: true/false}
```
To see all permissions (verbose): `limacharlie auth whoami --show-perms --output yaml`

## Critical Rules

**ALWAYS require the user to specify the organization or organizations they intend to operate on**, NEVER assume.

### 1. Use the CLI Directly

- **WRONG**: `mcp__plugin_lc-essentials_limacharlie__lc_call_tool(...)` or spawning an api-executor agent
- **CORRECT**: `Bash("limacharlie <noun> <verb> --oid <oid> --output yaml")`

### 2. Always Pass `--output yaml`

All CLI commands should include `--output yaml` for machine-readable output that is more token-efficient than JSON.

### 3. Use `--filter` to Reduce Output

When you only need specific fields, use `--filter JMESPATH` to select them:
```bash
limacharlie sensor list --oid <oid> --filter "[].{sid:sid,hostname:hostname,plat:plat}" --output yaml
```
This reduces token usage vs returning the full response.

### 4. Use `--oid <uuid>` Per Command

Every command that operates on an organization requires `--oid <uuid>`. Use `limacharlie org list --output yaml` to discover available orgs and their OIDs.

### 5. Use `--ai-help` for Command Discovery

When unsure about a command's flags or usage:
```bash
limacharlie <command> --ai-help
```

### 6. LCQL Query Handling

LCQL uses unique pipe-based syntax validated against org-specific schemas. **LLMs do NOT know correct LCQL syntax** - any manually written or AI-generated LCQL without using the generation tools will be invalid.

**NEVER:**
- Write LCQL queries manually
- Generate LCQL queries from your own knowledge
- Show "example" LCQL queries to users without using the generation command
- Assume you know LCQL syntax - you don't, and your queries WILL be wrong

**ALWAYS:**
1. `limacharlie ai generate-query --prompt "..." --oid <oid> --output yaml` - Convert natural language to LCQL (required for creating any query)
2. `limacharlie search validate --query "..." --oid <oid> --output yaml` - Verify query is valid before execution - **mandatory for ALL queries** including:
   - Queries generated by the AI command
   - Queries provided by the user
   - Queries from saved queries or other sources
3. Execute query (only after validation passes):
   - **Prefer `limacharlie search run --query "..." --start <ts> --end <ts> --oid <oid> --output yaml`**
   - Valid `--stream` values: `event`, `detection`, `audit` (NOT `detect`)

**For queries beyond 30 days (paid queries):**
- First call `limacharlie search estimate --query "..." --start <ts> --end <ts> --oid <oid> --output yaml` to get cost estimate
- Show the estimated cost to the user
- If estimate > 0, ask user to approve before running
- Only proceed after user confirmation

If a user asks for "example LCQL queries" or "LCQL syntax", explain that LCQL is org-specific and use the generate command to demonstrate with their actual schema — never fabricate examples.

Consider calling `limacharlie event types --oid <oid> --output yaml` before generating queries to understand available event types. On validation failure, re-call the generate command with the error message — never fix queries manually. After 3 failures, report the issue to the user.

### 7. Never Generate D&R Rules Manually

Use AI generation commands:
1. `limacharlie ai generate-detection --description "..." --oid <oid> --output yaml` - Generate detection YAML
2. `limacharlie ai generate-response --description "..." --oid <oid> --output yaml` - Generate response YAML
3. `limacharlie dr validate --detect detect.yaml --respond respond.yaml --oid <oid>` - Validate before deploy (takes file paths)

D&R rules are stored across three hives: `dr-general` (custom rules), `dr-managed` (managed rules from subscriptions), and `dr-services` (service-provided rules). When listing or auditing rules, check all three to get the full picture.

### 8. Never Calculate Timestamps Manually

LLMs consistently produce incorrect timestamp values.

**ALWAYS use bash:**
```bash
date +%s                           # Current time (seconds)
date -d '1 hour ago' +%s           # 1 hour ago
date -d '7 days ago' +%s           # 7 days ago
date -d '2025-01-15 00:00:00 UTC' +%s  # Specific date
```

Always run bash to get timestamps FIRST, verify `start_time < end_time` and that historical timestamps are in the past, then use the captured values in API calls.

### 9. OID is UUID, NOT Organization Name

- **WRONG**: `--oid "my-org-name"`
- **CORRECT**: `--oid "c1ffedc0-ffee-4a1e-b1a5-abc123def456"`
- Use `limacharlie org list --output yaml` to list all accessible orgs with their OIDs

### 10. Timestamp Milliseconds vs Seconds

- Detection/event data: **milliseconds** (13 digits)
- API parameters: **seconds** (10 digits)
- **ALWAYS** divide by 1000 when using detection timestamps for API queries

### 11. Never Fabricate Data

- Only report what APIs return
- Never estimate, infer, or extrapolate data
- Show "N/A" or "Data unavailable" for missing fields
- Never calculate costs (no pricing data in API)

### 12. Spawn Agents in Parallel

When processing multiple organizations or items:
- Use a SINGLE message with multiple Task calls
- Do NOT spawn agents sequentially
- Each agent handles ONE item, parent aggregates results

## Standard Operating Procedures (SOPs)

Organizations can define SOPs (Standard Operating Procedures) in LimaCharlie that guide how tasks are performed. SOPs can be large documents, so they are loaded lazily (similar to Claude Code Skills).

### On Conversation Start

Before running LimaCharlie operations:

**List all SOPs** using `limacharlie sop list --oid <oid> --output yaml` for each organization in scope, extracting only the name of the SOP and the `description` field.
**During operations** if an SOP description sounds like it applies to the current operation, call `limacharlie sop get --key <name> --oid <oid> --output yaml` to get the actual procedure.
**Take into account** the contents of the fetched SOP, if a match is found, announce: "Following SOP: [sop-name] - [description]"

## Sensor Selectors

Sensor selectors use [bexpr](https://github.com/hashicorp/go-bexpr) syntax. Use `*` to match all sensors. See [CONSTANTS.md](./CONSTANTS.md) for the full field reference, platform values, and examples.

## Extensions

Not all extensions have a configuration. To check subscriptions: `limacharlie extension list --oid <oid> --output yaml`.

## Infrastructure Sync

When using `limacharlie sync push`, **avoid using `--force`** unless you are certain you want to remove cloud resources not present in the local config file. Without `--force`, push only adds or updates resources — it never removes them. With `--force`, any resource in the cloud that is missing from the local file **will be deleted**, which can cause data loss if your local file is not a complete representation of the org's configuration.

## Billing, Features and Functionality

Don't assume you know anything about LimaCharlie billing, pricing, or features. Use the documentation: https://github.com/refractionPOINT/documentation/tree/master/docs/limacharlie/doc
