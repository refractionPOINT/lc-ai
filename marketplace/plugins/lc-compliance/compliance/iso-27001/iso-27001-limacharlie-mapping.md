# LimaCharlie for ISO/IEC 27001:2022 Compliance

How LimaCharlie capabilities map to the Annex A controls of ISO/IEC 27001:2022 (derived from ISO/IEC 27002:2022) across Windows, Linux, and macOS endpoints. Focused on the themes where LimaCharlie provides direct, measurable coverage: **A.8 Technological controls** (heaviest) and the subset of **A.5 Organizational controls** touching incident management and cloud services.

The 2022 refresh reorganized Annex A into **four themes** (down from fourteen categories in the 2013 edition):

- **A.5 — Organizational controls** (37 controls)
- **A.6 — People controls** (8 controls) — policy / awareness; minimal LC role
- **A.7 — Physical controls** (14 controls) — minimal LC role
- **A.8 — Technological controls** (34 controls) — primary LC coverage

The 2022 edition introduced **11 new controls**, including threat intelligence (A.5.7), information security for use of cloud services (A.5.23), ICT readiness for business continuity (A.5.30), physical security monitoring (A.7.4), configuration management (A.8.9), information deletion (A.8.10), data masking (A.8.11), data leakage prevention (A.8.12), monitoring activities (A.8.16), web filtering (A.8.23), and secure coding (A.8.28).

---

## A.8 — Technological Controls

### A.8.1 — User endpoint devices

**Requirement:** Information stored on, processed by, or accessible via user endpoint devices shall be protected.

**LimaCharlie coverage:**
- EDR sensor (Windows, Linux, macOS) provides continuous visibility into process, file, network, and registry (Windows) activity on every managed endpoint
- `CODE_IDENTITY` events expose binary hash + signature on every load, surfacing unauthorized software
- FIM and YARA protect sensitive paths and data-at-rest
- Sensor `isolate network` command contains a compromised device immediately

### A.8.2 — Privileged access rights

**Requirement:** The allocation and use of privileged access rights shall be restricted and managed.

**LimaCharlie coverage:** Detection rather than enforcement — LC telemetry surfaces privileged function execution:
- **Windows:** `WEL` 4672 (special privileges assigned), 4673 / 4674 (privileged service / object), 4728 / 4732 / 4756 (group additions)
- **Linux:** `NEW_PROCESS` for `sudo`, `su`, `pkexec`, `doas` with full command-line and user context
- **macOS:** `NEW_PROCESS` for `sudo`, `security authorize`; `MUL` entries from `authd` / `opendirectoryd`

D&R rules can correlate low-privilege user identity with privileged-function events to detect privilege misuse.

### A.8.3 — Information access restriction

**Requirement:** Access to information and other associated assets shall be restricted in accordance with the established topic-specific policy on access control.

**LimaCharlie coverage:**
- FIM monitors sensitive directories and files — any unauthorized read attempt surfaces as `FIM_HIT` (on platforms/kernels that support access monitoring) or subsequent file events
- `SENSITIVE_PROCESS_ACCESS` (Windows) surfaces cross-process handle opens against protected processes
- Platform-side, granular RBAC on API keys limits who can access what LC data

### A.8.5 — Secure authentication

**Requirement:** Secure authentication technologies and procedures shall be implemented based on information access restrictions and the topic-specific policy on access control.

**LimaCharlie coverage:** LC detects authentication events — it does not enforce authentication:
- **Windows:** `WEL` 4624 (success), 4625 (failure), 4634 (logoff), 4648 (explicit credentials), 4776 (NTLM validation)
- **Linux:** `/var/log/auth.log` / `/var/log/secure` via file adapter; `NEW_PROCESS` for `sshd` / `login` / `sudo` with user context
- **macOS:** native `USER_LOGIN` / `USER_LOGOUT` / `SSH_LOGIN` / `SSH_LOGOUT` events; `MUL` entries with `process == "authd"` or `subsystem == "com.apple.opendirectoryd"` for failures

### A.8.7 — Protection against malware

**Requirement:** Protection against malware shall be implemented and supported by appropriate user awareness.

**LimaCharlie coverage:**
- Platform-native **YARA** execution on file writes, process memory, or ad-hoc — produces `YARA_DETECTION` events on all three platforms
- **Windows Defender** integration via the EPP extension — Defender threat events flow as `WEL` for correlation
- D&R rules with **lookups** reference threat-intel feeds (known-bad hashes, IPs, domains) for real-time matching
- **Strelka** extension for deep file analysis (PE analysis, archive extraction) when files transit endpoints
- Automatic response actions can quarantine (`isolate network`), tag, or kill processes

### A.8.8 — Management of technical vulnerabilities

**Requirement:** Information about technical vulnerabilities of information systems in use shall be obtained, the organization's exposure to such vulnerabilities evaluated, and appropriate measures taken.

**LimaCharlie coverage:** The `os_packages` sensor command inventories installed software (Windows). `os_version` reports OS kernel/build across Windows, Linux, and macOS. Combined with a vulnerability-feed lookup, D&R rules or offline analysis flag endpoints running vulnerable software versions. The `fleet-payload-tasking` capability supports ad-hoc vulnerability sweeps via scripts pushed fleet-wide.

### A.8.9 — Configuration management (NEW in 2022)

**Requirement:** Configurations, including security configurations, of hardware, software, services, and networks shall be established, documented, implemented, monitored, and reviewed.

**LimaCharlie coverage:**
- **ext-git-sync** manages D&R rules, FIM configs, outputs, and extension configuration as code — all platform changes flow through git review
- FIM rules monitor configuration files per platform:
  - **Windows:** registry policy keys, Group Policy templates, `hosts` file
  - **Linux:** `/etc/ssh/sshd_config`, `/etc/sudoers`, `/etc/pam.d/*`, `/etc/passwd`, `/etc/shadow`
  - **macOS:** `/etc/sudoers`, `/etc/pam.d/*`, `/Library/LaunchDaemons/*`, `/Library/LaunchAgents/*`
- The platform `audit` stream records every LC configuration change with identity attribution

### A.8.10 — Information deletion (NEW in 2022)

**Requirement:** Information stored in information systems, devices, or in any other storage media shall be deleted when no longer required.

**LimaCharlie coverage:** `FILE_DELETE` events (Windows, macOS) show file deletions with process attribution. Linux relies on FIM rules with deletion semantics. D&R rules alert on deletion of sensitive-path files. The `file_del` sensor command provides cryptographic deletion when triggered as a response action.

### A.8.12 — Data leakage prevention (NEW in 2022)

**Requirement:** Data leakage prevention measures shall be applied to systems, networks, and any other devices that process, store, or transmit sensitive information.

**LimaCharlie coverage:** Detection-oriented DLP signal:
- Network-connection events (`NEW_TCP4/6_CONNECTION`, `NEW_UDP4/6_CONNECTION`) with process attribution show egress per process — correlate against known-bad destinations or suspicious destination countries via lookups
- `VOLUME_MOUNT` / `VOLUME_UNMOUNT` events (Windows, macOS) detect removable media that may carry data off-host
- `DNS_REQUEST` events detect DNS-based exfiltration patterns (long subdomains, high entropy)
- `NEW_DOCUMENT` (Windows, macOS) and `FILE_TYPE_ACCESSED` events show sensitive document activity
- FIM and YARA rules on data-classification markers detect sensitive-content movement

### A.8.15 — Logging

**Requirement:** Logs that record activities, exceptions, faults, and other relevant events shall be produced, stored, protected, and analysed.

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

**Log protection (A.8.15 requires protection from tampering):**
- Insight events are immutable — no API exposes individual event modification or deletion
- Platform RBAC via API keys with granular permissions (`insight.evt.get`, `dr.list`, etc.)
- The `audit` stream records all platform configuration changes with identity attribution — a tamper-evident log of administrative activity
- For retention beyond the hot window, S3/GCS outputs with object-lock provide immutable archival

### A.8.16 — Monitoring activities (NEW in 2022)

**Requirement:** Networks, systems, and applications shall be monitored for anomalous behaviour and appropriate actions taken to evaluate potential information security incidents.

**LimaCharlie coverage:** The core value proposition. Real-time EDR telemetry + D&R engine + YARA + lookups + managed detection extensions (Soteria, Sigma). Specific capabilities:
- **D&R rules** evaluate events in real-time against detection logic spanning process, file, network, registry, and log events
- **LCQL** provides interactive search, filtering, and correlation across the 90-day hot window
- **Cases extension** provides SOC triage, assignment, SLA tracking, and investigation workflows
- **Anomaly detection** via `op: is tagged` with expected-baseline tags and `op: new` for first-seen-on-host logic
- **Managed detection** via Soteria and Sigma subscriptions

### A.8.17 — Clock synchronization

**Requirement:** The clocks of information processing systems used by the organization shall be synchronized to approved time sources.

**LimaCharlie coverage:** `routing.event_time` is millisecond-precision UTC epoch, generated at the sensor. `routing.latency` shows cloud-receipt delta — organizations can alert on excessive latency as a clock-drift indicator. D&R rules on `NEW_PROCESS` for `w32tm` / `ntpdate` / `chronyc` / `systemd-timesyncd` detect unauthorized time-source changes.

### A.8.18 — Use of privileged utility programs

**Requirement:** The use of utility programs that might be capable of overriding system and application controls shall be restricted and tightly controlled.

**LimaCharlie coverage:** `NEW_PROCESS` visibility covers every utility invocation. High-risk utilities detected per platform:
- **Windows:** `psexec`, `procdump`, `procexp`, `mimikatz`, `sdelete`, `cipher /w`, `fsutil`, `sc.exe`, `reg.exe`, `wmic`, `bcdedit`, `takeown`, `icacls`
- **Linux:** `strace`, `ltrace`, `gdb`, `nmap`, `tcpdump`, `nc`, `socat`, `dd` to devices, `shred`, `tune2fs`
- **macOS:** `dtruss`, `dscl`, `spctl`, `csrutil`, `nvram`, `pfctl`, `launchctl`

### A.8.19 — Installation of software on operational systems

**Requirement:** Procedures and measures shall be implemented to securely manage software installation on operational systems.

**LimaCharlie coverage:**
- `CODE_IDENTITY` produces first-seen records for every binary loaded on every platform — the basis for software-inventory baselines
- `os_packages` (Windows) inventories installed packages
- D&R rules detect MSI installs (`msiexec /i`), package-manager invocations (`apt`, `dnf`, `yum`, `brew`, `winget`, `choco`), and install-from-download patterns
- `AUTORUN_CHANGE` (Windows), FIM on LaunchDaemons (macOS), systemd paths (Linux) catch persistence-layer installs

### A.8.20 — Network security

**Requirement:** Networks and network devices shall be secured, managed, and controlled to protect information in systems and applications.

**LimaCharlie coverage (endpoint-side):**
- Every network event (`NEW_TCP4/6_CONNECTION`, `NEW_UDP4/6_CONNECTION`, `DNS_REQUEST`) has process attribution — see exactly which binary initiated every connection on every platform
- D&R rules alert on connections to unexpected ports, private-to-public crosses from scripting interpreters, and DNS queries to suspicious TLDs
- Sensor `isolate network` command provides host-level network isolation (all three platforms)
- The `zeek` extension provides full network-monitor capability on Linux sensors

### A.8.21 — Security of network services

**Requirement:** Security mechanisms, service levels, and service requirements of network services shall be identified, implemented, and monitored.

**LimaCharlie coverage:** `SERVICE_CHANGE` events (Windows services, Linux systemd units, macOS launchd jobs) surface every network-service state change. D&R rules on process-started-by-sshd, webserver spawning shells, and database processes forking suspicious children detect service-level compromise.

### A.8.22 — Segregation of networks

**Requirement:** Groups of information services, users, and information systems shall be segregated in the organization's networks.

**LimaCharlie coverage:** LC doesn't enforce network segregation — that is a network-device responsibility — but detects segregation violations:
- Network events with process attribution show cross-subnet traffic from workstations to server VLANs
- D&R rules on `NEW_TCP*_CONNECTION` with `op: is private address` predicates alert on unexpected internal lateral movement
- Sensor `isolate network` / `rejoin network` commands enforce host-level isolation (note: the response action is spelled `isolate network`, not `segregate network`)

### A.8.23 — Web filtering (NEW in 2022)

**Requirement:** Access to external websites shall be managed to reduce exposure to malicious content.

**LimaCharlie coverage:** Detection-only — LC does not block HTTP traffic:
- `DNS_REQUEST` events with lookups against threat-intel feeds detect access to known-bad domains
- `NEW_TCP*_CONNECTION` with process attribution shows browser connections; correlated with lookups of destination IP reputation
- D&R rules on `NEW_PROCESS` detect download patterns (`curl http://...`, `wget http://...`, PowerShell `Invoke-WebRequest`, `DownloadString`)

### A.8.26 — Application security requirements

**Requirement:** Information security requirements shall be identified, specified, and approved when developing or acquiring applications.

**LimaCharlie coverage:** LC's role is runtime monitoring rather than SDLC governance. Runtime signal:
- `MODULE_LOAD` events surface DLL / shared-object dependencies
- `YARA_DETECTION` rules can scan application binaries for known-vulnerable components
- `CODE_IDENTITY` exposes signing status — unsigned or self-signed application binaries surface

### A.8.28 — Secure coding (NEW in 2022)

**Requirement:** Secure coding principles shall be applied to software development.

**LimaCharlie coverage:** LC does not analyze source code. Runtime contribution:
- D&R rules detect runtime artifacts of common vulnerability classes (command injection → shell child of web-server process; deserialization exploits → `java` / `python` forking to shells)
- FIM on application directories detects unauthorized binary replacement on production systems

### A.8.32 — Change management

**Requirement:** Changes to information processing facilities and information systems shall be subject to change management procedures.

**LimaCharlie coverage:**
- **ext-git-sync** manages LC configuration as code through your standard change-review process
- The platform `audit` stream records every LC configuration change with identity attribution
- Endpoint configuration changes (autoruns, services, drivers, registry on Windows; systemd units / FIM on Linux; launchd / FIM on macOS) surface as LC events for detection of unauthorized changes

### A.8.34 — Protection of information systems during audit testing

**Requirement:** Audit tests and other assurance activities involving assessment of operational systems shall be planned and agreed between the tester and appropriate management.

**LimaCharlie coverage:** The platform `audit` stream records who ran what administrative API calls; combined with sensor `NEW_PROCESS` events, it provides a verifiable trail of auditor activity on endpoints during planned assessments. Custom tags (e.g., `audit-session-2026-04`) can be applied to sensors during audit windows to segment telemetry.

---

## A.5 — Organizational Controls (LC-relevant subset)

### A.5.7 — Threat intelligence (NEW in 2022)

**Requirement:** Information relating to information security threats shall be collected and analysed to produce threat intelligence.

**LimaCharlie coverage:**
- **Lookups** provide the integration point for threat-intel feeds — hashes, IPs, domains, YARA rules, user-agent strings
- Referenced from D&R rules via `op: lookup` for real-time matching against incoming events
- **Soteria** and **Sigma** extensions provide managed, continuously-updated rule sets

### A.5.23 — Information security for use of cloud services (NEW in 2022)

**Requirement:** Processes for acquisition, use, management, and exit from cloud services shall be established.

**LimaCharlie coverage:** LimaCharlie itself is a cloud service. Customer-relevant controls:
- Regional deployment options (US, EU, CA, UK, India, etc.) for data-residency compliance
- API-key RBAC scopes and audit trail
- **Outputs** to customer-controlled S3/GCS provide data-portability for cloud-exit scenarios
- All telemetry remains accessible via LCQL / API during the contract; export via S3/GCS output is a one-time configuration

### A.5.24 — Information security incident management planning and preparation

**Requirement:** The organization shall plan and prepare for managing information security incidents by defining, establishing, and communicating processes, roles, and responsibilities.

**LimaCharlie coverage:**
- **Cases extension (ext-cases)** provides the full incident-lifecycle workflow: detection-to-case conversion, severity classification, analyst assignment, SLA tracking, investigation notes, conclusion, and audit trail
- **Playbook extension** for Python-based response automation and evidence enrichment
- D&R rule tags (`iso-27001`, control IDs) make compliance-relevant detections filterable

### A.5.25 — Assessment and decision on information security events

**Requirement:** The organization shall assess information security events and decide if they are to be categorized as information security incidents.

**LimaCharlie coverage:** Every detection emitted by a D&R rule includes structured metadata (severity, MITRE ATT&CK ID/tactic, description). In ext-cases, analysts triage detections, promote to cases based on organizational criteria, and document the decision rationale — the audit trail satisfies the assessment-decision evidence requirement.

### A.5.26 — Response to information security incidents

**Requirement:** Information security incidents shall be responded to in accordance with the documented procedures.

**LimaCharlie coverage:**
- **Automated response actions** (`isolate network`, `add tag`, `task`, `segregate network` is NOT a valid action — use `isolate network`) execute immediately on rule match without analyst intervention
- **Sensor tasking** supports live-response commands (acquire file, acquire memory, run scripts, kill processes) on demand
- **Velociraptor** extension for deep DFIR artifact collection on investigation
- **Playbook** extension for multi-step response orchestration

### A.5.27 — Learning from information security incidents

**Requirement:** Knowledge gained from information security incidents shall be used to strengthen and improve the information security controls.

**LimaCharlie coverage:**
- Cases maintain the long-form incident record (notes, artifacts, conclusion) for post-incident review
- Lookups and D&R rules authored during incident response persist as durable controls
- Rule-tag strategy (e.g., `incident-derived-2026-Q1`) enables coverage reporting per incident cohort

### A.5.28 — Collection of evidence

**Requirement:** The organization shall establish and implement procedures for the identification, collection, acquisition, and preservation of evidence related to information security events.

**LimaCharlie coverage:**
- Artifact collection (`wel://`, `mul://`, file paths) retrieves forensically-relevant data on schedule or on demand
- Sensor commands: `file_get`, `mem_dump`, `os_processes`, `os_services`, `os_autoruns` for live-response acquisition
- **Velociraptor** extension for VQL-based DFIR artifact collection (NTFS MFT, browser history, shellbags, etc.)
- Insight retention + immutable S3/GCS archival provides chain-of-custody for event-level evidence
- Every API action is attributed in the `audit` stream — sustaining the chain of custody through analyst activity

### A.5.30 — ICT readiness for business continuity (NEW in 2022)

**Requirement:** ICT readiness shall be planned, implemented, maintained, and tested based on business continuity objectives and ICT continuity requirements.

**LimaCharlie coverage:** LC is a SaaS control. Customer-relevant capabilities: multi-region LC deployment selection; S3/GCS output for customer-owned log retention independent of LC availability; ext-git-sync for configuration-as-code recovery of rules and outputs.

---

## Cross-Mapping to ISO/IEC 27002:2013

For organizations transitioning from the 2013 edition, the table below shows equivalences between the 2022 and 2013 control identifiers.

| 2022 Control | 2013 Equivalent(s) | Theme Shift |
|---|---|---|
| A.5.7 Threat intelligence | *(new)* | New control |
| A.5.23 Cloud services | *(new)* | New control |
| A.5.24 Incident mgmt. planning | A.16.1.1 | Organizational |
| A.5.25 Assessment of events | A.16.1.4 | Organizational |
| A.5.26 Response to incidents | A.16.1.5 | Organizational |
| A.5.27 Learning from incidents | A.16.1.6 | Organizational |
| A.5.28 Collection of evidence | A.16.1.7 | Organizational |
| A.5.30 ICT readiness for BC | *(new)* | New control |
| A.8.1 User endpoint devices | A.6.2.1, A.11.2.8 | Merged |
| A.8.2 Privileged access rights | A.9.2.3 | Renumbered |
| A.8.3 Information access restriction | A.9.4.1 | Renumbered |
| A.8.5 Secure authentication | A.9.4.2 | Renumbered |
| A.8.7 Protection against malware | A.12.2.1 | Renumbered |
| A.8.8 Technical vulnerabilities | A.12.6.1, A.18.2.3 | Merged |
| A.8.9 Configuration management | *(new)* | New control |
| A.8.10 Information deletion | *(new)* | New control |
| A.8.12 Data leakage prevention | *(new)* | New control |
| A.8.15 Logging | A.12.4.1, A.12.4.2, A.12.4.3 | Merged |
| A.8.16 Monitoring activities | *(new)* | New control |
| A.8.17 Clock synchronization | A.12.4.4 | Renumbered |
| A.8.18 Privileged utility programs | A.9.4.4 | Renumbered |
| A.8.19 Installation of software | A.12.5.1, A.12.6.2 | Merged |
| A.8.20 Network security | A.13.1.1 | Renumbered |
| A.8.21 Security of network services | A.13.1.2 | Renumbered |
| A.8.22 Segregation of networks | A.13.1.3 | Renumbered |
| A.8.23 Web filtering | *(new)* | New control |
| A.8.26 Application security requirements | A.14.1.2, A.14.1.3 | Merged |
| A.8.28 Secure coding | *(new)* | New control |
| A.8.32 Change management | A.12.1.2, A.14.2.2, A.14.2.3, A.14.2.4 | Merged |
| A.8.34 Protection during audit testing | A.12.7.1 | Renumbered |

---

## Coverage Summary

| Theme | LC Coverage |
|---|---|
| A.5 Organizational | Partial — incident-management controls (A.5.24–A.5.28), threat intel (A.5.7), cloud services (A.5.23) directly supported; policy-authorship controls out of scope |
| A.6 People | Minimal — awareness / training is organizational, not technical |
| A.7 Physical | Minimal — LC is endpoint-focused; physical security out of scope |
| A.8 Technological | **Strong** — direct coverage of logging, monitoring, malware protection, configuration management, access control, network security, privileged utilities, change management |

### Controls with partial / weak LC coverage

- **A.8.10 Information deletion** — LC detects deletions but does not provide certified cryptographic erasure for end-of-life media
- **A.8.12 Data leakage prevention** — LC provides detection signal; blocking / content inspection at the wire level requires a network DLP solution
- **A.8.22 Segregation of networks** — LC detects violations and isolates hosts but cannot enforce VLAN / subnet segregation
- **A.8.23 Web filtering** — Detection-only; inline HTTP blocking requires a web proxy / secure-web-gateway
- **A.8.26 / A.8.28 Application security / secure coding** — SDLC process controls fall outside LC's runtime-monitoring scope

---

## Data Retention Guidance

ISO 27001 does **not** prescribe a specific retention period for logs — retention is org-defined based on risk assessment (referenced by A.8.15). **Three years** is common industry practice driven by auditor expectations and overlapping regulatory regimes (GDPR, PCI DSS, HIPAA, SOX).

LimaCharlie retention model:
- **Insight** provides 90 days of hot retention as a managed capability — no endpoint storage is consumed
- **S3/GCS outputs** provide unlimited cold storage with no LC-side expiration
- Typical pattern: 90 days hot (Insight) + remainder of retention-policy window in customer-owned cold storage

Document your chosen retention period in your Statement of Applicability (SoA) and tie it to your A.5.33 (records of processing activities) register.

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
- Insight delivers A.8.15 hot retention
- D&R engine delivers A.8.16, A.8.7, A.8.15 real-time review
- Outputs deliver A.8.15 cold archival, A.5.26 external reporting
- ext-cases delivers A.5.24–A.5.28

---

## Cross-Framework Notes

ISO/IEC 27001:2022 shares significant control overlap with other frameworks — LC configurations satisfying ISO 27001 also contribute to:

- **SOC 2 (Trust Services Criteria)** — CC series maps strongly to A.8 Technological controls; see [soc2-limacharlie-mapping.md](../soc2/soc2-limacharlie-mapping.md)
- **NIST SP 800-53 Rev 5** — A.8 Technological ↔ AU / AC / SI / CM / SC families; see [nist-800-53-limacharlie-mapping.md](../nist-800-53/nist-800-53-limacharlie-mapping.md)
- **NIST CSF 2.0** — ISO 27002:2022 Annex B explicitly maps to CSF subcategories
- **PCI DSS 4.0** — Requirement 10 (logging) ↔ A.8.15; Requirement 11 (security testing) ↔ A.8.8; see [pci-dss-limacharlie-mapping.md](../pci-dss/pci-dss-limacharlie-mapping.md)
- **HIPAA Security Rule** — Audit controls (§164.312(b)) ↔ A.8.15; see [hipaa-limacharlie-mapping.md](../hipaa/hipaa-limacharlie-mapping.md)

See the companion [iso-27001-limacharlie-implementation.md](iso-27001-limacharlie-implementation.md) for deployable D&R rules, FIM rules, artifact collection rules, and extension configurations.
