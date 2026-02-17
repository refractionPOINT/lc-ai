# Using LimaCharlie

## Constants Reference

**Source:** [go-limacharlie/limacharlie/identification.go](https://github.com/refractionPOINT/go-limacharlie)

### Platform Codes

Platform codes are returned as `uint32` in sensor info responses.

| Platform | String | Hex | Decimal |
|----------|--------|-----|---------|
| Windows | `windows` | 0x10000000 | 268435456 |
| Linux | `linux` | 0x20000000 | 536870912 |
| macOS | `macos` | 0x30000000 | 805306368 |
| iOS | `ios` | 0x40000000 | 1073741824 |
| Android | `android` | 0x50000000 | 1342177280 |
| ChromeOS | `chrome` | 0x60000000 | 1610612736 |
| VPN | `vpn` | 0x70000000 | 1879048192 |

#### USP Adapter Platforms

| Platform | String | Hex | Decimal |
|----------|--------|-----|---------|
| Text | `text` | 0x80000000 | 2147483648 |
| JSON | `json` | 0x90000000 | 2415919104 |
| GCP | `gcp` | 0xA0000000 | 2684354560 |
| AWS | `aws` | 0xB0000000 | 2952790016 |
| Carbon Black | `carbon_black` | 0xC0000000 | 3221225472 |
| 1Password | `1password` | 0xD0000000 | 3489660928 |
| Office365 | `office365` | 0xE0000000 | 3758096384 |
| Sophos | `sophos` | 0xF0000000 | 4026531840 |
| Crowdstrike | `crowdstrike` | 0x01000000 | 16777216 |
| MS Defender | `msdefender` | 0x04000000 | 67108864 |
| Duo | `duo` | 0x05000000 | 83886080 |
| Okta | `okta` | 0x06000000 | 100663296 |
| SentinelOne | `sentinel_one` | 0x07000000 | 117440512 |
| GitHub | `github` | 0x08000000 | 134217728 |
| Slack | `slack` | 0x09000000 | 150994944 |
| Azure AD | `azure_ad` | 0x0C000000 | 201326592 |
| Azure Monitor | `azure_monitor` | 0x0D000000 | 218103808 |

### Architecture Codes

| Architecture | String | Hex | Decimal |
|--------------|--------|-----|---------|
| x86 | `x86` | 0x00000001 | 1 |
| x64 | `x64` | 0x00000002 | 2 |
| ARM | `arm` | 0x00000003 | 3 |
| ARM64 | `arm64` | 0x00000004 | 4 |
| Alpine64 | `alpine64` | 0x00000005 | 5 |
| Chromium | `chromium` | 0x00000006 | 6 |
| WireGuard | `wireguard` | 0x00000007 | 7 |
| ARM (L) | `arml` | 0x00000008 | 8 |
| USP Adapter | `usp_adapter` | 0x00000009 | 9 |

### IOC Types

Valid IOC types for `search_iocs` and `batch_search_iocs`.

**Source:** [lc-mcp-server/internal/tools/historical/historical.go](https://github.com/refractionPOINT/lc-mcp-server)

| Type | Aliases | Description |
|------|---------|-------------|
| `file_hash` | `hash` | File hash (MD5, SHA1, SHA256) |
| `domain` | - | Domain name |
| `ip` | - | IP address |
| `file_path` | - | Full file path |
| `file_name` | - | File name only |
| `user` | `username` | Username |
| `service_name` | - | Service name |
| `package_name` | - | Package name |
| `hostname` | - | Hostname (uses different endpoint) |

#### IOC Type Mapping (Extraction to Search)

When extracting IOCs from threat reports (plural field names) and searching via API (singular type values):

| Extraction Field | Search Type |
|------------------|-------------|
| `file_hashes` | `file_hash` |
| `domains` | `domain` |
| `ips` | `ip` |
| `file_names` | `file_name` |
| `file_paths` | `file_path` |
| `urls` | (extract domain/ip first) |

### Billing Amounts

All billing API responses return amounts in **CENTS**, not dollars.

```
display_amount = api_amount / 100

Example:
  API returns: {"total": 25342}
  Display: $253.42
```

## Required Tool

**ALWAYS use the `limacharlie` CLI via Bash** for all LimaCharlie API operations. Never call MCP tools directly.

## CLI Bootstrap

On first use, verify the CLI is available and authenticated:

1. Check CLI installed: `limacharlie --version`
2. Check auth: `limacharlie auth whoami --output yaml`
3. If no auth: guide user through `limacharlie auth login`
4. List orgs: `limacharlie org list --output yaml`
5. Require user to specify target org(s)
6. Check SOPs: `limacharlie sop list --oid <oid> --output yaml`

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

**For queries beyond 30 days (paid queries):**
- First call `limacharlie search estimate --query "..." --start <ts> --end <ts> --oid <oid> --output yaml` to get cost estimate
- Show the estimated cost to the user
- If estimate > 0, ask user to approve before running
- Only proceed after user confirmation

If a user asks for "example LCQL queries" or "LCQL syntax", explain that LCQL is org-specific and use the generate command to demonstrate with their actual schema - never fabricate examples.

**Before generating queries:**
- Consider calling `limacharlie event types --oid <oid> --output yaml` to understand available event types and fields in the org
- This helps generate more accurate queries targeting actual data that exists

**After query execution:**
- If results are empty or unexpected, consider:
  - Wrong time range (data may not exist in that window)
  - Wrong event type for the data source
  - Field names that exist but aren't populated for this org
- Ask the user for clarification rather than assuming the query is correct

**On validation failure:**
- Do NOT attempt to fix the query manually - you will make it worse
- If original natural language request is available:
  - Re-call the generate command with the original request plus the validation error message
  - Ask it to avoid the specific syntax issue
- If original natural language request is NOT available (user-provided query, saved query, etc.):
  - Ask the user to describe what they're trying to accomplish in plain language
  - Use their description to call the generate command fresh
- Validate the new query again
- If validation fails 3 times, report the issue to the user rather than continuing to retry

### 7. Never Generate D&R Rules Manually

Use AI generation commands:
1. `limacharlie ai generate-detection --description "..." --oid <oid> --output yaml` - Generate detection YAML
2. `limacharlie ai generate-response --description "..." --oid <oid> --output yaml` - Generate response YAML
3. `limacharlie dr validate --detect detect.yaml --respond respond.yaml --oid <oid>` - Validate before deploy (takes file paths)

### 8. Never Calculate Timestamps Manually

LLMs consistently produce incorrect timestamp values.

**ALWAYS use bash:**
```bash
date +%s                           # Current time (seconds)
date -d '1 hour ago' +%s           # 1 hour ago
date -d '7 days ago' +%s           # 7 days ago
date -d '2025-01-15 00:00:00 UTC' +%s  # Specific date
```

**Validation before API calls:**
1. Run bash to get timestamps FIRST, capture the actual values
2. Verify: historical timestamps must be in the past (less than current time)
3. Verify: time ranges must have `start_time < end_time`
4. Show calculated values in your reasoning before making API calls

**Example workflow:**
```
# Get timestamps
now=$(date +%s)           # e.g., 1737312000
start=$(date -d '24 hours ago' +%s)  # e.g., 1737225600

# Verify before API call
# now=1737312000, start=1737225600, start < now check
```

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

### Example Workflow

1. User signals intent to work on org 123
2. LLM lists SOPs on org 123: "malware-response" => description: "Standard procedure for malware incidents"
3. User asks to investigate a malware alert on org 123
4. LLM announces: "Following SOP: malware-response - Standard procedure for malware incidents"
5. LLM recognizes the "malware-response" SOP relates to this and loads the full procedure
6. LLM follows the documented steps from the loaded SOP content

## Sensor Selector Reference

Sensor selectors use [bexpr](https://github.com/hashicorp/go-bexpr) syntax to filter sensors. Use `*` to match all sensors.

### Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `sid` | string | Sensor ID (UUID) |
| `oid` | string | Organization ID (UUID) |
| `iid` | string | Installation Key ID (UUID) |
| `plat` | string | Platform name (see values below) |
| `ext_plat` | string | Extended platform (for multi-platform adapters like Carbon Black) |
| `arch` | string | Architecture (see values below) |
| `hostname` | string | Sensor hostname |
| `ext_ip` | string | External IP address |
| `int_ip` | string | Internal IP address |
| `mac_addr` | string | MAC address |
| `did` | string | Device ID |
| `enroll` | int | Enrollment timestamp |
| `alive` | int | Last seen timestamp |
| `is_del` | bool | Sensor is deleted |
| `isolated` | bool | Sensor is network isolated |
| `should_isolate` | bool | Sensor should be isolated |
| `kernel` | bool | Kernel mode enabled |
| `sealed` | bool | Sensor is sealed |
| `should_seal` | bool | Sensor should be sealed |
| `tags` | string[] | Sensor tags (use `in` operator) |

### Platform Values (`plat`, `ext_plat`)

**EDR Platforms:** `windows`, `linux`, `macos`, `ios`, `android`, `chrome`, `vpn`

**Adapter/USP Platforms:** `text`, `json`, `gcp`, `aws`, `carbon_black`, `1password`, `office365`, `sophos`, `crowdstrike`, `msdefender`, `sentinel_one`, `okta`, `duo`, `github`, `slack`, `azure_ad`, `azure_monitor`, `entraid`, `zeek`, `cef`, `wel`, `xml`, `guard_duty`, `k8s_pods`, `wiz`, `proofpoint`, `box`, `cylance`, `fortigate`, `netscaler`, `paloalto_fw`, `iis`, `trend_micro`, `trend_worryfree`, `bitwarden`, `mimecast`, `hubspot`, `zendesk`, `pandadoc`, `falconcloud`, `sublime`, `itglue`, `canary_token`, `lc_event`, `email`, `mac_unified_logging`, `azure_event_hub_namespace`, `azure_key_vault`, `azure_kubernetes_service`, `azure_network_security_group`, `azure_sql_audit`

### Architecture Values (`arch`)

`x86`, `x64`, `arm`, `arm64`, `alpine64`, `chromium`, `wireguard`, `arml`, `usp_adapter`

### Example Selectors

```
plat == windows                           # All Windows sensors
plat == windows and arch == x64           # 64-bit Windows only
plat == linux and hostname contains "web" # Linux with "web" in hostname
"prod" in tags                            # Sensors tagged "prod"
plat == windows and not isolated          # Non-isolated Windows
ext_plat == windows                       # Carbon Black/Crowdstrike reporting Windows endpoints
```

### Extensions
Not all extensions have a configuration, to determine if an extension is subscribed to, use `limacharlie extension list --oid <oid> --output yaml`.

### Billing, Features and Functionality
Don't assume you know anything about how LimaCharlie is billed, pricing structure, features etc. Use the documentation to ground your information: https://github.com/refractionPOINT/documentation/tree/master/docs/limacharlie/doc
