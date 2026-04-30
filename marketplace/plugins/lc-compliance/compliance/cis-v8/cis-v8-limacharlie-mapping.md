# LimaCharlie for CIS Critical Security Controls v8

How LimaCharlie capabilities map to the CIS Critical Security Controls v8 (released 2021), across Windows, Linux, and macOS endpoints. CIS v8 organises 18 Controls into **Safeguards** numbered `<control>.<safeguard>`, each tagged with an **Implementation Group (IG1, IG2, IG3)** — IG1 is the minimum for any organisation, IG2 adds essentials for medium-sized organisations, IG3 covers advanced capability for large/regulated organisations.

This document focuses on the controls where LimaCharlie provides direct, measurable coverage. For the deployable D&R rules, FIM rules, and adapter configs, see [cis-v8-limacharlie-implementation.md](cis-v8-limacharlie-implementation.md).

Event-to-platform coverage reflects actual sensor capability (per the LC EDR events reference) — it is not a superset. For the underlying event matrix, see [../nist-800-53/nist-800-53-limacharlie-mapping.md](../nist-800-53/nist-800-53-limacharlie-mapping.md#au-2--event-logging--au-3--content-of-audit-records--au-12--audit-record-generation).

---

## Control 1 — Inventory and Control of Enterprise Assets

Goal: actively manage (inventory, track, correct) all enterprise assets.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 1.1 | IG1 | Establish and Maintain Detailed Enterprise Asset Inventory | Partial. Every enrolled LC sensor contributes an asset record: `routing.sid` (unique ID), `routing.hostname`, `routing.platform`, `routing.arch`, `routing.int_ip`, `routing.ext_ip`, install date, and the last-seen timestamp. Query the inventory with `limacharlie sensors list` or LCQL on the fleet table. LC is an inventory **signal**, not a system of record — pair with an ITAM tool. |
| 1.2 | IG1 | Address Unauthorized Assets | Partial. LC cannot scan a network for unenrolled devices. Where network monitoring is in place (Zeek extension on a Linux network sensor, DHCP log adapter), unknown IPs or MAC addresses can be surfaced via D&R rules and correlated against the known-sensor list. |
| 1.3 | IG2 | Utilize an Active Discovery Tool | No direct LC role. LC is agent-based, not a network scanner. |
| 1.4 | IG2 | Use DHCP Logging to Update Enterprise Asset Inventory | Partial — a file/syslog adapter on DHCP server logs can ingest lease events for correlation against the LC sensor roster. |
| 1.5 | IG3 | Use a Passive Asset Discovery Tool | Partial — the Zeek extension on a Linux sensor positioned on a monitoring port provides passive discovery signal. |

**Net coverage:** LC is authoritative for the *managed-endpoint* portion of the asset inventory; external tooling is still needed for networked devices without an LC agent.

---

## Control 2 — Inventory and Control of Software Assets

Goal: actively manage (inventory, track, correct) all software on the network, so that only authorised software is installed and can execute.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 2.1 | IG1 | Establish and Maintain a Software Inventory | The `os_packages` sensor command inventories installed packages on Windows (MSI / registry-based). On Linux, `os_packages` returns dpkg/rpm inventory. On macOS, use Velociraptor artifacts or a `shell` task running `pkgutil --pkgs`. `CODE_IDENTITY` events give a first-seen record of every signed/unsigned binary loaded. |
| 2.2 | IG1 | Ensure Authorized Software is Currently Supported | Partial. `os_version` returns kernel/build; `os_packages` returns versions. Joined against an end-of-life lookup, D&R rules or scheduled LCQL queries can surface unsupported software. |
| 2.3 | IG1 | Address Unauthorized Software | Detection. D&R rules on `NEW_PROCESS` or `CODE_IDENTITY` match paths/hashes against an allow-list lookup; mismatches generate a detection. Enforcement (uninstall/blocking) is not a native LC capability — WDAC / AppLocker / Gatekeeper remain the enforcement surface. |
| 2.4 | IG2 | Utilize Automated Software Inventory Tools | `os_packages` can be pushed fleet-wide via reliable tasking; results are retrievable through LCQL. |
| 2.5 | IG2 | Allowlist Authorized Software | Detection-only. Paired with a lookup of approved hashes, D&R rules alert on unknown binaries via `CODE_IDENTITY`. |
| 2.6 | IG2 | Allowlist Authorized Libraries | `MODULE_LOAD` events on Windows and Linux (not macOS) expose DLL / shared-object loads for allow-listing. |
| 2.7 | IG3 | Allowlist Authorized Scripts | Detection. `NEW_PROCESS` events for `powershell.exe`, `wscript.exe`, `cscript.exe`, `osascript`, interpreter-on-Linux invocations with full command-line and script path. |

**Net coverage:** LC provides an *observed* software inventory and runs allowlist checks as detections. It does not **prevent** execution of unauthorised software — that requires the platform's own allowlisting (AppLocker, WDAC, Gatekeeper).

---

## Control 3 — Data Protection

Goal: develop processes and controls to identify, classify, securely handle, retain, and dispose of data.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 3.1 | IG1 | Establish and Maintain a Data Management Process | No LC role. |
| 3.2 | IG1 | Establish and Maintain a Data Inventory | No direct role. LC can stream file-access telemetry (`FILE_CREATE`, `NEW_DOCUMENT`, `FILE_TYPE_ACCESSED`) to feed an external DLP classifier. |
| 3.3 | IG1 | Configure Data Access Control Lists | No LC role — OS/file-server capability. |
| 3.4 | IG1 | Enforce Data Retention | No LC role for enterprise data. For audit data, Insight default retention and S3/GCS output cover LC's own logs. |
| 3.6 | IG1 | Encrypt Data on End-User Devices | No LC role — Bitlocker / FileVault / LUKS are the enforcement surface. LC can *detect* encryption state via `wel://Microsoft-Windows-BitLocker/BitLocker Management` artifact collection and `NEW_PROCESS` on `manage-bde`, `fdesetup`, `cryptsetup`. |
| 3.10 | IG2 | Encrypt Sensitive Data in Transit | No LC role. |
| 3.11 | IG2 | Encrypt Sensitive Data at Rest | No LC role (monitoring only, as 3.6). |
| 3.12 | IG2 | Segment Data Processing and Storage | No LC role. |
| 3.13 | IG3 | Deploy a Data Loss Prevention Solution | Partial. LC detects indicators of exfiltration — large outbound transfers via `NEW_TCP_CONNECTION` byte counts (where available), cloud-storage CLI invocations (`aws s3 cp`, `gsutil`, `rclone`, `mega-cli`), uncommon USB mount events (`VOLUME_MOUNT` on Win/Mac), archive creation preceding upload. Not a DLP replacement. |
| 3.14 | IG3 | Log Sensitive Data Access | Detection. FIM rules on sensitive directories produce `FIM_HIT` events when files are read (platform-dependent) / modified. Credential-material access (LSASS on Windows, `/etc/shadow` on Linux, keychain on macOS) is directly detectable. |

**Net coverage:** LC augments DLP with behavioural indicators but does not classify data.

---

## Control 4 — Secure Configuration of Enterprise Assets and Software

Goal: maintain the secure configuration of enterprise assets and software.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 4.1 | IG1 | Establish and Maintain a Secure Configuration Process | No LC role (policy artefact). |
| 4.2 | IG1 | Establish and Maintain a Secure Configuration Process for Network Infrastructure | No LC role. |
| 4.3 | IG1 | Configure Automatic Session Locking on Enterprise Assets | No LC role — OS setting. |
| 4.4 | IG1 | Implement and Manage a Firewall on Servers | Detection. `WEL` 4946–4950 (Windows Firewall changes), `NEW_PROCESS` for `iptables`/`nft`/`firewall-cmd`/`ufw` (Linux), `pfctl`/`socketfilterfw` (macOS). |
| 4.5 | IG1 | Implement and Manage a Firewall on End-User Devices | Same as 4.4. |
| 4.6 | IG1 | Securely Manage Enterprise Assets and Software | Detection. Administrative protocols (RDP `WEL 4624 LogonType=10`, SSH on macOS via `SSH_LOGIN`, `NEW_PROCESS` on `winrm`, `psexec`, `ssh`) are surfaced. |
| 4.7 | IG1 | Manage Default Accounts on Enterprise Assets and Software | Detection. `WEL` 4720/4722/4725/4726/4738/4767 on Windows; `NEW_PROCESS` on `useradd`/`usermod` (Linux) and `dscl` (macOS) capture default-account changes. |
| 4.8 | IG2 | Uninstall or Disable Unnecessary Services | Detection via `SERVICE_CHANGE`. `WEL` 7040/7045 for service state and install changes. |
| 4.9 | IG2 | Configure Trusted DNS Servers on Enterprise Assets | Detection. FIM on `/etc/resolv.conf` (Linux), `/etc/resolver/*` (macOS), registry keys under `Tcpip\Parameters` (Windows). |
| 4.10 | IG2 | Enforce Automatic Device Lockout on Portable End-User Devices | No LC role. |
| 4.11 | IG2 | Enforce Remote Wipe Capability on Portable End-User Devices | No LC role (MDM). |
| 4.12 | IG3 | Separate Enterprise Workspaces on Mobile End-User Devices | No LC role. |

**Net coverage:** LC detects drift from a documented baseline via FIM + D&R rules. Enforcement is an OS/MDM responsibility.

---

## Control 5 — Account Management

Goal: use processes and tools to assign and manage authorisation to credentials.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 5.1 | IG1 | Establish and Maintain an Inventory of Accounts | Partial. `USER_OBSERVED` on all platforms records observed users. Windows: `WEL 4720/4722/4725/4726`. Linux: `NEW_PROCESS` on `useradd`/`usermod`/`userdel` plus FIM on `/etc/passwd`. macOS: `NEW_PROCESS` on `dscl`/`sysadminctl`. |
| 5.2 | IG1 | Use Unique Passwords | No LC role. |
| 5.3 | IG1 | Disable Dormant Accounts | Detection. Absence of login events for N days is calculable via LCQL aggregation over `WEL 4624` (Windows) and `USER_LOGIN`/`SSH_LOGIN` (macOS). Linux requires auth-log adapter. |
| 5.4 | IG1 | Restrict Administrator Privileges to Dedicated Administrator Accounts | Detection. `WEL 4672` captures privileged logons; rules alert when a non-admin-named account receives privileges. |
| 5.5 | IG2 | Establish and Maintain an Inventory of Service Accounts | Partial — service accounts surface as `NEW_PROCESS` events with distinctive `USER_NAME` values; LCQL aggregation builds the inventory. |
| 5.6 | IG2 | Centralize Account Management | No LC role — IdP capability. |

**Net coverage:** LC provides the event stream for account-lifecycle auditing but does not manage accounts.

---

## Control 6 — Access Control Management

Goal: use processes and tools to create, assign, manage, and revoke access credentials and privileges.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 6.1 | IG1 | Establish an Access Granting Process | No LC role. |
| 6.2 | IG1 | Establish an Access Revoking Process | No LC role. |
| 6.3 | IG1 | Require MFA for Externally-Exposed Applications | No LC role. |
| 6.4 | IG1 | Require MFA for Remote Network Access | No LC role. |
| 6.5 | IG1 | Require MFA for Administrative Access | No LC role — IdP capability. |
| 6.6 | IG2 | Establish and Maintain an Inventory of Authentication and Authorization Systems | Partial — detection of auth-server contact via `NEW_TCP_CONNECTION` to LDAP/Kerberos/RADIUS/SAML endpoints. |
| 6.7 | IG2 | Centralize Access Control | No LC role. |
| 6.8 | IG3 | Define and Maintain Role-Based Access Control | No LC role for enterprise systems. Within LC itself, API keys and user permissions are scoped per action. |

**Net coverage:** Detection — `WEL 4672/4673/4674` (Windows privileged use), `NEW_PROCESS` on `sudo`/`su`/`pkexec` (Linux), `sudo`/`security authorize` (macOS).

---

## Control 7 — Continuous Vulnerability Management

Goal: develop a plan to continuously assess and track vulnerabilities.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 7.1 | IG1 | Establish and Maintain a Vulnerability Management Process | No LC role (policy). |
| 7.2 | IG1 | Establish and Maintain a Remediation Process | No LC role. |
| 7.3 | IG1 | Perform Automated Operating System Patch Management | No LC role. |
| 7.4 | IG1 | Perform Automated Application Patch Management | No LC role. |
| 7.5 | IG2 | Perform Automated Vulnerability Scans of Internal Enterprise Assets | Partial. `os_packages` + `os_version` inventories, joined against a CVE-feed lookup, flag vulnerable versions. Not a vulnerability scanner replacement. |
| 7.6 | IG2 | Perform Automated Vulnerability Scans of Externally-Exposed Enterprise Assets | No LC role. |
| 7.7 | IG2 | Remediate Detected Vulnerabilities | No direct role; LC telemetry confirms whether an update occurred (new `CODE_IDENTITY` hash for patched binary). |

**Net coverage:** LC supports vulnerability management with endpoint inventory but does not scan for CVEs.

---

## Control 8 — Audit Log Management

Goal: collect, alert, review, and retain audit logs of events that could help detect, understand, or recover from an attack.

> This is the control family with the heaviest LC coverage.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 8.1 | IG1 | Establish and Maintain an Audit Log Management Process | Partial (policy artefact). LC provides the technical substrate: Insight retention, D&R rules, outputs, `audit` stream for LC-config changes. |
| 8.2 | IG1 | Collect Audit Logs | **Direct.** The LC EDR sensor emits `NEW_PROCESS`, `DNS_REQUEST`, `FILE_*`, `MODULE_LOAD`, `NETWORK_CONNECTIONS`, `SERVICE_CHANGE`, `CODE_IDENTITY`, `YARA_DETECTION`, `FIM_HIT`, plus Windows-only `WEL`, `REGISTRY_*`, `AUTORUN_CHANGE`, `DRIVER_CHANGE`, `SENSITIVE_PROCESS_ACCESS`, `THREAD_INJECTION`, `NEW_NAMED_PIPE`; macOS-only `MUL`, `USER_LOGIN`, `USER_LOGOUT`, `SSH_LOGIN`, `SSH_LOGOUT`. Windows event logs stream via `wel://` artifact rules. macOS unified logs stream via `mul://` artifact rules. Linux auth logs stream via a file adapter on `/var/log/auth.log` or auditd + file adapter. |
| 8.3 | IG1 | Ensure Adequate Audit Log Storage | **Direct.** Insight provides 90+ day managed retention — no endpoint storage is consumed. `days_retention` on artifact rules controls file/log artifact retention. |
| 8.4 | IG2 | Standardize Time Synchronization | Partial. `routing.event_time` is millisecond-precision UTC epoch from the sensor; `routing.latency` shows sensor-to-cloud delta, providing a clock-drift indicator. LC does not enforce NTP. |
| 8.5 | IG2 | Collect Detailed Audit Logs | **Direct.** All LC events carry full context: `routing.event_time`, `routing.hostname`, `routing.sid`, `routing.platform`, process `FILE_PATH`, `COMMAND_LINE`, `USER_NAME`, `PARENT`, hashes, network 5-tuple. |
| 8.6 | IG2 | Collect DNS Query Audit Logs | **Direct.** Native `DNS_REQUEST` events on Windows, Linux, and macOS with full query and response. |
| 8.7 | IG2 | Collect URL Request Audit Logs | Partial. Proxy/egress logs ingested via file adapter or syslog adapter; browser-process `NEW_PROCESS` + `NEW_TCP_CONNECTION` correlate URLs by destination. Native per-URL capture requires a web-proxy integration. |
| 8.8 | IG2 | Collect Command-Line Audit Logs | **Direct.** Every `NEW_PROCESS` event carries the full `COMMAND_LINE`. On Windows this augments `WEL 4688` (which lacks full command-line without advanced audit policy). |
| 8.9 | IG2 | Centralize Audit Logs | **Direct.** Every event sent by a sensor lands in Insight (the central store). Outputs forward to SIEM / S3 / Splunk / Elastic / Sentinel for enterprise log consolidation. |
| 8.10 | IG2 | Retain Audit Logs | **Direct.** Insight default ≥ 90 days (meets CIS minimum). For IG3 organisations with regulatory overlays (e.g., HIPAA 6 yrs, PCI 1 yr, SOX 7 yrs), add an S3/GCS output for unlimited cold archival. |
| 8.11 | IG2 | Conduct Audit Log Reviews | **Direct.** D&R rules evaluate events in real-time; LCQL supports ad-hoc interactive review; Cases extension (ext-cases) provides analyst workflows, SLAs, and audit trail. |
| 8.12 | IG3 | Collect Service Provider Logs | Partial. LC itself **is** a service provider; the `audit` stream exposes all LC administrative actions. For other SaaS providers (Okta, M365, AWS), use adapters (`okta://`, `msgraph://`, `cloudwatch://`, `eventhub://`) to pull provider logs into LC. |

**Net coverage:** LC provides the collection, centralisation, retention, and review substrate for Control 8. Safeguards 8.2, 8.3, 8.5, 8.6, 8.8, 8.9, 8.10, 8.11 are directly satisfied by the platform.

---

## Control 9 — Email and Web Browser Protections

Goal: improve protections and detections of threats from email and web vectors.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 9.1 | IG1 | Ensure Use of Only Fully Supported Browsers and Email Clients | Detection via `CODE_IDENTITY` on browser/email-client binaries (chrome.exe, msedge.exe, firefox.exe, outlook.exe, thunderbird). Joined with a supported-version lookup, D&R rules flag outdated clients. |
| 9.2 | IG1 | Use DNS Filtering Services | Partial. LC does not provide DNS filtering, but `DNS_REQUEST` events joined with a malicious-domain lookup generate detections for blocked domains. Works on all three platforms. |
| 9.3 | IG2 | Maintain and Enforce Network-Based URL Filters | No LC role — network capability. |
| 9.4 | IG2 | Restrict Unnecessary or Unauthorized Browser and Email Client Extensions | Detection via FIM on browser extension directories (`%LOCALAPPDATA%\Google\Chrome\User Data\*\Extensions\*`, `~/Library/Application Support/Google/Chrome/*/Extensions/*`, `~/.mozilla/firefox/*/extensions`). |
| 9.5 | IG2 | Implement DMARC | No LC role. |
| 9.6 | IG2 | Block Unnecessary File Types | Partial. YARA rules on file writes / `FILE_CREATE` with extension filters alert on disallowed types reaching endpoints. |
| 9.7 | IG3 | Deploy and Maintain Email Server Anti-Malware Protections | No LC role. |

**Net coverage:** LC provides *endpoint-side* detection of web/email threats — browser-spawning-shell detections, Office-macro child-process detections, drive-by-download indicators, malicious-domain DNS matches. Enforcement lives at the email gateway and DNS filter.

---

## Control 10 — Malware Defenses

Goal: prevent or control the installation, spread, and execution of malicious applications, code, or scripts.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 10.1 | IG1 | Deploy and Maintain Anti-Malware Software | The EPP extension brings Windows Defender under unified LC management (free). YARA scanning (platform-native) runs on file writes, process memory, or on-demand across Windows, Linux, and macOS. |
| 10.2 | IG1 | Configure Automatic Anti-Malware Signature Updates | Defender definition updates surface as `WEL` Event IDs 2001/2003/2006 on Windows; absence of update within N days is detectable. YARA rule sets are deployed via LC config and updated centrally. |
| 10.3 | IG1 | Disable Autorun and Autoplay for Removable Media | Detection. Registry FIM on `HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\NoDriveTypeAutoRun`; `VOLUME_MOUNT` events on Windows and macOS flag removable-media activity. |
| 10.4 | IG2 | Configure Automatic Anti-Malware Scanning of Removable Media | Partial. `VOLUME_MOUNT` events can trigger a YARA scan action via D&R rule. |
| 10.5 | IG2 | Enable Anti-Exploitation Features | Detection. `SENSITIVE_PROCESS_ACCESS` events expose cross-process handles (typical in exploitation); `THREAD_INJECTION` and `MODULE_MEM_DISK_MISMATCH` expose injection techniques. |
| 10.6 | IG2 | Centrally Manage Anti-Malware Software | The EPP extension centralises Defender management across the fleet. |
| 10.7 | IG3 | Use Behavior-Based Anti-Malware Software | The LC D&R engine is behavioural — process-tree heuristics, LOLBin abuse, process-injection detection, credential-dumping signals. Soteria and Sigma managed rule sets add curated behavioural detections with MITRE ATT&CK mapping. |

**Net coverage:** LC provides both signature-based (YARA, Defender via EPP) and behaviour-based (D&R engine, Soteria, Sigma) malware defence.

---

## Control 11 — Data Recovery

Goal: establish and maintain data recovery practices sufficient to restore enterprise assets to a pre-incident state.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 11.1–11.5 | IG1/IG2 | Backup, test, isolate, encrypt backups | No LC role for enterprise data recovery. LC supports the *detection* and *containment* side of ransomware (YARA on encryption behaviours, volume-snapshot-deletion detection via `vssadmin`, `bcdedit` monitoring), and the `isolate network` response action contains spread while recovery executes. |

**Net coverage:** Minimal — LC contains the spread, it does not perform backups.

---

## Control 12 — Network Infrastructure Management

Goal: establish, implement, and actively manage network devices.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 12.1–12.8 | IG1/IG2/IG3 | Network device configuration, documentation, version control, dedicated management infrastructure | Minimal LC role. LC is an endpoint platform — network device posture is out of scope. Syslog adapters can centralise device logs into LC for correlation, but LC does not configure network devices. |

**Net coverage:** None for enforcement; partial for log centralisation.

---

## Control 13 — Network Monitoring and Defense

Goal: operate processes and tooling to establish and maintain comprehensive network monitoring and defense against security threats.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 13.1 | IG2 | Centralize Security Event Alerting | **Direct.** Detections from all sensors flow to the `detect` output stream and Cases; outputs forward to SIEM/chat/ticketing. |
| 13.2 | IG2 | Deploy a Host-Based Intrusion Detection Solution | **Direct.** The LC EDR sensor with D&R rules is a host-based IDS. |
| 13.3 | IG2 | Deploy a Network Intrusion Detection Solution | Partial. The Zeek extension (Linux) provides network IDS telemetry from a mirror port or monitoring interface. |
| 13.4 | IG2 | Perform Traffic Filtering Between Network Segments | No LC role — firewall/segmentation capability. |
| 13.5 | IG2 | Manage Access Control for Remote Assets | No LC role. |
| 13.6 | IG2 | Collect Network Traffic Flow Logs | Partial. `NEW_TCP4_CONNECTION`, `NEW_TCP6_CONNECTION`, `NEW_UDP4_CONNECTION`, `NEW_UDP6_CONNECTION`, and `NETWORK_CONNECTIONS` summary events stream from every sensor on all three platforms with per-process attribution. Zeek extension (Linux) adds full flow logs. |
| 13.7 | IG3 | Deploy a Host-Based Intrusion Prevention Solution | Partial. YARA scanning can be set to scan-on-access, and D&R rules invoke `isolate network`, `task` (kill process), or `add tag` responses on match. |
| 13.8 | IG3 | Deploy a Network Intrusion Prevention Solution | No LC role. |
| 13.9 | IG3 | Deploy Port-Level Access Control | No LC role. |
| 13.10 | IG3 | Perform Application Layer Filtering | No LC role. |
| 13.11 | IG3 | Tune Security Event Alerting Thresholds | **Direct.** D&R rule `suppression` blocks, `fp-pattern-finder`, and the Detection Tuner skill tune alert thresholds. |

**Net coverage:** LC delivers HIDS capability (13.2, 13.7), connection-flow telemetry (13.6), and the alerting/tuning substrate (13.1, 13.11).

---

## Control 14 — Security Awareness and Skills Training

No LC role. (Policy/training control.)

---

## Control 15 — Service Provider Management

No LC role. (Third-party-risk control.)

---

## Control 16 — Application Software Security

Goal: manage the security life cycle of in-house developed, hosted, or acquired software.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 16.1 | IG2 | Establish and Maintain a Secure Application Development Process | No LC role. |
| 16.2 | IG2 | Establish and Maintain a Process to Accept and Address Software Vulnerabilities | No LC role. |
| 16.3 | IG2 | Perform Root Cause Analysis on Security Vulnerabilities | No LC role. |
| 16.4 | IG2 | Establish and Manage an Inventory of Third-Party Software Components | Partial — `os_packages`, `CODE_IDENTITY`, and `MODULE_LOAD` contribute observed-component data. |
| 16.5 | IG2 | Use Up-to-Date and Trusted Third-Party Software Components | As 16.4. |
| 16.6 | IG2 | Establish and Maintain a Severity Rating System and Process for Application Vulnerabilities | No LC role. |
| 16.7 | IG2 | Use Standard Hardening Configuration Templates for Application Infrastructure | Partial — FIM on application configuration paths detects drift. |
| 16.8 | IG3 | Separate Production and Non-Production Systems | No LC role. |
| 16.9 | IG3 | Train Developers in Application Security Concepts and Secure Coding | No LC role. |
| 16.10 | IG3 | Apply Secure Design Principles in Application Architectures | No LC role. |
| 16.11 | IG3 | Leverage Vetted Modules or Services for Application Security Components | No LC role. |
| 16.12 | IG3 | Implement Code-Level Security Checks | No LC role. |
| 16.13 | IG3 | Conduct Application Penetration Testing | See Control 18. |
| 16.14 | IG3 | Conduct Threat Modeling | No LC role. |

**Net coverage:** Minimal for SDLC. LC contributes runtime detection of application abuse (Office macro child-processes, browser-spawning-shell, `NEW_DOCUMENT` on server-side document handlers).

---

## Control 17 — Incident Response Management

Goal: establish a programme to develop and maintain an incident response capability.

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 17.1 | IG1 | Designate Personnel to Manage Incident Handling | No LC role (role designation). |
| 17.2 | IG1 | Establish and Maintain Contact Information for Reporting Security Incidents | No LC role. |
| 17.3 | IG1 | Establish and Maintain an Enterprise Process for Reporting Incidents | Partial — the Cases extension (ext-cases) provides an incident-management process with statuses, assignees, SLAs, and audit trail. |
| 17.4 | IG2 | Establish and Maintain an Incident Response Process | Partial — Cases + Playbook extension (Python automation) realises a documented IR process. |
| 17.5 | IG2 | Assign Key Roles and Responsibilities | Cases supports assignees and ownership tracking. |
| 17.6 | IG2 | Define Mechanisms for Communicating During Incident Response | Outputs forward cases/detections to Slack, PagerDuty, email, Jira, Teams. |
| 17.7 | IG2 | Conduct Routine Incident Response Exercises | No LC role; detections on pentest-tagged sensors support exercises. |
| 17.8 | IG3 | Conduct Post-Incident Reviews | Cases retain the full investigation record for retrospective review. |
| 17.9 | IG3 | Establish and Maintain Security Incident Thresholds | D&R rule `priority` field and the Cases extension's severity escalation implement thresholds. |

**Net coverage:** LC delivers the detection-to-case pipeline, analyst workflow, automated response, and post-incident record for Control 17.

---

## Control 18 — Penetration Testing

Goal: test effectiveness and resilience by identifying and exploiting weaknesses in controls (people, processes, technology).

| Safeguard | IG | Text | LimaCharlie Coverage |
|---|---|---|---|
| 18.1 | IG2 | Establish and Maintain a Penetration Testing Program | Partial — scope tracking via sensor tags (`pentest-target`, `pentest-engagement-2026-q2`). |
| 18.2 | IG2 | Perform Periodic External Penetration Tests | No LC role. |
| 18.3 | IG2 | Remediate Penetration Test Findings | No LC role. |
| 18.4 | IG3 | Validate Security Measures | LC telemetry confirms which rules fired during a pentest — exercise report by pulling the detection stream filtered to the pentest tag. |
| 18.5 | IG3 | Perform Periodic Internal Penetration Tests | As 18.4. |

**Net coverage:** LC does not perform pentests but provides high-fidelity telemetry for scoring the results.

---

## Implementation Group Summary

| IG | Safeguards Covered (meaningful LC role) |
|---|---|
| IG1 (56 safeguards) | 1.1, 2.1, 2.2, 2.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.3, 5.4, 8.1, 8.2, 8.3, 9.1, 9.2, 10.1, 10.2, 10.3, 17.3 |
| IG2 (74 safeguards) | 1.4, 2.4–2.7, 3.13, 3.14, 4.8, 4.9, 5.5, 6.6, 7.5, 7.7, 8.4–8.11, 9.4, 9.6, 10.4–10.6, 13.1–13.3, 13.6, 13.11, 16.4, 16.5, 16.7, 17.4–17.7, 17.9, 18.1 |
| IG3 (23 safeguards) | 1.5, 2.7, 3.14, 8.12, 10.7, 13.7, 17.8, 17.9, 18.4, 18.5 |

LC contributes directly to every Control except 11 (Data Recovery), 14 (Training), and 15 (Service Provider Management).

---

## Deployment Architecture

```
                          ┌── Insight (90+ day hot retention) ─► LCQL search
                          │
Endpoints ──► LC Sensor ──┼── D&R Engine (real-time detection) ─► Outputs
(Win/Linux/Mac)           │                                      ├─► SIEM
                          │                                      ├─► S3/GCS (cold, ≥90d)
                          └── Artifact / FIM / YARA              └─► Cases (ext-cases)
```

- Insight delivers CIS 8.3, 8.10 retention
- D&R engine delivers CIS 8.11, 10.7, 13.2
- Outputs deliver CIS 8.9 centralisation and 13.1 alerting
- ext-cases delivers CIS 17.3–17.9
- Zeek extension (Linux) delivers CIS 13.3, 13.6

---

## Retention Guidance for CIS 8.10

CIS Safeguard 8.10 mandates **at least 90 days** of audit-log retention. Insight default retention meets this minimum. Extend via S3/GCS output for:

- IG3 organisations and any org with regulatory overlay (HIPAA 6 yr, PCI 1 yr, SOX 7 yr, FedRAMP High multi-year)
- Organisations that need historical search beyond 90 days — pair with a SIEM output (Splunk, Chronicle, Elastic, Sentinel) for long-window analytics

---

## Cross-Framework Notes

CIS Critical Security Controls v8 complements — not replaces — prescriptive frameworks. Controls mapped here also contribute to:

- **NIST SP 800-53 Rev 5** — the CIS Controls Navigator explicitly maps CIS Safeguards to 800-53 families. See [nist-800-53-limacharlie-mapping.md](../nist-800-53/nist-800-53-limacharlie-mapping.md).
- **NIST Cybersecurity Framework (CSF) 2.0** — CIS Safeguards are referenced as Informative References for CSF Subcategories.
- **PCI DSS v4** — Requirement 10 (logging) maps cleanly to CIS Control 8; Req 6 maps to CIS Control 16.
- **HIPAA Security Rule** — §164.308(a)(1)(ii)(D) (information system activity review) and §164.312(b) (audit controls) map to CIS Control 8.
- **ISO/IEC 27001:2022** — Annex A controls share substantial overlap with CIS Safeguards.
- **CMMC 2.0** — Level 2/3 controls are derived from 800-171/800-172, which transitively map to CIS. See [../cmmc/cmmc-limacharlie-mapping.md](../cmmc/cmmc-limacharlie-mapping.md).

---

For the deployable configuration — D&R rules, artifact collection rules, FIM rules, exfil rules, extension recommendations — see [cis-v8-limacharlie-implementation.md](cis-v8-limacharlie-implementation.md).
