# HIPAA Security Rule Compliance Implementation Guide — LimaCharlie

Concrete D&R rules, artifact collection rules, FIM rules, and extension recommendations to satisfy the HIPAA Security Rule (45 CFR Part 164, Subparts A & C) using LimaCharlie EDR on Windows, Linux, and macOS endpoints.

Companion to [hipaa-limacharlie-mapping.md](hipaa-limacharlie-mapping.md), which maps HIPAA safeguards to LC capabilities conceptually. This document provides the deployable configuration.

All D&R rule syntax in this document has been validated against `limacharlie dr validate`. Event-to-platform coverage reflects actual sensor capability (per the LC EDR events reference), not documentation aspirations.

HIPAA implementation specifications are tagged in each section as **Required (R)** or **Addressable (A)**. Addressable does *not* mean optional — the covered entity must assess reasonableness and either implement, implement an equivalent, or document a justified non-implementation (45 CFR §164.306(d)).

---

## Table of Contents

1. [Windows Event Log Artifact Collection Rules](#1-windows-event-log-artifact-collection-rules)
2. [macOS Unified Log Artifact Collection Rules](#2-macos-unified-log-artifact-collection-rules)
3. [Linux Audit Log Collection](#3-linux-audit-log-collection)
4. [File Integrity Monitoring (FIM) Rules](#4-file-integrity-monitoring-fim-rules)
5. [Exfil Event Collection Rules](#5-exfil-event-collection-rules)
6. [D&R Rules — §164.312(b) Audit Controls](#6-dr-rules--164312b-audit-controls)
7. [D&R Rules — §164.312(a) Access Control](#7-dr-rules--164312a-access-control)
8. [D&R Rules — §164.312(d) Person or Entity Authentication](#8-dr-rules--164312d-person-or-entity-authentication)
9. [D&R Rules — §164.312(c) Integrity](#9-dr-rules--164312c-integrity)
10. [D&R Rules — §164.308 Administrative Safeguards (Technical Portions)](#10-dr-rules--164308-administrative-safeguards-technical-portions)
11. [D&R Rules — §164.312(e) Transmission Security](#11-dr-rules--164312e-transmission-security)
12. [D&R Rules — Breach Notification Support (§164.400–414)](#12-dr-rules--breach-notification-support-164400-414)
13. [Recommended Extensions](#13-recommended-extensions)
14. [Deployment Notes](#14-deployment-notes)

---

## 1. Windows Event Log Artifact Collection Rules

The `wel://` pattern streams Windows Event Logs as first-class `WEL` telemetry — preferred over `.evtx` file collection because events are evaluated by D&R rules in real time.

> **Prerequisite:** The **Reliable Tasking** and **Artifact Collection** extensions must be enabled.

Rule map entries are added to `ext-artifact` configuration (web UI Artifact Collection section, `limacharlie extension config-set --name ext-artifact`, or ext-git-sync).

### Security Log

```yaml
hipaa-wel-security:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Security:*"
```

**Key Event IDs produced (HIPAA mapping):**

| Event ID | Category | HIPAA Safeguard |
|---|---|---|
| 4624 | Successful logon | §164.312(b), §164.312(d), §164.308(a)(5)(ii)(C) |
| 4625 | Failed logon | §164.312(b), §164.308(a)(5)(ii)(C) |
| 4634 | Logoff | §164.312(b), §164.312(a)(2)(iii) |
| 4647 | User-initiated logoff | §164.312(b), §164.312(a)(2)(iii) |
| 4648 | Logon with explicit credentials | §164.312(b), §164.312(a)(1) |
| 4672 | Special privileges assigned to new logon | §164.312(b), §164.312(a)(1) |
| 4673 | Privileged service called | §164.312(a)(1) |
| 4674 | Operation attempted on privileged object | §164.312(a)(1) |
| 4688 | Process creation (if audit enabled) | §164.312(b) |
| 4697 | Service installed on the system | §164.312(c)(1) |
| 4698 | Scheduled task created | §164.312(c)(1) |
| 4699 | Scheduled task deleted | §164.312(c)(1) |
| 4719 | Audit policy changed | §164.312(b) |
| 4720 | User account created | §164.308(a)(3)(ii)(C), §164.312(a)(2)(i) |
| 4722 | User account enabled | §164.308(a)(3)(ii)(C) |
| 4723 | Password change attempted | §164.308(a)(5)(ii)(D) |
| 4724 | Password reset attempted | §164.308(a)(5)(ii)(D) |
| 4725 | User account disabled | §164.308(a)(3)(ii)(C) |
| 4726 | User account deleted | §164.308(a)(3)(ii)(C) |
| 4728 | Member added to security-enabled global group | §164.312(a)(1) |
| 4732 | Member added to security-enabled local group | §164.312(a)(1) |
| 4735 | Security-enabled local group changed | §164.312(a)(1) |
| 4738 | User account changed | §164.308(a)(3)(ii)(C) |
| 4740 | User account locked out | §164.308(a)(5)(ii)(C) |
| 4756 | Member added to universal security group | §164.312(a)(1) |
| 4767 | User account unlocked | §164.308(a)(3)(ii)(C) |
| 4776 | Credential validation (NTLM) | §164.312(d) |
| 4946 | Firewall rule added | §164.312(e)(1) |
| 4947 | Firewall rule modified | §164.312(e)(1) |
| 4948 | Firewall rule deleted | §164.312(e)(1) |
| 4950 | Firewall setting changed | §164.312(e)(1) |
| 1102 | Security log cleared | §164.312(b) (tamper indicator) |

### System Log

```yaml
hipaa-wel-system:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://System:*"
```

**Key Event IDs:** 7034 (service crash), 7036 (service start/stop), 7040 (service start type changed), 7045 (new service installed — §164.312(c)(1)), 1074 (shutdown/restart), 6005/6006 (event log service start/stop — §164.312(b) tamper indicator).

### PowerShell Operational Log

```yaml
hipaa-wel-powershell:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-PowerShell/Operational:*"
```

**Key Event IDs:** 4103 (module logging), 4104 (script block logging), 4105/4106 (script start/stop). Script-block logging captures commands used to access, modify, or exfiltrate ePHI — critical for §164.312(b) and §164.308(a)(1)(ii)(D).

### Windows Defender Operational Log

```yaml
hipaa-wel-defender:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Defender/Operational:*"
```

**Key Event IDs:** 1006/1007 (malware action taken), 1116/1117 (threat detected / action taken — §164.308(a)(5)(ii)(B)), 2001/2003/2006 (definition update), 5001 (real-time protection disabled — tamper indicator).

### Task Scheduler Operational Log

```yaml
hipaa-wel-taskscheduler:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-TaskScheduler/Operational:*"
```

### Windows Firewall Log

```yaml
hipaa-wel-firewall:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Firewall With Advanced Security/Firewall:*"
```

Covers §164.312(e)(1) transmission-security boundary events on Windows endpoints.

---

## 2. macOS Unified Log Artifact Collection Rules

The `mul://` pattern streams macOS Unified Log entries as real-time `MUL` telemetry. Predicates use standard macOS unified-log predicate syntax.

> **Prerequisite:** `MUL` must be enabled in the Exfil Control rules for macOS (see Section 5).

> **Field path verification:** D&R rules in Section 6 that match `MUL` events use field paths based on macOS `log` command keys (`eventMessage`, `processImagePath`, `subsystem`). Verify the exact field paths against your first few `MUL` events in Timeline after deployment — the sensor may flatten or re-key some fields. Adjust `path:` values accordingly.

### Authentication & Authorization (§164.312(d), §164.308(a)(5)(ii)(C))

```yaml
hipaa-mul-auth:
  days_retention: 90
  filters:
    platforms:
      - macos
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.opendirectoryd"'
    - 'mul://process == "authd"'
    - 'mul://process == "securityd"'
```

Required for failed-SSH coverage — native `SSH_LOGIN` fires only on success and has no `IS_SUCCESS` field.

### Login & Session Events (§164.312(a)(2)(i), §164.312(a)(2)(iii))

```yaml
hipaa-mul-sessions:
  days_retention: 90
  filters:
    platforms:
      - macos
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.loginwindow"'
    - 'mul://process == "loginwindow"'
    - 'mul://process == "CGSession"'
```

Complements native `USER_LOGIN` / `SSH_LOGIN` events; captures session-lock / screensaver state for §164.312(a)(2)(iii) auto-logoff validation.

### Privilege Use (§164.312(a)(1))

```yaml
hipaa-mul-privilege:
  days_retention: 90
  filters:
    platforms:
      - macos
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://process == "sudo"'
    - 'mul://process == "authopen"'
```

### Launch Services (§164.312(c)(1))

```yaml
hipaa-mul-launch:
  days_retention: 90
  filters:
    platforms:
      - macos
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.xpc.launchd"'
    - 'mul://process == "launchctl"'
```

### Endpoint Security / System Integrity

```yaml
hipaa-mul-security:
  days_retention: 90
  filters:
    platforms:
      - macos
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.securityd"'
    - 'mul://subsystem == "com.apple.TCC"'
```

TCC (Transparency, Consent, and Control) is the macOS privacy framework — prompts and grants for access to protected resources are auditable for §164.312(a)(1).

---

## 3. Linux Audit Log Collection

The LC Linux EDR sensor does **not** emit `USER_LOGIN` / `SSH_LOGIN` events. HIPAA §164.312(b) audit controls for Linux require one of the approaches below.

### Option A — Artifact Collection (Retention, Not Streaming)

Use when compliance requires **retention** of the raw auth log but real-time detection is not needed:

```yaml
hipaa-artifact-authlog:
  days_retention: 90
  filters:
    platforms:
      - linux
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - /var/log/auth.log
    - /var/log/secure
```

Artifacts are retrievable from the Artifacts UI but are not streamed to the Timeline.

### Option B — File Adapter (Real-Time Streaming, Separate Stream)

Use when you want auth events in the Timeline and evaluable by D&R rules. Deploys a LimaCharlie Adapter binary on each Linux endpoint (separate from the EDR sensor).

1. Create an Installation Key for the adapter and download the appropriate binary
2. Deploy on each Linux endpoint with this config (`/etc/lc/authlog.yaml`):

```yaml
file:
  client_options:
    identity:
      installation_key: <installation_key>
      oid: <oid>
    platform: text
    sensor_seed_key: authlog-<hostname>
  file_path: /var/log/auth.log
  no_follow: false
```

3. Run: `./lc_adapter file /etc/lc/authlog.yaml`
4. Persist via systemd unit

Events arrive as the `text` platform — D&R rules match on `event/raw` with regex patterns.

### Option C — Auditd Rules (Recommended for HIPAA / High-Risk ePHI Environments)

Deploy auditd rules on Linux endpoints (via configuration management) that cover HIPAA technical-safeguard categories. Then collect `/var/log/audit/audit.log` via file adapter or artifact collection using the same approach as Options A/B.

Minimum auditd rules for HIPAA §164.312(b) / §164.308(a)(1)(ii)(D):

```
# /etc/audit/rules.d/hipaa.rules
# Identity changes (§164.312(a)(2)(i), §164.308(a)(3)(ii)(C))
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k identity
-w /etc/sudoers.d/ -p wa -k identity

# Authentication config (§164.312(d))
-w /etc/pam.d/ -p wa -k auth-config
-w /etc/ssh/sshd_config -p wa -k sshd-config
-w /etc/login.defs -p wa -k auth-config

# Privilege escalation (§164.312(a)(1))
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation
-a always,exit -F arch=b32 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation

# ePHI directory access (§164.312(b), §164.312(c)(1)) — adjust paths per site
# -w /var/data/ephi -p rwa -k ephi-access

# Time changes (§164.312(b) — auditable log timestamp integrity)
-a always,exit -F arch=b64 -S settimeofday,clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Audit subsystem integrity (§164.312(b) tamper indicator)
-w /etc/audit/ -p wa -k audit-config
-w /etc/libaudit.conf -p wa -k audit-config
-e 2
```

The final `-e 2` makes the audit configuration immutable until reboot — strong tamper protection. Deploy via Ansible, Puppet, or similar; verify with `auditctl -l`.

---

## 4. File Integrity Monitoring (FIM) Rules

FIM generates `FIM_HIT` events on monitored files, directories, and Windows registry keys across all three platforms — the technical mechanism for §164.312(c)(1) Integrity and §164.312(c)(2) Authenticate ePHI.

> Linux FIM works with `inotify` (active monitoring) or eBPF (on supported kernels). Windows and macOS use passive kernel monitoring.

### Windows

```yaml
hipaa-fim-windows-system:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\drivers\etc\hosts
    - ?:\Windows\System32\config\SAM
    - ?:\Windows\System32\config\SYSTEM
    - ?:\Windows\System32\config\SECURITY

hipaa-fim-windows-grouppolicy:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\GroupPolicy\*
    - ?:\Windows\SYSVOL\*

hipaa-fim-windows-powershell-profiles:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    - ?:\Users\*\Documents\WindowsPowerShell\profile.ps1

hipaa-fim-windows-registry-persistence:
  filters:
    platforms:
      - windows
  patterns:
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run*
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce*
    - \REGISTRY\USER\S-*\SOFTWARE\Microsoft\Windows\CurrentVersion\Run*
    - \REGISTRY\MACHINE\SYSTEM\CurrentControlSet\Services*
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon*
    - \REGISTRY\MACHINE\SOFTWARE\Policies\Microsoft\Windows*

# §164.312(a)(2)(iii) Automatic Logoff — inactivity timeout policies
hipaa-fim-windows-inactivity-policy:
  filters:
    platforms:
      - windows
  patterns:
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\InactivityTimeoutSecs
    - \REGISTRY\MACHINE\SOFTWARE\Policies\Microsoft\Windows\Control Panel\Desktop\ScreenSaveTimeOut
    - \REGISTRY\USER\S-*\Control Panel\Desktop\ScreenSaveTimeOut

# §164.312(c) — ePHI paths (customize per site)
hipaa-fim-windows-ephi:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\ePHI\*
    - ?:\PHI\*
    - ?:\PatientData\*
    - ?:\Medical\*
```

> **ePHI paths are site-specific.** Replace `?:\ePHI\*` with actual directories (e.g., `D:\EMR\Patients\*`, `E:\HL7Messages\*`). Over-broad FIM generates excessive volume — scope to directories holding ePHI at rest.

### Linux

```yaml
hipaa-fim-linux-identity:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/passwd
    - /etc/shadow
    - /etc/group
    - /etc/gshadow
    - /etc/sudoers
    - /etc/sudoers.d/*

hipaa-fim-linux-auth:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/pam.d/*
    - /etc/ssh/sshd_config
    - /etc/ssh/ssh_config
    - /etc/security/*
    - /etc/login.defs

hipaa-fim-linux-ssh-keys:
  filters:
    platforms:
      - linux
  patterns:
    - /root/.ssh/authorized_keys
    - /root/.ssh/*
    - /home/*/.ssh/*

hipaa-fim-linux-persistence:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/cron.d/*
    - /etc/cron.daily/*
    - /etc/cron.hourly/*
    - /etc/cron.weekly/*
    - /etc/cron.monthly/*
    - /etc/crontab
    - /etc/systemd/system/*
    - /usr/lib/systemd/system/*
    - /etc/init.d/*
    - /etc/rc.local

hipaa-fim-linux-audit:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/audit/*
    - /etc/libaudit.conf

# §164.312(a)(2)(iii) Automatic Logoff — session timeout
hipaa-fim-linux-inactivity-policy:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/profile
    - /etc/profile.d/*
    - /etc/systemd/logind.conf
    - /etc/gdm3/custom.conf
    - /etc/gdm/custom.conf

# §164.312(c) — ePHI paths (customize per site)
hipaa-fim-linux-ephi:
  filters:
    platforms:
      - linux
  patterns:
    - /var/ephi/*
    - /var/phi/*
    - /srv/patient-data/*
    - /opt/ehr/data/*
```

### macOS

```yaml
hipaa-fim-macos-identity:
  filters:
    platforms:
      - macos
  patterns:
    - /etc/sudoers
    - /etc/sudoers.d/*
    - /etc/pam.d/*

hipaa-fim-macos-ssh-keys:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/.ssh/*
    - /var/root/.ssh/*

hipaa-fim-macos-launch-daemons:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/LaunchDaemons/*
    - /Library/LaunchAgents/*
    - /System/Library/LaunchDaemons/*
    - /System/Library/LaunchAgents/*
    - /Users/*/Library/LaunchAgents/*

hipaa-fim-macos-keychains:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/Library/Keychains/*
    - /Library/Keychains/*

# §164.312(a)(2)(iii) Automatic Logoff — screensaver / idle policy
hipaa-fim-macos-inactivity-policy:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/Preferences/com.apple.screensaver.plist
    - /Users/*/Library/Preferences/ByHost/com.apple.screensaver.*.plist
    - /Library/Preferences/com.apple.screensaver.plist

# §164.312(c) — ePHI paths (customize per site)
hipaa-fim-macos-ephi:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/Shared/ePHI/*
    - /Volumes/*/ePHI/*
    - /Users/*/Documents/PatientData/*
```

---

## 5. Exfil Event Collection Rules

Additive to default exfil rules — ensures HIPAA-required event types stream to the cloud even if defaults change.

### Windows

```yaml
hipaa-windows-events:
  events:
    - NEW_PROCESS
    - TERMINATE_PROCESS
    - FILE_CREATE
    - FILE_DELETE
    - FILE_MODIFIED
    - REGISTRY_CREATE
    - REGISTRY_WRITE
    - REGISTRY_DELETE
    - NEW_TCP4_CONNECTION
    - NEW_TCP6_CONNECTION
    - NEW_UDP4_CONNECTION
    - NEW_UDP6_CONNECTION
    - DNS_REQUEST
    - MODULE_LOAD
    - SERVICE_CHANGE
    - DRIVER_CHANGE
    - AUTORUN_CHANGE
    - FIM_HIT
    - WEL
    - YARA_DETECTION
    - CODE_IDENTITY
    - SENSITIVE_PROCESS_ACCESS
    - NEW_NAMED_PIPE
    - THREAD_INJECTION
    - NEW_DOCUMENT
    - NETWORK_CONNECTIONS
    - VOLUME_MOUNT
    - VOLUME_UNMOUNT
  filters:
    platforms:
      - windows
```

### Linux

```yaml
hipaa-linux-events:
  events:
    - NEW_PROCESS
    - TERMINATE_PROCESS
    - NEW_TCP4_CONNECTION
    - NEW_TCP6_CONNECTION
    - NEW_UDP4_CONNECTION
    - NEW_UDP6_CONNECTION
    - DNS_REQUEST
    - MODULE_LOAD
    - SERVICE_CHANGE
    - FIM_HIT
    - YARA_DETECTION
    - CODE_IDENTITY
    - NETWORK_CONNECTIONS
  filters:
    platforms:
      - linux
```

### macOS

```yaml
hipaa-macos-events:
  events:
    - NEW_PROCESS
    - TERMINATE_PROCESS
    - FILE_CREATE
    - FILE_DELETE
    - FILE_MODIFIED
    - NEW_TCP4_CONNECTION
    - NEW_TCP6_CONNECTION
    - NEW_UDP4_CONNECTION
    - NEW_UDP6_CONNECTION
    - DNS_REQUEST
    - SERVICE_CHANGE
    - FIM_HIT
    - MUL
    - YARA_DETECTION
    - CODE_IDENTITY
    - USER_LOGIN
    - USER_LOGOUT
    - SSH_LOGIN
    - SSH_LOGOUT
    - NETWORK_CONNECTIONS
    - VOLUME_MOUNT
    - VOLUME_UNMOUNT
  filters:
    platforms:
      - macos
```

---

## 6. D&R Rules — §164.312(b) Audit Controls

**Status: Required (R).** These rules surface audit-worthy activity on ePHI-bearing endpoints in real time and feed §164.308(a)(1)(ii)(D) Information System Activity Review.

### Windows — Failed Logon (§164.312(b), §164.308(a)(5)(ii)(C))

```yaml
name: hipaa-164-312-b-failed-logon-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4625'
respond:
  - action: report
    name: hipaa-164-312-b-failed-logon-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(b), §164.308(a)(5)(ii)(C)'
      description: Failed Windows logon — log-in monitoring
      mitre_attack_id: T1078
      mitre_tactic: initial-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-164-312-b-failed-logon-windows
tags:
  - hipaa
  - audit
comment: '§164.312(b) / §164.308(a)(5)(ii)(C) — Failed Windows logon (Event ID 4625)'
```

### Windows — Brute Force (§164.308(a)(5)(ii)(C))

```yaml
name: hipaa-308-a-5-brute-force-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4625'
respond:
  - action: report
    name: hipaa-308-a-5-brute-force-windows
    priority: 4
    metadata:
      hipaa_safeguard: '§164.308(a)(5)(ii)(C), §164.312(b)'
      description: Possible brute force — 10+ failed logons in 10 min
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      min_count: 10
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-308-a-5-brute-force-windows
tags:
  - hipaa
  - audit
comment: '§164.308(a)(5)(ii)(C) — Windows threshold-based brute force'
```

### macOS — Failed Authentication via Unified Log (§164.312(b), §164.308(a)(5)(ii)(C))

The native `SSH_LOGIN` event fires only on successful login and has no `IS_SUCCESS` field. Failed SSH and other authentication failures on macOS must be collected from the Unified Log. Deploy the `hipaa-mul-auth` artifact rule (Section 2), then match the MUL stream:

```yaml
name: hipaa-164-312-b-auth-failed-macos
detect:
  event: MUL
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/eventMessage
      re: '(?i)(authentication failure|failed password|failed to authenticate|auth_ok: false)'
respond:
  - action: report
    name: hipaa-164-312-b-auth-failed-macos
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(b), §164.308(a)(5)(ii)(C)'
      description: Authentication failure logged to macOS Unified Log
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-164-312-b-auth-failed-macos
tags:
  - hipaa
  - audit
comment: '§164.312(b) — macOS auth failures from Unified Log. Requires hipaa-mul-auth (Section 2).'
```

### Linux — Failed Auth via Process / Adapter

LC Linux sensor does not emit `SSH_LOGIN`. Detection of failed auth on Linux relies on the file adapter on `/var/log/auth.log` (Section 3, Option B) or auditd. If using the file adapter, author rules against the adapter's `text` platform event stream.

**File-adapter rule (runs on adapter `text` events):**

```yaml
name: hipaa-164-312-b-failed-auth-linux
detect:
  event: text
  op: matches
  path: event/raw
  re: '(?i)(Failed password|authentication failure|Failed publickey|pam_unix.*authentication failure)'
respond:
  - action: report
    name: hipaa-164-312-b-failed-auth-linux
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(b), §164.308(a)(5)(ii)(C)'
      description: Linux authentication failure from /var/log/auth.log file adapter
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-164-312-b-failed-auth-linux
tags:
  - hipaa
  - audit
comment: '§164.312(b) — Linux auth failure via file adapter (requires Option B from Section 3)'
```

### Windows — Audit Policy Changed (§164.312(b) Tamper)

```yaml
name: hipaa-164-312-b-audit-policy-changed
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4719'
respond:
  - action: report
    name: hipaa-164-312-b-audit-policy-changed
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(b)'
      description: Audit policy changed — potential tampering with HIPAA audit trail
      mitre_attack_id: T1562.002
      mitre_tactic: defense-evasion
tags:
  - hipaa
  - audit
comment: '§164.312(b) — Windows audit policy change (Event ID 4719)'
```

### Windows — Security Event Log Cleared (§164.312(b) Tamper)

```yaml
name: hipaa-164-312-b-event-log-cleared
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '1102'
respond:
  - action: report
    name: hipaa-164-312-b-event-log-cleared
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(b)'
      description: Security event log cleared — strong tampering indicator
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: hipaa-audit-tamper
    ttl: 86400
tags:
  - hipaa
  - audit
comment: '§164.312(b) — Windows event log clearing (1102). Tamper tag TTL 24h for SOC follow-up.'
```

### Windows — Event Log Service Tampering

```yaml
name: hipaa-164-312-b-eventlog-service-stop-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)stop\s+.*eventlog'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)sc\s+.*stop\s+.*eventlog'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)wevtutil\s+cl'
respond:
  - action: report
    name: hipaa-164-312-b-eventlog-service-stop-windows
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(b)'
      description: Attempt to stop event log service or clear event logs
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: hipaa-audit-tamper
    ttl: 86400
tags:
  - hipaa
  - audit
comment: '§164.312(b) — Windows event log tampering'
```

### Linux — Auditd Tampering

```yaml
name: hipaa-164-312-b-auditd-tamper-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\b(systemctl|service)\s+(stop|disable|mask)\s+auditd'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\bauditctl\s+.*-e\s+0'
        - op: matches
          path: event/FILE_PATH
          re: '(?i)/sbin/auditctl$'
respond:
  - action: report
    name: hipaa-164-312-b-auditd-tamper-linux
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(b)'
      description: Attempt to stop or disable Linux auditd
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: hipaa-audit-tamper
    ttl: 86400
tags:
  - hipaa
  - audit
comment: '§164.312(b) — Linux auditd tampering'
```

### macOS — Unified Log Tampering

```yaml
name: hipaa-164-312-b-log-tamper-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\blog\s+erase'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\blog\s+config\s+.*--mode\s+"level:off'
respond:
  - action: report
    name: hipaa-164-312-b-log-tamper-macos
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(b)'
      description: Attempt to erase or disable macOS unified log
      mitre_attack_id: T1070
      mitre_tactic: defense-evasion
  - action: add tag
    tag: hipaa-audit-tamper
    ttl: 86400
tags:
  - hipaa
  - audit
comment: '§164.312(b) — macOS log erase / disable'
```

### Windows Defender Real-Time Protection Disabled

```yaml
name: hipaa-308-a-5-defender-rtp-disabled
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Microsoft-Windows-Windows Defender/Operational
    - op: is
      path: event/EVENT/System/EventID
      value: '5001'
respond:
  - action: report
    name: hipaa-308-a-5-defender-rtp-disabled
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(5)(ii)(B), §164.312(b)'
      description: Windows Defender real-time protection disabled
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - hipaa
  - audit
  - defense-evasion
comment: '§164.308(a)(5)(ii)(B) — Defender RTP disabled (Event ID 5001)'
```

---

## 7. D&R Rules — §164.312(a) Access Control

**Status:** §164.312(a)(1) is the standard; specifications are a mix of R and A.

### §164.312(a)(2)(i) — Unique User Identification (R)

User identification is enforced by the OS / IdP — LC's contribution is ensuring every event carries attributable identity. Coverage is validated by the exfil rules (Section 5) and the WEL / MUL artifact rules (Sections 1, 2), plus these detection rules below.

#### Windows — User Account Created

```yaml
name: hipaa-312-a-2-i-user-created-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4720'
respond:
  - action: report
    name: hipaa-312-a-2-i-user-created-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(i), §164.308(a)(3)(ii)(C)'
      description: New Windows user account created
      mitre_attack_id: T1136.001
      mitre_tactic: persistence
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(2)(i) — Windows local user creation (Event ID 4720)'
```

#### Windows — User Added to Privileged Group

```yaml
name: hipaa-312-a-1-privileged-group-add-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: or
      rules:
        - op: is
          path: event/EVENT/System/EventID
          value: '4728'
        - op: is
          path: event/EVENT/System/EventID
          value: '4732'
        - op: is
          path: event/EVENT/System/EventID
          value: '4756'
respond:
  - action: report
    name: hipaa-312-a-1-privileged-group-add-windows
    priority: 4
    metadata:
      hipaa_safeguard: '§164.312(a)(1)'
      description: User added to a Windows security-enabled group
      mitre_attack_id: T1098
      mitre_tactic: persistence
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(1) — Windows group-membership addition (4728, 4732, 4756)'
```

#### Windows — User Account Deleted

```yaml
name: hipaa-308-a-3-user-deleted-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4726'
respond:
  - action: report
    name: hipaa-308-a-3-user-deleted-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.308(a)(3)(ii)(C)'
      description: Windows user account deleted — correlate with termination workflow
tags:
  - hipaa
  - access-control
comment: '§164.308(a)(3)(ii)(C) — Windows user deletion (Event ID 4726)'
```

#### Linux — Account Management Binary Execution

```yaml
name: hipaa-312-a-2-i-user-mgmt-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(useradd|usermod|userdel|groupadd|groupmod|groupdel|gpasswd|chpasswd)$'
respond:
  - action: report
    name: hipaa-312-a-2-i-user-mgmt-linux
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(i), §164.308(a)(3)(ii)(C)'
      description: Linux account management binary executed
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(2)(i) — Linux user/group management'
```

#### macOS — Account Management via dscl

```yaml
name: hipaa-312-a-2-i-user-mgmt-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: or
      rules:
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '/usr/bin/dscl$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\s-(create|delete|append|change|mergepwpolicy|passwd)\b'
        - op: matches
          path: event/FILE_PATH
          re: '(?i)/(sysadminctl|dsimport)$'
respond:
  - action: report
    name: hipaa-312-a-2-i-user-mgmt-macos
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(i), §164.308(a)(3)(ii)(C)'
      description: macOS account management (dscl / sysadminctl)
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(2)(i) — macOS account management'
```

### §164.312(a)(1) — Privileged Access

#### Windows — Special Privileges Assigned

```yaml
name: hipaa-312-a-1-special-privilege-logon
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4672'
respond:
  - action: report
    name: hipaa-312-a-1-special-privilege-logon
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(a)(1)'
      description: Special privileges assigned to new logon
      mitre_attack_id: T1078
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-a-1-special-privilege-logon
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(1) — Windows special privileges (Event ID 4672)'
```

#### Windows — Privileged Service Called

```yaml
name: hipaa-312-a-1-privileged-service-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: or
      rules:
        - op: is
          path: event/EVENT/System/EventID
          value: '4673'
        - op: is
          path: event/EVENT/System/EventID
          value: '4674'
respond:
  - action: report
    name: hipaa-312-a-1-privileged-service-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(a)(1)'
      description: Privileged service or object operation
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-a-1-privileged-service-windows
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(1) — Windows privileged service call (4673, 4674)'
```

#### Linux — sudo / su / pkexec

```yaml
name: hipaa-312-a-1-privilege-escalation-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(sudo|su|pkexec|doas)$'
respond:
  - action: report
    name: hipaa-312-a-1-privilege-escalation-linux
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(a)(1)'
      description: Linux privilege-escalation command
      mitre_attack_id: T1548.003
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(1) — Linux sudo/su/pkexec/doas per-user-per-hour'
```

#### macOS — sudo Execution

```yaml
name: hipaa-312-a-1-sudo-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/usr/bin/sudo$'
respond:
  - action: report
    name: hipaa-312-a-1-sudo-macos
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(a)(1)'
      description: macOS sudo invocation
      mitre_attack_id: T1548.003
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(1) — macOS sudo'
```

### §164.312(a)(2)(iii) — Automatic Logoff (A)

LC does not enforce auto-logoff but detects configuration changes that weaken it.

#### Windows — Inactivity Timeout Policy Changed

```yaml
name: hipaa-312-a-2-iii-autologoff-config-change-windows
detect:
  event: FIM_HIT
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\Policies\\System\\(InactivityTimeoutSecs|ScreenSaveTimeOut)'
respond:
  - action: report
    name: hipaa-312-a-2-iii-autologoff-config-change-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(iii)'
      description: Windows inactivity-timeout / screensaver policy changed
      mitre_attack_id: T1562
      mitre_tactic: defense-evasion
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(2)(iii) — Windows auto-logoff policy change. Requires hipaa-fim-windows-inactivity-policy FIM rule (Section 4).'
```

#### Linux — Session Timeout Config Changed

```yaml
name: hipaa-312-a-2-iii-autologoff-config-change-linux
detect:
  event: FIM_HIT
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/etc/(profile|systemd/logind\.conf|gdm3?/custom\.conf)'
respond:
  - action: report
    name: hipaa-312-a-2-iii-autologoff-config-change-linux
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(iii)'
      description: Linux session-timeout / logind policy changed
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(2)(iii) — Linux auto-logoff config change. Requires hipaa-fim-linux-inactivity-policy FIM rule (Section 4).'
```

#### macOS — Screensaver Idle Time Changed

```yaml
name: hipaa-312-a-2-iii-autologoff-config-change-macos
detect:
  event: FILE_MODIFIED
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/Library/Preferences/com\.apple\.screensaver\.plist$'
respond:
  - action: report
    name: hipaa-312-a-2-iii-autologoff-config-change-macos
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(iii)'
      description: macOS screensaver / auto-logoff policy changed
      mitre_attack_id: T1562
      mitre_tactic: defense-evasion
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(2)(iii) — macOS screensaver policy change via FILE_MODIFIED'
```

### §164.312(a)(2)(iv) — Encryption and Decryption (A)

#### Windows — BitLocker Disabled / Status Change

BitLocker state changes are captured in `wel://Microsoft-Windows-BitLocker/BitLocker Management:*`. Add the artifact collection rule (same pattern as Section 1), then:

```yaml
name: hipaa-312-a-2-iv-bitlocker-disabled-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: or
      rules:
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)\\manage-bde\.exe$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)(-off|-disable)'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)\\powershell(\.exe)?$|\\pwsh\.exe$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)(Disable-BitLocker|Suspend-BitLocker)'
respond:
  - action: report
    name: hipaa-312-a-2-iv-bitlocker-disabled-windows
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(iv)'
      description: BitLocker disabled or suspended — ePHI encryption at rest degraded
      mitre_attack_id: T1486
      mitre_tactic: impact
tags:
  - hipaa
  - access-control
  - encryption
comment: '§164.312(a)(2)(iv) — Windows BitLocker disable / suspend'
```

#### macOS — FileVault Disabled

```yaml
name: hipaa-312-a-2-iv-filevault-disabled-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/usr/bin/fdesetup$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\s(disable|off)\b'
respond:
  - action: report
    name: hipaa-312-a-2-iv-filevault-disabled-macos
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(a)(2)(iv)'
      description: macOS FileVault disabled — ePHI encryption at rest degraded
      mitre_attack_id: T1486
      mitre_tactic: impact
tags:
  - hipaa
  - access-control
  - encryption
comment: '§164.312(a)(2)(iv) — macOS FileVault disable'
```

### §164.312(a)(1) / §164.308(a)(4) — Remote Access

#### Windows — RDP Logon

```yaml
name: hipaa-312-a-1-rdp-logon
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4624'
    - op: is
      path: event/EVENT/EventData/LogonType
      value: '10'
respond:
  - action: report
    name: hipaa-312-a-1-rdp-logon
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(a)(1), §164.308(a)(4)'
      description: RDP logon (LogonType 10)
      mitre_attack_id: T1021.001
      mitre_tactic: lateral-movement
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-a-1-rdp-logon
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(1) — Windows RDP logon'
```

#### macOS — SSH Login

```yaml
name: hipaa-312-a-1-ssh-login-macos
detect:
  event: SSH_LOGIN
  op: is mac
respond:
  - action: report
    name: hipaa-312-a-1-ssh-login-macos
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(a)(1), §164.308(a)(4)'
      description: macOS SSH session established
      mitre_attack_id: T1021.004
      mitre_tactic: lateral-movement
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-a-1-ssh-login-macos
tags:
  - hipaa
  - access-control
comment: '§164.312(a)(1) — macOS SSH login (success only — no IS_SUCCESS field)'
```

---

## 8. D&R Rules — §164.312(d) Person or Entity Authentication

**Status: Required (R).**

### Windows — Password Change / Reset (§164.308(a)(5)(ii)(D))

```yaml
name: hipaa-312-d-password-change-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: or
      rules:
        - op: is
          path: event/EVENT/System/EventID
          value: '4723'
        - op: is
          path: event/EVENT/System/EventID
          value: '4724'
respond:
  - action: report
    name: hipaa-312-d-password-change-windows
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(d), §164.308(a)(5)(ii)(D)'
      description: Windows password change (4723) or reset (4724)
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-d-password-change-windows
tags:
  - hipaa
  - authentication
comment: '§164.312(d) — Windows password change / reset'
```

### Linux — Password Management Utility

```yaml
name: hipaa-312-d-password-change-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(passwd|chage|chpasswd)$'
respond:
  - action: report
    name: hipaa-312-d-password-change-linux
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(d), §164.308(a)(5)(ii)(D)'
      description: Linux password management utility executed
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - hipaa
  - authentication
comment: '§164.312(d) — Linux passwd/chage/chpasswd'
```

### macOS — Password Change via passwd / dscl

```yaml
name: hipaa-312-d-password-change-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: or
      rules:
        - op: matches
          path: event/FILE_PATH
          re: '(?i)/usr/bin/passwd$'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/usr/bin/dscl$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\s-passwd\b'
respond:
  - action: report
    name: hipaa-312-d-password-change-macos
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(d), §164.308(a)(5)(ii)(D)'
      description: macOS password change (passwd / dscl)
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - hipaa
  - authentication
comment: '§164.312(d) — macOS password change'
```

### Windows — NTLM Authentication Tracking

```yaml
name: hipaa-312-d-ntlm-auth
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4776'
respond:
  - action: report
    name: hipaa-312-d-ntlm-auth
    priority: 1
    metadata:
      hipaa_safeguard: '§164.312(d)'
      description: NTLM credential validation
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-d-ntlm-auth
tags:
  - hipaa
  - authentication
comment: '§164.312(d) — NTLM tracking. High suppression — noisy in AD.'
```

### Windows — Account Lockout (§164.308(a)(5)(ii)(C))

```yaml
name: hipaa-308-a-5-account-lockout-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4740'
respond:
  - action: report
    name: hipaa-308-a-5-account-lockout-windows
    priority: 4
    metadata:
      hipaa_safeguard: '§164.308(a)(5)(ii)(C), §164.312(d)'
      description: Windows account locked due to failed logons
      mitre_attack_id: T1110
      mitre_tactic: credential-access
tags:
  - hipaa
  - authentication
comment: '§164.308(a)(5)(ii)(C) — Windows account lockout (4740)'
```

---

## 9. D&R Rules — §164.312(c) Integrity

**Status:** §164.312(c)(1) is the standard; §164.312(c)(2) (Authenticate ePHI) is Addressable (A).

### FIM Hit on ePHI Path (All Platforms)

```yaml
name: hipaa-312-c-fim-hit
detect:
  event: FIM_HIT
  op: exists
  path: event/FILE_PATH
respond:
  - action: report
    name: hipaa-312-c-fim-hit
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1), §164.312(c)(2)'
      description: File integrity change on monitored path
      mitre_attack_id: T1565
      mitre_tactic: impact
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) / §164.312(c)(2) — FIM hit on any monitored path. Pair with Section 4 FIM rules to scope to ePHI.'
```

### ePHI File Modified by LOLBin / Scripting Host (Windows)

```yaml
name: hipaa-312-c-ephi-touched-by-lolbin-windows
detect:
  event: FILE_MODIFIED
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(ephi|phi|patient|medical)\\.*\.(db|mdb|sql|bak|xlsx?|csv|json)$'
    - op: matches
      path: event/PROCESS/FILE_PATH
      re: '(?i)\\(powershell|pwsh|cmd|wscript|cscript|mshta|rundll32|regsvr32|certutil)\.exe$'
respond:
  - action: report
    name: hipaa-312-c-ephi-touched-by-lolbin-windows
    priority: 4
    metadata:
      hipaa_safeguard: '§164.312(c)(1), §164.312(c)(2)'
      description: ePHI-bearing file modified by scripting / LOLBin process
      mitre_attack_id: T1565
      mitre_tactic: impact
tags:
  - hipaa
  - integrity
comment: '§164.312(c) — ePHI path touched by LOLBin. Adjust regex to match site ePHI paths.'
```

### ePHI File Modified (macOS)

```yaml
name: hipaa-312-c-ephi-file-modified-macos
detect:
  event: FILE_MODIFIED
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)(ephi|phi|patient|medical)[\\/]'
respond:
  - action: report
    name: hipaa-312-c-ephi-file-modified-macos
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1), §164.312(c)(2)'
      description: ePHI-path file modified
tags:
  - hipaa
  - integrity
comment: '§164.312(c) — macOS ePHI path FILE_MODIFIED. Customize regex per site ePHI layout.'
```

### YARA Detection (All Platforms) — §164.308(a)(5)(ii)(B)

```yaml
name: hipaa-308-a-5-yara-detection
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: hipaa-308-a-5-yara-detection
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(5)(ii)(B), §164.312(c)(1)'
      description: YARA rule match — possible malware
      mitre_tactic: execution
tags:
  - hipaa
  - malware
comment: '§164.308(a)(5)(ii)(B) — YARA on any platform'
```

### Windows Defender Threat Detected

```yaml
name: hipaa-308-a-5-defender-threat
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Microsoft-Windows-Windows Defender/Operational
    - op: or
      rules:
        - op: is
          path: event/EVENT/System/EventID
          value: '1116'
        - op: is
          path: event/EVENT/System/EventID
          value: '1117'
respond:
  - action: report
    name: hipaa-308-a-5-defender-threat
    priority: 4
    metadata:
      hipaa_safeguard: '§164.308(a)(5)(ii)(B)'
      description: Windows Defender detected or acted on a threat
      mitre_tactic: execution
tags:
  - hipaa
  - malware
comment: '§164.308(a)(5)(ii)(B) — Defender threat alerts (1116, 1117)'
```

### Ransomware Precursor — Shadow Copy Deletion (§164.312(c)(1) / §164.308(a)(6)(ii))

```yaml
name: hipaa-312-c-ransomware-precursor-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(vssadmin|wbadmin|wmic|bcdedit)\.exe$'
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)(delete\s+shadows|delete\s+catalog|shadowcopy\s+delete)'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)bcdedit\s+.*\s+(recoveryenabled\s+no|bootstatuspolicy\s+ignoreallfailures)'
respond:
  - action: report
    name: hipaa-312-c-ransomware-precursor-windows
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(c)(1), §164.308(a)(6)(ii)'
      description: Shadow copy deletion or boot-recovery disabled — ransomware precursor
      mitre_attack_id: T1490
      mitre_tactic: impact
  - action: add tag
    tag: hipaa-ransomware-precursor
    ttl: 86400
tags:
  - hipaa
  - integrity
  - impact
comment: '§164.312(c)(1) — Windows shadow copy delete / recovery disable'
```

### Windows — LSASS Access (Credential Dumping)

```yaml
name: hipaa-312-a-1-lsass-access
detect:
  event: SENSITIVE_PROCESS_ACCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/TARGET/FILE_PATH
      re: '(?i)\\lsass\.exe$'
respond:
  - action: report
    name: hipaa-312-a-1-lsass-access
    priority: 5
    metadata:
      hipaa_safeguard: '§164.312(a)(1), §164.312(d)'
      description: Sensitive handle to LSASS — possible credential dumping
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-a-1-lsass-access
tags:
  - hipaa
  - integrity
  - credential-access
comment: '§164.312(a)(1) / §164.312(d) — LSASS access'
```

### Windows — Thread Injection

```yaml
name: hipaa-312-c-thread-injection
detect:
  event: THREAD_INJECTION
  op: is windows
respond:
  - action: report
    name: hipaa-312-c-thread-injection
    priority: 4
    metadata:
      hipaa_safeguard: '§164.312(c)(1)'
      description: Thread injection — process injecting code into another
      mitre_attack_id: T1055
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-c-thread-injection
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — Thread injection'
```

### Unsigned Binary in Trusted Path (Win / macOS) — §164.312(c)(2)

```yaml
name: hipaa-312-c-2-unsigned-binary
detect:
  event: CODE_IDENTITY
  op: and
  rules:
    - op: or
      rules:
        - op: is windows
        - op: is mac
    - op: is
      path: event/SIGNATURE/FILE_IS_SIGNED
      value: '0'
    - op: matches
      path: event/FILE_PATH
      re: '(?i)(\\(windows|program files|program files \(x86\))\\|^/(System|Library|usr)/)'
respond:
  - action: report
    name: hipaa-312-c-2-unsigned-binary
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(2)'
      description: Unsigned binary loaded from a system path — integrity check failure
      mitre_attack_id: T1574
      mitre_tactic: persistence
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.FILE_PATH }}'
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(2) — Unsigned binary in trusted system path (Win/macOS)'
```

### Windows — New Service / Scheduled Task

```yaml
name: hipaa-312-c-new-service-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: System
    - op: is
      path: event/EVENT/System/EventID
      value: '7045'
respond:
  - action: report
    name: hipaa-312-c-new-service-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1), §164.308(a)(1)(ii)(D)'
      description: New Windows service installed
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — Windows new service (7045)'
```

```yaml
name: hipaa-312-c-scheduled-task-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4698'
respond:
  - action: report
    name: hipaa-312-c-scheduled-task-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1)'
      description: Scheduled task created
      mitre_attack_id: T1053.005
      mitre_tactic: persistence
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — Windows scheduled task (4698)'
```

### Linux — Cron / Systemd Persistence

```yaml
name: hipaa-312-c-cron-modification-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\bcrontab\s+(-e|-r|[^\s-])'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\bsystemctl\s+(enable|start|daemon-reload)\b'
respond:
  - action: report
    name: hipaa-312-c-cron-modification-linux
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1)'
      description: Linux persistence mechanism modification (cron, systemd)
      mitre_attack_id: T1053.003
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-c-cron-modification-linux
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — Linux crontab / systemctl enable'
```

### macOS — LaunchAgent / LaunchDaemon Changes

```yaml
name: hipaa-312-c-launchd-modification-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/bin/launchctl$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\b(load|bootstrap|enable)\b'
respond:
  - action: report
    name: hipaa-312-c-launchd-modification-macos
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1)'
      description: macOS launchctl load / bootstrap — persistence indicator
      mitre_attack_id: T1543.001
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-c-launchd-modification-macos
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — macOS launchctl load/bootstrap'
```

### Windows — Autorun Changed

```yaml
name: hipaa-312-c-autorun-change-windows
detect:
  event: AUTORUN_CHANGE
  op: is windows
respond:
  - action: report
    name: hipaa-312-c-autorun-change-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1)'
      description: Windows autorun persistence change
      mitre_attack_id: T1547.001
      mitre_tactic: persistence
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-c-autorun-change-windows
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — Windows autorun change'
```

### Windows — Driver Change

```yaml
name: hipaa-312-c-driver-change
detect:
  event: DRIVER_CHANGE
  op: is windows
respond:
  - action: report
    name: hipaa-312-c-driver-change
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(c)(1)'
      description: Driver installed or modified
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — Driver change'
```

### Service Change (All Platforms)

```yaml
name: hipaa-312-c-service-change
detect:
  event: SERVICE_CHANGE
  op: exists
  path: event/SVC_NAME
respond:
  - action: report
    name: hipaa-312-c-service-change
    priority: 2
    metadata:
      hipaa_safeguard: '§164.312(c)(1)'
      description: Service configuration changed
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - hipaa-312-c-service-change
tags:
  - hipaa
  - integrity
comment: '§164.312(c)(1) — Service change. Suppressed for patching noise.'
```

---

## 10. D&R Rules — §164.308 Administrative Safeguards (Technical Portions)

### §164.308(a)(3)(ii)(C) — Termination Procedures (A)

**Pre-requisite:** create a hive lookup populated by HR / IdP with terminated usernames. The lookup name must match the `resource:` field below.

```
limacharlie hive get --name hipaa-terminated-users --hive-name lookup
```

> **Populating the lookup:** feed from the IdP via a scheduled Playbook that queries the IAM termination list and writes to the lookup, or via webhook adapter from the HRIS (Workday, BambooHR, etc.). See the `lc-essentials:adapter-assistant` skill.

#### Continued Process Activity From Terminated User (Windows)

```yaml
name: hipaa-308-a-3-terminated-user-activity-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: lookup
      path: event/USER_NAME
      resource: hive://lookup/hipaa-terminated-users
respond:
  - action: report
    name: hipaa-308-a-3-terminated-user-activity-windows
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(3)(ii)(C)'
      description: Process activity from a user in the terminated-users lookup
      mitre_attack_id: T1078
      mitre_tactic: persistence
  - action: add tag
    tag: hipaa-terminated-user-activity
    ttl: 604800
tags:
  - hipaa
  - access-control
  - insider-risk
comment: '§164.308(a)(3)(ii)(C) — Activity from terminated user (Windows). Requires hive://lookup/hipaa-terminated-users populated from HR/IdP.'
```

#### Continued Activity From Terminated User (Linux)

```yaml
name: hipaa-308-a-3-terminated-user-activity-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: lookup
      path: event/USER_NAME
      resource: hive://lookup/hipaa-terminated-users
respond:
  - action: report
    name: hipaa-308-a-3-terminated-user-activity-linux
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(3)(ii)(C)'
      description: Process activity from a user in the terminated-users lookup
      mitre_attack_id: T1078
      mitre_tactic: persistence
  - action: add tag
    tag: hipaa-terminated-user-activity
    ttl: 604800
tags:
  - hipaa
  - access-control
  - insider-risk
comment: '§164.308(a)(3)(ii)(C) — Activity from terminated user (Linux)'
```

#### Terminated User SSH / Console Login (macOS)

```yaml
name: hipaa-308-a-3-terminated-user-login-macos
detect:
  event: USER_LOGIN
  op: and
  rules:
    - op: is mac
    - op: lookup
      path: event/USER_NAME
      resource: hive://lookup/hipaa-terminated-users
respond:
  - action: report
    name: hipaa-308-a-3-terminated-user-login-macos
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(3)(ii)(C)'
      description: Login from user in the terminated-users lookup
      mitre_attack_id: T1078
      mitre_tactic: persistence
tags:
  - hipaa
  - access-control
  - insider-risk
comment: '§164.308(a)(3)(ii)(C) — Terminated-user login on macOS'
```

### §164.308(a)(5)(ii)(B) — Protection from Malicious Software (A)

Covered by rules in Section 9 (`hipaa-308-a-5-yara-detection`, `hipaa-308-a-5-defender-threat`, `hipaa-308-a-5-defender-rtp-disabled`) plus subscribed managed rulesets (Soteria, Sigma).

### §164.308(a)(5)(ii)(C) — Log-in Monitoring (A)

Covered by rules in Sections 6 and 8 (`hipaa-164-312-b-failed-logon-windows`, `hipaa-308-a-5-brute-force-windows`, `hipaa-164-312-b-auth-failed-macos`, `hipaa-164-312-b-failed-auth-linux`, `hipaa-308-a-5-account-lockout-windows`).

### §164.308(a)(6)(ii) — Response and Reporting (R)

#### Tag Endpoints on Critical Threats — Case Triage

```yaml
name: hipaa-308-a-6-critical-threat-tag
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: hipaa-308-a-6-critical-threat-tag
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(6)(ii)'
      description: YARA detection — tagged for case triage / breach-notification clock
  - action: add tag
    tag: hipaa-incident
    ttl: 604800
tags:
  - hipaa
  - incident-response
comment: '§164.308(a)(6)(ii) — Tag endpoints on YARA detection (7-day tag for SOC triage)'
```

#### Automated Network Isolation (Opt-In)

> Network isolation is disruptive. Deploy only with stakeholder approval for well-tuned, high-confidence detections. Enable by adding the `isolation-enabled` tag to sensors that have been enrolled in the response policy.

```yaml
name: hipaa-308-a-6-isolate-on-credential-dump
detect:
  event: SENSITIVE_PROCESS_ACCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/TARGET/FILE_PATH
      re: '(?i)\\lsass\.exe$'
    - op: is tagged
      tag: isolation-enabled
respond:
  - action: report
    name: hipaa-308-a-6-isolate-on-credential-dump
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(6)(ii), §164.312(a)(1)'
      description: LSASS access on isolation-enrolled host — automated containment
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
  - action: isolate network
tags:
  - hipaa
  - incident-response
comment: '§164.308(a)(6)(ii) — Isolate host on LSASS access. Opt-in via "isolation-enabled" sensor tag.'
```

```yaml
name: hipaa-308-a-6-isolate-on-ransomware-precursor
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: is tagged
      tag: isolation-enabled
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\vssadmin\.exe$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)(delete\s+shadows|shadowcopy\s+delete)'
respond:
  - action: report
    name: hipaa-308-a-6-isolate-on-ransomware-precursor
    priority: 5
    metadata:
      hipaa_safeguard: '§164.308(a)(6)(ii), §164.312(c)(1)'
      description: Shadow copy deletion on isolation-enrolled host — automated containment
      mitre_attack_id: T1490
      mitre_tactic: impact
  - action: isolate network
tags:
  - hipaa
  - incident-response
comment: '§164.308(a)(6)(ii) — Isolate on shadow-copy deletion. Opt-in.'
```

---

## 11. D&R Rules — §164.312(e) Transmission Security

**Status:** §164.312(e)(1) is the standard; §164.312(e)(2)(i) and (ii) are Addressable.

### Outbound Connection From Scripting / LOLBin Process (§164.312(e)(1), §164.312(e)(2)(i))

```yaml
name: hipaa-312-e-suspicious-outbound
detect:
  event: NEW_TCP4_CONNECTION
  op: and
  rules:
    - op: is public address
      path: event/NETWORK_ACTIVITY/DESTINATION/IP_ADDRESS
    - op: matches
      path: event/PROCESS/FILE_PATH
      re: '(?i)\\(powershell|pwsh|cmd|wscript|cscript|mshta|rundll32|regsvr32)\.exe$|/usr/bin/(curl|wget|nc|ncat)$'
respond:
  - action: report
    name: hipaa-312-e-suspicious-outbound
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(e)(1), §164.312(e)(2)(i)'
      description: Outbound public-IP connection from command-line / scripting utility
      mitre_attack_id: T1071
      mitre_tactic: command-and-control
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.PROCESS.FILE_PATH }}'
tags:
  - hipaa
  - transmission
comment: '§164.312(e)(1) — Outbound from scripting / LOLBin'
```

### Plaintext Egress to Public Addresses (§164.312(e)(2)(ii))

```yaml
name: hipaa-312-e-plaintext-egress
detect:
  event: NEW_TCP4_CONNECTION
  op: and
  rules:
    - op: is public address
      path: event/NETWORK_ACTIVITY/DESTINATION/IP_ADDRESS
    - op: or
      rules:
        - op: is
          path: event/NETWORK_ACTIVITY/DESTINATION/PORT
          value: '21'
        - op: is
          path: event/NETWORK_ACTIVITY/DESTINATION/PORT
          value: '23'
        - op: is
          path: event/NETWORK_ACTIVITY/DESTINATION/PORT
          value: '80'
        - op: is
          path: event/NETWORK_ACTIVITY/DESTINATION/PORT
          value: '110'
        - op: is
          path: event/NETWORK_ACTIVITY/DESTINATION/PORT
          value: '143'
respond:
  - action: report
    name: hipaa-312-e-plaintext-egress
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(e)(2)(ii)'
      description: Outbound plaintext protocol (FTP/Telnet/HTTP/POP3/IMAP) to public address
      mitre_attack_id: T1048
      mitre_tactic: exfiltration
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.NETWORK_ACTIVITY.DESTINATION.PORT }}'
tags:
  - hipaa
  - transmission
  - encryption
comment: '§164.312(e)(2)(ii) — Plaintext egress. Tune to exclude approved HTTP destinations.'
```

### ePHI Exfil Staging (Bulk Archive / Copy) — Windows

```yaml
name: hipaa-312-e-ephi-staging-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)(robocopy|xcopy|Compress-Archive|7z(\.exe)?\s+a)\b.*\\(ephi|phi|patient|medical)\\'
respond:
  - action: report
    name: hipaa-312-e-ephi-staging-windows
    priority: 4
    metadata:
      hipaa_safeguard: '§164.312(e)(1), §164.308(a)(6)(ii)'
      description: Bulk copy / archive involving ePHI-path contents — possible exfil staging
      mitre_attack_id: T1560
      mitre_tactic: collection
tags:
  - hipaa
  - transmission
  - exfil
comment: '§164.312(e)(1) — ePHI staging. Tune ePHI path regex to site layout.'
```

### Firewall Rule Changed — Windows

```yaml
name: hipaa-312-e-firewall-changed-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: or
      rules:
        - op: is
          path: event/EVENT/System/EventID
          value: '4946'
        - op: is
          path: event/EVENT/System/EventID
          value: '4947'
        - op: is
          path: event/EVENT/System/EventID
          value: '4948'
        - op: is
          path: event/EVENT/System/EventID
          value: '4950'
respond:
  - action: report
    name: hipaa-312-e-firewall-changed-windows
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(e)(1)'
      description: Windows Firewall rule or setting changed
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - hipaa
  - transmission
comment: '§164.312(e)(1) — Windows firewall changes (4946-4950)'
```

### Firewall Changes — Linux

```yaml
name: hipaa-312-e-firewall-changed-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: or
      rules:
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/(iptables|ip6tables|nft)$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\s-(A|D|I|F|X|P)\s'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/firewall-cmd$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)--(add|remove|permanent)'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/ufw$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\s(allow|deny|disable|enable|reset|delete)\b'
respond:
  - action: report
    name: hipaa-312-e-firewall-changed-linux
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(e)(1)'
      description: Linux firewall modification (iptables / nft / firewall-cmd / ufw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - hipaa
  - transmission
comment: '§164.312(e)(1) — Linux firewall changes'
```

### Firewall Changes — macOS

```yaml
name: hipaa-312-e-firewall-changed-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: or
      rules:
        - op: matches
          path: event/FILE_PATH
          re: '(?i)/sbin/pfctl$'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/usr/libexec/ApplicationFirewall/socketfilterfw$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)--(set|add|remove)'
respond:
  - action: report
    name: hipaa-312-e-firewall-changed-macos
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(e)(1)'
      description: macOS firewall modification (pfctl / socketfilterfw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - hipaa
  - transmission
comment: '§164.312(e)(1) — macOS firewall changes'
```

### Suspicious DNS — Known-Bad / Newly-Registered Domains

> Requires a `hive://lookup/hipaa-bad-domains` lookup populated from a threat-intel feed (AlienVault OTX, Emerging Threats, etc.).

```yaml
name: hipaa-312-e-bad-domain-dns
detect:
  event: DNS_REQUEST
  op: and
  rules:
    - op: lookup
      path: event/DOMAIN_NAME
      resource: hive://lookup/hipaa-bad-domains
respond:
  - action: report
    name: hipaa-312-e-bad-domain-dns
    priority: 4
    metadata:
      hipaa_safeguard: '§164.312(e)(1), §164.308(a)(5)(ii)(B)'
      description: DNS request to a domain in the known-bad-domain lookup
      mitre_attack_id: T1071.004
      mitre_tactic: command-and-control
tags:
  - hipaa
  - transmission
comment: '§164.312(e)(1) — DNS-based C2 detection via threat-intel lookup'
```

---

## 12. D&R Rules — Breach Notification Support (§164.400–414)

These rules do not themselves trigger breach notification — that is a legal / compliance determination — but they produce the timestamped detection-to-case record that documents when the covered entity *discovered* the incident (the start of the 60-day notification clock per §164.404(b)).

### Removable Media Mount on ePHI Endpoint (Windows / macOS)

```yaml
name: hipaa-400-removable-media-mount
detect:
  event: VOLUME_MOUNT
  op: and
  rules:
    - op: or
      rules:
        - op: is windows
        - op: is mac
    - op: is tagged
      tag: hipaa-ephi-host
respond:
  - action: report
    name: hipaa-400-removable-media-mount
    priority: 3
    metadata:
      hipaa_safeguard: '§164.310(d)(1), §164.312(e)(1), §164.400–414'
      description: Removable volume mounted on ePHI-designated endpoint
      mitre_attack_id: T1052.001
      mitre_tactic: exfiltration
tags:
  - hipaa
  - breach-notification
comment: '§164.400 — Removable media on ePHI host. Tag ePHI hosts with "hipaa-ephi-host".'
```

### Endpoint Sensor Disconnected — Coverage Gap

```yaml
name: hipaa-400-sensor-offline
detect:
  target: deployment
  event: disconnect
  op: is tagged
  tag: hipaa-ephi-host
respond:
  - action: report
    name: hipaa-400-sensor-offline
    priority: 3
    metadata:
      hipaa_safeguard: '§164.312(b), §164.400–414'
      description: Sensor disconnected from ePHI host — audit coverage gap begins
tags:
  - hipaa
  - audit
  - breach-notification
comment: '§164.312(b) — Sensor disconnection on ePHI host. Surfaces coverage gaps that could hide breach activity.'
```

### Open Case from Critical ePHI-Host Detection

This is an organizational pattern rather than a single rule: configure the **Cases extension** (ext-cases) ingestion to create a case for every detection tagged `hipaa-incident` on a sensor tagged `hipaa-ephi-host`. The case open timestamp is the defensible discovery time.

In ext-cases configuration:

```yaml
ingestion:
  mode: tailored
  rules:
    - match:
        tags_any:
          - hipaa-incident
        sensor_tags_any:
          - hipaa-ephi-host
      severity_floor: 3
      action: create_case
```

### Initial Scope Hunt (LCQL Template)

When a breach is suspected, the following LCQL query establishes initial scope by finding every host that touched the same file hash as the indexed IOC:

```
<90d -1h | event/HASH is "<suspect-hash>" | routing.hostname routing.sid event/FILE_PATH routing.event_time
```

Automate this via a playbook that triggers on `tag: hipaa-incident` and writes results to the case file.

---

## 13. Recommended Extensions

### Required

| Extension | Purpose | HIPAA Safeguards |
|---|---|---|
| **Reliable Tasking** | Prerequisite for Artifact Collection. Ensures tasks reach offline sensors. | §164.312(b), §164.308(a)(1)(ii)(D) |
| **Artifact Collection (ext-artifact)** | Manages WEL/MUL streaming and file/log retention. | §164.312(b), §164.316(b)(2)(i) |
| **Exfil Control (ext-exfil)** | Manages which event types flow from sensor to cloud. | §164.312(b) |
| **Integrity (ext-integrity)** | FIM / RIM rule management. | §164.312(c)(1), §164.312(c)(2) |

### Strongly Recommended

| Extension | Purpose | HIPAA Safeguards |
|---|---|---|
| **Cases (ext-cases)** | SOC case management with detection-to-case conversion, SLA tracking, investigation workflows — the defensible breach-discovery timeline. | §164.308(a)(6)(ii), §164.400–414 |
| **EPP (Endpoint Protection)** | Unified Windows Defender management and event collection. Free. | §164.308(a)(5)(ii)(B) |
| **Soteria EDR Rules** | Managed detection ruleset with MITRE ATT&CK mapping across 14 event types. | §164.308(a)(1)(ii)(D), §164.312(b) |
| **Sigma Rules** | Community and commercial Sigma rule conversion. | §164.308(a)(1)(ii)(D), §164.312(b) |

### Recommended for Enhanced Coverage

| Extension | Purpose | HIPAA Safeguards |
|---|---|---|
| **Strelka** | File analysis (YARA, PE, archive extraction) for files transiting endpoints — including ePHI attachments. | §164.308(a)(5)(ii)(B), §164.312(c)(1) |
| **Zeek** | Network monitoring and analysis (Linux sensors). | §164.312(e)(1) |
| **Velociraptor** | DFIR hunting and artifact collection for post-breach investigation. | §164.308(a)(6)(ii), §164.400–414 |
| **Playbook** | Python-based automation for custom response, enrichment, and HRIS integration (terminated-users lookup, case notifications). | §164.308(a)(3)(ii)(C), §164.308(a)(6)(ii) |
| **ext-git-sync** | Infrastructure as Code — D&R rules, FIM, outputs, extensions managed via git. Supports §164.316 documentation retention. | §164.316(b)(2)(i) |

---

## 14. Deployment Notes

### Retention

**HIPAA Security Rule does not specify an audit-log retention period.** §164.316(b)(2)(i) requires that documentation of policies and procedures be retained for **6 years from the date of creation or the date when it last was in effect, whichever is later**. Audit logs supporting §164.312(b) are commonly retained for the same 6 years by industry practice, since they may be needed to prove policies were in effect.

**Recommended retention strategy:**

| Tier | Mechanism | Period |
|---|---|---|
| Hot | Insight | 90 days (default) — sufficient for active investigation and §164.308(a)(1)(ii)(D) review |
| Cold | S3/GCS output with object-lifecycle policy | 6 years — aligns with §164.316(b)(2)(i) |
| Case records | ext-cases | 6 years — incident documentation is part of §164.308(a)(6)(ii) response record |
| Breach records | Separate bucket with legal hold | Until breach-notification cycle closes + 6 years |

All artifact collection rules in this document use `days_retention: 90`. Tune per your retention policy and regulatory interpretation.

### Tagging Strategy

All D&R rules use the `hipaa` tag, enabling:

- Filtering detections by compliance source in the Cases UI
- Routing HIPAA-specific detections to a dedicated output (e.g., a bucket subject to legal hold)
- Tracking HIPAA rule coverage separately from operational detections

Additionally, tag ePHI-bearing sensors with `hipaa-ephi-host` so that breach-notification rules (Section 12) scope correctly.

### Suppression Tuning

Many rules include starting-point suppression. Tune after deployment:

1. Run for a 7-day burn-in period
2. Use `/lc-essentials:fp-pattern-finder` to identify systematic noise
3. Author FP rules for known-safe patterns (service accounts, approved admin tools, scheduled backup jobs)

### Windows Audit Policy Prerequisites

Windows endpoints need the **Advanced Audit Policy** configured — `wel://Security:*` collection alone is not enough if the events are not being generated by the OS.

| Audit Category | Subcategory | Setting | HIPAA |
|---|---|---|---|
| Account Logon | Credential Validation | Success, Failure | §164.312(d) |
| Account Management | User Account Management | Success, Failure | §164.308(a)(3)(ii)(C) |
| Account Management | Security Group Management | Success, Failure | §164.312(a)(1) |
| Detailed Tracking | Process Creation | Success | §164.312(b) |
| Logon/Logoff | Logon | Success, Failure | §164.312(b), §164.308(a)(5)(ii)(C) |
| Logon/Logoff | Logoff | Success | §164.312(a)(2)(iii) |
| Object Access | File System | Success, Failure | §164.312(b), §164.312(c) |
| Policy Change | Audit Policy Change | Success, Failure | §164.312(b) |
| Privilege Use | Sensitive Privilege Use | Success, Failure | §164.312(a)(1) |
| System | Security State Change | Success | §164.312(b) |
| System | System Integrity | Success, Failure | §164.312(c)(1) |

Deploy via Group Policy: `Computer Configuration → Windows Settings → Security Settings → Advanced Audit Policy Configuration`.

### Linux Audit Policy Prerequisites

Deploy the auditd rules from Section 3 via Ansible/Puppet/Chef. Verify with `auditctl -l`. Ensure `/var/log/audit/audit.log` rotation is configured to retain at minimum the Insight retention window (default 90 days); align with the 6-year §164.316 retention via the file-adapter or artifact-collection stream plus S3/GCS cold archival.

### macOS Audit Policy Prerequisites

macOS Unified Log retention is managed via `log config` policies. Default retention is often shorter than 90 days — validate on a sample endpoint with `log stats --overview`. Adjust predicate patterns (Section 2) to balance visibility with volume.

### ePHI Path Customization

The FIM rules in Section 4 (`hipaa-fim-windows-ephi`, `hipaa-fim-linux-ephi`, `hipaa-fim-macos-ephi`) and D&R rules in Sections 9 and 11 (`hipaa-312-c-ephi-touched-by-lolbin-windows`, `hipaa-312-c-ephi-file-modified-macos`, `hipaa-312-e-ephi-staging-windows`) use placeholder paths and regexes (`ephi`, `phi`, `patient`, `medical`). Before deploying:

1. Identify the actual paths where ePHI is stored on each platform (EMR data directories, HL7 message stores, DICOM archives, backup volumes, temporary export directories)
2. Replace the placeholder patterns with site-specific paths
3. Re-validate with `limacharlie dr validate` after each path change — regex changes can silently break a rule

### Terminated-User Lookup Maintenance

The `hipaa-308-a-3-terminated-user-activity-*` rules depend on a `hive://lookup/hipaa-terminated-users` lookup. Keep this lookup current with one of:

- **Playbook** that queries Okta / Entra ID / Google Workspace daily and syncs the terminated list
- **Webhook adapter** from the HRIS (Workday, BambooHR, etc.) on termination events
- **Manual update** via `limacharlie hive set --name <user> --hive-name lookup` — fragile; only for small orgs

### Deployment Order

1. Enable **Reliable Tasking**, **Artifact Collection**, **Exfil Control**, **Integrity** extensions
2. Deploy Windows WEL artifact collection rules (Section 1)
3. Deploy macOS MUL artifact collection rules (Section 2)
4. Deploy Linux auditd rules + file adapter or artifact rules (Section 3)
5. Deploy FIM rules per platform — customize ePHI paths (Section 4)
6. Deploy exfil event rules per platform (Section 5)
7. Create the `hipaa-terminated-users` lookup; populate from HR / IdP
8. Create the `hipaa-bad-domains` lookup (optional) from threat-intel feed
9. Deploy D&R rules (Sections 6–12) — detections begin firing
10. Tag ePHI-bearing sensors with `hipaa-ephi-host`
11. Enable **Cases (ext-cases)** — configure ingestion to auto-create cases for `hipaa-incident` + `hipaa-ephi-host` (Section 12)
12. Subscribe to **Soteria** and/or **Sigma** — adds managed detection coverage
13. Configure **S3/GCS output** with a 6-year object-lifecycle policy for §164.316(b)(2)(i)
14. Burn-in for 7 days, then tune via FP pattern finder

### Validation

Every YAML rule in this document passes `limacharlie dr validate`. For end-to-end validation against historical telemetry, use `limacharlie dr replay` against recent data from representative endpoints (one Windows, one Linux, one macOS ePHI host).

### Risk Analysis Alignment

HIPAA §164.308(a)(1)(ii)(A) requires an **accurate and thorough assessment of the potential risks and vulnerabilities to the confidentiality, integrity, and availability of ePHI**. The detections in this document are *evidence-generating controls* — they should be referenced in the risk-analysis document as the mechanism that converts identified risks (unauthorized access, data tampering, malware, exfiltration) into reviewable, timestamped findings. Tie each detection in this document to an entry in the risk register so auditors can trace risk → control → evidence.
