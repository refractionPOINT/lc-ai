# LimaCharlie for SOC 2 Compliance

How LimaCharlie capabilities map to the **AICPA Trust Services Criteria (2017, with the 2022 points-of-focus refresh)**. SOC 2 is organized around five categories — Security (the Common Criteria, required for every report) plus the optional Availability, Confidentiality, Processing Integrity, and Privacy categories. LimaCharlie's strongest coverage is in the Common Criteria (CC6, CC7, CC8, CC9), with meaningful contributions to Availability (A1) and Confidentiality (C1).

This document maps criteria to LC capabilities conceptually. For the deployable configuration (D&R rules, FIM rules, artifact collection, exfil rules, extensions), see [soc2-limacharlie-implementation.md](soc2-limacharlie-implementation.md).

> **Scope note:** SOC 2 Type II reports evaluate the operating effectiveness of controls over a defined observation period (typically 6–12 months). The telemetry, detections, and audit trails described below constitute evidence of control operation. See [Retention Guidance](#retention-guidance) for how to retain that evidence across the observation window.

---

## Criteria Structure

| Category | Abbrev | Required? | LC Coverage |
|---|---|---|---|
| Security / Common Criteria | CC | Always | **Heavy** — CC6, CC7, CC8, CC9 |
| Availability | A1 | Optional | **Partial** — A1.2 (monitoring) |
| Confidentiality | C1 | Optional | **Partial** — exfil / credential-dump indicators |
| Processing Integrity | PI1 | Optional | **Minimal** — LC is not a data-validation platform |
| Privacy | P | Optional | **Minimal** — LC does not process subject data directly |

---

## Common Criteria — CC2: Communication and Information

### CC2.1, CC2.2, CC2.3 — Internal and External Communication of Security Information

**Requirement:** The entity communicates information to internal and external parties to support the functioning of internal control.

**LimaCharlie coverage:**
- The **detection output stream** routes real-time security findings to Slack, email, PagerDuty, Jira, SIEM, or custom webhooks, providing a structured channel for internal security communications
- The **audit stream** records all platform configuration changes with identity attribution — evidence that control changes are communicated and tracked
- **Cases (ext-cases)** provides analyst notes, assignment history, and timelined communication per incident, supporting internal handoff and external reporting
- **ext-git-sync** records configuration changes as commits, giving auditors a reviewable communication trail for control evolution

---

## Common Criteria — CC3: Risk Assessment

### CC3.2, CC3.4 — Identification, Analysis, and Assessment of Risk

**Requirement:** The entity identifies risks to the achievement of its objectives and analyzes the significance.

**LimaCharlie coverage (partial — feeds risk data, does not perform risk assessment):**
- Telemetry volume, detection frequency, and sensor coverage metrics from the **reporting skill** and custom LCQL queries provide empirical risk data — which systems are most targeted, which controls most frequently trigger detections
- **`os_packages`** and **`os_version`** sensor commands feed software-inventory data into vulnerability risk assessment (partial — depends on external CVE correlation)
- D&R rule catalog serves as an evidenced list of identified risks the organization has chosen to detect — each rule is a documented risk acceptance or mitigation decision

---

## Common Criteria — CC4: Monitoring Activities

### CC4.1 — Ongoing and Separate Evaluations

**Requirement:** The entity selects, develops, and performs ongoing and/or separate evaluations to ascertain whether the components of internal control are present and functioning.

**LimaCharlie coverage:** The LC detection engine **is** the ongoing monitoring activity for this criterion:
- Real-time event evaluation across Windows, Linux, and macOS endpoints
- 24/7 automated control-operation monitoring via D&R rules
- The Soteria and Sigma managed detection extensions provide separate evaluation by a third-party ruleset

### CC4.2 — Communication of Control Deficiencies

**Requirement:** The entity evaluates and communicates control deficiencies in a timely manner.

**LimaCharlie coverage:** Detections and cases constitute the "deficiency communication" mechanism. Every detection carries a `priority`, `metadata.description`, and MITRE ATT&CK context. Cases track deficiency remediation from detection through resolution.

---

## Common Criteria — CC6: Logical and Physical Access Controls

**LC's heaviest coverage area.** Every CC6 subcriterion has direct EDR telemetry and D&R rule support.

### CC6.1 — Logical Access Security Measures

**Requirement:** The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events.

**LimaCharlie coverage:**
- **Windows:** `WEL` events from `wel://Security:*` artifact rule — 4624 (successful logon), 4625 (failed logon), 4634 (logoff), 4647 (user-initiated logoff), 4648 (logon with explicit credentials), 4672 (special privilege assignment)
- **Linux:** `/var/log/auth.log` (Debian/Ubuntu) or `/var/log/secure` (RHEL/CentOS) via a file adapter — see [Linux auth-event caveat](#linux-auth-event-caveat)
- **macOS:** Native `USER_LOGIN`, `USER_LOGOUT`, `SSH_LOGIN`, `SSH_LOGOUT` events plus `MUL` events from `wel://com.apple.opendirectoryd` predicates

D&R rules flag anomalous logons (unusual source, time of day, account type) and produce detections that feed the case system.

### CC6.2, CC6.3 — Role-Based Access Management

**Requirement:** Prior to issuing system credentials and granting system access, the entity registers and authorizes new internal and external users (CC6.2). The entity authorizes, modifies, or removes access to data, software, functions, and other protected information assets based on roles, responsibilities, or the system design and changes, giving consideration to the concepts of least privilege and segregation of duties (CC6.3).

**LimaCharlie coverage (detection of account lifecycle events):**
- **Windows:** `WEL` Event IDs 4720 (user created), 4722 (enabled), 4725 (disabled), 4726 (deleted), 4738 (changed), 4728 / 4732 / 4756 (group additions)
- **Linux:** `NEW_PROCESS` for `useradd`, `usermod`, `userdel`, `groupadd`, `gpasswd`, `chpasswd`
- **macOS:** `NEW_PROCESS` for `dscl` (canonical account-management binary), `sysadminctl`, `dsimport`; `MUL` auth subsystem events

LC is a **detection-and-evidence** control for CC6.2/CC6.3 — identity lifecycle is enforced by the directory service, but every create/modify/remove action produces an auditable LC event with the identity that performed it.

### CC6.6 — Protection Against Threats from Outside System Boundaries

**Requirement:** The entity implements logical access security measures to protect against threats from sources outside its system boundaries.

**LimaCharlie coverage:**
- **Remote access detection:** Windows RDP (`WEL` 4624 + `LogonType=10`), macOS SSH (`SSH_LOGIN`), Linux SSH (`NEW_PROCESS` on `sshd` children plus file-adapter auth-log events)
- **Inbound connection telemetry:** `NEW_TCP4_CONNECTION`, `NEW_TCP6_CONNECTION`, `NEW_UDP4_CONNECTION`, `NEW_UDP6_CONNECTION` events on all three platforms with process attribution — surfaces unauthorized inbound services
- **Firewall change detection:** Windows (`WEL` 4946–4950), Linux (`NEW_PROCESS` on `iptables`/`nft`/`firewall-cmd`/`ufw`), macOS (`pfctl`, `socketfilterfw`) — alerts when perimeter controls are modified
- **Network isolation response:** The `isolate network` response action quarantines a compromised host in real time on all three platforms

### CC6.7 — Restriction of Information Transmission, Movement, and Removal

**Requirement:** The entity restricts the transmission, movement, and removal of information to authorized internal and external users and processes, and protects it during transmission, movement, or removal.

**LimaCharlie coverage (detection-focused):**
- **Exfil indicators:** `NEW_TCP4_CONNECTION` / `NEW_UDP4_CONNECTION` to public destinations from scripting / command-line utilities (PowerShell, curl, wget, nc, osascript)
- **Removable media (Windows, macOS):** `VOLUME_MOUNT`, `VOLUME_UNMOUNT` events detect USB / removable drive attachment
- **DNS data-channel indicators:** `DNS_REQUEST` events with high-entropy labels, unusually long queries, or requests to uncommon TLDs
- **Cloud-storage beaconing:** D&R rules match `DNS_REQUEST` / `NEW_TCP4_CONNECTION` to unsanctioned cloud-storage FQDNs

LC does not enforce DLP — it provides the detection feed that DLP / proxy enforcement integrates with.

### CC6.8 — Prevention or Detection of Unauthorized or Malicious Software

**Requirement:** The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software to meet the entity's objectives.

**LimaCharlie coverage:**
- **YARA scanning** — platform-native YARA execution on file writes, process memory, or ad-hoc. Produces `YARA_DETECTION` events on Windows, Linux, and macOS
- **Windows Defender integration** via the EPP extension — Defender threat events flow as `WEL` for SOC correlation
- **Code-identity telemetry** — `CODE_IDENTITY` events on all three platforms provide hash + path + signature, enabling allowlist/blocklist detection via lookups
- **LOLBin / LOLBAS detection** — D&R rules flag misuse of built-in tools (Windows: `mshta`, `regsvr32`, `certutil`, encoded PowerShell; Linux: `curl | sh`, `python -c` with network modules; macOS: `osascript` shell-out, `curl | sh`)
- **Autorun / persistence detection** — `AUTORUN_CHANGE`, `DRIVER_CHANGE`, `SERVICE_CHANGE` on Windows; FIM on `/etc/cron*`, `/etc/systemd/system`, `~/.ssh/authorized_keys`, `/Library/LaunchAgents`, `/Library/LaunchDaemons`
- **Automated response** — `isolate network` on high-confidence malware detections for real-time containment

---

## Common Criteria — CC7: System Operations

### CC7.1 — Detection of Unauthorized Changes and Malicious Software

**Requirement:** The entity uses detection and monitoring procedures to identify changes to configurations that result in the introduction of new vulnerabilities, and susceptibilities to newly discovered vulnerabilities.

**LimaCharlie coverage:**
- **FIM (all platforms)** — `FIM_HIT` events on monitored files, directories, and Windows registry keys
- **Autorun / service / driver change events (Windows)** — `AUTORUN_CHANGE`, `SERVICE_CHANGE`, `DRIVER_CHANGE`
- **Launch agent / daemon monitoring (macOS)** — FIM on `/Library/LaunchDaemons/*`, `/Library/LaunchAgents/*`, `~/Library/LaunchAgents/*`
- **Cron / systemd monitoring (Linux)** — FIM on `/etc/cron*`, `/etc/systemd/system/*`, `/etc/init.d/*`
- **Code-identity drift** — `CODE_IDENTITY` events expose new hashes loaded in trusted system paths; D&R rules flag unsigned binaries in those paths (Windows, macOS)

### CC7.2 — System Component Monitoring for Anomalies

**Requirement:** The entity monitors system components and the operation of those components for anomalies that are indicative of malicious acts, natural disasters, and errors.

**LimaCharlie coverage:** The core value proposition:
- Real-time EDR telemetry across Windows, Linux, macOS with a common event schema
- D&R detection engine evaluates every event against a rule catalog
- Managed detection extensions (Soteria, Sigma) add maintained rulesets aligned to MITRE ATT&CK
- LCQL enables ad-hoc anomaly hunts over the 90-day hot window
- Stateful operators (`with child`, `with descendant`) enable multi-event correlation for process trees and kill chains

### CC7.3 — Evaluation of Security Events

**Requirement:** The entity evaluates security events to determine whether they could or have resulted in a failure of the entity to meet its objectives (security incidents) and, if so, takes actions to prevent or address such failures.

**LimaCharlie coverage:**
- **Cases extension** provides the evaluation workflow: severity assignment, analyst triage, investigation notes, classification (true positive / false positive / benign), conclusion documentation
- Every detection carries `priority` (1–5), `metadata.description`, `mitre_attack_id`, and `mitre_tactic` for analyst-time evaluation
- The **AI SOC extensions** (Agentic SOC agents — l1-bot, general-analyst, bulk-triage, l2-analyst) apply automated evaluation / enrichment / classification to detections

### CC7.4 — Incident Response

**Requirement:** The entity responds to identified security incidents by executing a defined incident response program to understand, contain, remediate, and communicate security incidents, as appropriate.

**LimaCharlie coverage:**
- **Automated response actions** trigger on rule match without analyst intervention:
  - `isolate network` — host-level quarantine on Windows, Linux, macOS
  - `add tag` — mark hosts for workflow / policy routing
  - `task` — dispatch sensor commands (kill process, delete file, memory dump, run Velociraptor artifact)
- **Cases (ext-cases)** runs the IR lifecycle: assignment, SLA tracking, investigation notes, related-entity linking, resolution, audit trail
- **Playbook extension** provides Python-based response automation for custom enrichment / containment workflows
- **Velociraptor integration** for deep forensic triage on the host during active incidents

### CC7.5 — Recovery from Security Incidents

**Requirement:** The entity identifies, develops, and implements activities to recover from identified security incidents.

**LimaCharlie coverage (partial — detection and forensic support for recovery):**
- **`rejoin network`** response action restores an isolated host after remediation
- **Velociraptor** collections enable evidence preservation for post-incident analysis
- **Artifact Collection** retains logs and files from impacted endpoints for recovery verification
- **Cases** maintains a timeline of actions taken, supporting after-action review
- LC does **not** perform system restoration / backup restoration — recovery-side data protection is separate

---

## Common Criteria — CC8: Change Management

### CC8.1 — Authorized Changes

**Requirement:** The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, and implements changes to infrastructure, data, software, and procedures to meet its objectives.

**LimaCharlie coverage (control-side evidence):**
- **ext-git-sync** manages D&R rules, outputs, FIM rules, and extension configuration as code — every change flows through git review, approval, and commit history
- The platform **audit stream** records every LC configuration change with the identity that performed it — a tamper-evident log of LC control-surface modifications
- **API-key scoping** restricts what each integration or user can change, supporting segregation of duties

**LimaCharlie coverage (infrastructure-side detection):**
- **Configuration-file FIM** — FIM rules on `/etc/ssh/sshd_config`, `/etc/sudoers`, `/etc/pam.d/*`, Windows registry policy keys, macOS `/etc/sudoers` and LaunchAgents. Any modification outside an approved change window fires a detection
- **Service / driver / autorun change detection** — Windows `SERVICE_CHANGE`, `DRIVER_CHANGE`, `AUTORUN_CHANGE`; Linux `SERVICE_CHANGE` (systemd units); macOS `SERVICE_CHANGE` (launchd)
- **`CODE_IDENTITY`** events provide a first-seen model — new hashes in system paths surface previously unknown binaries for change review

---

## Common Criteria — CC9: Risk Mitigation

### CC9.1 — Identification and Mitigation of Business Disruption Risks

**Requirement:** The entity identifies, selects, and develops risk mitigation activities for risks arising from potential business disruptions.

**LimaCharlie coverage:**
- **Service-stop detection** — D&R rules alert on attempts to stop critical services (Windows event log, auditd on Linux, macOS logging) that could result in disruption-of-monitoring
- **Ransomware indicators** — FIM velocity rules and mass-file-modification detection surface disruption precursors
- **Resource-exhaustion indicators** — D&R rules match on process spawning velocity, connection-flood patterns that may indicate DoS

### CC9.2 — Vendor and Business Partner Risk Management

**Requirement:** The entity assesses and manages risks associated with vendors and business partners.

**LimaCharlie coverage (indirect):**
- Third-party software installed on managed endpoints surfaces via `CODE_IDENTITY`, `MODULE_LOAD`, `NEW_PROCESS` — provides visibility into vendor software actually running
- D&R rules targeting specific vendor software (e.g., remote-support tools: AnyDesk, TeamViewer, ScreenConnect) support vendor-risk policies restricting remote-access tooling
- Outputs can segregate detections from vendor-supplied systems into dedicated streams for vendor-risk review

LC does not perform vendor-due-diligence assessment — it provides the technical evidence channel that supports it.

---

## Availability Category — A1

### A1.2 — Environmental Protections, Software, Data Backup, and Recovery Infrastructure

**Requirement:** The entity authorizes, designs, develops or acquires, implements, operates, approves, maintains, and monitors environmental protections, software, data back-up processes, and recovery infrastructure to meet its objectives.

**LimaCharlie coverage (monitoring contribution):**
- **Service-stop detection** — alerts on attempts to disable critical services (backup agents, monitoring agents, hypervisor tools) that would impact availability
- **Process-terminator detection** — `NEW_PROCESS` rules matching `taskkill`, `stop-process`, `kill -9` against critical service binaries
- **Disk-space / resource indicators** — the `os_version` command and `NETWORK_SUMMARY` event provide periodic host-health visibility; combined with LCQL can surface degrading endpoints
- **Ransomware and data-destruction detection** — file-modification velocity rules, shadow-copy deletion (`vssadmin delete`), backup-destruction command-line patterns

A1.1 (performance monitoring / capacity) and A1.3 (recovery testing) are **outside LC scope** — those are handled by cloud provider metrics, APM tools, and backup-system reporting.

---

## Confidentiality Category — C1

### C1.1 — Identification and Maintenance of Confidential Information

**Requirement:** The entity identifies and maintains confidential information to meet the entity's objectives related to confidentiality.

**LimaCharlie coverage (partial):**
- **File-access telemetry** — `FILE_CREATE`, `FILE_MODIFIED`, `FILE_DELETE` on Windows and macOS with process attribution; FIM (all platforms) for designated confidential paths
- **YARA scanning** on confidential-data patterns (credit-card numbers, SSN patterns, API keys) via custom rules
- **`NEW_DOCUMENT`** event (Windows, macOS) for document-access tracking by specific processes

### C1.2 — Disposal of Confidential Information

**Requirement:** The entity disposes of confidential information to meet the entity's objectives related to confidentiality.

**LimaCharlie coverage:**
- **`FILE_DELETE` events** (Windows, macOS) record deletion with process attribution and timestamp — evidence of disposal
- **Secure-delete tool detection** — `NEW_PROCESS` rules for `sdelete`, `shred`, `srm` execute with target paths

### Confidentiality — Credential-Dump / Exfil Indicators

Although not a formal subcriterion, SOC 2 auditors expect detection of common confidentiality threats:
- **LSASS access (Windows)** — `SENSITIVE_PROCESS_ACCESS` with target `lsass.exe` surfaces credential dumping
- **SAM / SYSTEM registry hive access (Windows)** — FIM on `C:\Windows\System32\config\SAM`, `SYSTEM`
- **/etc/shadow access (Linux)** — FIM + `NEW_PROCESS` rules matching shadow-file read by non-root parent
- **macOS keychain access** — FIM on `~/Library/Keychains/*`, `/Library/Keychains/*`

---

## Processing Integrity Category — PI1

**LimaCharlie coverage — minimal.** PI1 focuses on the accuracy, completeness, and authorization of data processing — this is largely an application-layer concern (input validation, transaction integrity, processing logs), not an endpoint-security concern.

Where LC contributes:
- **`FILE_MODIFIED` events** (Windows, macOS) on processing-system data files provide tamper evidence
- **FIM on application binaries and config files** — detects unauthorized changes to the software doing the processing
- **`CODE_IDENTITY`** — hash stability for processing-system binaries

Do not rely on LC as the primary PI1 control. Database-audit, application-log, and transaction-log systems are the appropriate controls.

---

## Privacy Category — P

**LimaCharlie coverage — minimal / indirect.** LC does not process PII or subject data and has no native privacy-management features.

Indirect contributions:
- **FIM on data stores** containing PII provides tamper evidence
- **File-access telemetry** on designated PII paths supports audit-trail requirements for data access
- **Cases** can track privacy incidents in the same workflow as security incidents — a practical integration point

Privacy controls (consent management, subject-access requests, data-subject-rights workflows) are handled by dedicated privacy platforms.

---

## Event-to-Platform Coverage Matrix

LC sensor event availability differs by platform. Before writing D&R rules, verify the event fires on the target platform:

| Event | Windows | Linux | macOS |
|---|---|---|---|
| `NEW_PROCESS`, `EXISTING_PROCESS`, `TERMINATE_PROCESS` | ✅ | ✅ | ✅ |
| `DNS_REQUEST` | ✅ | ✅ | ✅ |
| `NEW_TCP4/6_CONNECTION`, `NEW_UDP4/6_CONNECTION`, `NETWORK_CONNECTIONS` | ✅ | ✅ | ✅ |
| `CODE_IDENTITY`, `YARA_DETECTION`, `FIM_HIT` | ✅ | ✅ | ✅ |
| `SERVICE_CHANGE` | ✅ | ✅ | ✅ |
| `FILE_CREATE`, `FILE_DELETE`, `FILE_MODIFIED` | ✅ | ❌ | ✅ |
| `MODULE_LOAD` | ✅ | ✅ | ❌ |
| `WEL` | ✅ | ❌ | ❌ |
| `MUL` | ❌ | ❌ | ✅ |
| `USER_LOGIN`, `USER_LOGOUT`, `SSH_LOGIN`, `SSH_LOGOUT` | ❌ | ❌ | ✅ |
| `AUTORUN_CHANGE`, `DRIVER_CHANGE`, `REGISTRY_*`, `SENSITIVE_PROCESS_ACCESS`, `THREAD_INJECTION`, `NEW_NAMED_PIPE` | ✅ | ❌ | ❌ |

### Linux auth-event caveat

The LC Linux sensor does **not** emit `USER_LOGIN` or `SSH_LOGIN` events. For CC6.1 / CC6.6 auth telemetry on Linux, use one of:

1. Stream `/var/log/auth.log` (or `/var/log/secure` on RHEL/CentOS) via a LimaCharlie **file adapter** — events appear on a separate adapter telemetry stream
2. Collect the auth log via **Artifact Collection** for periodic retention (no real-time stream)
3. Derive session signal from `NEW_PROCESS` events on `sshd`, `login`, `sudo` — weaker signal but no adapter required
4. Deploy **auditd** rules covering `execve`, identity file writes, and auth events, then collect `/var/log/audit/audit.log` via file adapter

### `SSH_LOGIN` caveat (macOS)

The `SSH_LOGIN` event fires **only on success** and has no `IS_SUCCESS` field. Failed SSH detection on macOS must match `MUL` events with a predicate covering authentication failures.

---

## Retention Guidance

SOC 2 Type II reports cover an observation period — commonly **12 months** for annual reports, 6 months for initial reports, or the period specified in the service agreement. Auditors expect evidence to be retained across the observation window.

| Evidence Type | LC Native Retention | Recommendation |
|---|---|---|
| EDR telemetry (process, network, file events) | Insight: 90 days hot | S3/GCS output for 12-month archival |
| Detections | Insight + Cases (case-level indefinite) | S3 output of `detect` stream recommended |
| Platform configuration changes | `audit` stream (90 days) | S3 output of `audit` stream for full observation period |
| WEL / MUL / file-adapter events | Artifact retention (`days_retention` — configurable) | Set `days_retention: 365` or route to cold storage |
| FIM hits | 90 days Insight | Same as EDR telemetry — S3 cold archival |
| Cases | Indefinite retention in ext-cases | No additional config required |

**Recommended deployment pattern for SOC 2 Type II:**

1. Enable Insight for 90-day hot retention (default)
2. Configure S3 or GCS output streaming `event`, `detect`, and `audit` streams — provides 12-month+ archival for auditor evidence requests
3. Use Cases for case-level narrative — Cases persist beyond Insight retention
4. Document the retention architecture in the SOC 2 system description

---

## Deployment Architecture

```
                          ┌── Insight (90+ day hot) ─► LCQL search (auditor evidence queries)
                          │
Endpoints ──► LC Sensor ──┼── D&R Engine ─► Detections ─► Cases (CC7.3, CC7.4)
(Win/Linux/Mac)           │                │
                          │                └─► Outputs
                          │                      ├─► SIEM (CC4.1)
                          │                      ├─► S3/GCS cold (12-month retention)
                          │                      └─► Ticketing / Chat (CC2.1)
                          │
                          └── FIM / YARA / Artifact Collection
                              (CC6.8, CC7.1, CC8.1)
```

---

## Criteria-to-Capability Quick Reference

| Criterion | Primary LC Capability | Platform Coverage |
|---|---|---|
| CC2.1 | Outputs, audit stream, Cases | All |
| CC3.2 | Telemetry volume / detection metrics | All |
| CC4.1 | D&R engine (ongoing monitoring) | All |
| CC4.2 | Detections + Cases | All |
| CC6.1 | `WEL` 4624/4625 (Win), `USER_LOGIN`/`SSH_LOGIN` (macOS), file adapter (Linux) | Per-platform |
| CC6.2/CC6.3 | `WEL` 4720–4740 (Win), `NEW_PROCESS` on identity binaries (Linux/macOS) | All |
| CC6.6 | `WEL` RDP, `SSH_LOGIN`, firewall-change detection, `isolate network` | All |
| CC6.7 | Network telemetry, `VOLUME_MOUNT`, `DNS_REQUEST` | All |
| CC6.8 | YARA, CODE_IDENTITY, LOLBin rules, AUTORUN_CHANGE | All |
| CC7.1 | FIM, AUTORUN_CHANGE, DRIVER_CHANGE, SERVICE_CHANGE | All |
| CC7.2 | D&R engine + Soteria/Sigma | All |
| CC7.3 | Cases, detection metadata, AI SOC agents | All |
| CC7.4 | `isolate network`, `task`, Playbook, Cases | All |
| CC7.5 | `rejoin network`, Velociraptor, artifact collection | All |
| CC8.1 | ext-git-sync, audit stream, FIM on config files | All |
| CC9.1 | Service-stop detection, ransomware indicators | All |
| CC9.2 | Third-party software telemetry (CODE_IDENTITY) | All |
| A1.2 | Service-stop, ransomware, process-terminator detection | All |
| C1.1 | FIM, YARA, file-access telemetry | Win/Mac (file events), All (FIM) |
| C1.2 | `FILE_DELETE`, secure-delete tool detection | Win/Mac |

---

## Cross-Framework Notes

SOC 2 criteria overlap substantially with other frameworks:

- **ISO 27001** — Annex A controls cover similar ground, particularly A.12 (Operations Security) and A.16 (Incident Management)
- **NIST 800-53 Rev 5** — AU, AC, IA, SI, IR, CM families provide more-granular control language for the same capabilities. See [nist-800-53-limacharlie-mapping.md](../nist-800-53/nist-800-53-limacharlie-mapping.md)
- **CMMC** — For organizations holding FCI/CUI alongside SOC-2-reportable systems, see [cmmc-limacharlie-mapping.md](../cmmc/cmmc-limacharlie-mapping.md)
- **HIPAA Security Rule** — The audit, access-control, and integrity safeguards align with CC6/CC7. See [hipaa](../hipaa/) mapping
- **PCI DSS** — Requirements 10 (logging), 11 (monitoring), and 12 (incident response) align closely with CC7 and CC8. See [pci-dss](../pci-dss/) mapping

SOC 2 reports may incorporate findings from these other frameworks — a single LC deployment produces evidence for all of them simultaneously.
