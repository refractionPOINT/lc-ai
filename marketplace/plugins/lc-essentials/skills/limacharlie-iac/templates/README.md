# LimaCharlie Infrastructure as Code

This repository manages LimaCharlie organization configurations using Infrastructure as Code.

## Structure

```
├── org-manifest.yaml       # Friendly name → OID mapping
├── hives/                  # Global configs (all tenants)
│   ├── dr-general.yaml     # Detection rules
│   ├── fp.yaml             # False positive rules
│   ├── outputs.yaml        # Output destinations
│   ├── extensions.yaml     # Extensions
│   ├── integrity.yaml      # FIM rules
│   ├── artifact.yaml       # Artifact collection
│   ├── exfil.yaml          # Exfil monitoring
│   ├── resources.yaml      # Resources/payloads
│   └── installation_keys.yaml
├── orgs/                   # Per-tenant configs
│   └── <oid>/
│       ├── index.yaml      # Includes global + custom
│       └── custom/         # Tenant-specific configs
└── exports/                # ext-git-sync exports
```

## Usage with ext-git-sync

This repository is designed to work with LimaCharlie's `ext-git-sync` extension.

### Setup

1. Enable `ext-git-sync` extension in each organization
2. Create SSH deploy key and add to this repository
3. Store private key in each org's Secret Manager
4. Configure ext-git-sync with this repo's SSH URL
5. Enable "Recurring Apply" for automatic deployment

### Manual Deployment

```bash
limacharlie configs push \
  --oid <oid> \
  --config ./orgs/<oid>/index.yaml \
  --force \
  --hive-dr-general \
  --hive-fp \
  --outputs \
  --integrity \
  --artifact \
  --exfil \
  --resources \
  --extensions \
  --installation-keys
```

## Managed by limacharlie-iac Skill

This repository is managed by the `limacharlie-iac` Claude Code skill. Common commands:

- "Add tenant acme-corp" - Add organization to IaC
- "Add global rule for X" - Add detection to all tenants
- "Import rule Y from acme-corp" - Import existing rule
- "Promote rule Z to global" - Make tenant rule apply to all

## Secrets

Never commit plaintext secrets. Use LimaCharlie Secret Manager references:

```yaml
outputs:
  slack:
    slack_api_token: hive://secret/slack-token
```
