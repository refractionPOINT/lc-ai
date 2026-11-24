---
name: iac
description: LimaCharlie Infrastructure as Code — ext-git-sync repository structure, sync push/pull, global vs tenant-specific configs, importing and promoting rules across tenants. Use when managing multi-tenant configurations via git, setting up ext-git-sync, or syncing org configs.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Infrastructure as Code

How to manage LimaCharlie configurations using git-based Infrastructure as Code, compatible with the `ext-git-sync` extension.

## Repository Structure

```
my-lc-iac/
├── org-manifest.yaml              # Friendly name -> OID mapping
├── hives/                         # Global configs (all tenants)
│   ├── dr-general.yaml            # D&R rules
│   ├── fp.yaml                    # False positive rules
│   ├── outputs.yaml               # Output destinations
│   ├── extensions.yaml            # Extensions to enable
│   ├── integrity.yaml             # FIM rules
│   ├── artifact.yaml              # Artifact collection
│   ├── exfil.yaml                 # Exfil monitoring
│   ├── resources.yaml             # Resources/payloads
│   └── installation_keys.yaml     # Sensor install keys
├── orgs/                          # Per-tenant configs
│   └── <oid>/
│       ├── index.yaml             # Includes global + custom
│       └── custom/                # Tenant-specific overrides
│           ├── rules.yaml
│           └── fim.yaml
└── exports/                       # ext-git-sync exports
```

## YAML Format

All config files use version 3 format:

```yaml
version: 3
hives:
  dr-general:
    rule-name:
      data:
        detect:
          event: NEW_PROCESS
          op: contains
          path: event/COMMAND_LINE
          value: "-enc"
        respond:
          - action: report
            name: encoded-powershell
      usr_mtd:
        enabled: true
        expiry: 0
        tags: []
```

### org-manifest.yaml

Maps friendly names to OIDs (ext-git-sync requires OID folder names):

```yaml
version: 1
orgs:
  acme-corp:
    oid: 7e41e07b-c44c-43a3-b78d-41f34204789d
    description: "Acme Corporation - Production"
    added: "2025-11-30"
```

### index.yaml (per org)

References global configs via relative includes, plus custom overrides:

```yaml
version: 3
include:
  - ../../hives/extensions.yaml
  - ../../hives/dr-general.yaml
  - ../../hives/fp.yaml
  - ../../hives/outputs.yaml
  - ../../hives/integrity.yaml
  # Custom configs (uncomment as needed)
  # - custom/rules.yaml
```

## ext-git-sync Setup

### Subscribe

```bash
limacharlie extension subscribe --name ext-git-sync --oid <oid>
```

### Configure

```bash
cat > /tmp/git-sync-config.yaml << 'EOF'
repo_url: "git@github.com:your-org/your-repo.git"
branch: "main"
conf_root: "orgs/<oid>/index.yaml"
ssh_key_source: "secret"
ssh_key_secret_name: "git-sync-ssh-key"
EOF
limacharlie extension config-set --name ext-git-sync --input-file /tmp/git-sync-config.yaml --oid <oid>
```

**Required fields:** `repo_url` (NOT `repository`), `branch`, `conf_root`, `ssh_key_source`, `ssh_key_secret_name`.

### Store SSH Key

```bash
limacharlie secret set --key git-sync-ssh-key --input-file /tmp/ssh-key.txt --oid <oid>
```

### Verify Setup

```bash
limacharlie extension list --oid <oid> --output yaml
limacharlie secret list --oid <oid> --output yaml
limacharlie extension config-get --name ext-git-sync --oid <oid> --output yaml
limacharlie org errors --oid <oid> --output yaml
```

## Manual Sync (CLI)

### Push (Local to Cloud)

```bash
limacharlie sync push --config-file ./orgs/<oid>/index.yaml --oid <oid> \
  --hive-dr-general --hive-fp --outputs --integrity --artifact --exfil \
  --resources --extensions --installation-keys
```

**Avoid `--force`** — it deletes cloud resources not present in the local config.

### Pull (Cloud to Local)

```bash
limacharlie sync pull --config-file <path> --oid <oid>
```

## Importing Rules from LC

```bash
# List existing rules
limacharlie dr list --oid <oid> --output yaml

# Get a specific rule
limacharlie dr get --key <rule-name> --oid <oid> --output yaml
```

Add the fetched rule to `hives/dr-general.yaml` (global) or `orgs/<oid>/custom/rules.yaml` (tenant-specific).

## Config Type Reference

| Config | Global File | Custom File | Sync Flag |
|--------|------------|-------------|-----------|
| D&R Rules | `hives/dr-general.yaml` | `custom/rules.yaml` | `--hive-dr-general` |
| FP Rules | `hives/fp.yaml` | `custom/fp.yaml` | `--hive-fp` |
| Outputs | `hives/outputs.yaml` | `custom/outputs.yaml` | `--outputs` |
| Extensions | `hives/extensions.yaml` | - | `--extensions` |
| FIM | `hives/integrity.yaml` | `custom/fim.yaml` | `--integrity` |
| Artifact Collection | `hives/artifact.yaml` | - | `--artifact` |
| Exfil Monitoring | `hives/exfil.yaml` | - | `--exfil` |
| Resources | `hives/resources.yaml` | - | `--resources` |
| Installation Keys | `hives/installation_keys.yaml` | - | `--installation-keys` |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `repo_url is required` | Use `repo_url`, not `repository` |
| `ssh_key is required` | Verify secret exists: `limacharlie secret list` |
| `conf_root not found` | Use full path: `orgs/<oid>/index.yaml` |
| SSH auth failure | Check deploy key in GitHub, verify public key |
| Sync runs but no changes | Verify `branch` matches repo's default branch |
| Include path not found | Check relative path from index.yaml location |

## Best Practices

- Use branches for changes, merge to main for deployment
- Let ext-git-sync handle deployment from main branch
- Never commit plaintext secrets — use `hive://secret/<name>`
- Test on one org before rolling out globally
- Use `--dry-run` on sync push before actual deployment
