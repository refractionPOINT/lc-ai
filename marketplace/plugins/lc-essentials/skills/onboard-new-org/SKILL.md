---
name: onboard-new-org
description: Complete organization onboarding wizard for LimaCharlie. Discovers local cloud CLIs (GCP, AWS, Azure, DigitalOcean), surveys cloud projects, identifies VMs for EDR installation and security-relevant log sources (IAM, audit logs, network logs). Guides EDR deployment via OS Config (GCP), SSM (AWS), VM Run Command (Azure). Creates cloud adapters for log ingestion. Confirms sensor connectivity and data flow. Use when setting up new tenants, connecting cloud infrastructure, deploying EDR fleet-wide, or onboarding hybrid environments.
allowed-tools:
  - Task
  - Read
  - Bash
  - Skill
  - AskUserQuestion
  - WebFetch
  - WebSearch
  - Glob
  - Grep
---

# Onboard New Organization

A comprehensive onboarding wizard that discovers cloud infrastructure, identifies assets for monitoring, and guides through EDR deployment and log source integration for LimaCharlie organizations.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### API Access Pattern

All LimaCharlie API calls go through the `limacharlie-api-executor` sub-agent:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: <function-name>
    - Parameters: {<params>}
    - Return: RAW | <extraction instructions>
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **MCP Access** | Call `mcp__*` directly | Use `limacharlie-api-executor` sub-agent |
| **LCQL Queries** | Write query syntax manually | Use `generate_lcql_query()` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `list_user_orgs` if needed) |

---

## When to Use

Use this skill when:

- **Setting up a new LimaCharlie organization**: Full onboarding of cloud infrastructure
- **Connecting cloud platforms**: GCP, AWS, Azure, DigitalOcean, or other cloud providers
- **Deploying EDR to cloud VMs**: Mass deployment of LimaCharlie agents
- **Onboarding hybrid environments**: Mix of cloud VMs and log sources
- **Expanding monitoring coverage**: Adding new cloud projects or accounts

Common scenarios:
- "I want to onboard my AWS environment to LimaCharlie"
- "Set up monitoring for all my GCP VMs"
- "Connect my Azure audit logs and deploy EDR to my VMs"
- "I have a new organization, help me set everything up"
- "What can I monitor from my cloud infrastructure?"

## What This Skill Does

This skill performs a complete onboarding workflow:

1. **Organization Selection**: Select target LimaCharlie organization
2. **Cloud CLI Discovery**: Detect installed and authenticated cloud CLIs
3. **Infrastructure Survey**: Discover projects, VMs, and security-relevant services
4. **Onboarding Plan**: Suggest what should be monitored (with user confirmation)
5. **Cloud Adapter Setup**: Create adapters for log sources (via adapter-assistant)
6. **EDR Deployment**: Install agents on VMs using cloud-native methods
7. **Verification**: Confirm sensors online and data flowing
8. **Final Report**: Generate comprehensive onboarding summary

### Supported Cloud Platforms

| Platform | CLI | VM Deployment Method | Log Sources |
|----------|-----|---------------------|-------------|
| **GCP** | gcloud | OS Config | Cloud Audit Logs, VPC Flow Logs, Cloud Armor, IAM logs |
| **AWS** | aws | SSM Run Command | CloudTrail, VPC Flow Logs, GuardDuty, IAM logs |
| **Azure** | az | VM Run Command | Activity Log, Azure AD, NSG Flow Logs, Key Vault |
| **DigitalOcean** | doctl | SSH (manual) | Audit logs (API-based) |

## Workflow Phases

### Phase 0: Organization Selection

Ask user to select the target LimaCharlie organization:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

Present available organizations and use AskUserQuestion to let user select one.

### Phase 1: Cloud CLI Discovery

Detect installed and authenticated cloud CLIs:

```bash
# GCP
which gcloud && gcloud auth list 2>/dev/null | grep -q ACTIVE && echo "GCP: authenticated"

# AWS
which aws && aws sts get-caller-identity 2>/dev/null && echo "AWS: authenticated"

# Azure
which az && az account show 2>/dev/null && echo "Azure: authenticated"

# DigitalOcean
which doctl && doctl account get 2>/dev/null && echo "DigitalOcean: authenticated"
```

Present discovered CLIs and ask user which platforms to onboard:

```
AskUserQuestion(
  questions=[{
    "question": "Which cloud platforms would you like to onboard?",
    "header": "Platforms",
    "multiSelect": true,
    "options": [
      {"label": "GCP", "description": "Google Cloud Platform"},
      {"label": "AWS", "description": "Amazon Web Services"},
      {"label": "Azure", "description": "Microsoft Azure"},
      {"label": "DigitalOcean", "description": "DigitalOcean"}
    ]
  }]
)
```

### Phase 2: Infrastructure Survey

For each selected platform, discover projects/accounts and resource types.

#### GCP Survey

```bash
# List projects
gcloud projects list --format="json"

# For each project, check enabled APIs
gcloud services list --project=PROJECT_ID --enabled --format="json"
```

Key services to check for security relevance:
- `logging.googleapis.com` - Cloud Logging (audit logs available)
- `compute.googleapis.com` - Compute Engine VMs
- `container.googleapis.com` - GKE clusters
- `iam.googleapis.com` - IAM (identity logs)
- `cloudresourcemanager.googleapis.com` - Organization-level audit
- `cloudasset.googleapis.com` - Asset inventory

#### AWS Survey

```bash
# Get current account
aws sts get-caller-identity --output json

# List regions with activity
aws ec2 describe-regions --output json

# For each region, list EC2 instances
aws ec2 describe-instances --region REGION --output json

# Check CloudTrail status
aws cloudtrail describe-trails --output json
```

Key services:
- EC2 instances (for EDR)
- CloudTrail (audit logs)
- GuardDuty (threat detection)
- VPC Flow Logs
- IAM (identity events)

#### Azure Survey

```bash
# List subscriptions
az account list --output json

# For each subscription, list resource groups
az group list --subscription SUB_ID --output json

# List VMs
az vm list --subscription SUB_ID --output json

# Check diagnostic settings
az monitor diagnostic-settings list --resource RESOURCE_ID --output json
```

Key services:
- Virtual Machines (for EDR)
- Activity Log (audit events)
- Azure AD / Entra ID (identity)
- NSG Flow Logs (network)
- Key Vault audit logs

#### DigitalOcean Survey

```bash
# List droplets
doctl compute droplet list --format json

# List projects
doctl projects list --format json
```

### Phase 3: Resource Discovery and Classification

After surveying, categorize discovered resources:

#### Virtual Machines (EDR Targets)

Present discovered VMs with OS information:

| Platform | Instance ID | Name | OS | Zone/Region | Status |
|----------|-------------|------|----|-----------:|--------|
| GCP | instance-1 | web-server | Ubuntu 22.04 | us-central1-a | RUNNING |
| AWS | i-abc123 | api-server | Amazon Linux 2 | us-east-1 | running |
| Azure | vm-001 | database | Windows Server 2022 | eastus | running |

Ask user to confirm which VMs should have EDR installed:

```
AskUserQuestion(
  questions=[{
    "question": "Which VMs should have the LimaCharlie EDR installed?",
    "header": "VMs",
    "multiSelect": true,
    "options": [
      {"label": "All Linux VMs (Recommended)", "description": "Install EDR on all discovered Linux VMs"},
      {"label": "All Windows VMs", "description": "Install EDR on all discovered Windows VMs"},
      {"label": "Production VMs only", "description": "Only VMs tagged as production"},
      {"label": "Let me select individually", "description": "Choose specific VMs"}
    ]
  }]
)
```

#### Security-Relevant Log Sources

Identify log sources with security value:

| Priority | Source | Platform | Type | Description |
|----------|--------|----------|------|-------------|
| High | CloudTrail | AWS | Audit | API activity, authentication |
| High | Cloud Audit Logs | GCP | Audit | Admin and data access logs |
| High | Azure Activity Log | Azure | Audit | Control plane operations |
| High | Azure AD Sign-ins | Azure | Identity | Authentication events |
| Medium | VPC Flow Logs | AWS/GCP | Network | Network traffic metadata |
| Medium | GuardDuty | AWS | Threat Intel | AWS threat findings |
| Medium | NSG Flow Logs | Azure | Network | Network traffic |
| Low | Custom app logs | Various | Application | App-specific logging |

Ask user to confirm log sources:

```
AskUserQuestion(
  questions=[{
    "question": "Which log sources should be ingested into LimaCharlie?",
    "header": "Log Sources",
    "multiSelect": true,
    "options": [
      {"label": "All high-priority sources (Recommended)", "description": "Audit logs and identity events"},
      {"label": "High + Medium priority", "description": "Include network flow logs"},
      {"label": "All discovered sources", "description": "Everything including application logs"},
      {"label": "Let me select individually", "description": "Choose specific log sources"}
    ]
  }]
)
```

### Phase 4: Installation Key Creation

Create installation keys for each logical segment:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: create_installation_key
    - Parameters: {
        \"oid\": \"<org-id>\",
        \"description\": \"GCP VMs - Project X\",
        \"tags\": [\"gcp\", \"project-x\", \"auto-onboarded\"]
      }
    - Return: RAW
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

Create separate keys for:
- Each cloud platform
- Each major project/subscription
- Windows vs Linux (for easier management)

### Phase 5: Cloud Adapter Setup

For each confirmed log source, invoke the adapter-assistant skill:

```
Skill("adapter-assistant")
```

The adapter-assistant handles:
- Determining adapter type (Cloud Sensor, External Adapter, On-prem)
- Researching configuration requirements
- Creating necessary credentials/permissions
- Deploying the adapter
- Validating data flow

#### GCP Cloud Audit Logs Setup

1. Create Pub/Sub topic and subscription
2. Create logging sink to Pub/Sub
3. Configure LimaCharlie Cloud Sensor for GCP Pub/Sub

#### AWS CloudTrail Setup

1. Create S3 bucket (if not existing)
2. Configure CloudTrail to S3
3. Configure LimaCharlie Cloud Sensor for S3

#### Azure Activity Log Setup

1. Create Event Hub namespace
2. Configure diagnostic settings to Event Hub
3. Configure LimaCharlie Cloud Sensor for Event Hub

### Phase 6: EDR Deployment

Deploy EDR to confirmed VMs using cloud-native deployment methods.

> **CRITICAL - No Reboots or Interruptions**
> - NEVER use deployment methods that require host reboots (e.g., user data scripts, startup scripts)
> - NEVER use methods that would interrupt or disrupt running workloads
> - ONLY use live installation methods: OS Config (GCP), SSM Run Command (AWS), VM Run Command (Azure), or direct SSH
> - The LimaCharlie sensor installs without requiring a reboot - use methods that execute immediately on running systems

#### Pre-requisites

Read EDR installation documentation:
```
WebFetch(
  url="https://raw.githubusercontent.com/refractionPOINT/documentation/docs/windows-agent-installation/docs/limacharlie/doc/Sensors/installation.md",
  prompt="Extract installation commands for Windows and Linux"
)
```

#### GCP: OS Config Deployment

```bash
# Create OS Config policy for Linux
gcloud compute os-config os-policy-assignments create lc-edr-linux \
  --project=PROJECT_ID \
  --location=ZONE \
  --file=os-policy-linux.yaml

# OS Policy content
cat > os-policy-linux.yaml << 'EOF'
osPolicies:
  - id: install-limacharlie
    mode: ENFORCEMENT
    resourceGroups:
      - resources:
          - id: download-installer
            exec:
              validate:
                interpreter: SHELL
                script: |
                  pgrep -x rphcp > /dev/null
              enforce:
                interpreter: SHELL
                script: |
                  curl -o /tmp/lc-installer https://downloads.limacharlie.io/sensor/linux/64
                  chmod +x /tmp/lc-installer
                  /tmp/lc-installer -i INSTALLATION_KEY
                  rm /tmp/lc-installer
    allowNoResourceGroupMatch: false
instanceFilter:
  inclusionLabels:
    - labels:
        lc-edr: "true"
EOF
```

For Windows, use similar OS Config with PowerShell:
```powershell
# Validate: check if service is running
if (Get-Service -Name "rphcpsvc" -ErrorAction SilentlyContinue | Where-Object {$_.Status -eq "Running"}) { exit 0 } else { exit 1 }

# Enforce: download and install
Invoke-WebRequest -Uri "https://downloads.limacharlie.io/sensor/windows/64" -OutFile "$env:TEMP\lc-installer.exe"
Start-Process -FilePath "$env:TEMP\lc-installer.exe" -ArgumentList "-i", "INSTALLATION_KEY" -Wait
Remove-Item "$env:TEMP\lc-installer.exe"
```

#### AWS: SSM Run Command Deployment

```bash
# For Linux instances
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:lc-edr,Values=true" \
  --parameters 'commands=[
    "curl -o /tmp/lc-installer https://downloads.limacharlie.io/sensor/linux/64",
    "chmod +x /tmp/lc-installer",
    "/tmp/lc-installer -i INSTALLATION_KEY",
    "rm /tmp/lc-installer"
  ]' \
  --region REGION

# For Windows instances
aws ssm send-command \
  --document-name "AWS-RunPowerShellScript" \
  --targets "Key=tag:lc-edr,Values=true" \
  --parameters 'commands=[
    "Invoke-WebRequest -Uri \"https://downloads.limacharlie.io/sensor/windows/64\" -OutFile \"$env:TEMP\\lc-installer.exe\"",
    "Start-Process -FilePath \"$env:TEMP\\lc-installer.exe\" -ArgumentList \"-i\", \"INSTALLATION_KEY\" -Wait",
    "Remove-Item \"$env:TEMP\\lc-installer.exe\""
  ]' \
  --region REGION
```

#### Azure: VM Run Command Deployment

```bash
# For Linux VMs
az vm run-command invoke \
  --resource-group RESOURCE_GROUP \
  --name VM_NAME \
  --command-id RunShellScript \
  --scripts '
    curl -o /tmp/lc-installer https://downloads.limacharlie.io/sensor/linux/64
    chmod +x /tmp/lc-installer
    /tmp/lc-installer -i INSTALLATION_KEY
    rm /tmp/lc-installer
  '

# For Windows VMs
az vm run-command invoke \
  --resource-group RESOURCE_GROUP \
  --name VM_NAME \
  --command-id RunPowerShellScript \
  --scripts '
    Invoke-WebRequest -Uri "https://downloads.limacharlie.io/sensor/windows/64" -OutFile "$env:TEMP\lc-installer.exe"
    Start-Process -FilePath "$env:TEMP\lc-installer.exe" -ArgumentList "-i", "INSTALLATION_KEY" -Wait
    Remove-Item "$env:TEMP\lc-installer.exe"
  '
```

#### Deployment Tracking

After initiating deployments, wait for completion:

```bash
# GCP: Check OS Config assignment status
gcloud compute os-config os-policy-assignments describe lc-edr-linux \
  --project=PROJECT_ID \
  --location=ZONE

# AWS: Check SSM command status
aws ssm list-command-invocations --command-id COMMAND_ID

# Azure: Check run command status (synchronous - waits for completion)
```

### Phase 7: Verification

#### EDR Sensor Verification

Wait up to 2 minutes for sensors to appear, then verify:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {
        \"oid\": \"<org-id>\",
        \"selector\": \"iid == \\`<installation-key-iid>\\`\"
      }
    - Return: Count and hostnames of new sensors
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

Verify sensors are online:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {
        \"oid\": \"<org-id>\",
        \"selector\": \"iid == \\`<installation-key-iid>\\`\",
        \"online_only\": true
      }
    - Return: Count and hostnames of online sensors
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

Verify data is flowing (check for recent events):

```bash
# Calculate timestamps
start=$(date -d '5 minutes ago' +%s)
end=$(date +%s)
```

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_historic_events
    - Parameters: {
        \"oid\": \"<org-id>\",
        \"sid\": \"<sensor-id>\",
        \"start\": <start>,
        \"end\": <end>,
        \"limit\": 10
      }
    - Return: Count of events and event types
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

#### Cloud Adapter Verification

For each cloud adapter, verify sensor appears and data flows:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_cloud_sensors
    - Parameters: {\"oid\": \"<org-id>\"}
    - Return: RAW
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

Check for recent events from cloud sensor:

```bash
start=$(date -d '10 minutes ago' +%s)
end=$(date +%s)
```

Use LCQL to query for specific sensor data:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: generate_lcql_query
    - Parameters: {
        \"oid\": \"<org-id>\",
        \"prompt\": \"Find events from sensor with hostname containing 'cloudtrail' in the last 10 minutes\",
        \"time_window\": \"10m\"
      }
    - Return: RAW
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

### Phase 8: Final Report

Generate a comprehensive Markdown report:

```markdown
# Onboarding Report: [Organization Name]

**Date**: [Date]
**Organization ID**: [OID]

## Summary

| Metric | Count |
|--------|-------|
| Cloud Platforms Discovered | N |
| VMs Targeted for EDR | N |
| EDR Sensors Online | N |
| Log Sources Configured | N |
| Adapters Created | N |

## EDR Deployment

### Installation Keys Created

| Key Description | IID | Tags | VMs Using |
|-----------------|-----|------|-----------|
| GCP Linux VMs | abc-123 | gcp, linux | 5 |
| AWS Windows VMs | def-456 | aws, windows | 3 |

### Sensors Deployed

| Hostname | Platform | Status | Data Flowing |
|----------|----------|--------|--------------|
| web-server-1 | linux | Online | Yes |
| db-server-1 | linux | Online | Yes |
| win-server-1 | windows | Offline | Pending |

### Deployment Issues

- win-server-1: SSM agent not responding - requires manual installation

## Cloud Log Sources

### Adapters Created

| Adapter Name | Type | Source | Status |
|--------------|------|--------|--------|
| gcp-audit-logs | Cloud Sensor | GCP Pub/Sub | Active |
| aws-cloudtrail | Cloud Sensor | S3 | Active |

### Data Flow Status

| Source | Last Event | Event Count (1h) |
|--------|------------|------------------|
| gcp-audit-logs | 2 min ago | 423 |
| aws-cloudtrail | 5 min ago | 156 |

## Credentials and Access

### Service Accounts Created

| Platform | Account | Purpose |
|----------|---------|---------|
| GCP | lc-pubsub-reader@proj.iam | Pub/Sub subscription read |
| AWS | LimaCharlieS3Reader | CloudTrail S3 bucket read |

### Secrets Stored in LimaCharlie

| Secret Name | Purpose |
|-------------|---------|
| gcp-service-account | GCP service account key |
| aws-access-key | AWS access credentials |

## Recommended Next Steps

1. **Configure Detection Rules**: Set up D&R rules for the new log sources
2. **Review Sensor Coverage**: Ensure all critical assets have EDR
3. **Set Up Outputs**: Configure SIEM forwarding if needed
4. **Enable Extensions**: Consider enabling threat intel extensions

## Commands for Reference

### Check Sensor Status
```bash
# Using LimaCharlie CLI
limacharlie sensor list --org [OID] --tag auto-onboarded
```

### Troubleshooting
- If EDR sensors don't appear: Check firewall rules for outbound HTTPS
- If adapters show errors: Verify credentials in Secrets

---
Generated by LimaCharlie Onboard New Org Skill
```

## Error Handling

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| CLI not authenticated | Token expired | Run `gcloud auth login`, `aws configure`, etc. |
| Permission denied | Insufficient IAM roles | Check required permissions below |
| VM deployment failed | SSM agent not running | Install SSM agent first |
| Sensor not appearing | Firewall blocking | Check outbound HTTPS to *.limacharlie.io |

### Required Permissions

#### GCP
- `compute.instances.list` - List VMs
- `osconfig.osPolicyAssignments.create` - Deploy OS Config
- `pubsub.topics.create` - Create Pub/Sub topics
- `logging.sinks.create` - Create log sinks

#### AWS
- `ec2:DescribeInstances` - List EC2 instances
- `ssm:SendCommand` - Run SSM commands
- `s3:GetObject` - Read CloudTrail logs
- `cloudtrail:DescribeTrails` - List CloudTrail configuration

#### Azure
- `Microsoft.Compute/virtualMachines/read` - List VMs
- `Microsoft.Compute/virtualMachines/runCommand/action` - Run commands
- `Microsoft.EventHub/namespaces/read` - Event Hub access

## Related Skills

- `adapter-assistant` - For detailed adapter configuration
- `sensor-coverage` - For monitoring sensor health after onboarding
- `detection-engineering` - For creating detection rules
- `limacharlie-call` - For direct API operations

## Reference

- EDR Installation: https://doc.limacharlie.io/docs/sensors/
- Cloud Sensors: https://doc.limacharlie.io/docs/sensors/cloud-sensors/
- Adapters: https://doc.limacharlie.io/docs/sensors/adapters/
