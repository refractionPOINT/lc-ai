# LimaCharlie for CMMC Level 2 and Level 3 Compliance

How LimaCharlie capabilities map to CMMC audit, accountability, and security controls.

## Level 2 — Audit & Accountability (NIST 800-171 family 3.3)

### AU.L2-3.3.1 — System Auditing

**Requirement:** Create and retain system audit logs to enable monitoring, analysis, investigation, and reporting of unauthorized activity.

**Required event types:** Authentication events, privileged function execution, failed logons, file access, process execution.

**LimaCharlie coverage:**

| Required Data | LC Event Type | Description |
|---------------|---------------|-------------|
| Process execution | `NEW_PROCESS` | Process start with full command line, file path, parent process, user context |
| Process termination | `TERMINATE_PROCESS` | Process exit tracking |
| User authentication | `USER_LOGIN`, `USER_LOGOUT` | OS-level authentication events |
| SSH authentication | `SSH_LOGIN`, `SSH_LOGOUT` | SSH session tracking |
| Failed logons | `WEL` (Event ID 4625) | Windows Event Log capture includes failed logon events |
| Privileged function execution | `WEL` (Event IDs 4672, 4673, 4674) | Special privilege assignment and use |
| File creation | `FILE_CREATE` | File creation with process context |
| File modification | `FILE_MODIFIED` | File content/attribute changes |
| File deletion | `FILE_DELETE` | File removal tracking |
| File integrity | `FIM_HIT` | Triggered when monitored files/directories/registry keys change |
| Registry changes | `REGISTRY_CREATE`, `REGISTRY_WRITE`, `REGISTRY_DELETE` | Registry key/value modifications |
| Network connections | `NEW_TCP4_CONNECTION`, `NEW_UDP4_CONNECTION`, `NEW_TCP6_CONNECTION`, `NEW_UDP6_CONNECTION` | Connection establishment with process attribution |
| DNS queries | `DNS_REQUEST` | DNS resolution attempts with responses |
| DLL/module loads | `MODULE_LOAD` | Library loading into processes |
| Service changes | `SERVICE_CHANGE` | Windows service modifications |
| Driver changes | `DRIVER_CHANGE` | Driver installation/modification |
| Autorun changes | `AUTORUN_CHANGE` | Persistence mechanism modifications |

**Configuration:** The LC EDR sensor collects these events by default — no per-event opt-in is required. Windows Event Log (`WEL`) collection can be configured to capture specific event IDs relevant to authentication and privilege use.

### AU.L2-3.3.2 — User Accountability

**Requirement:** Actions of individual users must be uniquely traceable.

**LimaCharlie coverage:** Every EDR event includes `routing` metadata with the sensor ID, hostname, and timestamp. Process events include user context. `USER_LOGIN` / `USER_LOGOUT` events track session boundaries. Combined with `WEL` events for Windows audit logs, individual user actions are attributable.

### AU.L2-3.3.4 — Alert on Audit Logging Process Failure

**Requirement:** Alert when the audit logging process fails.

**LimaCharlie coverage:**
- The `deployment` output stream captures sensor lifecycle events (enrollment, disconnection)
- Sensor heartbeat monitoring via `limacharlie sensor list` with `alive` timestamps identifies sensors that have stopped reporting
- D&R rules can be written against deployment events to alert on sensor disconnection
- The `audit` stream captures platform-level errors including output delivery failures

### AU.L2-3.3.5 — Correlate Audit Records

**Requirement:** Correlate audit record review, analysis, and reporting for investigation.

**LimaCharlie coverage:**
- LCQL provides direct search and correlation across all stored events within the retention window
- **D&R rules** provide real-time correlation at the platform level, matching patterns across event types

### AU.L2-3.3.6 — Audit Record Reduction and Report Generation

**Requirement:** Provide capability for audit record reduction and report generation.

**LimaCharlie coverage:**
- LCQL queries filter and aggregate events by type, time range, sensor, user, etc.
- **Outputs with filtering:** `event_white_list` / `event_black_list` on outputs reduce data before delivery
- **`custom_transform`** on outputs reshapes event data for downstream report generation
- D&R rules with `report` actions generate structured detections from raw events

### AU.L2-3.3.7 — Time-Stamped Audit Records

**Requirement:** Provide system capability that compares and synchronizes system clocks to generate time stamps for audit records.

**LimaCharlie coverage:** Every event includes `routing.event_time` (millisecond-precision epoch timestamp). The `routing.latency` field shows the delta between event generation and cloud receipt, providing a built-in measure of clock accuracy.

### AU.L2-3.3.8 — Protect Audit Information

**Requirement:** Protect audit information and tools from unauthorized access, modification, and deletion.

**LimaCharlie coverage:**
- Events stored in Insight are immutable — no user-facing API to modify or delete individual events
- Role-based access control on the platform limits who can access event data
- API key permissions are granular (`insight.evt.get`, `dr.list`, etc.)
- Output data, once forwarded, is protected by the destination system's access controls
- The `audit` stream logs all platform configuration changes, providing a tamper-evident record of who changed what

### AU.L2-3.3.9 — Limit Audit Logging Management

**Requirement:** Limit management of audit logging to privileged users.

**LimaCharlie coverage:** Platform access is controlled via API keys with specific permissions. Sensor configuration, D&R rule management, and output configuration all require explicit permissions. The `audit` stream records all administrative actions with the identity that performed them.

### Data Retention for Level 2

**Requirement:** 90 days active, organization-defined archival.

Insight is configured for 90+ day retention. All events are searchable via LCQL within the retention window. For long-term archival beyond the active retention period, an S3/GCS output can be added for cold storage.

---

## Level 3 — Enhanced Controls (NIST 800-172)

Level 3 builds on all Level 2 requirements and adds enhanced capabilities.

### 3.3.1e — Cross-Organizational Audit Correlation

**Requirement:** Support cross-organizational analysis and correlation of audit records.

**LimaCharlie coverage:**
- Multi-tenant architecture natively supports multiple organizations under a single management umbrella
- Outputs from multiple orgs can be routed to a shared SIEM/data lake for cross-org correlation
- Organization groups allow managing D&R rules and configurations across orgs
- LCQL queries can be scoped per-org, and results aggregated externally

### 3.3.2e — Automated Audit Analysis

**Requirement:** Deploy automated mechanisms to review audit records for unusual or suspicious activity, and report findings.

**LimaCharlie coverage:**
- **D&R rules** — real-time detection engine evaluates events as they arrive, matching behavioral patterns and generating detections. Rules can target specific MITRE ATT&CK techniques.
- **Stateful operators** — `with child`, `with descendant` (and proposed `with ancestor`) enable multi-event correlation for process tree analysis
- **YARA scanning** — `YARA_DETECTION` events from file and memory scanning for known malware signatures
- **Lookups** — D&R rules can reference threat intelligence feeds, known-bad hashes, or IP reputation lists during evaluation
- **Automated response** — matched detections can trigger actions (report, tag, isolate network, task sensors) without human intervention
- **Extensions** — third-party and custom extensions add detection capabilities (e.g., Strelka for file analysis, Zeek for network analysis)

---

## Beyond Audit: Other CMMC Controls Addressed by LimaCharlie

### Access Control (AC)

| Control | LC Capability |
|---------|---------------|
| AC.L2-3.1.7 — Prevent non-privileged users from executing privileged functions | D&R rules detecting privileged function execution via `NEW_PROCESS` and `WEL` events |

### System & Information Integrity (SI)

| Control | LC Capability |
|---------|---------------|
| SI.L2-3.14.1 — Flaw remediation | `os_packages` and `os_version` commands inventory installed software and OS versions for patch assessment |
| SI.L2-3.14.2 — Malicious code protection | YARA scanning, D&R detection rules, real-time event analysis |
| SI.L2-3.14.3 — Security alerts and advisories | D&R rules can match against updated threat intel lookups |
| SI.L2-3.14.6 — Monitor systems for attacks | Real-time EDR telemetry with D&R detection engine |
| SI.L2-3.14.7 — Identify unauthorized use | `USER_LOGIN`, `NEW_PROCESS`, network connection events with D&R rules for anomaly detection |

### Incident Response (IR)

| Control | LC Capability |
|---------|---------------|
| IR.L2-3.6.1 — Incident handling | Detections, case management (ext-cases), automated response actions |
| IR.L2-3.6.2 — Incident reporting/tracking | Detection output stream, case management with investigation workflows |

### Configuration Management (CM)

| Control | LC Capability |
|---------|---------------|
| CM.L2-3.4.1 — Baseline configurations | IaC via ext-git-sync for managing detection rules, outputs, and org configuration as code |
| CM.L2-3.4.5 — Access restrictions for change | API key permissions, audit stream for change tracking |

---

## Deployment Architecture

```
Endpoints → LC EDR Sensor → LimaCharlie Cloud → Insight (90+ day retention)
                                                → D&R Engine (real-time detection)
                                                → Outputs (SIEM, archival)
```

- Insight provides 90+ day active retention, meeting Level 2 requirements
- LCQL provides direct search and correlation (AU.L2-3.3.5, 3.3.6)
- D&R engine evaluates events in real-time for detection and automated response
- Optional outputs forward events to a SIEM for SOC workflows or to S3/GCS for long-term archival beyond the Insight retention window
