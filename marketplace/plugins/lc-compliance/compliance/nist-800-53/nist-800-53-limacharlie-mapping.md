# LimaCharlie for NIST SP 800-53 Rev 5 Compliance

How LimaCharlie capabilities map to NIST SP 800-53 Revision 5 controls across Windows, Linux, and macOS endpoints. Focused on the control families where LimaCharlie provides direct, measurable coverage: AU (Audit & Accountability), AC (Access Control), IA (Identification & Authentication), SI (System & Information Integrity), IR (Incident Response), CM (Configuration Management), SC (System & Communications Protection), and RA (Risk Assessment).

Control-selection baselines referenced below (Low / Moderate / High) come from [NIST SP 800-53B](https://csrc.nist.gov/publications/detail/sp/800-53b/final). Controls are relevant to all baselines unless a baseline is called out explicitly.

---

## Audit and Accountability (AU)

### AU-2 — Event Logging / AU-3 — Content of Audit Records / AU-12 — Audit Record Generation

**Requirement:** Identify and log event types. Records must include what, when, where, source, outcome, and identity. Provide audit record generation capability.

**LimaCharlie coverage:** The LC EDR sensor natively generates the event types below. Platform coverage reflects actual sensor capability — this is not a superset. Every event includes `routing.event_time` (ms epoch), `routing.hostname`, `routing.sid`, `routing.platform`, and event-specific fields (`COMMAND_LINE`, `FILE_PATH`, `USER_NAME`, `PARENT`, etc.).

| Event | Windows | Linux | macOS | Purpose |
|---|---|---|---|---|
| `NEW_PROCESS`, `EXISTING_PROCESS`, `TERMINATE_PROCESS` | ✅ | ✅ | ✅ | Process lifecycle with parent-child, command-line, user context |
| `DNS_REQUEST` | ✅ | ✅ | ✅ | DNS queries with responses |
| `NEW_TCP4_CONNECTION`, `NEW_TCP6_CONNECTION`, `NEW_UDP4_CONNECTION`, `NEW_UDP6_CONNECTION` | ✅ | ✅ | ✅ | Outbound/inbound connection establishment with process attribution |
| `TERMINATE_TCP4_CONNECTION`, `TERMINATE_TCP6_CONNECTION`, `TERMINATE_UDP4_CONNECTION`, `TERMINATE_UDP6_CONNECTION` | ✅ | ✅ | ✅ | Connection teardown |
| `NETWORK_CONNECTIONS`, `NETWORK_SUMMARY` | ✅ | ✅ | ✅ | Connection rollups |
| `CODE_IDENTITY` | ✅ | ✅ | ✅ | Hash + path + signature combinations (first-seen model) |
| `YARA_DETECTION` | ✅ | ✅ | ✅ | YARA rule match on file or memory |
| `FIM_HIT` | ✅ | ✅ | ✅ | File / directory / registry key modification on monitored path |
| `SERVICE_CHANGE` | ✅ | ✅ | ✅ | Service (Windows) / systemd unit (Linux) / launchd change (macOS) |
| `FILE_CREATE`, `FILE_DELETE`, `FILE_MODIFIED` | ✅ | ❌ | ✅ | Native file events — Linux relies on FIM |
| `MODULE_LOAD` | ✅ | ✅ | ❌ | DLL / shared-object loads |
| `WEL` | ✅ | ❌ | ❌ | Windows Event Log stream (via `wel://` artifact rule) |
| `MUL` | ❌ | ❌ | ✅ | macOS Unified Log stream (via `mul://` artifact rule) |
| `USER_LOGIN`, `USER_LOGOUT` | ❌ | ❌ | ✅ | OS login sessions — macOS only |
| `SSH_LOGIN`, `SSH_LOGOUT` | ❌ | ❌ | ✅ | SSH sessions — macOS only |
| `USER_OBSERVED` | ✅ | ✅ | ✅ | User session observation (all platforms) |
| `AUTORUN_CHANGE` | ✅ | ❌ | ❌ | Registry-driven autorun changes |
| `DRIVER_CHANGE` | ✅ | ❌ | ❌ | Driver install / modification |
| `REGISTRY_CREATE`, `REGISTRY_WRITE`, `REGISTRY_DELETE` | ✅ | ❌ | ❌ | Registry modifications |
| `SENSITIVE_PROCESS_ACCESS` | ✅ | ❌ | ❌ | Cross-process handle to protected processes |
| `THREAD_INJECTION`, `NEW_REMOTE_THREAD` | ✅ | ❌ | ❌ | Process injection indicators |
| `NEW_NAMED_PIPE`, `OPEN_NAMED_PIPE` | ✅ | ❌ | ❌ | Named pipe creation / open |
| `NEW_DOCUMENT`, `FILE_TYPE_ACCESSED` | ✅ | ❌ | ✅ | Document creation / process-document interaction |
| `VOLUME_MOUNT`, `VOLUME_UNMOUNT` | ✅ | ❌ | ✅ | Removable media events |
| `HIDDEN_MODULE_DETECTED` | ✅ | ❌ | ❌ | Unlinked module detection |
| `MODULE_MEM_DISK_MISMATCH` | ✅ | ✅ | ✅ | On-disk vs in-memory module drift |

**Linux auth-event caveat:** The LC Linux sensor does **not** emit `USER_LOGIN` or `SSH_LOGIN` events. For equivalent telemetry, choose one of:
1. Stream `/var/log/auth.log` (or `/var/log/secure` on RHEL/CentOS) via a LimaCharlie **file adapter** — events appear on a separate adapter telemetry stream.
2. Collect the auth log via an **Artifact Collection** rule for periodic retention (no real-time stream).
3. Derive session signal from `NEW_PROCESS` events on `sshd`, `login`, `sudo`, and related binaries with user context.

**Windows auth events** flow as `WEL` via a `wel://Security:*` artifact collection rule, not as dedicated `USER_LOGIN` events.

### AU-4 — Audit Log Storage Capacity

**Requirement:** Allocate storage capacity to accommodate audit logging.

**LimaCharlie coverage:** Insight provides 90+ day active retention as a managed capability — no endpoint storage is consumed. Artifact collection rules use `days_retention` for file/log artifacts. For long-term archival, an S3/GCS output provides unlimited cold storage.

### AU-6 — Audit Record Review, Analysis, and Reporting

**Requirement:** Review and analyze audit records for indications of inappropriate or unusual activity, and report findings.

**LimaCharlie coverage:**
- **D&R rules** evaluate events in real-time, producing detections that represent reviewable findings
- **LCQL** provides interactive search, filtering, and correlation across the 90-day hot window
- **Outputs** route detections to SIEM, case management, ticketing, or chat tools for human review
- **Cases extension (ext-cases)** provides SOC triage, assignment, SLA tracking, and investigation workflows

### AU-7 — Audit Record Reduction and Report Generation

**Requirement:** Provide capability to process audit records without altering the original content.

**LimaCharlie coverage:**
- LCQL filters and aggregates events by type, time, sensor, user, or any event field
- Output filters (`event_white_list`, `event_black_list`) reduce data before delivery to downstream systems
- `custom_transform` on outputs reshapes event data for report generation without modifying source records
- D&R rules with `report` actions produce structured detections distinct from raw telemetry

### AU-8 — Time Stamps

**Requirement:** Use internal system clocks to generate time stamps and record time stamps that meet organization-defined granularity.

**LimaCharlie coverage:** `routing.event_time` is millisecond-precision UTC epoch, generated at the sensor. `routing.latency` shows cloud-receipt delta — organizations can alert on excessive latency as a clock-drift indicator.

### AU-9 — Protection of Audit Information

**Requirement:** Protect audit information and tools from unauthorized access, modification, and deletion.

**LimaCharlie coverage:**
- Insight events are immutable — no API exposes individual event modification or deletion
- Platform RBAC via API keys with granular permissions (`insight.evt.get`, `dr.list`, etc.)
- The `audit` stream records all platform configuration changes with identity attribution — a tamper-evident log of administrative activity
- Outbound output data is protected by the destination system's access controls
- AU-9(4) (Access by subset of privileged users): API key scoping

### AU-11 — Audit Record Retention

**Requirement:** Retain audit records for the organization-defined period.

**LimaCharlie coverage:** Insight default retention is configurable to 90+ days. For retention beyond Insight's window (common for High-baseline systems with 1+ year requirements), an S3/GCS output provides cold storage with no LC-side expiration.

---

## Access Control (AC)

### AC-2 — Account Management

**Requirement:** Manage system accounts, including establishment, activation, modification, review, disabling, and removal.

**LimaCharlie coverage:**
- **Windows:** `WEL` events from `wel://Security:*` artifact rule — 4720 (created), 4722 (enabled), 4725 (disabled), 4726 (deleted), 4738 (changed), 4728 / 4732 / 4756 (group additions)
- **Linux:** `NEW_PROCESS` events for `useradd`, `usermod`, `userdel`, `groupadd`, `gpasswd`; auth events via file adapter on `/var/log/auth.log` or `/var/log/secure`
- **macOS:** `NEW_PROCESS` events for `dscl` (the canonical account-management binary on modern macOS), `sysadminctl`, `dsimport`; `MUL` events with appropriate predicate

### AC-6 — Least Privilege

**Requirement:** Employ least privilege, allowing only authorized accesses necessary to accomplish assigned tasks.

**LimaCharlie coverage:** Detection rather than enforcement — LC telemetry surfaces privileged function execution:
- **Windows:** `WEL` 4672 (special privileges), 4673 / 4674 (privileged service / object)
- **Linux:** `NEW_PROCESS` for `sudo`, `su`, `pkexec` with full command-line and user context
- **macOS:** `NEW_PROCESS` for `sudo`, `security authorize`

AC-6(9) (auditing privileged functions) is directly supported; AC-6(10) (non-privileged users executing privileged functions) can be detected via rules correlating low-privilege user context with privileged-function events.

### AC-7 — Unsuccessful Logon Attempts

**Requirement:** Enforce a limit on consecutive invalid logon attempts and automatically lock the account or device.

**LimaCharlie coverage:** LC detects — it does not enforce lockout (that is an OS capability).
- **Windows:** `WEL` 4625 (failed logon) and 4740 (lockout)
- **Linux:** `/var/log/auth.log` / `/var/log/secure` via file adapter; PAM failure patterns. `NEW_PROCESS` events for `sshd` children with exit codes provide indirect signal
- **macOS:** `USER_LOGIN` with failure metadata when `authd` denies; `MUL` events with predicate `subsystem == "com.apple.opendirectoryd"` or `process == "authd"`

### AC-17 — Remote Access

**Requirement:** Authorize and monitor remote access sessions.

**LimaCharlie coverage:**
- **Windows RDP:** `WEL` 4624 with `LogonType=10` (RemoteInteractive)
- **macOS SSH:** `SSH_LOGIN` / `SSH_LOGOUT` events (native)
- **Linux SSH:** `NEW_PROCESS` for `sshd` child processes with command context; auth-log file adapter for session boundaries

D&R rules alert on remote access from unexpected source IPs or outside business hours.

---

## Identification and Authentication (IA)

### IA-2 — Identification and Authentication (Organizational Users)

**Requirement:** Uniquely identify and authenticate organizational users and associate their unique identification with processes acting on their behalf.

**LimaCharlie coverage:** Every `NEW_PROCESS` event includes `USER_NAME` context. On macOS, `USER_LOGIN` / `SSH_LOGIN` establish session boundaries; subsequent process events in the session carry the authenticated user identity. On Windows, `WEL` 4624 / 4634 combined with process-event user context provides attribution. On Linux, user context is present in process events; session boundaries come from the auth log.

### IA-5 — Authenticator Management

**Requirement:** Manage system authenticators.

**LimaCharlie coverage:**
- **Windows:** `WEL` 4723 (password change), 4724 (password reset), 4776 (NTLM validation)
- **Linux:** `NEW_PROCESS` for `passwd`, `chage`, `chpasswd`, `pam_tally2`
- **macOS:** `NEW_PROCESS` for `passwd`, `dscl . passwd`

---

## System and Information Integrity (SI)

### SI-3 — Malicious Code Protection

**Requirement:** Implement malicious code protection mechanisms; update mechanisms; configure to scan and take action.

**LimaCharlie coverage:**
- **YARA scanning** — platform-native YARA execution on file writes, process memory, or ad-hoc. Produces `YARA_DETECTION` events on all three platforms
- **Windows Defender integration** via the EPP extension — Defender threat events flow as `WEL` for correlation
- **D&R rules with lookups** reference threat-intel feeds (known-bad hashes, IOCs) for real-time matching
- **Strelka extension** for deep file analysis when files transit endpoints

### SI-4 — System Monitoring

**Requirement:** Monitor the system to detect attacks and indicators of potential attacks; unauthorized local, network, and remote connections; and the unauthorized use of the system.

**LimaCharlie coverage:** The core value prop. Real-time EDR telemetry + D&R engine + YARA + lookups + managed detection extensions (Soteria, Sigma). SI-4(2) (automated tools for real-time analysis), SI-4(4) (inbound/outbound traffic), SI-4(5) (system-generated alerts), and SI-4(24) (indicators of compromise) are directly satisfied.

### SI-7 — Software, Firmware, and Information Integrity

**Requirement:** Employ integrity verification tools to detect unauthorized changes.

**LimaCharlie coverage:**
- FIM rules generate `FIM_HIT` events on monitored files, directories, and Windows registry keys — available on all three platforms
- `CODE_IDENTITY` events on Windows, Linux, and macOS expose hash + path + signature information for every loaded binary
- `AUTORUN_CHANGE` events track Windows persistence-mechanism modifications. For Linux (cron, systemd, `/etc/init.d`) and macOS (LaunchAgents, LaunchDaemons), use FIM rules on the relevant paths
- SI-7(1) (integrity checks) via FIM with configurable paths per platform
- SI-7(7) (integration of detection and response) via D&R rules on `FIM_HIT` / `AUTORUN_CHANGE` / `CODE_IDENTITY` events

---

## Incident Response (IR)

### IR-4 — Incident Handling

**Requirement:** Implement an incident handling capability for incidents consistent with the incident response plan.

**LimaCharlie coverage:**
- **Cases extension (ext-cases)** provides the full incident lifecycle: detection-to-case conversion, severity, assignment, SLA tracking, analyst notes, conclusion, and audit trail
- **Automated response actions** (`isolate network`, `add tag`, `task`) execute immediately on rule match without analyst intervention
- **Playbook extension** for Python-based response automation and enrichment

### IR-5 — Incident Monitoring

**Requirement:** Track and document incidents.

**LimaCharlie coverage:** Every detection appears in the detection output stream with full event context, timestamps, and MITRE ATT&CK metadata (when rules are authored with it). Cases maintain the long-form record.

### IR-6 — Incident Reporting

**Requirement:** Require personnel to report suspected incidents; report incident information to authorities.

**LimaCharlie coverage:** Outputs route detections and cases to external systems (Slack, email, PagerDuty, Jira, SIEM) where reporting workflows are enforced. The `detect` output stream provides programmatic access for custom reporting integrations.

---

## Configuration Management (CM)

### CM-3 — Configuration Change Control

**Requirement:** Determine, document, approve, and audit configuration-controlled changes.

**LimaCharlie coverage:**
- **ext-git-sync** manages D&R rules, outputs, FIM, and extensions as code — all changes flow through git review/approval
- The platform `audit` stream records every LC configuration change with the identity that performed it
- Endpoint configuration changes (autoruns, services, drivers, registry on Windows; systemd units / FIM on Linux; launchd / FIM on macOS) surface as LC events for detection

### CM-5 — Access Restrictions for Change

**Requirement:** Define, document, approve, and enforce physical and logical access restrictions for changes.

**LimaCharlie coverage:** Granular API-key permissions scope what each integration or user can change. All administrative actions are recorded in the `audit` stream. At the endpoint level, detection rules alert on firewall changes, service installations, driver loads, and autorun modifications.

### CM-6 — Configuration Settings

**Requirement:** Establish and document configuration settings; implement; monitor and control changes.

**LimaCharlie coverage:** FIM rules monitor configuration files:
- **Windows:** registry policy keys, Group Policy templates, `hosts` file
- **Linux:** `/etc/ssh/sshd_config`, `/etc/sudoers`, `/etc/sudoers.d/*`, `/etc/pam.d/*`, `/etc/passwd`, `/etc/shadow`
- **macOS:** `/etc/sudoers`, `/etc/pam.d/*`, `/Library/LaunchDaemons/*`, `/Library/LaunchAgents/*`

D&R rules alert on modifications. For cross-org consistency, ext-git-sync keeps configuration identical across tenants.

### CM-7 — Least Functionality

**Requirement:** Configure the system to provide only essential capabilities; prohibit or restrict unauthorized functions.

**LimaCharlie coverage:** LOLBin/LOLBAS detections (Windows: `mshta`, `regsvr32`, `certutil`, encoded PowerShell; Linux: `curl`/`wget` writing to world-writable paths, `python -c` with network modules; macOS: `osascript` remote invocation, `curl | sh`) surface unauthorized use of built-in tooling. The `os_packages` sensor command inventories installed software on Windows for baseline comparison.

---

## System and Communications Protection (SC)

### SC-7 — Boundary Protection

**LimaCharlie coverage (detection only):** Windows firewall rule changes (`WEL` Event IDs 4946-4950). Network-connection events (`NEW_TCP4/6_CONNECTION`, `NEW_UDP4/6_CONNECTION`) show egress/ingress from individual processes on all platforms. LC does not enforce boundary controls — perimeter enforcement remains the responsibility of network devices. Sensor `segregate network` / `rejoin network` commands provide host-level isolation (all three platforms via `SEGREGATE_NETWORK` / `REJOIN_NETWORK`).

### SC-18 — Mobile Code

**LimaCharlie coverage:** PowerShell operational log (`wel://Microsoft-Windows-PowerShell/Operational`), Office macro execution (detected via `NEW_PROCESS` parent-child relationships from `winword.exe` / `excel.exe`), and `MODULE_LOAD` events for DLL sideloading surface mobile-code use on Windows. On macOS, `osascript` and script-interpreter invocations surface via `NEW_PROCESS`.

---

## Risk Assessment (RA)

### RA-5 — Vulnerability Monitoring and Scanning

**LimaCharlie coverage:** The `os_packages` sensor command inventories installed software (Windows only per the sensor reference). `os_version` reports OS kernel/build across Windows, Linux, and macOS. Combined with a vulnerability-feed lookup, D&R rules or offline analysis can flag endpoints running vulnerable software versions. The fleet-payload-tasking skill supports ad-hoc vulnerability sweeps via scripts pushed to all platforms.

---

## Baseline Applicability

| Control | Low | Moderate | High |
|---|---|---|---|
| AU-2, AU-3, AU-4, AU-6, AU-8, AU-9, AU-11, AU-12 | ✅ | ✅ | ✅ |
| AU-7, AU-9(4) | | ✅ | ✅ |
| AC-2, AC-7, AC-17 | ✅ | ✅ | ✅ |
| AC-6, AC-6(9), AC-6(10) | | ✅ | ✅ |
| IA-2, IA-5 | ✅ | ✅ | ✅ |
| SI-3, SI-4, SI-7 | ✅ | ✅ | ✅ |
| SI-4(2), SI-4(4), SI-4(5), SI-4(24), SI-7(1), SI-7(7) | | ✅ | ✅ |
| IR-4, IR-5, IR-6 | ✅ | ✅ | ✅ |
| CM-3, CM-5, CM-6, CM-7 | ✅ | ✅ | ✅ |
| SC-7, SC-18 | ✅ | ✅ | ✅ |
| RA-5 | ✅ | ✅ | ✅ |

---

## Data Retention Guidance

- **Low baseline:** AU-11 is org-defined. Insight default (90 days) is typically sufficient.
- **Moderate baseline:** Many agencies require 1 year. Configure an S3/GCS output for cold archival alongside the 90-day Insight retention.
- **High baseline:** Multi-year retention is common. Cold archival is mandatory; consider a dedicated analytics output (e.g., Chronicle, Splunk, Elastic) for long-window search.

---

## Deployment Architecture

```
                          ┌── Insight (90+ day hot retention) ─► LCQL search
                          │
Endpoints ──► LC Sensor ──┼── D&R Engine (real-time detection) ─► Outputs
(Win/Linux/Mac)           │                                      ├─► SIEM
                          │                                      ├─► S3/GCS (cold)
                          └── Artifact / FIM / YARA              └─► Cases
```

- Sensor covers Windows, Linux, macOS with a common event schema — detection logic is largely portable, but platform-specific events (WEL / MUL / registry / auth) require per-platform rule branches
- Insight delivers AU-4, AU-11 hot retention
- D&R engine delivers AU-6, SI-4, SI-7(7) real-time review
- Outputs deliver AU-6, AU-11 (cold archival), IR-6 (reporting)
- ext-cases delivers IR-4, IR-5

---

## Cross-Framework Notes

NIST SP 800-53 Rev 5 is the parent catalog for several derivative frameworks — controls mapped here also satisfy:

- **FedRAMP** (Low, Moderate, High) — direct inheritance
- **FISMA** (Federal Information Security Modernization Act) — 800-53 is the canonical control set
- **NIST SP 800-171** / **CMMC** — 800-171 derives a subset of 800-53 Moderate. See [cmmc-limacharlie-mapping.md](../cmmc/cmmc-limacharlie-mapping.md) for CMMC-specific coverage
- **StateRAMP** — parallel catalog with state/local overlay
