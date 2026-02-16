# LimaCharlie CLI Access

All LimaCharlie operations are performed through the `limacharlie` CLI. This document explains how the CLI works and common usage patterns.

## CLI Basics

```bash
limacharlie <noun> <verb> [flags] --oid <oid> --output yaml
```

- `<noun>`: The resource type (e.g., `sensor`, `rule`, `search`, `org`)
- `<verb>`: The action (e.g., `list`, `get`, `create`, `delete`, `run`)
- `--oid <uuid>`: Organization ID (required for most commands)
- `--output yaml`: Machine-readable YAML output (always use this)

## Authentication

Authentication is managed via:
- **Config file**: `~/.limacharlie` config (set via `limacharlie auth login`)
- **Environment variables**: `LC_OID`, `LC_API_KEY` (override config file)
- **Per-command**: `--oid <uuid>` overrides the default org

### Auth Commands

```bash
# Check current auth
limacharlie auth whoami --output yaml

# Login interactively
limacharlie auth login

# List accessible orgs
limacharlie org list --output yaml
```

## Command Discovery

```bash
# Discover available commands
limacharlie discover

# Get AI-powered help for a specific command
limacharlie <command> --ai-help

# Get help for a topic
limacharlie help <topic>
```

## Output Handling

- `--output yaml`: YAML output (always use -- more token-efficient than JSON)
- `--filter JMESPATH`: Pre-filter output with JMESPath expressions (replaces piping to jq)
- `--output json`: JSON output (only for edge cases; prefer yaml)
- `--wide`: Show all fields in table output

For large results, use `--filter` to select only the fields you need:
```bash
# Select specific fields from a sensor list
limacharlie sensor list --oid <oid> --filter "[].{sid:sid,hostname:hostname,plat:plat}" --output yaml

# Filter to specific platform
limacharlie sensor list --oid <oid> --filter "[?plat=='windows']" --output yaml
```

Or use CLI-level filtering:
```bash
limacharlie sensor list --oid <oid> --selector 'plat == windows' --output yaml
```

## Common Patterns

### Pattern 1: Get Single Resource

```bash
limacharlie sensor get --sid <sid> --oid <oid> --output yaml
limacharlie rule get <name> --oid <oid> --output yaml
limacharlie sop get <name> --oid <oid> --output yaml
```

### Pattern 2: List Resources

```bash
limacharlie sensor list --oid <oid> --output yaml
limacharlie rule list --oid <oid> --output yaml
limacharlie output list --oid <oid> --output yaml
```

### Pattern 3: Server-Side Filtering

```bash
# Filter sensors by platform
limacharlie sensor list --oid <oid> --selector 'plat == windows' --output yaml

# Online sensors only
limacharlie sensor list --oid <oid> --online --output yaml

# Combined filters
limacharlie sensor list --oid <oid> --selector 'plat == windows' --online --output yaml
```

### Pattern 4: Create/Update Resources

```bash
limacharlie rule create <name> --detect '...' --respond '...' --oid <oid>
limacharlie output create <name> --module <m> --type <t> --oid <oid>
limacharlie secret set <name> --value '...' --oid <oid>
```

### Pattern 5: Delete Resources

```bash
limacharlie rule delete <name> --oid <oid>
limacharlie output delete <name> --oid <oid>
limacharlie sensor delete <sid> --confirm --oid <oid>
```

### Pattern 6: Run LCQL Queries

```bash
# Generate query from natural language (REQUIRED - never write LCQL manually)
limacharlie ai generate-query --prompt "find DNS requests to example.com" --oid <oid> --output yaml

# Validate query
limacharlie search validate --query "<generated-query>" --oid <oid> --output yaml

# Execute query
limacharlie search run --query "<validated-query>" --start <ts> --end <ts> --oid <oid> --output yaml
```

### Pattern 7: Search IOCs

```bash
limacharlie ioc search --type domain --value malicious.com --oid <oid> --output yaml
limacharlie ioc batch-search --input-file iocs.txt --oid <oid> --output yaml
limacharlie ioc hosts <hostname-prefix> --oid <oid> --output yaml
```

### Pattern 8: Live Sensor Commands

```bash
limacharlie task send --sid <sid> --task os_processes --oid <oid> --output yaml
limacharlie task send --sid <sid> --task os_netstat --oid <oid> --output yaml
limacharlie task send --sid <sid> --task os_version --oid <oid> --output yaml
```

### Pattern 9: AI-Powered Generation

```bash
# Generate D&R detection rule
limacharlie ai generate-detection --description "detect encoded PowerShell" --oid <oid> --output yaml

# Generate D&R response rule
limacharlie ai generate-response --description "report with priority 8, add tag" --oid <oid> --output yaml

# Generate sensor selector
limacharlie ai generate-selector --description "all production Windows servers" --oid <oid> --output yaml

# Generate LCQL query
limacharlie ai generate-query --prompt "find lateral movement via PsExec" --oid <oid> --output yaml
```

## Multi-Org Operations

```bash
# List all accessible orgs
limacharlie org list --output yaml

# Use --oid per-command for each org
limacharlie sensor list --oid <org1-uuid> --output yaml
limacharlie sensor list --oid <org2-uuid> --output yaml
```

For parallel multi-org operations, skills spawn specialized sub-agents (one per org) that each call the CLI directly.

## Error Handling

CLI exit codes:
- `0`: Success
- `1`: General error
- `2`: Authentication error
- `3`: Not found
- `4`: Validation error

Errors are written to stderr. YAML output on stdout is only produced on success.

```bash
# Check for errors
if ! result=$(limacharlie sensor get --sid <sid> --oid <oid> --output yaml 2>/tmp/lc-err.txt); then
  echo "Error: $(cat /tmp/lc-err.txt)"
fi
```

## Organization ID (OID)

The OID is a **UUID** (e.g., `c1ffedc0-ffee-4a1e-b1a5-abc123def456`), **NOT** the organization name.

- Use `limacharlie org list --output yaml` to get all accessible orgs with their OIDs
- All commands require OID except: `limacharlie org list`, `limacharlie auth whoami`

## Timestamp Formats

| API | Format | Example |
|-----|--------|---------|
| CLI query parameters | **Seconds** (10 digits) | `1699574400` |
| Detection/event data | Milliseconds (13 digits) | `1699574400000` |

**Always divide by 1000** when using timestamps from detection data in CLI queries.

## Key CLI Command Reference

| Operation | CLI Command |
|---|---|
| List orgs | `limacharlie org list` |
| Org info | `limacharlie org info --oid <oid>` |
| List sensors | `limacharlie sensor list --oid <oid>` |
| Get sensor | `limacharlie sensor get --sid <sid> --oid <oid>` |
| Online sensors | `limacharlie sensor list --online --oid <oid>` |
| Check online | `limacharlie sensor online <sid> --oid <oid>` |
| Add/remove tag | `limacharlie tag add/remove <sid> <tag> --oid <oid>` |
| Isolate sensor | `limacharlie endpoint-policy isolate <sid> --oid <oid>` |
| Generate LCQL | `limacharlie ai generate-query --prompt "..." --oid <oid>` |
| Run query | `limacharlie search run --query "..." --start <ts> --end <ts> --oid <oid>` |
| Search IOCs | `limacharlie ioc search --type <t> --value <v> --oid <oid>` |
| Historic events | `limacharlie event list --sid <sid> --start <ts> --end <ts> --oid <oid>` |
| Historic detections | `limacharlie detection list --start <ts> --end <ts> --oid <oid>` |
| Generate D&R detection | `limacharlie ai generate-detection --description "..." --oid <oid>` |
| Validate D&R | `limacharlie rule validate --detect '...' --respond '...' --oid <oid>` |
| Create rule | `limacharlie rule create <name> --detect '...' --respond '...' --oid <oid>` |
| List rules | `limacharlie rule list --oid <oid>` |
| List SOPs | `limacharlie sop list --oid <oid>` |
| Send task | `limacharlie task send --sid <sid> --task <task-name> --oid <oid>` |
| Reliable task | `limacharlie task reliable-send --sid <sid> --task '...' --oid <oid>` |
| Upload payload | `limacharlie payload upload <name> --file <path> --oid <oid>` |
| Event schema | `limacharlie event schema <event_type> --oid <oid>` |
| Event types | `limacharlie event types --oid <oid>` |

**Note:** Some command flag names are approximations. Use `limacharlie <cmd> --ai-help` to verify exact flags at runtime.
