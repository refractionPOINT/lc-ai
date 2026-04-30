# LimaCharlie for PCI DSS v4.0 Compliance

How LimaCharlie capabilities map to the Payment Card Industry Data Security Standard v4.0 across Windows, Linux, and macOS endpoints inside the Cardholder Data Environment (CDE). Focused on the requirements where LimaCharlie provides direct, measurable coverage: Req 1 (Network Security Controls), Req 2 (Secure Configurations), Req 5 (Anti-malware), Req 6 (Secure Systems and Software), Req 7 (Access Restriction), Req 8 (User Identification / Authentication), Req 10 (Logging and Monitoring — the heaviest-covered requirement), Req 11 (Testing), and Req 12 (Policy support).

PCI DSS v4.0 requirement IDs are referenced exactly as they appear in the standard (e.g., `10.2.1.1`, `10.4.1`, `11.5.2`). Where LimaCharlie enables detection but not enforcement (e.g., account lockout policy, firewall ruleset enforcement), the distinction is called out explicitly so compensating controls can be planned.

---

## Requirement 1 — Install and Maintain Network Security Controls

LimaCharlie does not enforce network boundary controls — that remains the responsibility of firewalls, router ACLs, and cloud security groups. However, LC provides detection-only coverage for changes to host-level network controls inside the CDE.

### Req 1.2.5 — Services, protocols, and ports identified, approved, and authorized

**LimaCharlie coverage:**
- `NEW_TCP4/6_CONNECTION`, `NEW_UDP4/6_CONNECTION` events on all three platforms expose every listening port and outbound connection with per-process attribution (`event/PROCESS/FILE_PATH`, `event/PROCESS/COMMAND_LINE`)
- LCQL queries or D&R rules identify unauthorized services/protocols

### Req 1.4.x — Network connections between trusted and untrusted networks controlled

**LimaCharlie coverage (detection only):**
- **Windows:** `WEL` Event IDs 4946–4950 — firewall rule added / modified / deleted / setting changed
- **Linux:** `NEW_PROCESS` for `iptables`, `ip6tables`, `nft`, `firewall-cmd`, `ufw` with modification arguments
- **macOS:** `NEW_PROCESS` for `/sbin/pfctl` and `/usr/libexec/ApplicationFirewall/socketfilterfw`

D&R rules alert when an in-scope CDE host modifies its host-based firewall, which PCI QSAs view as a Req 1.4 exception requiring change-ticket correlation.

### Req 1.5.1 — NSCs between CDE and third-party connections

**LimaCharlie coverage:** `NEW_TCP4/6_CONNECTION` and `DNS_REQUEST` events on CDE endpoints surface outbound destinations. Combined with an allowlist lookup (`lookup://pci-approved-destinations`), D&R rules alert on CDE host connections to unapproved external networks.

---

## Requirement 2 — Apply Secure Configurations

### Req 2.2.1 — Configuration standards developed, documented, maintained

**LimaCharlie coverage:** LC does not author configuration baselines — that remains a process control. LC provides **drift detection** against a baseline:
- **FIM rules** on configuration files produce `FIM_HIT` events when baseline files change
- **CODE_IDENTITY** events on all three platforms provide a first-seen binary inventory against which baseline approval is tracked
- **ext-git-sync** keeps LC configuration itself (D&R rules, FIM, outputs) under version control — each change is peer-reviewed and auditable

### Req 2.2.2 — Vendor default accounts managed

**LimaCharlie coverage:** Process and auth events detect default-account usage patterns:
- Windows: `WEL` 4624 with `TargetUserName` matching known defaults (`Administrator`, `Guest`)
- Linux: `NEW_PROCESS` with `USER_NAME=root` from non-console sources
- macOS: `USER_LOGIN` with the built-in `root` account

### Req 2.2.4 — Only necessary services, protocols, daemons, and functions enabled

**LimaCharlie coverage:**
- `SERVICE_CHANGE` events (Windows / Linux systemd / macOS launchd) detect new or modified services
- `NEW_TCP4/6_CONNECTION` listening sockets enumerate active services
- The `os_packages` sensor command (Windows) inventories installed software

### Req 2.2.6 — System security parameters configured to prevent misuse

**LimaCharlie coverage:** FIM rules on hardening files — `/etc/sysctl.conf`, `/etc/security/limits.conf`, `/etc/ssh/sshd_config` on Linux; registry hardening keys on Windows; `/Library/Preferences/com.apple.security.plist` on macOS.

---

## Requirement 5 — Protect All Systems and Networks from Malicious Software

### Req 5.2.1 — Anti-malware solution deployed on all in-scope system components

**LimaCharlie coverage:**
- **YARA scanning** — platform-native YARA execution on file writes, process memory, or ad-hoc. Produces `YARA_DETECTION` events on Windows, Linux, and macOS
- **Windows Defender integration** via the EPP extension — Defender threat events flow as `WEL` for correlation
- **Managed detection rulesets** — Soteria EDR Rules and community/commercial Sigma rulesets extend coverage

### Req 5.2.2 — Anti-malware solution detects / removes / blocks known and unknown malware

**LimaCharlie coverage:** D&R rules with `YARA_DETECTION` trigger automated `isolate network` or `task` actions. `CODE_IDENTITY` first-seen analysis surfaces previously unknown binaries for analyst triage.

### Req 5.2.3 — Anti-malware solution actively running and cannot be disabled

**LimaCharlie coverage:**
- The LC sensor itself reports as offline in the fleet view if tampered with
- `WEL` Event ID 5001 (Defender real-time protection disabled) + `WEL` 1102 (Security log cleared) + auditd tampering detections (Linux) + `log erase` detection (macOS) together cover attempts to disable telemetry
- Sensor offline alerts via deployment stream

### Req 5.3.1 — Anti-malware solution kept current (signatures / behavioral updates)

**LimaCharlie coverage:** YARA rulesets via ext-git-sync or managed rule subscriptions (Soteria, Sigma). Managed ruleset versions are tracked in the platform audit log. LC's EDR detection logic is behavioral rather than signature-based — no signature update cycle is required for the EDR layer.

### Req 5.3.2 — Periodic scans / continuous behavioral analysis

**LimaCharlie coverage:** YARA can be triggered on file write (`YARA_DETECTION` on `FILE_CREATE`) or run ad-hoc against the fleet via `limacharlie yara run`. D&R rules provide continuous behavioral analysis — no scheduled scan is required since every process, file, registry, and network event is evaluated in real time.

### Req 5.3.3 — Removable media scanned when connected

**LimaCharlie coverage (Windows, macOS only):** `VOLUME_MOUNT` / `VOLUME_UNMOUNT` events fire on Windows and macOS. A D&R rule on `VOLUME_MOUNT` can trigger a YARA scan (`task` action with a YARA rule URL) across the mounted volume. Linux lacks native volume events in the LC sensor.

---

## Requirement 6 — Develop and Maintain Secure Systems and Software

### Req 6.3.3 — Security patches / updates installed

**LimaCharlie coverage:** Not an enforcement or deployment capability — LC provides **telemetry for verification**:
- `CODE_IDENTITY` hash + path + signature for every binary loaded (Win/Linux/macOS)
- `os_version` sensor command reports OS build across all platforms
- `os_packages` sensor command inventories installed packages (Windows)
- Custom fleet tasking via the `fleet-payload-tasking` skill surveys patch levels on Linux (`dpkg -l`, `rpm -qa`) and macOS (`softwareupdate --history`)

### Req 6.4.1 — Public-facing web apps protected against attacks (WAF equivalent)

**LimaCharlie coverage:** Not a WAF. LC provides post-exploitation visibility — detection of web-shell drops, LOLBin abuse under `w3wp.exe` / `nginx` / `httpd` parents, and outbound C2 from web-server processes.

### Req 6.5.x — Changes to system components managed

**LimaCharlie coverage:**
- `FIM_HIT` events on application directories, binaries, config files
- `CODE_IDENTITY` exposes hash + signature of every loaded binary — unknown hash on a production-tagged host is actionable
- **ext-git-sync** keeps LC config under version control for the LC components themselves

---

## Requirement 7 — Restrict Access to System Components and Cardholder Data by Business Need to Know

### Req 7.2.1 — Access control model defined

LimaCharlie coverage is detection-oriented; access model definition is a process control.

### Req 7.2.4 — Access reviews performed regularly

**LimaCharlie coverage:** LCQL queries surface all users who executed on CDE-tagged endpoints in the review window. Combined with AD group membership (from `WEL` 4728/4732/4756 events), quarterly access reviews can be generated programmatically.

### Req 7.2.5 — Application / system access managed

**LimaCharlie coverage:**
- **Windows:** `WEL` Event ID 4672 (special privileges assigned to new logon), 4673/4674 (privileged service / object) surface privileged-function execution
- **Linux:** `NEW_PROCESS` for `sudo`, `su`, `pkexec`, `doas` with full command-line and user context
- **macOS:** `NEW_PROCESS` for `sudo`, `security authorize`

### Req 7.3.x — Access control system deny-by-default

Enforcement is OS-level. LC detects privilege escalations that bypass the policy.

---

## Requirement 8 — Identify Users and Authenticate Access to System Components

### Req 8.2.1 — All users identified with unique ID

**LimaCharlie coverage:** Every `NEW_PROCESS` event includes `USER_NAME` context. On macOS, `USER_LOGIN` / `SSH_LOGIN` establish session boundaries. On Windows, `WEL` 4624/4634 combined with process-event user context provides attribution. On Linux, user context is present in process events; session boundaries come from the auth log file adapter.

### Req 8.2.4 — User account lifecycle events logged

**LimaCharlie coverage:**
- **Windows:** `WEL` 4720 (created), 4722 (enabled), 4725 (disabled), 4726 (deleted), 4738 (changed), 4728 / 4732 / 4756 (group additions)
- **Linux:** `NEW_PROCESS` for `useradd`, `usermod`, `userdel`, `groupadd`, `gpasswd`; file-adapter auth events from `/var/log/auth.log`
- **macOS:** `NEW_PROCESS` for `dscl`, `sysadminctl`, `dsimport`; `MUL` events on `subsystem == "com.apple.opendirectoryd"`

### Req 8.3.x — Strong authentication

Enforcement is OS / IdP level. LC detects:
- Password changes (Windows `WEL` 4723 / 4724, Linux `passwd`/`chage` process execution, macOS `passwd` / `dscl . passwd`)
- NTLM authentication events (`WEL` 4776) — helps with Req 8.3.11 where LANMAN / NTLMv1 must be disabled

### Req 8.3.4 — Repeated failed access attempts limited

**LimaCharlie coverage:** LC detects — it does not enforce lockout (OS / IdP responsibility).
- **Windows:** `WEL` 4625 (failed logon) + 4740 (account locked)
- **Linux:** `/var/log/auth.log` / `/var/log/secure` via file adapter; PAM failure patterns
- **macOS:** `MUL` events matching `(authentication failure|failed password)` patterns — `SSH_LOGIN` has NO `IS_SUCCESS` field (fires only on success), so failed SSH on macOS must be caught in `MUL`

### Req 8.5.1 — MFA implemented appropriately

Enforcement and configuration is IdP / OS level. LC detects anomalous auth patterns that indicate MFA bypass:
- Successful logon from an IP not seen in the prior 30 days (D&R rule against `WEL` 4624 + private IP lookup)
- Successful logon outside business hours
- Kerberos TGT with unusual `encryption type` on Windows (pass-the-ticket)

### Req 8.6.1 — Accounts used by systems and applications managed

**LimaCharlie coverage:** Service-account process execution is fully visible via `NEW_PROCESS`. D&R rules alert when a service account executes an interactive command (shell, RDP, SSH).

---

## Requirement 10 — Log and Monitor All Access to System Components and Cardholder Data

**The heaviest-covered PCI DSS requirement for LimaCharlie.** LC's core value prop is real-time EDR telemetry + D&R engine, which maps directly to Req 10's audit logging and monitoring obligations.

### Req 10.2.1 — Audit logs enabled and active for all system components

**LimaCharlie coverage:** The LC EDR sensor natively emits the events below. Platform coverage reflects actual sensor capability.

| Event | Windows | Linux | macOS | Purpose |
|---|---|---|---|---|
| `NEW_PROCESS`, `EXISTING_PROCESS`, `TERMINATE_PROCESS` | ✅ | ✅ | ✅ | Process lifecycle with parent-child, command-line, user |
| `DNS_REQUEST` | ✅ | ✅ | ✅ | DNS queries with responses |
| `NEW_TCP4/6_CONNECTION`, `NEW_UDP4/6_CONNECTION` | ✅ | ✅ | ✅ | Connection establishment with process attribution |
| `CODE_IDENTITY` | ✅ | ✅ | ✅ | Hash + path + signature combinations |
| `YARA_DETECTION` | ✅ | ✅ | ✅ | YARA rule match on file or memory |
| `FIM_HIT` | ✅ | ✅ | ✅ | File / directory / registry modification |
| `SERVICE_CHANGE` | ✅ | ✅ | ✅ | Service / systemd / launchd change |
| `FILE_CREATE`, `FILE_DELETE`, `FILE_MODIFIED` | ✅ | ❌ | ✅ | Native file events — Linux uses FIM |
| `MODULE_LOAD` | ✅ | ✅ | ❌ | DLL / shared-object loads |
| `WEL` | ✅ | ❌ | ❌ | Windows Event Log stream |
| `MUL` | ❌ | ❌ | ✅ | macOS Unified Log stream |
| `USER_LOGIN`, `USER_LOGOUT`, `SSH_LOGIN`, `SSH_LOGOUT` | ❌ | ❌ | ✅ | Session boundaries — macOS only |
| `AUTORUN_CHANGE`, `DRIVER_CHANGE`, `REGISTRY_*` | ✅ | ❌ | ❌ | Persistence / registry |
| `SENSITIVE_PROCESS_ACCESS`, `THREAD_INJECTION` | ✅ | ❌ | ❌ | Injection / credential-dump indicators |
| `NEW_NAMED_PIPE`, `HIDDEN_MODULE_DETECTED`, `MODULE_MEM_DISK_MISMATCH` | ✅ | ✅/❌ | ❌ | Advanced tradecraft |
| `USER_OBSERVED` | ✅ | ✅ | ✅ | User session observation (all platforms) |

**Linux auth-event caveat:** The LC Linux sensor does **not** emit `USER_LOGIN` or `SSH_LOGIN`. For equivalent telemetry, deploy a LimaCharlie **file adapter** streaming `/var/log/auth.log` or `/var/log/secure`, or an auditd file adapter.

### Req 10.2.1.1 — Audit logs capture all individual user access to cardholder data

**LimaCharlie coverage:** `FIM_HIT` on CDE data paths correlated with process-level `USER_NAME` provides per-user attribution. FIM rules defined on PAN storage directories (`/var/pci/*`, `D:\CDE\*`) produce events with the accessing process and user.

### Req 10.2.1.2 — Audit logs capture all actions taken by any individual with administrative access

**LimaCharlie coverage:**
- Windows: `WEL` 4672 (special privileges), 4673 / 4674 (privileged service / object), 4688 (process creation with token elevation)
- Linux: `NEW_PROCESS` for `sudo` / `su` / `pkexec` plus child-process tracing for full admin-session capture
- macOS: `NEW_PROCESS` for `sudo`, `security authorize`; `MUL` events with `subsystem == "com.apple.sudo"`

### Req 10.2.1.3 — Audit logs capture access to all audit logs

**LimaCharlie coverage:**
- Windows: `WEL` 1102 (Security log cleared), 4719 (audit policy changed)
- Linux: FIM on `/var/log/audit/audit.log` and `/etc/audit/*`; `NEW_PROCESS` for `auditctl`, `ausearch`, `aureport`
- macOS: `NEW_PROCESS` for `log erase`, `log config --mode "level:off"`

### Req 10.2.1.4 — Audit logs capture invalid logical access attempts

**LimaCharlie coverage:** `WEL` 4625 (failed logon) on Windows; file-adapter `auth.log` lines on Linux; `MUL` authentication failure patterns on macOS.

### Req 10.2.1.5 — Audit logs capture changes to identification and authentication credentials

**LimaCharlie coverage:**
- Windows: `WEL` 4720 / 4722 / 4723 / 4724 / 4725 / 4726 / 4738 / 4740 / 4767 / 4776
- Linux: `NEW_PROCESS` for `passwd` / `chage` / `useradd` / `usermod`; FIM on `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`
- macOS: `NEW_PROCESS` for `passwd`, `dscl`, `sysadminctl`; FIM on `/etc/sudoers`

### Req 10.2.1.6 — Initialization, stopping, or pausing of audit logs

**LimaCharlie coverage:** Detections named in the implementation doc for `auditd` tamper, `eventlog` service stop, `log erase` / `log config` on macOS.

### Req 10.2.1.7 — Creation and deletion of system-level objects

**LimaCharlie coverage:** `NEW_PROCESS`, `SERVICE_CHANGE`, `DRIVER_CHANGE`, `AUTORUN_CHANGE`, FIM on system directories.

### Req 10.2.2 — Audit logs record, for each event: user, event type, date/time, success/failure, origination, affected data/resource

**LimaCharlie coverage:** Every event includes `routing.event_time` (ms epoch UTC), `routing.hostname`, `routing.sid`, `routing.platform`, and event-specific fields (`COMMAND_LINE`, `FILE_PATH`, `USER_NAME`, `PARENT`, source/destination IP for network events, etc.). These fields collectively satisfy the six Req 10.2.2 data points for each event type.

### Req 10.3.1 — Read access to audit logs limited to need-to-know

**LimaCharlie coverage:** Platform RBAC — API keys with granular permissions (`insight.evt.get`, `dr.list`, etc.); org membership and group-based permissions for console users.

### Req 10.3.2 — Audit log files protected to prevent modifications

**LimaCharlie coverage:** Insight events are immutable — no user-facing API exposes individual event modification or deletion. Once an event reaches the cloud, it is write-once within the retention window.

### Req 10.3.3 — Audit log files promptly backed up to an internal log server or media

**LimaCharlie coverage:** **Outputs** to S3, GCS, Azure Blob Storage, Chronicle, Splunk, Elastic, or SIEM forward events to internal retention infrastructure in near real-time (seconds to minutes). The output latency is visible in the audit stream.

### Req 10.3.4 — File integrity monitoring or change-detection on audit logs

**LimaCharlie coverage:** FIM rules on log file paths — `C:\Windows\System32\winevt\Logs\*.evtx` (Windows), `/var/log/*` (Linux), `/var/log/` + `/private/var/log/` (macOS). `FIM_HIT` events alert on any modification to audit log files themselves.

### Req 10.4.1 — Audit logs reviewed at least once daily

**LimaCharlie coverage:**
- **D&R rules** evaluate events in real-time, producing detections — effectively continuous automated review
- **LCQL** provides interactive search, filtering, and correlation across the 90-day hot window
- **Cases extension (ext-cases)** provides SOC triage, assignment, SLA tracking, and investigation workflows for human review
- **Outputs** route detections to SIEM, case management, ticketing, or chat tools for recorded daily review

Automated review (D&R engine) satisfies the intent of 10.4.1.1 continuous automated mechanisms.

### Req 10.4.1.1 — Automated mechanisms to perform audit log review

**LimaCharlie coverage:** The D&R engine is exactly this — automated rule evaluation against every event in real time, producing structured detections with priority, MITRE tagging, and suppression.

### Req 10.4.2 — Logs of critical system components reviewed periodically

**LimaCharlie coverage:** LCQL saved queries + dashboards (Web UI) provide curated views. Detection output streams surface priority findings for human review. Cases provide the audit trail for review evidence.

### Req 10.4.3 — Exceptions / anomalies identified during review are addressed

**LimaCharlie coverage:** ext-cases tracks detection-to-resolution workflow with analyst notes, classification, SLA. Every detection that converts to a case generates an audit trail suitable for QSA evidence.

### Req 10.5.1 — Audit log history retained for at least 12 months, with at least 3 months immediately available for analysis

**LimaCharlie coverage — IMPORTANT:**
- **Insight default retention = 90 days = 3 months immediately available ✅** — this directly satisfies the "3 months immediately available" clause
- **9 months cold archival required** — configure an S3 or GCS output to send all events to object storage with object-lock (WORM) policies. This provides the remaining 9 months without LC-side cost or expiration
- Extended Insight retention tiers (180 / 365 day) are available via platform configuration for orgs preferring hot-only retention

**Reference architecture for Req 10.5.1:**

```
Endpoints ──► LC Sensor ──► Insight (90d hot, searchable via LCQL)
                        │
                        └──► S3/GCS output (12+ months cold, immutable via object-lock)
```

### Req 10.6.x — Time-synchronization mechanisms

**LimaCharlie coverage:**
- `routing.event_time` is millisecond-precision UTC epoch, generated at the sensor
- `routing.latency` shows cloud-receipt delta — organizations alert on excessive latency as a clock-drift indicator
- Time-sync configuration is OS-level; LC provides FIM on `/etc/chrony.conf`, `/etc/ntp.conf`, Windows time-service registry keys to detect tampering

### Req 10.7.1 — Failures of critical security control systems detected, alerted on, and addressed promptly

**LimaCharlie coverage:**
- **Sensor heartbeat monitoring** — sensors report a continuous heartbeat to the cloud. `deployment` output stream captures enrollment/disconnection events. D&R rules alert when a CDE-tagged sensor goes offline
- **Defender RTP disabled** (`WEL` 5001) detection
- **Audit tamper** detections (eventlog service stop, auditd disable, macOS log erase)
- **Output delivery failures** surface in the `audit` stream — alert when a SIEM output fails to deliver

### Req 10.7.2 — Failure of any critical security control response

**LimaCharlie coverage:** ext-cases + output to ticketing (ServiceNow, Jira, PagerDuty) ensures failures are assigned and resolved with a recorded owner and timestamp.

### Req 10.7.3 — Failures addressed promptly

LC provides detection and ticket routing — remediation is a process control.

---

## Requirement 11 — Test Security of Systems and Networks Regularly

### Req 11.3.x — Internal / external vulnerability scans

LimaCharlie is not a vulnerability scanner. LC provides input data for vulnerability correlation:
- `os_version` (all platforms) — OS and kernel build
- `os_packages` (Windows) — installed software inventory
- `CODE_IDENTITY` — loaded binary hash + signature + path
- The `fleet-payload-tasking` skill pushes ad-hoc vulnerability-sweep scripts to all platforms

### Req 11.4.x — Penetration testing

LimaCharlie is not a pen-test tool. LC captures telemetry during pen tests so blue-team detection coverage can be evaluated against red-team activity.

### Req 11.5.1 — Intrusion-detection and/or intrusion-prevention techniques used

**LimaCharlie coverage:** LC is a platform-native intrusion detection system. All D&R rules in the implementation doc contribute. SI-4-style coverage for host-based IDS is direct.

### Req 11.5.2 — Change-detection mechanism deployed (specifically calls out FIM)

**LimaCharlie coverage — directly satisfies:**
- **FIM rules** generate `FIM_HIT` events on monitored files, directories, and Windows registry keys on all three platforms
- Rules compare a weekly or monthly baseline; `FIM_HIT` events alert on deltas
- See Section 4 of the implementation doc for required FIM coverage paths per platform

PCI DSS v4.0 Req 11.5.2 explicitly names FIM as the expected mechanism. LC directly satisfies the control.

### Req 11.6.1 — Change- and tamper-detection on payment pages

Out of scope for LC (web-server layer). LC provides complementary coverage for the underlying host.

---

## Requirement 12 — Support Information Security with Organizational Policies and Programs

LC is primarily a technical-control platform. Req 12 is heavily process-oriented. Direct coverage:

### Req 12.10.x — Incident response plan

**LimaCharlie coverage:**
- **Cases extension (ext-cases)** provides the full incident lifecycle: detection-to-case conversion, severity, assignment, SLA tracking, analyst notes, conclusion, and audit trail — the working evidence a QSA expects under Req 12.10
- **Playbook extension** for Python-based response automation and enrichment
- **Automated response actions** (`isolate network`, `add tag`, `task`) execute on rule match without analyst intervention

### Req 12.5.1 — Inventory of system components in scope

**LimaCharlie coverage:** The sensor fleet view + `os_version` + `os_packages` + sensor tags (`cde`, `pci-in-scope`) provide a live inventory of systems running the LC agent. Combined with adapter data, this functions as a CDE component inventory with real-time state.

### Req 12.9.x — Service provider responsibilities documented

LC itself is a service provider to the customer. LC's SOC 2 Type II, ISO 27001, and other attestations cover this.

---

## Baseline Applicability — PCI DSS v4.0 Milestones

PCI DSS v4.0 contains both "Defined Approach" requirements (required for all entities) and "Customized Approach" (risk-based alternatives requiring QSA review). The table below maps coverage to Defined Approach Req IDs only.

| Requirement | Direct LC Coverage | Partial | Process-Only |
|---|---|---|---|
| 1.2.5, 1.4.x, 1.5.1 | | ✅ | |
| 2.2.1, 2.2.4, 2.2.6 | | ✅ | |
| 2.2.2 | ✅ | | |
| 5.2.1, 5.2.2, 5.2.3, 5.3.2 | ✅ | | |
| 5.3.1, 5.3.3 | | ✅ | |
| 6.3.3, 6.5.x | | ✅ | |
| 6.4.1 | | | ✅ |
| 7.2.4, 7.2.5 | ✅ | | |
| 7.2.1, 7.3.x | | | ✅ |
| 8.2.1, 8.2.4, 8.3.4 | ✅ | | |
| 8.3.x, 8.5.1, 8.6.1 | | ✅ | |
| 10.2.1.x (all sub-reqs) | ✅ | | |
| 10.2.2 | ✅ | | |
| 10.3.1, 10.3.2, 10.3.3, 10.3.4 | ✅ | | |
| 10.4.1, 10.4.1.1, 10.4.2, 10.4.3 | ✅ | | |
| 10.5.1 | ✅ (with cold archival) | | |
| 10.6.x | | ✅ | |
| 10.7.1, 10.7.2 | ✅ | | |
| 11.5.1, 11.5.2 | ✅ | | |
| 11.3.x, 11.4.x, 11.6.1 | | | ✅ |
| 12.10.x | ✅ | | |
| 12.5.1 | | ✅ | |

---

## Data Retention Guidance (Req 10.5.1)

PCI DSS Req 10.5.1 mandates **12 months retention with 3 months immediately available for analysis**.

- **Insight default (90 days) = 3 months immediately available ✅** — satisfies the "immediately available" clause
- **Cold archival of the remaining 9 months is required** — configure an S3 or GCS output with:
  - Object-lock / WORM (write-once-read-many) policies for tamper resistance
  - Lifecycle rules moving objects to Glacier / Coldline after 90 days to minimize cost
  - Minimum 12-month retention before any deletion
- Alternative: an extended Insight hot-retention tier (180 / 365 day) eliminates the need for cold archival but at higher cost

See the implementation doc (Section 14) for S3 output configuration with WORM settings.

---

## Deployment Architecture

```
                          ┌── Insight (90d hot = 3 months for Req 10.5.1) ─► LCQL search
                          │
CDE Endpoints ──► LC Sensor ──┼── D&R Engine (real-time Req 10.4.1.1) ─► Outputs
(Win/Linux/Mac)               │                                      ├─► SIEM (daily review)
                              │                                      ├─► S3/GCS WORM (9-12 months cold for Req 10.5.1)
                              └── Artifact / FIM / YARA              └─► Cases (Req 10.4.3, Req 12.10.x)
                                  (Req 11.5.2, Req 5.2)
```

- Tag CDE-scope sensors with `cde` or `pci-in-scope` and filter outputs / rules by that tag to scope telemetry
- D&R engine delivers Req 10.4.1.1 continuous automated review
- Insight hot retention delivers Req 10.5.1 "3 months immediately available"
- S3/GCS output with WORM delivers Req 10.5.1 12-month retention
- ext-cases delivers Req 10.4.3 and Req 12.10.x incident lifecycle

---

## Cross-Framework Notes

PCI DSS v4.0 shares significant control surface with:

- **NIST SP 800-53 Rev 5** — the AU, AC, IA, SI families have direct PCI Req 10 overlap. See [nist-800-53-limacharlie-mapping.md](../nist-800-53/nist-800-53-limacharlie-mapping.md)
- **CMMC / NIST 800-171** — 800-171 family 3.3 (Audit) overlaps PCI Req 10. See [cmmc-limacharlie-mapping.md](../cmmc/cmmc-limacharlie-mapping.md)
- **SOC 2 (Common Criteria CC7)** — monitoring and detection obligations share coverage
- **HIPAA Security Rule** — §164.308(a)(1)(ii)(D) audit controls share coverage with Req 10

Orgs subject to multiple frameworks can use a single LC deployment with framework-specific tags (`pci-dss`, `nist-800-53`, `hipaa`) on D&R rules to scope reporting.
