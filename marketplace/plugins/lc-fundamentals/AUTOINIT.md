# LimaCharlie Platform Concepts

LimaCharlie is the Agentic SecOps Workspace. This document maps core platform concepts so you can identify what area of the platform a user is referring to.

## CLI Conventions

All LimaCharlie operations use the `limacharlie` CLI via Bash. Key rules:

- **Always pass `--output yaml`** for machine-readable, token-efficient output
- **Always pass `--oid <uuid>`** — every org-scoped command requires it. Use `limacharlie org list --output yaml` to discover OIDs
- **Use `--ai-help`** for command discovery: `limacharlie <command> --ai-help`
- **Use `--filter JMESPATH`** to reduce output to only needed fields
- **Never fabricate data** — only report what APIs return
- **OID is a UUID**, never an organization name

## Organizations (Orgs)

The basic tenancy unit. Identified by an Organization ID (OID), which is a UUID. Everything — sensors, rules, outputs, configs — lives within an org. Each org is an isolated environment with its own security data, configurations, and assets.

## Org Groups

Multi-tenant access management. An Org Group binds a set of Users, a set of Permissions, and a set of Organizations — granting those permissions to the users across those orgs. Members receive the permissions. Owners can modify the group but do NOT receive its permissions. Permissions granted via groups are additive on top of per-org permissions.

## Sensors

Umbrella term for how telemetry is ingested into LimaCharlie. Every sensor is identified by a Sensor ID (SID), which is a UUID, and belongs to exactly one org.

### EDR (Endpoint Agents)

Cross-platform lightweight endpoint sensors (Windows, Linux, macOS, ChromeOS, iOS, Android). Generate real-time telemetry: processes, network connections, DNS requests, file activity, registry changes, etc. EDR sensors can be **tasked** — commands sent to them for investigation or response (file collection, process kill, host isolation, memory dump). For sensors that may be offline, the Reliable Tasking extension (ext-reliable-tasking) guarantees delivery when they reconnect.

### Adapters

Bring in third-party telemetry, treated as first-class sensors with their own SIDs.

- **Cloud-to-Cloud**: ingest from SaaS/cloud sources (Office365, AWS CloudTrail, Okta, GCP, Azure, Slack, GitHub, 1Password, etc.)
- **On-Premises**: ingest from local sources (syslog, firewalls, Windows Event Logs, Zeek, etc.)
- **External Adapters**: cloud-managed adapter instances run by LimaCharlie

### Installation Keys

Base64-encoded strings used to register sensors and adapters with an org. Each key contains an OID and an Installer ID (IID, UUID). Keys can carry default tags applied to sensors at enrollment.

### Sensor Tags

Dynamic labels attached to sensors for organizing and targeting. Tags can be set via installation keys, the API, the UI, or D&R rule response actions. Used in sensor selectors and D&R rule targeting.

## Events & Data Streams

All data in LimaCharlie flows through one of four streams:

- **`event`**: real-time telemetry from sensors — process execution (NEW_PROCESS), DNS queries (DNS_REQUEST), network connections (NETWORK_CONNECTIONS), file operations, etc.
- **`detect`**: alerts generated when D&R rules match events (via the `report` action)
- **`audit`**: platform management events — config changes, user actions, API calls
- **`deployment`**: sensor lifecycle events — installs, uninstalls, version updates, cloning

### Event Structure

Every event has two top-level objects:
- **`routing`**: consistent metadata envelope (always present, same structure regardless of event type)
- **`event`**: event-type-specific payload (varies by `event_type`)

Field paths follow the pattern `event/FIELD_NAME` or `routing/FIELD_NAME`.

### The Routing Object (Critical)

The `routing` object is the backbone of all LimaCharlie data. It is present in every event and contains:

| Field | Type | Description |
|-------|------|-------------|
| `oid` | UUID | Organization ID |
| `sid` | UUID | Sensor ID |
| `event_type` | string | Event type (NEW_PROCESS, DNS_REQUEST, etc.) |
| `event_time` | integer | Timestamp in **milliseconds** (13 digits) |
| `event_id` | UUID | Unique event identifier |
| `hostname` | string | Sensor hostname |
| `iid` | UUID | Installation Key ID |
| `did` | UUID | **Device ID** — hardware-derived, persists across sensor reinstalls. Distinct from SID. |
| `ext_ip` | string | External IP |
| `int_ip` | string | Internal IP |
| `plat` | integer | Platform (Windows=268435456, Linux=536870912, macOS=805306368) |
| `arch` | integer | Architecture |
| `tags` | list | Sensor tags at event time |
| `this` | hash | Hash of the **current process/object** generating this event |
| `parent` | hash | Hash of the **parent process** |
| `target` | hash | Hash of the **target object** (optional, present for cross-process operations) |

#### The Three Process Correlation Hashes

`routing/this`, `routing/parent`, and `routing/target` are the keys to process tree navigation and stateful detection rules:

- **`this`**: identifies the process/object that generated the event. Used to correlate all events from the same process.
- **`parent`**: identifies the parent process. Used by `with child` / `with descendant` stateful rules to build process trees (e.g., detecting `cmd.exe → calc.exe`).
- **`target`**: identifies a target object in cross-process operations (e.g., the target of a `SENSITIVE_PROCESS_ACCESS`). Not always present.

These hashes are NOT PIDs — they are stable identifiers that persist across events and enable stateful rule correlation.

#### Device ID vs Sensor ID

- **SID** (Sensor ID): unique per sensor installation. Changes if the sensor is reinstalled.
- **DID** (Device ID): hardware-derived identifier. Persists across reinstalls on the same physical/virtual machine. Use DID to track a device across sensor reinstalls. The `entire_device: true` tag action applies tags to all sensors sharing a DID.

### Timestamps: Milliseconds vs Seconds

- **Event data** (`routing/event_time`, detection timestamps): **milliseconds** (13 digits, e.g., `1656959942437`)
- **API parameters** (`--start`, `--end` for search/replay): **seconds** (10 digits, e.g., `1656959942`)
- **Always divide by 1000** when using event timestamps for API queries

### Understanding Latency

The `routing.latency` field in detections is the delta between `routing/event_time` and detection creation time. **This is NOT D&R engine processing time** — the D&R engine processes events in under 100ms. The latency value includes ALL upstream delays:

- Third-party platform delays (Microsoft 365 events can be delayed hours in Microsoft's pipeline)
- Sensor sleep/wake cycles (laptop sleeps for 12 hours → events arrive with 12h latency)
- Network interruptions (sensor buffers locally, transmits on reconnect)
- OS-level delays (macOS/Windows delay writing to internal logs)

**Diagnostic approach**: look at the **minimum** latency value for a sensor, not the maximum. If minimum latency is hundreds of milliseconds, the LimaCharlie pipeline is healthy — high maximum alongside low minimum indicates source-side delays.

### Data Flow: Event to Detection

1. A sensor generates an **Event**
2. A **D&R rule** evaluates the event — if the detection logic matches, the response actions fire
3. The `report` response action creates a **Detection** — inheriting the event's routing and adding detection metadata (name, severity, extracted IOCs)

Detection field paths: `detect/FIELD_NAME` (event data), `routing/FIELD_NAME`, or top-level fields like `cat` (category), `priority`, `detect_id`.

### The Four Output Stream Structures

Each stream has a **different schema** — they are NOT interchangeable:

- **Event stream**: canonical `{ routing: {...}, event: {...} }` two-level structure
- **Detection stream**: flat with `cat`, `detect` (event copy), `detect_id`, `priority`, `detect_mtd`, `detect_data` (extracted IOCs), `source_rule`, `gen_time`
- **Audit stream**: flat with `oid`, `ts`, `etype`, `ident`, `entity`, `mtd`, `origin` (api/ui/cli/system) — does NOT use the routing/event split
- **Deployment stream**: uses routing/event structure but with deployment-specific event types (`sensor_installed`, `sensor_clone`, `sensor_over_quota`, `deleted_sensor`)

## D&R Rules (Detection & Response)

The automation engine. Each rule has two components:
- **Detection**: logic that matches (or doesn't match) an event
- **Response**: actions taken when the detection matches

Stored across three Hive namespaces: `dr-general` (custom rules), `dr-managed` (subscribed managed rulesets), `dr-services` (service-provided rules).

**False Positive (FP) Rules** suppress known benign detections without modifying the original rule.

Response actions include: `report` (create detection), `tag` (add/remove sensor tags), `task` (send command to sensor), `isolate` (network isolation), `start ai agent` (spawn AI session), and more.

## Detections

Events on the `detect` stream, generated by the `report` action in D&R rules. Each detection carries: category name (`cat`), severity/priority, detection metadata, and optionally extracted IOCs (`detect_data`). Detections can automatically create Cases for SOC triage.

## Outputs

How LimaCharlie sends data to external systems. Each output subscribes to one or more streams (`event`, `detect`, `audit`, `deployment`) and forwards matching data to a destination: S3, Syslog, Splunk, Elastic, BigQuery, Webhook, PubSub, GCS, SCP, SMTP, and others.

## Insight & LCQL

**Insight** is built-in data retention and search, enabled by default, with 1 year of retention. **LCQL** (LimaCharlie Query Language) is used to search and analyze retained data. Queries can target the `event`, `detect`, or `audit` streams. LCQL syntax is org-specific and schema-validated.

## Hive (Config Store)

A single generic CRUD API for configuration records. Each Hive type (namespace) has its own set of records, validators, and schema. All Hive records share the same envelope format (name, data, enabled flag, metadata) but carry different JSON payloads.

Key Hive types:
- `dr-general` / `dr-managed` / `dr-services`: D&R rules
- `fp`: false positive rules
- `lookup`: key-value lookup tables
- `secret`: encrypted credentials
- `yara`: YARA rules
- `cloud-sensors`: cloud sensor (adapter) configurations
- `query`: saved LCQL queries
- `ai_agent`: AI agent/session configurations
- `extension_config`: extension configurations
- `sop`: standard operating procedures

Records can be referenced across the platform using `hive://<type>/<key>` URIs (e.g., `hive://secret/my-api-key`).

## Lookups

Key-value dictionaries stored in the `lookup` Hive. The key can be queried at runtime in D&R rules for enrichment or detection logic (e.g., checking if an IP is in a blocklist). Can be populated manually, via API, or automatically via the Lookup Manager extension.

## Secrets

Secure credential storage in the `secret` Hive. Stores API keys, passwords, tokens, and other sensitive values. Referenced via `hive://secret/<name>` in outputs, adapters, AI session configs, and other components. Decouples credentials from their usage — users can configure outputs without seeing the underlying secret.

## Artifacts

Arbitrary blobs of data ingested into LimaCharlie. Sources include: manual upload via REST API, EDR-collected files (Windows Event Logs, raw logs, memory dumps, PCAP), and extension-driven collection. Artifacts are searchable via Insight and can be scanned with YARA rules.

## Extensions

Optional capabilities that must be subscribed to (enabled) per-org. Some extensions have configuration stored in the `extension_config` Hive. Key extensions:

- **Cases** (ext-cases): SOC case management and triage
- **Reliable Tasking** (ext-reliable-tasking): guaranteed command delivery to offline sensors
- **Artifact Collection** (ext-artifact): automated artifact collection rules
- **Git Sync** (ext-git-sync): Infrastructure as Code — sync org config from git repos
- **Feedback** (ext-feedback): interactive human-in-the-loop channels (Slack, Teams, Email, Telegram, Web)
- **Integrity** (ext-integrity): file and registry integrity monitoring
- **EPP** (ext-epp): endpoint protection platform integration
- **Exfil** (ext-exfil): data exfiltration monitoring
- **YARA Manager** (ext-yara-manager): YARA rule lifecycle management
- **Payload Manager** (ext-payload-manager): payload storage and deployment
- **Sensor Cull** (ext-sensor-cull): automatic cleanup of inactive sensors

## API Keys

UUIDs for programmatic API access. Two types:

- **User API Key**: represents all permissions associated with a user based on their org memberships. Requires a User ID (UID — NOT a UUID) and an API Key.
- **Org API Key**: scoped to a single organization. Requires only OID + API Key.

## Permissions (RBAC)

Granular role-based access control. Permissions are set per-user per-org, or granted via Org Groups (additive). Permission categories include: `sensor`, `dr`, `output`, `insight`, `secret`, `extension`, `user`, `billing`, `ai_agent`, and others. Pre-set permission schemes (Owner, Operator, Viewer, etc.) are available as templates.

## AI Sessions

Run Claude AI within LimaCharlie's security context:

- **D&R-Driven Sessions**: automated, fire-and-forget sessions triggered by D&R rule `start ai agent` response action. Used for automated triage, investigation, and enrichment.
- **User Sessions**: interactive sessions via the web UI or API. Used for ad-hoc investigation and analysis.

AI agent configurations are stored in the `ai_agent` Hive. Sessions use Bring-Your-Own-Key (Anthropic API key stored as a Secret).

## Cases

SOC triage and case management provided by the Cases extension (ext-cases). Cases can be created automatically from detections (via D&R rules) or manually for ad-hoc investigations. Each case has: a case number, status (new, in_progress, resolved, closed), severity, classification, entities (IPs, hashes, domains with verdicts), telemetry references, and analyst notes.

## Payloads

Scripts or binary files stored in LimaCharlie that can be deployed to sensors via tasking commands. Managed via the Payload Manager extension (ext-payload-manager). Used for fleet-wide operations like vulnerability scanning, data collection, or software deployment.

## YARA Rules

YARA rules stored in the `yara` Hive. Can be scanned against artifacts, memory dumps, and files on endpoints. Managed via the YARA Manager extension (ext-yara-manager) for lifecycle operations (import, versioning, scheduling scans).

## Playbooks

Python scripts that run in LimaCharlie's serverless execution environment (ext-playbook extension). Playbooks have full SDK access and can be triggered by D&R rule response actions, feedback responses, the API, or other extensions. Common uses: automated response workflows (isolate host, block IOC), notification pipelines (Slack alerts on case events), and custom integrations. Playbook definitions are stored in the `playbook` Hive.

## Infrastructure as Code (IaC)

The Git Sync extension (ext-git-sync) synchronizes org configuration from a git repository. Supports D&R rules, FP rules, outputs, lookups, extensions, integrity rules, and more. The CLI provides `limacharlie sync push` (local to cloud) and `limacharlie sync pull` (cloud to local) for manual synchronization.
