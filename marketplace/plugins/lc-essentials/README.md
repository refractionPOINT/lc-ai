# LimaCharlie Essentials Plugin

Essential LimaCharlie skills for CLI-based API access, sensor management, detection engineering, and security operations. Includes 124 comprehensive skills covering core operations, historical data, forensics, detection rules, threat intelligence analysis, MSSP multi-tenant reporting, configuration management, and administration.

## Important: Organization ID (OID) Requirements

**⚠️ OID is a UUID, not an Organization Name**

Most skills in this plugin require an **Organization ID (OID)**, which is a UUID like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`, **NOT** the human-readable organization name.

**To get your OID:**
```
Use the `list-user-orgs` skill to see all organizations you have access to and their corresponding OIDs.
```

This skill returns a mapping of organization names to their UUIDs, which you'll need for most other operations.

**Exception - Skills that don't require a specific OID:**

A small number of skills operate at the user-level or global level and **do not require a specific organization ID**. For these skills, **omit the `oid` parameter` when calling the API:

- **`list-user-orgs`** - Lists all organizations you have access to (user-level operation)
- **`create-org`** - Creates a new organization (user-level operation)
- **`get-platform-names`** - Gets list of platform names from ontology (global operation)

All other 119 skills require a valid, specific organization ID.

## Important: EDR Agent Platform Limitation

**⚠️ LimaCharlie EDR Agents Only Run on Windows, Linux, macOS, and Chrome OS**

LimaCharlie EDR agents provide full system inspection capabilities (processes, registry, file system, network connections, etc.) but are **only available on Windows, Linux, macOS, and Chrome OS platforms**.

**Do NOT attempt to query system-level information from non-EDR sensors:**
- Cloud sensors (Azure, AWS, GCP, Office 365, etc.) - Log ingestion only
- External adapters (webhook receivers, syslog, API integrations) - Log ingestion only
- USP adapters (on-premises log forwarders) - Log ingestion only

These non-EDR sensors only provide **log ingestion capabilities** and cannot respond to system inspection commands like:
- Get running processes
- Query Windows registry
- List file system contents
- Show network connections
- Scan memory with YARA

Always verify the sensor type before attempting system-level queries. EDR sensors will have platforms like `windows`, `linux`, `macos`, or `chrome`, while non-EDR sensors will show platform types related to their cloud service or adapter type.

## What It Does

This plugin provides 124 comprehensive skills:

### Skills Organized by Category

### Core Operations & Documentation
- **Documentation Search**: Intelligent search through LimaCharlie docs (platform, Python SDK, Go SDK)
- **Organization Management**: List orgs, get org info, create orgs, manage API keys
- **Sensor Management**: List/search/delete sensors, get sensor info, check online status

### Event Schemas & Telemetry
- **Event Schemas**: Get schemas for event types, list available events by platform
- **Platform Support**: Get platform names and platform-specific event types

### Live Sensor Interaction
- **Process Investigation**: Get processes, modules, strings, YARA scan processes
- **Network Analysis**: Get network connections, investigate C2 communications
- **System Forensics**: Get OS version, users, services, drivers, autoruns, packages
- **File System**: List directories, find files by hash, string search across processes
- **Windows Registry**: Query registry keys and values (Windows sensors only)
- **YARA Scanning**: Scan processes, files, directories, and memory with YARA rules

### Detection & Response
- **D&R Rules**: List, get, create, update, delete detection rules (general and managed)
- **False Positive Rules**: Manage FP rules to suppress known-good detections
- **YARA Rules**: Manage organization-wide YARA rules for threat hunting
- **Rule Validation**: Validate D&R rule components and YARA syntax

### Historical Data & Investigation
- **Historic Events**: Query historical telemetry using LCQL
- **Historic Detections**: Search past detection hits
- **LCQL Queries**: Run LCQL queries, manage saved queries
- **IOC Search**: Search for IoCs (IPs, domains, hashes) across historical data
- **Host Search**: Search for hosts by hostname or other attributes

### Threat Intelligence & Analysis
- **Threat Report Evaluation**: Systematically evaluate threat reports, breach analyses, and IOC reports to search for compromise indicators, extract IOCs, perform searches, identify malicious behaviors, generate LCQL queries, and create D&R rules and lookups

### MSSP & Multi-Tenant Reporting
- **MSSP Reporting**: Generate comprehensive multi-tenant security and operational reports across 50+ customer organizations. Includes billing summaries, usage analytics, detection trends, sensor health monitoring, and configuration audits with strict data accuracy guardrails. Supports partial report generation when organizations fail, with transparent error documentation.

### Configuration & Integrations
- **Extensions**: List, get, create, update, delete extension configs
- **Outputs**: Manage output destinations (SIEM, cloud storage, webhooks)
- **External Adapters**: Configure cloud sensors and external data sources
- **Secrets**: Securely store and manage credentials for integrations
- **Lookups**: Manage lookup tables for enrichment

### Response & Tasking
- **Network Isolation**: Isolate/rejoin sensors from the network
- **Reliable Tasking**: Execute commands on sensors with guaranteed delivery
- **Playbooks**: Manage automated response playbooks

### Advanced Features
- **Installation Keys**: Create and manage sensor deployment keys
- **Tags**: Add/remove tags from sensors
- **Artifacts**: List and retrieve artifacts from investigations
- **MITRE ATT&CK**: Get MITRE ATT&CK coverage reports
- **Billing & Usage**: View usage stats, billing details, SKU definitions

## Specialized Skills & Agents

### Sensor Health Reporting

The **sensor-health** skill orchestrates parallel sensor health checks across multiple LimaCharlie organizations for fast, comprehensive fleet reporting.

**Architecture:**
- **Skill**: `sensor-health` - Orchestrates the workflow
- **Agent**: `sensor-health-reporter` - Checks a single organization (spawned in parallel, one per org)
- **Model**: Sonnet (fast and cost-effective)

**How It Works:**
1. Skill gets list of user's organizations
2. Skill spawns one `sensor-health-reporter` agent per org **in parallel**
3. Each agent checks its assigned organization independently
4. Skill aggregates results and presents unified report

**Key Features:**
- **Massive Parallelization**: Checks 10+ orgs simultaneously
- **Fast Execution**: Using Sonnet model + parallel agents = seconds, not minutes
- **Comprehensive**: Covers all organizations in your account
- **Flexible**: Handles various query types (connectivity, data availability, offline sensors)

**Supported Queries:**
- **Connectivity Issues**: "Show me sensors online but not sending data"
- **Offline Sensors**: "List sensors that haven't been online for 7 days"
- **Data Availability**: "Which sensors have no events in the last hour?"
- **Fleet Health**: "Find all offline sensors across my organizations"
- **Status Reports**: "Show me sensors with connectivity issues"

**Example Usage:**
```
"Show me sensors that are online but not reporting events in the last hour"
→ Skill spawns 12 parallel agents (one per org)
→ Each agent checks its org's sensors
→ Results aggregated into single report
→ Execution time: ~5-10 seconds for 12 orgs

"List all sensors offline for more than 7 days"
→ Checks sensor 'alive' timestamps across all orgs
→ Reports sensors that haven't checked in

"Which sensors in lc_demo haven't sent data today?"
→ Can target specific org if needed
```

**Performance:**
- Sequential approach: ~30-60 seconds for 12 orgs
- Parallel approach: ~5-10 seconds for 12 orgs
- Scales efficiently to dozens of organizations

## Usage Examples

### Getting Started
```
"List all my organizations" → Uses list-user-orgs
"Show me all sensors in my org" → Uses list-sensors
"Get event schema for DNS_REQUEST" → Uses get-event-schema
```

### Investigation
```
"Get running processes on sensor XYZ" → Uses get-processes
"Show network connections for sensor ABC" → Uses get-network-connections
"YARA scan process 1234 on sensor DEF" → Uses yara-scan-process
"Search for IP 1.2.3.4 in historical data" → Uses search-iocs
```

### Detection Engineering
```
"List all D&R rules" → Uses list-rules
"Create a new D&R rule for suspicious PowerShell" → Uses set-rule
"Get all detections from the last 24 hours" → Uses get-historic-detections
```

### Configuration
```
"Configure Slack output" → Uses add-output
"Create installation key for production deployment" → Uses create-installation-key
"Set up cloud sensor for AWS CloudTrail" → Uses set-cloud-sensor
```

## How It Works

Skills in this plugin connect to the LimaCharlie API via the `limacharlie` CLI to:

1. **Authenticate** using your LimaCharlie API credentials
2. **Execute operations** against your organization(s)
3. **Return results** in a structured, readable JSON format

Most skills require:
- **OID**: Organization ID (UUID) - get this via `limacharlie org list --output json`
- **Additional parameters**: Sensor IDs, rule names, query parameters, etc.

See [CALLING_API.md](./CALLING_API.md) for details on CLI usage patterns.

## Documentation Coverage

- **Platform Documentation**: Complete LimaCharlie platform docs
- **Python SDK**: Python SDK reference and examples
- **Go SDK**: Go SDK reference and examples
- **API Reference**: Direct API access documentation

## Skills Summary

See [SKILLS_SUMMARY.md](./SKILLS_SUMMARY.md) for a complete list of all 121 skills with descriptions.

## API Calling Guide

See [CALLING_API.md](./CALLING_API.md) for comprehensive documentation on making direct API calls to LimaCharlie.
