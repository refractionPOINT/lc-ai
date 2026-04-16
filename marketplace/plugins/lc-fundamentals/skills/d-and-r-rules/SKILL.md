---
name: d-and-r-rules
description: Working with Detection & Response rules in LimaCharlie — AI-assisted generation, validation, unit testing, historical replay, deployment, FP rules, stateful rules, behavioral detection patterns, suppression, alternate detection targets, and response actions. Use when creating, testing, modifying, or managing D&R rules, false positive rules, or understanding detection patterns.
allowed-tools:
  - Bash
  - Read
---

# D&R Rules

How to work with Detection & Response rules in LimaCharlie. This covers rule generation, validation, testing, deployment, stateful rules, behavioral detection patterns, suppression, alternate targets, and response actions.

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
| `isolate network` | Persistent network isolation (survives reboot) |
| `rejoin network` | Remove network isolation |
| `seal` / `unseal` | Tamper-resistance for the EDR |
| `add var` / `del var` | Set/remove sensor variables |
| `extension request` | Call an extension asynchronously |
| `start ai agent` | Spawn AI session |
| `output` | Forward event to a specific output |
| `wait` | Delay before next action (max 1 minute) |

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

FP rules suppress known benign detections without modifying the original detection rule. **FP rules operate on the detection output, not the raw event** — the paths reference detection fields, not event fields.

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

### List / Delete FP Rules

```bash
limacharlie fp list --oid <oid> --output yaml
limacharlie fp delete --key <fp-rule-name> --confirm --oid <oid>
```

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
| `is platform` | Platform check |
| `is tagged` | Tag check |
| `is windows` | Windows platform shorthand |
| `lookup` | Look up a value against a lookup table or API resource |
| `is public address` | Check if IP is public |
| `string distance` | Levenshtein distance |

---

# Stateful Rules

Stateful rules track and remember the state of past events to detect patterns over time. Unlike stateless rules (which evaluate events in isolation), stateful rules detect patterns like "process A spawning process B" or "5 failed logins within 60 seconds."

Events in LimaCharlie have well-defined relationships via `routing/this`, `routing/parent`, and `routing/target`. Stateful rules leverage these relationships.

## Detecting Children / Descendants

Use `with child` (direct children only) or `with descendant` (children, grandchildren, etc.) to detect process tree patterns:

```yaml
# Detect cmd.exe spawning calc.exe
event: NEW_PROCESS
op: ends with
path: event/FILE_PATH
value: cmd.exe
case sensitive: false
with child:
  op: ends with
  event: NEW_PROCESS
  path: event/FILE_PATH
  value: calc.exe
  case sensitive: false
```

This detects `cmd.exe → calc.exe` but NOT `cmd.exe → firefox.exe → calc.exe`. Use `with descendant` to match at any depth.

### Complex Child Patterns with `and`/`or`

Stateful rules support full operator nesting. Detect outlook.exe spawning a browser AND dropping a PowerShell script:

```yaml
event: NEW_PROCESS
op: ends with
path: event/FILE_PATH
value: outlook.exe
case sensitive: false
with child:
  op: and
  rules:
    - op: ends with
      event: NEW_PROCESS
      path: event/FILE_PATH
      value: chrome.exe
      case sensitive: false
    - op: ends with
      event: NEW_DOCUMENT
      path: event/FILE_PATH
      value: .ps1
      case sensitive: false
```

## Detecting Proximal Events (Repetition)

Use `with events` to detect event repetition on the same sensor within a time window:

```yaml
# 5 failed login attempts within 60 seconds
event: WEL
op: is windows
with events:
  event: WEL
  op: is
  path: event/EVENT/System/EventID
  value: '4625'
  count: 5
  within: 60
```

## Counting Events in Process Trees

`with child` and `with descendant` also support `count` and `within`:

```yaml
# Outlook writing 5+ .ps1 files within 60 seconds
event: NEW_PROCESS
op: ends with
path: event/FILE_PATH
value: outlook.exe
case sensitive: false
with child:
  op: ends with
  event: NEW_DOCUMENT
  path: event/FILE_PATH
  value: .ps1
  case sensitive: false
  count: 5
  within: 60
```

## Choosing Which Event to Report

By default, stateful detections include the initial parent event. Use `report latest event: true` to include the most recent matching event instead:

```yaml
event: NEW_PROCESS
op: ends with
path: event/FILE_PATH
value: outlook.exe
case sensitive: false
report latest event: true
with child:
  op: ends with
  event: NEW_PROCESS
  path: event/FILE_PATH
  value: chrome.exe
  case sensitive: false
```

**Note**: non-report actions (like `task`) ALWAYS observe the latest event, regardless of this flag. So `<<routing/parent>>` in a task action references the latest event's parent.

## Flipping Back to Stateless

Within a `with child`/`with descendant` context, all operators are stateful (matching across multiple events). To force a sub-operator to match a single event, use `is stateless: true`:

```yaml
event: NEW_PROCESS
op: ends with
path: event/FILE_PATH
value: outlook.exe
case sensitive: false
with child:
  op: and
  is stateless: true
  rules:
    - op: ends with
      event: NEW_PROCESS
      path: event/FILE_PATH
      value: evil.exe
      case sensitive: false
    - op: contains
      path: event/COMMAND_LINE
      value: something-else
      case sensitive: false
```

With `is stateless: true`, BOTH conditions must match the SAME event (a single NEW_PROCESS that is evil.exe AND contains "something-else").

## Stateful Rules Caveats

- **Forward-looking only**: stateful rules track state from the moment they are deployed. Changing a rule resets ALL state tracking — the parent event must re-occur for the rule to start watching for children again.
- **FIFO processing**: events from a single sensor are processed first-in-first-out, in order. One slow rule (e.g., with `wait` or external lookup) blocks processing of all subsequent events from that sensor.

---

# Behavioral Detection Patterns

LimaCharlie supports behavioral detection using D&R rules and the suppression system. These patterns detect anomalous behavior without external analytics infrastructure.

## Suppression System

Suppression is the mechanism for frequency control. It is supported on **every response action**, not just `report`. Every action can have its own suppression parameters.

### Suppression Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `max_count` | integer | Maximum action executions per period per key. Use `1` for first-seen. |
| `min_count` | integer | Minimum activations before the action fires. Must be used with `max_count`. |
| `period` | string | Time window. Formats: `s`, `m`, `h`. Range: 1s to 720h (30 days). |
| `is_global` | boolean | `true` = org-wide counter. `false` (default) = per-sensor counter. |
| `keys` | list | Template strings forming the uniqueness key. Supports `{{ .event.* }}`, `{{ .routing.* }}`, and `{{ .mtd.* }}`. |
| `count_path` | string | Path to an integer in the event to use as the increment instead of 1. |

### Three Suppression Modes

1. **Frequency limit** (`max_count` only): fire at most N times per period per key
2. **Threshold activation** (`min_count` + `max_count`): suppress until min_count reached, then fire once
3. **Variable count** (`count_path` + `min_count`/`max_count`): increment counter by event value, not by 1

### Key Template Namespaces

| Namespace | Source | Example |
|-----------|--------|---------|
| `.event.*` | Raw event payload | `{{ .event.FILE_PATH }}` |
| `.routing.*` | Event routing metadata | `{{ .routing.hostname }}` |
| `.mtd.*` | Metadata from lookup operators | `{{ .mtd.lcr___api_ip_geo.country.iso_code }}` |

**Gotcha — metadata key naming**: the `.mtd` key name is derived from the resource name with special characters replaced by underscores. `lcr://api/ip-geo` becomes `.mtd.lcr___api_ip_geo`. `hive://lookup/my-list` becomes `.mtd.my_list`.

**Gotcha — key is an AND**: all keys together form the uniqueness key. Missing a key component creates separate suppression buckets. Adding a constant string to keys (e.g., `'my-rule-name'`) prevents cross-rule suppression collisions.

### Suppression Limitations

- **Fixed time windows** that reset on expiry (not rolling/sliding)
- **Maximum period: 30 days** (720h)
- **Static thresholds only** — no adaptive baselines
- **No statistical comparison** — detects "above N" or "first occurrence," not "unusual vs baseline"

## First-Seen Detection

Suppression with `max_count: 1` fires exactly once per unique key combination per window — a first-seen detector.

**First time a host resolves a domain (within 30 days):**

```yaml
detect:
  event: DNS_REQUEST
  op: exists
  path: event/DOMAIN_NAME

respond:
  - action: report
    name: new-domain-for-host
    suppression:
      max_count: 1
      period: 720h
      is_global: false
      keys:
        - 'first-domain'
        - '{{ .event.DOMAIN_NAME }}'
```

**First time a user logs in from a new country (using GeoIP lookup):**

```yaml
detect:
  event: USER_LOGIN
  op: lookup
  path: event/SOURCE_IP
  resource: lcr://api/ip-geo

respond:
  - action: report
    name: first-login-from-country
    suppression:
      max_count: 1
      period: 720h
      is_global: true
      keys:
        - 'first-country'
        - '{{ .event.USER_NAME }}'
        - '{{ .mtd.lcr___api_ip_geo.country.iso_code }}'
```

**First time a threat-intel-matched hash appears on a host:**

```yaml
detect:
  event: NEW_PROCESS
  op: lookup
  path: event/HASH
  resource: hive://lookup/threat-intel-hashes

respond:
  - action: report
    name: first-ti-match-on-host
    suppression:
      max_count: 1
      period: 720h
      is_global: false
      keys:
        - 'first-ti-hash'
        - '{{ .event.HASH }}'
        - '{{ .mtd.threat_intel_hashes.category }}'
```

## Cardinality Detection (Two-Rule Chaining)

Detect when an entity accumulates too many unique values. Requires two rules:

1. **Rule 1 (dedup)**: reports once per unique value using `max_count: 1`
2. **Rule 2 (count)**: targets the detection from Rule 1 using the `detection` target and counts with `min_count: N`

**Detect a host resolving 100+ unique domains in 1 hour (DGA/C2):**

```yaml
# Rule 1: Deduplicate — one report per unique domain per sensor per hour
detect:
  event: DNS_REQUEST
  op: exists
  path: event/DOMAIN_NAME

respond:
  - action: report
    name: dns-domain-observed
    suppression:
      max_count: 1
      period: 1h
      is_global: false
      keys:
        - 'dns-dedup'
        - '{{ .event.DOMAIN_NAME }}'
```

```yaml
# Rule 2: Count — fire when unique domains exceed threshold
detect:
  event: dns-domain-observed
  target: detection
  op: exists
  path: detect

respond:
  - action: report
    name: excessive-dns-diversity
    suppression:
      min_count: 100
      max_count: 100
      period: 1h
      is_global: false
      keys:
        - 'dns-diversity-count'
```

**Detect a user accessing 5+ unique hosts in 6 hours (lateral movement):**

```yaml
# Rule 1: Deduplicate per (user, host) — global because user moves across sensors
detect:
  event: USER_LOGIN
  op: exists
  path: event/USER_NAME

respond:
  - action: report
    name: user-host-access-observed
    suppression:
      max_count: 1
      period: 6h
      is_global: true
      keys:
        - 'lateral-dedup'
        - '{{ .event.USER_NAME }}'
        - '{{ .routing.hostname }}'
```

```yaml
# Rule 2: Count unique hosts per user
detect:
  event: user-host-access-observed
  target: detection
  op: exists
  path: detect

respond:
  - action: report
    name: possible-lateral-movement
    suppression:
      min_count: 5
      max_count: 5
      period: 6h
      is_global: true
      keys:
        - 'lateral-count'
        - '{{ .detect.event.USER_NAME }}'
```

## Volume Detection

The `count_path` parameter increments the counter by an event value instead of 1. Alert when a host uploads more than 1 GB to external IPs in 24 hours:

```yaml
detect:
  event: USP_NETFLOW
  op: is public address
  path: event/dst_ip

respond:
  - action: report
    name: high-egress-volume
    suppression:
      min_count: 1073741824
      max_count: 1073741824
      period: 24h
      is_global: false
      count_path: event/bytes_out
      keys:
        - 'egress-volume'
```

## Multi-Signal Aggregation

Multiple rules can feed into a shared suppression counter. When independent detections report the same name, the counter accumulates across them:

```yaml
# Rule A: Suspicious DNS
respond:
  - action: report
    name: indicator-hit

# Rule B: Sensitive process access
respond:
  - action: report
    name: indicator-hit

# Aggregation rule — fires when 5 indicators on one host in 1 hour
detect:
  event: indicator-hit
  target: detection
  op: exists
  path: detect

respond:
  - action: report
    name: high-risk-host
    priority: 1
    suppression:
      min_count: 5
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - 'risk-aggregation'
```

---

# Alternate Detection Targets

D&R rules run against `edr` events by default, but there are **7 other targets**:

| Target | Purpose | Supported Actions |
|--------|---------|-------------------|
| `detection` | Chain rules on detections from other rules | All |
| `deployment` | Sensor lifecycle events (enrollment, clone, over-quota, deletion) | All |
| `artifact` | Parsed artifact content (logs, PCAP, WEL) | `report` only |
| `artifact_event` | Artifact lifecycle events (ingest, export_complete) | All |
| `schedule` | Timed events fired at intervals per-org or per-sensor | All |
| `audit` | Platform management events (config changes, API calls) | All |
| `billing` | Billing and quota events | All |

## Detection Chaining (`target: detection`)

Run rules on detections generated by other rules. The `event:` field refers to the `name` of the detection from the original rule's `report` action.

```yaml
# Run when virus-total-hit detection occurs on a VIP host
target: detection
op: and
rules:
  - op: is
    path: cat
    value: virus-total-hit
  - op: is
    path: routing/hostname
    value: ceo-laptop
```

### Double-Underscore Reports (Internal Only)

Prefixing a report `name` with `__` makes the detection visible to chained D&R rules but NOT sent to outputs:

```yaml
- action: report
  name: __intermediate-signal
```

This is useful for multi-stage detection pipelines that shouldn't generate external alerts at intermediate stages.

### The `publish` Flag

`publish: true` (default) sends the detection to outputs. `publish: false` keeps it internal — visible to detection chaining but not stored or forwarded.

## Deployment Target

Detect sensor lifecycle events: `enrollment`, `sensor_clone`, `sensor_over_quota`, `deleted_sensor`.

```yaml
# Auto-fix cloned sensors on Windows
target: deployment
event: sensor_clone
op: is windows
```

## Artifact Target

Run detection logic against parsed artifact content (logs, PCAP, WEL). Only supports the `report` action.

Special parameters: `artifact type` (txt, pcap, zeek, wel, auth), `artifact path` (path prefix match), `artifact source` (source hostname match).

```yaml
target: artifact
artifact type: txt
artifact path: /var/log/auth.log
op: matches
re: .*(authentication failure|Failed password).*
path: /text
case sensitive: false
```

## Schedule Target

Timed events triggered at intervals per-organization or per-sensor. Useful for periodic checks.

## Billing Target

Billing and quota events. Useful for usage threshold alerts (e.g., alert when extension usage exceeds a budget).

---

# Response Actions Deep Dive

## Report Action

```yaml
- action: report
  name: my-detection-name
  publish: true       # defaults to true — set false to keep internal
  priority: 3         # integer, added to detection as `priority`
  metadata:           # free-form, added as `detect_mtd`
    author: security-team
  detect_data:        # free-form, added as structured IOCs
    hash: '{{ .event.HASH }}'
```

The `name`, `metadata`, and `detect_data` parameters support template strings. The template context is the **detection itself**, so use `.detect.event.USER_NAME`, not `.event.USER_NAME`.

## Tag Actions

```yaml
- action: add tag
  tag: vip
  ttl: 300            # optional, seconds until tag expires
  entire_device: true  # optional, applies to ALL sensors sharing Device ID
```

**Gotcha**: `entire_device: true` applies the tag to every sensor with the same Device ID, not just the current sensor. Useful for cross-sensor coordination (e.g., start full PCAP on all sensors on a device).

## Sensor Variables (`add var` / `del var`)

Variables are per-sensor key-value stores that allow D&R rules to share state across different rules on the same sensor. See the sensor-variables documentation for patterns.

```yaml
- action: add var
  name: recently-seen-paths
  value: <<event/FILE_PATH>>
  ttl: 300
```

Read variables in detection rules using `[[variable_name]]` syntax:

```yaml
op: is
path: event/FILE_PATH
value: '[[recently-seen-paths]]'
```

Limits: 16 variable names per sensor, 32 values per variable.

## Network Isolation

**`isolate network`** is persistent — survives reboots. Sets a cloud flag that re-isolates the sensor on reconnect. Only allows traffic to LimaCharlie cloud.

**`segregate_network`** (sensor command via `task`) is stateless — resets on reboot.

Always prefer `isolate network` (D&R action) over `segregate_network` (sensor command) for reliable isolation.

## Wait Action

```yaml
- action: wait
  duration: 10s
```

**Gotcha**: `wait` blocks processing of ALL events from that sensor for the specified duration. D&R rules run at wire-speed and in-order, so a 60-second wait means 60 seconds of events queue up.

## Extension Request

```yaml
- action: extension request
  extension name: dumper
  extension action: dump
  extension request:
    sid: '{{ .routing.sid }}'
```

The `extension request` parameter is a template transform. Use `based on report: true` to base the transform on the latest `report` action's output instead of the original event (requires a `report` action before it).

---

# Managed Rulesets

## Soteria EDR Rules

Professional detection rules covering Windows, Linux, and macOS with MITRE ATT&CK mapping. LimaCharlie acts as broker — Soteria never accesses your data. Rules cannot be edited.

**Required events for Soteria EDR**: `CODE_IDENTITY`, `DNS_REQUEST`, `EXISTING_PROCESS`, `FILE_CREATE`, `FILE_MODIFIED`, `MODULE_LOAD`, `NETWORK_CONNECTIONS`, `NEW_DOCUMENT`, `NEW_NAMED_PIPE`, `NEW_PROCESS`, `REGISTRY_WRITE`, `REGISTRY_CREATE`, `SENSITIVE_PROCESS_ACCESS`, `THREAD_INJECTION`

## Community Rules

AI-converted rules from Sigma, Anvilogic, Panther, Okta. Searchable by CVE, keyword, or MITRE ATT&CK ID. Available from Automation → Rules → Add Rule → Community Library.

---

# Naming Conventions

Rules: `[category]-[description]` (e.g., `lateral-movement-psexec`, `ransomware-vssadmin-delete`)

FP Rules: `fp-[category]-[pattern]-[YYYYMMDD]` (e.g., `fp-suspicious-process-sccm-server-20250415`)

# Gotchas Summary

| Gotcha | Detail |
|--------|--------|
| Stateful rule state resets on change | Changing detection logic resets all tracking — parent events must re-occur |
| Events are FIFO per sensor | One slow rule (wait, external lookup) blocks all subsequent events from that sensor |
| `publish: false` keeps detections internal | Visible to chaining but not stored or forwarded to outputs |
| IR mode limits D&R to 4 event types | When `ir` tag is applied: only `CODE_IDENTITY`, `DNS_REQUEST`, `NETWORK_CONNECTIONS`, `NEW_PROCESS` |
| FP rules operate on detection output | Paths reference detection fields (`cat`, `detect/event/*`), not raw event fields |
| Suppression key is an AND | All keys together form one uniqueness key — missing components create separate buckets |
| `.mtd` key naming | Special chars replaced by underscores: `lcr://api/ip-geo` → `.mtd.lcr___api_ip_geo` |
| Cardinality needs two rules | Dedup + count pattern requires chaining via `detection` target |
| `wait` blocks sensor processing | Events queue during wait — use sparingly |
| Suppression windows are fixed | Reset on expiry, not rolling/sliding |
