# LimaCharlie for HIPAA Security Rule Compliance

How LimaCharlie capabilities map to the HIPAA Security Rule (45 CFR Part 164, Subparts A & C) across Windows, Linux, and macOS endpoints. Focused on the **Technical Safeguards (§164.312)** where LC provides direct, measurable coverage, with partial coverage of **Administrative Safeguards (§164.308)** where endpoint telemetry is load-bearing (log review, malware protection, log-in monitoring, incident response) and the **Breach Notification Rule (§164.400–414)** where detection-to-case workflow supports breach identification and investigation timelines.

HIPAA implementation specifications are marked **Required (R)** or **Addressable (A)**. "Addressable" does not mean optional — the covered entity must assess whether the specification is a reasonable and appropriate safeguard in its environment, and either implement it, implement an equivalent, or document why neither applies (45 CFR §164.306(d)).

---

## Technical Safeguards — §164.312

### §164.312(a)(1) — Access Control

**Requirement:** Implement technical policies and procedures for electronic information systems that maintain ePHI to allow access only to those persons or software programs that have been granted access rights.

**LimaCharlie coverage:** Detection of access events and enforcement-by-containment on the sensor. LC does not manage user accounts or authentication directly — it observes and alerts on the OS-layer actions that implement access control. For identity-provider integration (Okta, Entra ID, Google Workspace) use adapters or webhook ingestion to correlate platform auth with endpoint telemetry.

#### §164.312(a)(2)(i) — Unique User Identification (R)

**Requirement:** Assign a unique name and/or number for identifying and tracking user identity.

**LimaCharlie coverage:** Every `NEW_PROCESS`, `FILE_CREATE`, `FILE_MODIFIED`, `FILE_DELETE`, and `MODULE_LOAD` event includes the invoking `USER_NAME` (SID on Windows, uid/username on Linux/macOS). Combined with `routing.sid` (sensor), `routing.hostname`, and `routing.event_time` (ms epoch UTC), every action against an ePHI-bearing endpoint is attributable to a specific user identity. On macOS, `USER_LOGIN` / `SSH_LOGIN` establish session boundaries. On Windows, `WEL` 4624/4634 from the `wel://Security:*` artifact rule provides session boundaries. On Linux, session boundaries come from the auth-log file adapter (see `§164.312(b)` below).

#### §164.312(a)(2)(ii) — Emergency Access Procedure (R)

**Requirement:** Establish (and implement as needed) procedures for obtaining necessary ePHI during an emergency.

**LimaCharlie coverage:** LC is detection-focused, but supports the *audit side* of emergency access — specifically, ensuring that break-glass account usage is logged and reviewable:
- Tag break-glass sensors / accounts and author a D&R rule that reports on process events under those identities, producing a continuous audit trail during emergency access
- Cases extension (ext-cases) retains the incident record with analyst notes, satisfying the "implemented as needed" review requirement

#### §164.312(a)(2)(iii) — Automatic Logoff (A)

**Requirement:** Implement electronic procedures that terminate an electronic session after a predetermined time of inactivity.

**LimaCharlie coverage:** Auto-logoff is an OS configuration (Windows `InactivityTimeoutSecs`, macOS `com.apple.screensaver idleTime`, Linux screen-lock modules). LC does not enforce logoff but can *detect* that the configuration is in place and alert on changes:
- **Windows:** FIM on the relevant registry policy paths + `WEL` 4719 (audit policy changed)
- **Linux:** FIM on `/etc/profile`, `/etc/gdm*/custom.conf`, `/etc/systemd/logind.conf`
- **macOS:** FIM on `/Library/Preferences/com.apple.screensaver.plist`

#### §164.312(a)(2)(iv) — Encryption and Decryption (A)

**Requirement:** Implement a mechanism to encrypt and decrypt ePHI.

**LimaCharlie coverage:** Encryption at rest is typically BitLocker / FileVault / LUKS — OS-layer capabilities. LC contributes by:
- Detecting processes that interact with known ePHI paths without authorization (FIM on ePHI directories + D&R rules)
- Detecting ransomware indicators via YARA, `FILE_MODIFIED` bursts, and known-bad command-line patterns
- Inventorying FileVault / BitLocker status via sensor commands (`os_version`, custom Velociraptor artifacts) for compliance reporting

### §164.312(b) — Audit Controls (R)

**Requirement:** Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use ePHI.

**LimaCharlie coverage:** This is LC's core value proposition. The sensor natively generates the event types below; platform coverage reflects actual sensor capability.

| Event | Windows | Linux | macOS | Purpose |
|---|---|---|---|---|
| `NEW_PROCESS`, `EXISTING_PROCESS`, `TERMINATE_PROCESS` | ✅ | ✅ | ✅ | Process lifecycle with parent-child, command-line, user context |
| `DNS_REQUEST` | ✅ | ✅ | ✅ | DNS queries with responses |
| `NEW_TCP4_CONNECTION`, `NEW_TCP6_CONNECTION`, `NEW_UDP4_CONNECTION`, `NEW_UDP6_CONNECTION` | ✅ | ✅ | ✅ | Connection establishment with process attribution |
| `NETWORK_CONNECTIONS`, `NETWORK_SUMMARY` | ✅ | ✅ | ✅ | Connection rollups |
| `CODE_IDENTITY` | ✅ | ✅ | ✅ | Hash + path + signature of loaded binaries |
| `YARA_DETECTION` | ✅ | ✅ | ✅ | YARA rule match on file or memory |
| `FIM_HIT` | ✅ | ✅ | ✅ | Monitored file / directory / registry-key modification |
| `SERVICE_CHANGE` | ✅ | ✅ | ✅ | Service / systemd unit / launchd change |
| `FILE_CREATE`, `FILE_DELETE`, `FILE_MODIFIED` | ✅ | ❌ | ✅ | Native file events — Linux relies on FIM |
| `MODULE_LOAD` | ✅ | ✅ | ❌ | DLL / shared-object loads |
| `WEL` | ✅ | ❌ | ❌ | Windows Event Log stream (via `wel://` artifact rule) |
| `MUL` | ❌ | ❌ | ✅ | macOS Unified Log stream (via `mul://` artifact rule) |
| `USER_LOGIN`, `USER_LOGOUT` | ❌ | ❌ | ✅ | OS login sessions — macOS only |
| `SSH_LOGIN`, `SSH_LOGOUT` | ❌ | ❌ | ✅ | SSH sessions — macOS only (success only; no `IS_SUCCESS` field) |
| `AUTORUN_CHANGE` | ✅ | ❌ | ❌ | Registry-driven autorun changes |
| `DRIVER_CHANGE` | ✅ | ❌ | ❌ | Driver install / modification |
| `REGISTRY_CREATE`, `REGISTRY_WRITE`, `REGISTRY_DELETE` | ✅ | ❌ | ❌ | Registry modifications |
| `SENSITIVE_PROCESS_ACCESS` | ✅ | ❌ | ❌ | Cross-process handle to protected processes |
| `THREAD_INJECTION`, `NEW_REMOTE_THREAD` | ✅ | ❌ | ❌ | Process injection indicators |
| `NEW_NAMED_PIPE`, `OPEN_NAMED_PIPE` | ✅ | ❌ | ❌ | Named pipe creation / open |

**Linux authentication caveat:** The LC Linux sensor does **not** emit `USER_LOGIN` or `SSH_LOGIN` events. For HIPAA §164.312(b) audit of interactive access, choose one of:
1. Stream `/var/log/auth.log` (or `/var/log/secure` on RHEL/CentOS) via a LimaCharlie **file adapter** — real-time auth events arrive on the adapter telemetry stream and are evaluable by D&R rules.
2. Deploy **auditd** rules and ingest `/var/log/audit/audit.log` via the same file-adapter pattern — richer telemetry at higher volume.
3. Use **Artifact Collection** (file pattern) for retention-only — not streamed.

**macOS SSH failure caveat:** `SSH_LOGIN` fires only on success and has no `IS_SUCCESS` field. Failed SSH / authentication attempts on macOS must be derived from `MUL` events (subsystem `com.apple.opendirectoryd`, process `authd`, process `securityd`) via a `mul://` artifact rule.

**Windows authentication:** flows as `WEL` via a `wel://Security:*` artifact rule — not as dedicated `USER_LOGIN` events. Key events: 4624 (successful logon), 4625 (failed logon), 4634 / 4647 (logoff), 4672 (special privileges), 4648 (logon with explicit credentials), 4776 (NTLM credential validation).

Every event carries `routing.event_time` (ms epoch UTC), `routing.hostname`, `routing.sid`, and `routing.platform` — the *what, when, where, source, outcome, identity* demanded by auditable HIPAA logging.

### §164.312(c)(1) — Integrity

**Requirement:** Implement policies and procedures to protect ePHI from improper alteration or destruction.

#### §164.312(c)(2) — Mechanism to Authenticate ePHI (A)

**Requirement:** Implement electronic mechanisms to corroborate that ePHI has not been altered or destroyed in an unauthorized manner.

**LimaCharlie coverage:**
- **FIM rules** generate `FIM_HIT` events on monitored ePHI-bearing files, directories, and Windows registry keys — all three platforms. Configure FIM on the database / file-share paths that hold ePHI.
- **`CODE_IDENTITY`** events on Windows, Linux, and macOS expose hash + path + signature for every loaded binary — detects substitution of application binaries that access ePHI.
- **YARA scanning** detects known ransomware and wiper families that represent destructive alteration.
- **Integrity extension (ext-integrity)** centralizes FIM / RIM rule management.
- **Windows registry monitoring:** `REGISTRY_WRITE` / `REGISTRY_DELETE` plus FIM on policy keys covers registry-stored ePHI configuration (encryption settings, access policies).

### §164.312(d) — Person or Entity Authentication (R)

**Requirement:** Implement procedures to verify that a person or entity seeking access to ePHI is the one claimed.

**LimaCharlie coverage:** Detection of authentication events and anomalies — enforcement remains with the OS / IdP:
- **Windows:** `WEL` 4624 (successful logon with `LogonType`), 4625 (failed logon), 4648 (explicit credentials), 4776 (NTLM validation)
- **Linux:** `/var/log/auth.log` via file adapter — PAM success/failure records; `NEW_PROCESS` for `sshd` / `login` / `sudo` with user context
- **macOS:** `USER_LOGIN`, `SSH_LOGIN` (native success-only), plus `MUL` with subsystem predicate `com.apple.opendirectoryd` or process `authd` / `securityd` for failure coverage

Anomalous authentication is surfaced via D&R rules (impossible-travel patterns when combined with IdP data, unusual hours, first-time-seen source IPs for privileged accounts).

### §164.312(e)(1) — Transmission Security

**Requirement:** Implement technical security measures to guard against unauthorized access to ePHI that is being transmitted over an electronic communications network.

#### §164.312(e)(2)(i) — Integrity Controls (A)

**LimaCharlie coverage:**
- Connection telemetry (`NEW_TCP4/6_CONNECTION`, `NEW_UDP4/6_CONNECTION`) captures every outbound flow with process attribution — supports detection of ePHI exfiltration to unauthorized destinations
- `DNS_REQUEST` events reveal resolution of unauthorized or known-bad domains before the TCP/UDP connection
- D&R rules combined with IOC / allow-list lookups flag transmission to non-approved destinations
- FIM on the ePHI source paths correlates with subsequent network events to surface exfiltration chains

#### §164.312(e)(2)(ii) — Encryption (A)

**LimaCharlie coverage:** Transmission encryption (TLS) is an application / network-layer responsibility. LC contributes by:
- Detecting plaintext protocols (`NEW_TCP4_CONNECTION` to port 21/23/80/110/143 from processes that handle ePHI)
- Detecting unusual outbound TLS on non-standard ports that may indicate tunneling
- YARA matches on known TLS-stripping or downgrade-attack tooling

---

## Administrative Safeguards — §164.308 (Partial Coverage)

### §164.308(a)(1)(ii)(D) — Information System Activity Review (R)

**Requirement:** Implement procedures to regularly review records of information system activity, such as audit logs, access reports, and security incident tracking reports.

**LimaCharlie coverage:** Directly addressed — the core review mechanism:
- **D&R rules** evaluate events in real-time, producing reviewable detections
- **LCQL** provides interactive search, filtering, and correlation across the Insight hot window (90+ days by default)
- **Outputs** route detections to SIEM, case management, ticketing, or chat for human review
- **Cases extension (ext-cases)** captures SOC triage, assignment, SLA, analyst notes, and investigation conclusion — the auditable review record
- **AI agents / Agentic SOC** (baselining-soc, lean-soc, tiered-soc, etc.) provide automated first-pass review with human confirmation

### §164.308(a)(3)(ii)(C) — Termination Procedures (A, Partial)

**Requirement:** Implement procedures for terminating access to ePHI when the employment of, or other arrangement with, a workforce member ends.

**LimaCharlie coverage:** LC does not revoke access — that is the IdP / AD responsibility — but *detects continued access post-termination*:
- Maintain a `terminated-users` lookup (updated from HR / IdP)
- D&R rule matches `event/USER_NAME` against the lookup across `NEW_PROCESS`, `WEL` logon events, and `SSH_LOGIN` → high-severity alert on hit

### §164.308(a)(5)(ii)(B) — Protection from Malicious Software (A)

**Requirement:** Implement procedures for guarding against, detecting, and reporting malicious software.

**LimaCharlie coverage:**
- **YARA** — platform-native execution on file writes, process memory, and ad-hoc scans; `YARA_DETECTION` events on all three platforms
- **Windows Defender integration** via the EPP extension — Defender threat events flow as `WEL` for correlation
- **Soteria / Sigma managed detections** — subscribed rulesets for continuously updated malware coverage
- **Strelka extension** for deep file analysis when files transit endpoints (PE, archive, macro extraction)
- **IOC lookups** — domain, IP, and hash feeds referenced by D&R rules for real-time matching

### §164.308(a)(5)(ii)(C) — Log-in Monitoring (A)

**Requirement:** Implement procedures for monitoring log-in attempts and reporting discrepancies.

**LimaCharlie coverage:**
- **Windows:** `WEL` 4624 (success), 4625 (failed), 4740 (account locked out) — from `wel://Security:*` artifact rule
- **Linux:** `/var/log/auth.log` via file adapter — PAM/sshd success and failure; `NEW_PROCESS` for `sshd` / `sudo` / `login`
- **macOS:** `USER_LOGIN`, `SSH_LOGIN` (native, success-only), `MUL` with `com.apple.opendirectoryd` / `authd` predicate for failures

Discrepancies (brute-force patterns, off-hours logins, geographic anomalies) are detected via D&R rules with time-windowed suppression / `min_count`.

### §164.308(a)(6)(ii) — Response and Reporting (R)

**Requirement:** Identify and respond to suspected or known security incidents; mitigate, to the extent practicable, harmful effects of security incidents that are known to the covered entity; and document security incidents and their outcomes.

**LimaCharlie coverage:**
- **Cases extension (ext-cases)** — full incident lifecycle: detection-to-case conversion, severity, assignment, SLA tracking, analyst notes, conclusion, audit trail
- **Automated response actions** (`isolate network`, `add tag`, `task`) execute immediately on rule match — mitigation without analyst intervention
- **Playbook extension** for Python-based response automation, enrichment, and notification
- Outputs route detections / cases to SIEM, Slack, PagerDuty, Jira, email for reporting

---

## Physical Safeguards — §164.310

LC is software on endpoints — physical controls (facility access, workstation location, media disposal) are outside scope. LC contributes indirectly:
- **§164.310(c) — Workstation Security:** LC detects removable-media events (`VOLUME_MOUNT` / `VOLUME_UNMOUNT` on Windows/macOS) and suspicious process activity on workstations handling ePHI
- **§164.310(d)(2)(i) — Disposal:** sensor `os_packages` and Velociraptor artifact collection provide software / content inventory prior to decommissioning

---

## Breach Notification Rule — §164.400–414

**Requirement:** Covered entities must notify affected individuals, HHS, and (in some cases) the media of breaches of unsecured ePHI within 60 days of discovery.

**LimaCharlie coverage:**
- **Detection-to-case workflow** (ext-cases) timestamps every stage: initial detection, triage, analyst assignment, investigation milestones, conclusion — provides the defensible timeline required by §164.404(b) / §164.408(b)
- **Insight hot retention** (90+ days) enables root-cause reconstruction within the notification window
- **S3/GCS cold archival** via outputs preserves evidence beyond Insight's hot window — supports the extended post-breach investigations that often outlast the 60-day notification deadline
- **LCQL** supports IOC hunts across the fleet to scope the breach (which other hosts? when did it start?)
- **Artifact collection** for on-demand file/log pulls from affected endpoints during investigation
- **Velociraptor extension** for deep forensic triage when a breach is confirmed

The defensible investigation timeline is LC's strongest contribution to breach notification — the platform produces a tamper-evident record of *when* the covered entity discovered the incident (first D&R detection / case open) and *what* investigative actions were taken.

---

## §164.316 — Documentation

### §164.316(b)(2)(i) — Time Limit on Documentation Retention (R)

**Requirement:** Retain required documentation for **6 years from the date of its creation or the date when it last was in effect, whichever is later**.

**HIPAA and audit log retention:** The Security Rule itself does **not** prescribe a specific audit-log retention period. §164.316(b)(2)(i)'s 6-year requirement applies to *policies and procedures documentation*. Industry practice, however, is to retain audit logs supporting §164.312(b) for the same 6-year period, since those logs may be needed to prove the policies were in effect.

**LimaCharlie coverage:**
- **Insight:** 90+ day hot retention (default), fully searchable via LCQL
- **S3/GCS output:** unlimited cold archival — configure with object lifecycle policy to retain 6 years
- Artifact collection rules use `days_retention` per-artifact for file/log artifacts
- The platform `audit` stream records every LC configuration change with identity attribution — retain to S3/GCS for the 6-year window

---

## Safeguard Applicability Matrix

| Safeguard | Status | LC Coverage |
|---|---|---|
| §164.312(a)(1) Access Control | – | Detection + isolation |
| §164.312(a)(2)(i) Unique User Identification | R | Direct (event user context) |
| §164.312(a)(2)(ii) Emergency Access | R | Indirect (audit trail during emergency) |
| §164.312(a)(2)(iii) Automatic Logoff | A | Config-change detection |
| §164.312(a)(2)(iv) Encryption/Decryption | A | Indirect (ransomware / unauthorized-access detection) |
| §164.312(b) Audit Controls | R | **Direct (core value)** |
| §164.312(c)(1) Integrity | – | FIM + CODE_IDENTITY + YARA |
| §164.312(c)(2) Authenticate ePHI | A | FIM on ePHI paths |
| §164.312(d) Person or Entity Authentication | R | Detection of auth events / anomalies |
| §164.312(e)(1) Transmission Security | – | Network telemetry + DNS + YARA |
| §164.312(e)(2)(i) Integrity Controls | A | Connection + DNS telemetry |
| §164.312(e)(2)(ii) Encryption | A | Plaintext-protocol detection |
| §164.308(a)(1)(ii)(D) Information System Activity Review | R | **Direct (D&R + LCQL + Cases)** |
| §164.308(a)(3)(ii)(C) Termination Procedures | A | Partial (terminated-user lookup + D&R) |
| §164.308(a)(5)(ii)(B) Protection from Malicious Software | A | YARA + EPP + Soteria + Sigma |
| §164.308(a)(5)(ii)(C) Log-in Monitoring | A | Per-platform auth telemetry |
| §164.308(a)(6)(ii) Response and Reporting | R | **Direct (Cases + automated actions)** |
| §164.310(c) Workstation Security | – | Indirect (removable media + process monitoring) |
| §164.400–414 Breach Notification | – | Detection-to-case timeline + cold archival + forensic triage |
| §164.316(b)(2)(i) 6-Year Retention | R | Insight hot + S3/GCS cold (6-year lifecycle) |

R = Required, A = Addressable, – = standard (no implementation spec)

---

## Data Retention Guidance

- **Audit logs supporting §164.312(b):** No prescribed period in the Security Rule, but 6 years by industry practice (aligned with §164.316(b)(2)(i)). Insight 90 days hot + S3/GCS lifecycle policy for 6 years cold.
- **Detection records / cases:** Retain for the same 6-year window — cases are part of the §164.308(a)(6)(ii) response record.
- **Raw ePHI files:** Out of scope for LC. HIPAA retention applies per state / specialty (commonly 6–10 years).

---

## Deployment Architecture

```
                          ┌── Insight (90+ day hot retention) ─► LCQL search
                          │
Endpoints ──► LC Sensor ──┼── D&R Engine (real-time detection) ─► Outputs
(Win/Linux/Mac)           │                                      ├─► SIEM
                          │                                      ├─► S3/GCS (6-yr cold)
                          └── Artifact / FIM / YARA              └─► Cases (ext-cases)
```

- Sensor covers Windows, Linux, macOS with a common event schema — detection logic is largely portable, but platform-specific events (WEL / MUL / registry / auth) require per-platform rule branches
- Insight delivers §164.312(b) hot audit retention
- D&R engine delivers §164.308(a)(1)(ii)(D) activity review and §164.308(a)(6)(ii) response
- Outputs deliver §164.316(b)(2)(i) cold archival and §164.308(a)(6)(ii) reporting
- ext-cases delivers §164.308(a)(6)(ii) incident documentation and the §164.400–414 breach-notification investigation timeline

---

## Coverage Gaps and Compensating Controls

HIPAA includes several safeguards where LC's contribution is **indirect or partial**. These are honestly called out:

| Safeguard | Gap | Compensating Control |
|---|---|---|
| §164.312(a)(2)(ii) Emergency Access | LC cannot grant break-glass access | Document procedure; use LC for audit trail only |
| §164.312(a)(2)(iii) Automatic Logoff | No enforcement | OS/Group Policy enforcement + LC FIM on config |
| §164.312(a)(2)(iv) Encryption at rest | Not enforced by LC | BitLocker / FileVault / LUKS + LC for ransomware detection |
| §164.312(e)(2)(ii) Transmission Encryption | Not enforced by LC | TLS-enforcing network controls + LC for plaintext-protocol detection |
| §164.308(a)(3)(ii)(C) Termination | LC cannot disable accounts | IdP / AD deprovisioning + LC `terminated-users` lookup for detection |
| Linux auth events | No native `USER_LOGIN` / `SSH_LOGIN` | File adapter on `/var/log/auth.log` or auditd |
| macOS SSH failures | `SSH_LOGIN` success-only | `MUL` artifact rule with `com.apple.opendirectoryd` predicate |
| Physical safeguards | Out of scope | Facility controls / access badges |

---

## Cross-Framework Notes

HIPAA Security Rule controls mapped here overlap substantially with other frameworks:

- **HITRUST CSF** — HITRUST directly references HIPAA; controls map 1:1 via the HITRUST reference manual
- **NIST 800-66 (HIPAA Implementation Guide)** — NIST's canonical HIPAA overlay aligns the 800-53 control catalog with the Security Rule. See [../nist-800-53/nist-800-53-limacharlie-mapping.md](../nist-800-53/nist-800-53-limacharlie-mapping.md) for the underlying 800-53 coverage.
- **SOC 2 Common Criteria** — CC6 (Logical Access), CC7 (System Operations), and CC8 (Change Management) share coverage with HIPAA §164.312 and §164.308
- **State breach notification laws** (e.g., California CCPA/CPRA, New York SHIELD Act) — share the detection-to-notification timeline requirement addressed by ext-cases

---

## Companion Document

For deployable D&R rules, FIM rules, artifact collection rules, exfil rules, and extension configuration that satisfy the safeguards mapped above, see [hipaa-limacharlie-implementation.md](hipaa-limacharlie-implementation.md).
