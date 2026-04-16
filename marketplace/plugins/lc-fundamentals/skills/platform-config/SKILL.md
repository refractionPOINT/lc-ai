---
name: platform-config
description: Working with LimaCharlie platform configuration — Hive (generic config store), outputs, extensions, lookups, secrets, YARA rules, API keys, and permissions. The admin toolbox for platform configuration. Use when managing outputs, extensions, lookups, secrets, API keys, or any Hive-based configuration.
allowed-tools:
  - Bash
  - Read
---

# Platform Config

How to work with LimaCharlie's configuration layer — Hive, outputs, extensions, lookups, secrets, YARA rules, API keys, and permissions.

## Hive (Generic Config Store)

Hive provides a single CRUD API for all configuration records. Each record has an envelope (name, enabled flag, metadata) with JSON data.

### Generic Hive Operations

```bash
# List records in a hive
limacharlie hive list --hive-name <hive_type> --oid <oid> --output yaml

# Get a record
limacharlie hive get --hive-name <hive_type> --key <name> --oid <oid> --output yaml

# Set a record
limacharlie hive set --hive-name <hive_type> --key <name> --input-file /tmp/data.yaml --oid <oid> --output yaml

# Delete a record
limacharlie hive delete --hive-name <hive_type> --key <name> --confirm --oid <oid>

# Enable/disable a record
limacharlie hive enable --hive-name <hive_type> --key <name> --oid <oid>
limacharlie hive disable --hive-name <hive_type> --key <name> --oid <oid>
```

### Key Hive Types

| Hive Type | Description | Dedicated CLI |
|-----------|-------------|--------------|
| `dr-general` | Custom D&R rules | `limacharlie dr` |
| `fp` | False positive rules | `limacharlie fp` |
| `lookup` | Key-value lookups | `limacharlie lookup` |
| `secret` | Encrypted credentials | `limacharlie secret` |
| `yara` | YARA rules | `limacharlie yara` |
| `cloud-sensors` | Cloud adapter configs | `limacharlie cloud-adapter` |
| `query` | Saved LCQL queries | `limacharlie search saved-*` |
| `ai_agent` | AI agent configs | Via hive commands |
| `extension_config` | Extension configs | `limacharlie extension config-*` |
| `sop` | Standard operating procedures | `limacharlie sop` |
| `playbook` | Playbook definitions | Via hive commands |

**Prefer dedicated CLI commands** over generic hive commands when available.

## Outputs

Stream telemetry to external destinations.

```bash
# List outputs
limacharlie output list --oid <oid> --output yaml

# Create output (write config to file first)
cat > /tmp/output.yaml << 'EOF'
name: my-syslog
module: syslog
for: detect
dest_host: siem.example.com:514
EOF
limacharlie output create --input-file /tmp/output.yaml --oid <oid> --output yaml

# Delete output
limacharlie output delete --name <name> --confirm --oid <oid>
```

Each output subscribes to one or more streams: `event`, `detect`, `audit`, `deployment`.

## Extensions

Optional capabilities enabled per-org.

```bash
# List subscribed extensions
limacharlie extension list --oid <oid> --output yaml

# List ALL available extensions (marketplace — subscribed and unsubscribed)
limacharlie extension list-available --oid <oid> --output yaml

# Subscribe to an extension
limacharlie extension subscribe --name <ext-name> --oid <oid>

# Unsubscribe
limacharlie extension unsubscribe --name <ext-name> --oid <oid>

# Rotate an extension's API key
limacharlie extension rekey --name <ext-name> --oid <oid>

# List all extension configs
limacharlie extension config-list --oid <oid> --output yaml

# Get extension config
limacharlie extension config-get --name <ext-name> --oid <oid> --output yaml

# Set extension config
limacharlie extension config-set --name <ext-name> --input-file /tmp/config.yaml --oid <oid>

# Delete extension config
limacharlie extension config-delete --name <ext-name> --confirm --oid <oid>

# Get extension config schema
limacharlie extension schema --name <ext-name> --oid <oid> --output yaml

# Make extension request (invoke an action)
limacharlie extension request --name <ext-name> --action <action> --oid <oid> --output yaml
limacharlie extension request --name <ext-name> --action <action> --data '<json>' --oid <oid> --output yaml
```

Use `list-available` to discover what extensions exist before subscribing. Use `list` to check what's already subscribed in an org.

### Extension Config as Web UI Features

Several web UI features are configured as extension configs:

| Web UI Feature | Extension Name |
|----------------|---------------|
| Artifact Collection Rules | `ext-artifact` |
| File & Registry Integrity Monitoring | `ext-integrity` |
| EPP / Defender Integration | `ext-epp` |
| Exfil Watch | `ext-exfil` |

### Copying Extension Configs Between Orgs

1. Export: `limacharlie extension config-get --name <ext> --oid <source>`
2. Extract the `data:` section to a file
3. Import: `limacharlie extension config-set --name <ext> --input-file <file> --oid <target>`
4. Enable: `limacharlie hive enable --hive-name extension_config --key <ext> --oid <target>`

The target org must already be subscribed to the extension.

## Lookups

Key-value dictionaries queryable at runtime in D&R rules for enrichment and detection logic. Referenced in rules via the `lookup` operator with `resource: hive://lookup/<name>`.

### CLI Operations

```bash
# List lookups
limacharlie lookup list --oid <oid> --output yaml

# Get a lookup
limacharlie lookup get --key <name> --oid <oid> --output yaml

# Set a lookup
limacharlie lookup set --key <name> --input-file /tmp/lookup.yaml --oid <oid> --output yaml

# Delete a lookup
limacharlie lookup delete --key <name> --confirm --oid <oid>
```

### Lookup Data Formats

Lookups support three data formats in their payload:

| Format | Description | Use Case |
|--------|-------------|----------|
| `lookup_data` | Direct JSON `{ "key": { metadata } }` | Structured data with per-key metadata |
| `newline_content` | Keys separated by newlines (empty metadata) | Simple blocklists/allowlists |
| `yaml_content` | YAML string with dictionary keys and metadata | Human-readable configs |

### How Lookups Work in D&R Rules

When a D&R rule uses `op: lookup`, the value at `path` is looked up in the referenced resource. If the key exists, the rule matches and the **metadata dictionary** for that key is returned. The metadata is accessible in suppression keys via the `.mtd` namespace.

**Gotcha**: lookups return the metadata dict `{}` on match — if the key has no metadata, you get an empty dict. The match itself is the meaningful signal, not the returned value.

**Gotcha**: the `.mtd` key name for `hive://lookup/my-list` is `.mtd.my_list` (hyphens become underscores).

### Lookup Manager Extension

The Lookup Manager extension (`ext-lookup-manager`) auto-refreshes lookups every 24 hours from remote sources (URLs or ARLs). Pre-configured public lookups are available from the [lc-public-lookups GitHub repo](https://github.com/refractionpoint/lc-public-lookups), including Tor exit nodes, AlienVault IP reputation, and more.

### IaC Format

```yaml
hives:
  lookup:
    my-blocklist:
      data:
        lookup_data:
          8.8.8.8: {}
          1.1.1.1: { category: dns }
      usr_mtd:
        enabled: true
        expiry: 0
        tags: [blocklist]
```

## Secrets

Secure credential storage. Referenced via `hive://secret/<name>`.

```bash
# List secrets (shows names only, not values)
limacharlie secret list --oid <oid> --output yaml

# Set a secret
limacharlie secret set --key <name> --oid <oid>
# (prompts for value, or use --input-file)

# Delete a secret
limacharlie secret delete --key <name> --confirm --oid <oid>
```

## YARA Rules

YARA in LimaCharlie has two concepts: **sources** (where rules come from) and **rules** (compiled rule sets).

```bash
# List YARA sources
limacharlie yara sources-list --oid <oid> --output yaml

# Add a YARA source
limacharlie yara source-add --name <name> --source-file /tmp/source.yaml --oid <oid> --output yaml

# Get a YARA source
limacharlie yara source-get --name <name> --oid <oid> --output yaml

# Delete a YARA source
limacharlie yara source-delete --name <name> --oid <oid>

# List compiled YARA rules
limacharlie yara rules-list --oid <oid> --output yaml

# Add a YARA rule
limacharlie yara rule-add --name <name> --sources-file /tmp/rule.yar --oid <oid> --output yaml

# Delete a YARA rule
limacharlie yara rule-delete --name <name> --oid <oid>

# Scan a sensor with a YARA rule
limacharlie yara scan --sid <sid> --rule-file /tmp/rule.yar --oid <oid> --output yaml
```

## API Keys

```bash
# List API keys
limacharlie api-key list --oid <oid> --output yaml

# Create an API key
limacharlie api-key create --name <name> --permissions <perm1,perm2> --oid <oid> --output yaml

# Delete an API key
limacharlie api-key delete --key-hash <hash> --confirm --oid <oid>
```

## Permissions

### Check Auth and Permissions

```bash
# Check current auth
limacharlie auth whoami --output yaml

# Check specific permission (MUST include --oid)
limacharlie auth whoami --oid <oid> --check-perm ai_agent.operate --output yaml

# Show all permissions
limacharlie auth whoami --show-perms --oid <oid> --output yaml
```

**IMPORTANT:** `--check-perm` without `--oid` always returns `has_perm: false`.

## Organizations

```bash
# List accessible orgs
limacharlie org list --output yaml

# Get org info
limacharlie org info --oid <oid> --output yaml

# Get org usage stats
limacharlie org stats --oid <oid> --output yaml

# Check org errors
limacharlie org errors --oid <oid> --output yaml
```

## Billing

```bash
# Get billing details
limacharlie billing details --oid <oid> --output yaml

# Get invoice URL
limacharlie billing invoice-url --oid <oid> --output yaml
```

## Artifacts

Manage uploaded logs, memory dumps, and other forensic data.

```bash
# List artifacts
limacharlie artifact list --oid <oid> --output yaml

# List by type
limacharlie artifact list --type velociraptor --oid <oid> --output yaml

# Download an artifact
limacharlie artifact download --id <artifact_id> --output-path <path> --oid <oid>
```

## Playbooks

Python scripts that run in LimaCharlie's serverless execution environment with full SDK access. Triggered by D&R rules, the API, feedback responses, or other extensions.

```bash
# List playbooks
limacharlie playbook list --oid <oid> --output yaml

# Get a playbook
limacharlie playbook get --key <name> --oid <oid> --output yaml

# Create/update a playbook
limacharlie playbook set --key <name> --input-file /tmp/playbook.yaml --oid <oid> --output yaml

# Delete a playbook
limacharlie playbook delete --key <name> --confirm --oid <oid>

# Enable/disable
limacharlie playbook enable --key <name> --oid <oid>
limacharlie playbook disable --key <name> --oid <oid>
```

Playbook data contains a `python` field with the script source code. Requires the `ext-playbook` extension to be subscribed.

## Standard Operating Procedures (SOPs)

```bash
# List SOPs
limacharlie sop list --oid <oid> --output yaml

# Get SOP details
limacharlie sop get --key <name> --oid <oid> --output yaml
```

SOPs guide how tasks are performed. Before running operations, check if relevant SOPs exist.

## Infrastructure Sync

```bash
# Push local config to cloud
limacharlie sync push --config-file <path> --oid <oid>

# Pull cloud config to local
limacharlie sync pull --oid <oid>
```

**Avoid `--force`** on push unless certain — it deletes cloud resources not present in the local config file.

## Gotchas Summary

| Gotcha | Detail |
|--------|--------|
| REST API `usr_mtd` REPLACES entirely | Hive metadata updates via API replace the full metadata object, they don't merge. Always read current state first. |
| `--check-perm` needs `--oid` | `limacharlie auth whoami --check-perm X` without `--oid` always returns `has_perm: false` |
| Secret values are write-only | `secret list` shows names only, you cannot read back secret values |
| Prefer dedicated CLI over hive | Use `limacharlie dr`, `limacharlie fp`, `limacharlie lookup` etc. instead of generic `limacharlie hive` when available |
| Extension config = web UI features | Artifact collection, FIM, EPP, exfil are all extension configs, not separate APIs |
