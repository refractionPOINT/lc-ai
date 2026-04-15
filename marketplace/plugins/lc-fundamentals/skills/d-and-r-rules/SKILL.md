---
name: d-and-r-rules
description: Working with Detection & Response rules in LimaCharlie — AI-assisted generation, validation, unit testing, historical replay, deployment, and FP rules. Use when creating, testing, modifying, or managing D&R rules or false positive rules.
allowed-tools:
  - Bash
  - Read
---

# D&R Rules

How to work with Detection & Response rules in LimaCharlie. This covers the mechanics of rule generation, validation, testing, and deployment. For higher-level detection engineering workflows, see composed skills.

## Critical Rule: NEVER Write D&R Rules Manually

D&R rule syntax is validated against organization-specific schemas. Manual YAML will fail validation. **Always use AI generation commands.**

## Rule Generation

### Generate Detection Component

```bash
limacharlie ai generate-detection --description "Detect NEW_PROCESS events where the command line contains '-enc' and the process is powershell.exe" --oid <oid> --output yaml
```

### Generate Response Component

```bash
limacharlie ai generate-response --description "Report the detection with priority 8, add tag 'encoded-powershell' with 7 day TTL" --oid <oid> --output yaml
```

### Common Response Actions

| Action | Description |
|--------|-------------|
| `report` | Create a detection (alert) |
| `tag` | Add/remove sensor tags |
| `task` | Send command to sensor |
| `isolate network` | Network isolation |
| `start ai agent` | Spawn AI session |
| `extension request` | Call an extension (e.g., ext-feedback) |

## Validation

**Always validate before deploying.** Write YAML to temp files, then validate:

```bash
cat > /tmp/detect.yaml << 'EOF'
<detection_yaml>
EOF
cat > /tmp/respond.yaml << 'EOF'
<response_yaml>
EOF
limacharlie dr validate --detect /tmp/detect.yaml --respond /tmp/respond.yaml --oid <oid>
```

## Unit Testing

Test rules against crafted sample events:

```bash
# Write combined rule file
cat > /tmp/rule.yaml << 'EOF'
detect:
  <detection>
respond:
  <response>
EOF

# Write test events
cat > /tmp/events.json << 'EOF'
[
  {
    "routing": {"event_type": "NEW_PROCESS"},
    "event": {
      "COMMAND_LINE": "powershell.exe -enc SGVsbG8=",
      "FILE_PATH": "C:\\Windows\\System32\\powershell.exe"
    }
  }
]
EOF

limacharlie dr test --input-file /tmp/rule.yaml --events /tmp/events.json --trace --oid <oid> --output yaml
```

Create both positive tests (MUST match) and negative tests (MUST NOT match).

## Historical Replay

Test rules against real historical data. The rule must be deployed first (use a temporary name):

```bash
# Deploy as temporary rule
limacharlie dr set --key temp-test-rule --input-file /tmp/rule.yaml --oid <oid>

# Calculate time range
start=$(date -d '1 hour ago' +%s) && end=$(date +%s)

# Estimate volume first (dry run)
limacharlie dr replay --name temp-test-rule --start $start --end $end --dry-run --oid <oid> --output yaml

# Run replay
limacharlie dr replay --name temp-test-rule --start $start --end $end --oid <oid> --output yaml

# With selector
limacharlie dr replay --name temp-test-rule --start $start --end $end --selector 'plat == "windows"' --oid <oid> --output yaml

# Clean up temporary rule
limacharlie dr delete --key temp-test-rule --confirm --oid <oid>
```

## Deployment

### Create/Update a Rule

```bash
cat > /tmp/rule.yaml << 'EOF'
detect:
  <validated_detection>
respond:
  <validated_response>
EOF
limacharlie dr set --key <rule-name> --input-file /tmp/rule.yaml --oid <oid>
```

### List Rules

```bash
limacharlie dr list --oid <oid> --output yaml
```

### Get a Rule

```bash
limacharlie dr get --key <rule-name> --oid <oid> --output yaml
```

### Delete a Rule

```bash
limacharlie dr delete --key <rule-name> --confirm --oid <oid>
```

## Rule Hive Namespaces

D&R rules are stored across three hives:

| Hive | Description | How Added |
|------|-------------|-----------|
| `dr-general` | Custom rules you create | `limacharlie dr set` |
| `dr-managed` | Managed rules from subscribed rulesets | Automatic from subscriptions |
| `dr-services` | Service-provided rules | From extensions/services |

When listing or auditing rules, check all three for the full picture.

## False Positive (FP) Rules

FP rules suppress known benign detections without modifying the original detection rule.

### Create FP Rule

```bash
cat > /tmp/fp-rule.yaml << 'EOF'
detection:
  op: and
  rules:
    - op: is
      path: cat
      value: suspicious_process
    - op: is
      path: routing/hostname
      value: SCCM-SERVER
EOF
limacharlie fp set --key <fp-rule-name> --input-file /tmp/fp-rule.yaml --oid <oid>
```

### FP Rule Paths

FP rules operate on detection output. Key paths:

| Path | Description |
|------|-------------|
| `cat` | Detection category |
| `detect/name` | Detection rule name |
| `detect/event/*` | Original event fields |
| `routing/hostname` | Sensor hostname |
| `routing/tags` | Sensor tags |
| `routing/sid` | Sensor ID |

### List FP Rules

```bash
limacharlie fp list --oid <oid> --output yaml
```

### Delete FP Rule

```bash
limacharlie fp delete --key <fp-rule-name> --confirm --oid <oid>
```

## Testing FP Rules

FP rules use the same detection logic syntax. Transform detections into test events:

```json
{
  "routing": {"event_type": "detection"},
  "event": {
    "cat": "suspicious_process",
    "detect": {"event": {"COMMAND_LINE": "..."}},
    "routing": {"hostname": "SCCM-SERVER"}
  }
}
```

Then use `limacharlie dr test` with the FP rule and transformed events.

## Detection Logic Operators

| Operator | Description |
|----------|-------------|
| `and` | All conditions must match |
| `or` | Any condition must match |
| `is` | Exact match |
| `contains` | Substring match |
| `starts with` | Prefix match |
| `ends with` | Suffix match |
| `exists` | Field exists |
| `matches` | Regex match |
| `is platform` | Platform check (more readable than decimal ID) |

## Naming Conventions

Rules: `[category]-[description]` (e.g., `lateral-movement-psexec`, `ransomware-vssadmin-delete`)

FP Rules: `fp-[category]-[pattern]-[YYYYMMDD]` (e.g., `fp-suspicious-process-sccm-server-20250415`)
