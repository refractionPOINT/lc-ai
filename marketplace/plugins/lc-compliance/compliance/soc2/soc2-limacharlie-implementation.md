# SOC 2 Compliance Implementation Guide — LimaCharlie

Concrete D&R rules, artifact collection rules, FIM rules, exfil rules, and extension recommendations to satisfy the AICPA Trust Services Criteria (2017, with the 2022 points-of-focus refresh) using LimaCharlie EDR on Windows, Linux, and macOS endpoints.

Companion to [soc2-limacharlie-mapping.md](soc2-limacharlie-mapping.md), which maps criteria to LC capabilities conceptually. This document provides the deployable configuration.

All D&R rule YAML in this document has been validated against `limacharlie dr validate`. Event-to-platform coverage reflects actual sensor capability (per the LC EDR events reference), not documentation aspirations.

---

## Table of Contents

1. [Windows Event Log Artifact Collection Rules](#1-windows-event-log-artifact-collection-rules)
2. [macOS Unified Log Artifact Collection Rules](#2-macos-unified-log-artifact-collection-rules)
3. [Linux Audit Log Collection](#3-linux-audit-log-collection)
4. [File Integrity Monitoring (FIM) Rules](#4-file-integrity-monitoring-fim-rules)
5. [Exfil Event Collection Rules](#5-exfil-event-collection-rules)
6. [D&R Rules — CC6: Logical and Physical Access Controls](#6-dr-rules--cc6-logical-and-physical-access-controls)
7. [D&R Rules — CC7: System Operations](#7-dr-rules--cc7-system-operations)
8. [D&R Rules — CC8: Change Management](#8-dr-rules--cc8-change-management)
9. [D&R Rules — CC9: Risk Mitigation](#9-dr-rules--cc9-risk-mitigation)
10. [D&R Rules — Availability (A1)](#10-dr-rules--availability-a1)
11. [D&R Rules — Confidentiality (C1)](#11-dr-rules--confidentiality-c1)
12. [Outputs for Long-Term Evidence Retention](#12-outputs-for-long-term-evidence-retention)
13. [Recommended Extensions](#13-recommended-extensions)
14. [Deployment Notes](#14-deployment-notes)

---

## 1. Windows Event Log Artifact Collection Rules

The `wel://` pattern streams Windows Event Logs as first-class `WEL` telemetry — preferred over `.evtx` file collection because events are evaluated by D&R rules in real time.

> **Prerequisite:** The **Reliable Tasking** and **Artifact Collection** extensions must be enabled.

Rule map entries are added to `ext-artifact` configuration (web UI Artifact Collection section, `limacharlie extension config-set --name ext-artifact`, or ext-git-sync).

> **SOC 2 retention note:** The `days_retention: 90` setting aligns with LC Insight's hot-retention window. For a 12-month Type II observation period, pair these artifact rules with the S3/GCS outputs in [Section 12](#12-outputs-for-long-term-evidence-retention) so that auditor evidence requests are serviceable across the full window.

### Security Log

```yaml
soc2-wel-security:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Security:*"
```

**Key Event IDs produced:**

| Event ID | Category | SOC 2 Criterion |
|---|---|---|
| 4624 | Successful logon | CC6.1 |
| 4625 | Failed logon | CC6.1 |
| 4634 | Logoff | CC6.1 |
| 4647 | User-initiated logoff | CC6.1 |
| 4648 | Logon with explicit credentials | CC6.1, CC6.3 |
| 4672 | Special privileges assigned to new logon | CC6.1, CC6.3 |
| 4673 | Privileged service called | CC6.3 |
| 4674 | Operation attempted on privileged object | CC6.3 |
| 4688 | Process creation (if audit enabled) | CC7.2 |
| 4689 | Process termination | CC7.2 |
| 4697 | Service installed on the system | CC7.1, CC8.1 |
| 4698 | Scheduled task created | CC7.1 |
| 4699 | Scheduled task deleted | CC7.1 |
| 4700 | Scheduled task enabled | CC7.1 |
| 4701 | Scheduled task disabled | CC7.1 |
| 4719 | Audit policy changed | CC7.1, CC8.1 |
| 4720 | User account created | CC6.2 |
| 4722 | User account enabled | CC6.2 |
| 4723 | Password change attempted | CC6.1 |
| 4724 | Password reset attempted | CC6.1 |
| 4725 | User account disabled | CC6.2 |
| 4726 | User account deleted | CC6.2 |
| 4728 | Member added to security-enabled global group | CC6.2, CC6.3 |
| 4732 | Member added to security-enabled local group | CC6.2, CC6.3 |
| 4735 | Security-enabled local group changed | CC6.3 |
| 4738 | User account changed | CC6.2 |
| 4740 | User account locked out | CC6.1 |
| 4756 | Member added to universal security group | CC6.2, CC6.3 |
| 4767 | User account unlocked | CC6.2 |
| 4776 | Credential validation (NTLM) | CC6.1 |
| 4946 | Firewall rule added | CC6.6, CC8.1 |
| 4947 | Firewall rule modified | CC6.6, CC8.1 |
| 4948 | Firewall rule deleted | CC6.6, CC8.1 |
| 4950 | Firewall setting changed | CC6.6, CC8.1 |
| 1102 | Security log cleared | CC7.1 (tampering) |

### System Log

```yaml
soc2-wel-system:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://System:*"
```

**Key Event IDs:** 7034 (service crash), 7036 (service start/stop), 7040 (service start type changed), 7045 (new service installed), 1074 (shutdown/restart), 6005/6006 (event log service start/stop).

### PowerShell Operational Log

```yaml
soc2-wel-powershell:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-PowerShell/Operational:*"
```

**Key Event IDs:** 4103 (module logging), 4104 (script block logging), 4105/4106 (script start/stop).

> If Sysmon is deployed, add `"wel://Microsoft-Windows-Sysmon/Operational:*"` as a pattern to enrich CC7.2 coverage.

### Windows Defender Operational Log

```yaml
soc2-wel-defender:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Defender/Operational:*"
```

**Key Event IDs:** 1006/1007 (malware action), 1116/1117 (threat detected/action taken), 2001/2003/2006 (definition update), 5001 (real-time protection disabled).

### Additional Channels

Use the same pattern structure for these additional channels as needed for your scope:

```yaml
soc2-wel-additional:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-TaskScheduler/Operational:*"
    - "wel://Microsoft-Windows-Windows Firewall With Advanced Security/Firewall:*"
    - "wel://Microsoft-Windows-Backup:*"
    - "wel://Application:*"
```

Covers CC7.2 (task scheduler, backup service health) and CC6.6 / CC8.1 (firewall audit trail).

---

## 2. macOS Unified Log Artifact Collection Rules

The `mul://` pattern streams macOS Unified Log entries as real-time `MUL` telemetry. Predicates use standard macOS unified-log predicate syntax.

> **Prerequisite:** `MUL` must be enabled in the Exfil Control rules for macOS (see Section 5).

> **Field path verification:** D&R rules in later sections that match `MUL` events use field paths based on macOS `log` command keys (`eventMessage`, `processImagePath`, `subsystem`). Verify the exact field paths against your first few `MUL` events in Timeline after deployment — the sensor may flatten or re-key some fields. Adjust `path:` values accordingly.

### Authentication & Authorization

```yaml
soc2-mul-auth:
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

Covers: CC6.1 (authentication), CC6.2 (identity lifecycle via `dscl`/`passwd`).

### Login & Session Events

```yaml
soc2-mul-sessions:
  days_retention: 90
  filters:
    platforms:
      - macos
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.loginwindow"'
    - 'mul://process == "loginwindow"'
```

Complements native `USER_LOGIN` / `SSH_LOGIN` events for CC6.1.

### System Configuration & Launch Services

```yaml
soc2-mul-system:
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

Covers: CC7.1, CC8.1 (launch agent / daemon changes).

### Privilege Escalation

```yaml
soc2-mul-privilege:
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

Covers: CC6.3 (privileged function use).

---

## 3. Linux Audit Log Collection

The LC Linux EDR sensor does **not** emit `USER_LOGIN` / `SSH_LOGIN` events. Linux authentication telemetry (required for CC6.1) requires one of the three approaches below.

### Option A — Artifact Collection (Retention Only)

Use when compliance requires **retention** of the raw auth log but real-time detection is not needed. Artifacts are retrievable from the Artifacts UI but are not streamed to the Timeline.

```yaml
soc2-artifact-authlog:
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

### Option B — File Adapter (Real-Time Streaming)

Deploy a LimaCharlie Adapter binary on each Linux endpoint (separate from the EDR sensor). Events arrive as the `text` platform — D&R rules match on `event/raw` with regex patterns.

```yaml
# /etc/lc/authlog.yaml
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

Run: `./lc_adapter file /etc/lc/authlog.yaml` and persist via systemd unit.

### Option C — Auditd Rules (Recommended for SOC 2 Environments Holding Regulated Data)

Deploy auditd rules on Linux endpoints via configuration management, then collect `/var/log/audit/audit.log` via file adapter or artifact collection using the same approach as Options A/B.

Minimum auditd rules for SOC 2 Common Criteria coverage:

```
# /etc/audit/rules.d/soc2.rules
# Identity changes (CC6.2, CC6.3)
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k identity
-w /etc/sudoers.d/ -p wa -k identity

# Authentication config (CC6.1)
-w /etc/pam.d/ -p wa -k auth-config
-w /etc/ssh/sshd_config -p wa -k sshd-config

# Privilege escalation (CC6.3)
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation
-a always,exit -F arch=b32 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation

# Time changes (CC7.1)
-a always,exit -F arch=b64 -S settimeofday,clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Audit subsystem integrity (CC7.1)
-w /etc/audit/ -p wa -k audit-config
-w /etc/libaudit.conf -p wa -k audit-config
-e 2
```

Deploy via Ansible, Puppet, or similar; verify with `auditctl -l`.

---

## 4. File Integrity Monitoring (FIM) Rules

FIM generates `FIM_HIT` events on monitored files, directories, and Windows registry keys across all three platforms. Directly supports CC7.1 (detection of unauthorized changes) and CC8.1 (change management evidence).

> Linux FIM works with `inotify` (active monitoring) or eBPF (on supported kernels). Windows and macOS use passive kernel monitoring.

### Windows

```yaml
soc2-fim-windows-system:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\drivers\etc\hosts
    - ?:\Windows\System32\config\SAM
    - ?:\Windows\System32\config\SYSTEM
    - ?:\Windows\System32\config\SECURITY

soc2-fim-windows-boot:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\boot\bcd
    - ?:\Windows\System32\boot\winload.exe

soc2-fim-windows-grouppolicy:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\GroupPolicy\*
    - ?:\Windows\SYSVOL\*

soc2-fim-windows-powershell-profiles:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    - ?:\Users\*\Documents\WindowsPowerShell\profile.ps1

soc2-fim-windows-registry-persistence:
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
```

### Linux

```yaml
soc2-fim-linux-identity:
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

soc2-fim-linux-auth:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/pam.d/*
    - /etc/ssh/sshd_config
    - /etc/ssh/ssh_config
    - /etc/security/*

soc2-fim-linux-ssh-keys:
  filters:
    platforms:
      - linux
  patterns:
    - /root/.ssh/authorized_keys
    - /root/.ssh/*
    - /home/*/.ssh/*

soc2-fim-linux-persistence:
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

soc2-fim-linux-boot:
  filters:
    platforms:
      - linux
  patterns:
    - /boot/grub/grub.cfg
    - /boot/grub2/grub.cfg
    - /etc/default/grub
    - /etc/fstab

soc2-fim-linux-audit:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/audit/*
    - /etc/libaudit.conf
```

### macOS

```yaml
soc2-fim-macos-identity:
  filters:
    platforms:
      - macos
  patterns:
    - /etc/sudoers
    - /etc/sudoers.d/*
    - /etc/pam.d/*

soc2-fim-macos-ssh-keys:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/.ssh/*
    - /var/root/.ssh/*

soc2-fim-macos-launch-daemons:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/LaunchDaemons/*
    - /Library/LaunchAgents/*
    - /System/Library/LaunchDaemons/*
    - /System/Library/LaunchAgents/*
    - /Users/*/Library/LaunchAgents/*

soc2-fim-macos-keychains:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/Library/Keychains/*
    - /Library/Keychains/*

soc2-fim-macos-boot:
  filters:
    platforms:
      - macos
  patterns:
    - /System/Library/CoreServices/boot.efi
    - /Library/Preferences/SystemConfiguration/*

soc2-fim-macos-kernel-extensions:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/Extensions/*
    - /System/Library/Extensions/*
```

### Confidential-Data FIM (C1.1)

If C1 is in scope, add one FIM rule per platform pointing at your confidential-data paths. Example patterns (replace `AppName` with your in-scope application path):

- Windows: `?:\ProgramData\AppName\exports\*`, `?:\Users\*\AppData\Local\AppName\secrets\*`
- Linux: `/var/lib/appname/exports/*`, `/etc/appname/secrets.d/*`
- macOS: `/Library/Application Support/AppName/exports/*`, `/Users/*/Library/Application Support/AppName/secrets/*`

Use the same `soc2-fim-<platform>-<name>` rule structure as the preceding rules in this section.

---

## 5. Exfil Event Collection Rules

Additive to default exfil rules — ensures required event types stream to the cloud even if defaults change.

### Windows

```yaml
soc2-windows-events:
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
    - VOLUME_MOUNT
    - VOLUME_UNMOUNT
    - NETWORK_CONNECTIONS
  filters:
    platforms:
      - windows
```

### Linux

```yaml
soc2-linux-events:
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
soc2-macos-events:
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
    - VOLUME_MOUNT
    - VOLUME_UNMOUNT
    - NETWORK_CONNECTIONS
  filters:
    platforms:
      - macos
```

---

## 6. D&R Rules — CC6: Logical and Physical Access Controls

### CC6.1 — Logical Access Security Measures

#### Windows — Failed Logon Detection

```yaml
name: soc2-cc6-1-failed-logon-windows
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
    name: soc2-cc6-1-failed-logon-windows
    priority: 3
    metadata:
      soc2_criterion: 'CC6.1'
      description: Failed Windows logon attempt
      mitre_attack_id: T1078
      mitre_tactic: initial-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-1-failed-logon-windows
tags:
  - soc2
  - logical-access
comment: 'CC6.1 — Failed Windows logon (Event ID 4625)'
```

#### Windows — Brute Force Detection

```yaml
name: soc2-cc6-1-brute-force-windows
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
    name: soc2-cc6-1-brute-force-windows
    priority: 4
    metadata:
      soc2_criterion: 'CC6.1'
      description: Possible brute force — 10+ failed logons within 10 min
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      min_count: 10
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-1-brute-force-windows
tags:
  - soc2
  - logical-access
comment: 'CC6.1 — Threshold-based brute force on Windows'
```

> Successful interactive logons (Event ID 4624 with LogonType 2/10/11) are captured by the `soc2-wel-security` artifact rule (Section 1). Auditors typically request these via LCQL queries or Insight export rather than per-event detections.

#### macOS — Failed Authentication via Unified Log

The native `SSH_LOGIN` event fires only on successful login and has no failure field. Failed SSH / authentication attempts on macOS must be collected from the Unified Log. Deploy the `soc2-mul-auth` artifact rule (Section 2), then match the MUL stream:

```yaml
name: soc2-cc6-1-auth-failed-macos
detect:
  event: MUL
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/eventMessage
      re: '(?i)(authentication failure|failed password|failed to authenticate)'
respond:
  - action: report
    name: soc2-cc6-1-auth-failed-macos
    priority: 3
    metadata:
      soc2_criterion: 'CC6.1'
      description: Authentication failure logged to macOS Unified Log
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-1-auth-failed-macos
tags:
  - soc2
  - logical-access
comment: 'CC6.1 — macOS authentication failures from Unified Log. Requires soc2-mul-auth (Section 2).'
```

#### macOS — Successful SSH Login

```yaml
name: soc2-cc6-1-ssh-login-macos
detect:
  event: SSH_LOGIN
  op: is mac
respond:
  - action: report
    name: soc2-cc6-1-ssh-login-macos
    priority: 2
    metadata:
      soc2_criterion: 'CC6.1, CC6.6'
      description: macOS SSH session established — remote access event
      mitre_attack_id: T1021.004
      mitre_tactic: lateral-movement
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-1-ssh-login-macos
tags:
  - soc2
  - logical-access
comment: 'CC6.1 / CC6.6 — macOS SSH login (success only — see mapping doc)'
```

#### Linux — Failed SSH via Process Context

LC Linux sensor does not emit `SSH_LOGIN`. Detection of failed auth on Linux relies on (a) auditd integration via the file adapter or (b) scanning `NEW_PROCESS` for `sshd` child `exec`s. If auditd is collected via adapter (Section 3), author rules on the adapter event stream matching `type=USER_AUTH` records.

### CC6.2 / CC6.3 — Identity Lifecycle and Least Privilege

#### Windows — User Account Created

```yaml
name: soc2-cc6-2-user-created-windows
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
    name: soc2-cc6-2-user-created-windows
    priority: 3
    metadata:
      soc2_criterion: 'CC6.2'
      description: New Windows user account created
      mitre_attack_id: T1136.001
      mitre_tactic: persistence
tags:
  - soc2
  - logical-access
comment: 'CC6.2 — Windows local user creation (Event ID 4720)'
```

#### Windows — User Added to Privileged Group

```yaml
name: soc2-cc6-3-user-added-to-group-windows
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
    name: soc2-cc6-3-user-added-to-group-windows
    priority: 4
    metadata:
      soc2_criterion: 'CC6.2, CC6.3'
      description: User added to a Windows security-enabled group
      mitre_attack_id: T1098
      mitre_tactic: persistence
tags:
  - soc2
  - logical-access
comment: 'CC6.3 — Windows group membership addition (4728, 4732, 4756)'
```

> Windows Event ID 4726 (account deleted), 4725 (disabled), 4722 (enabled), 4738 (changed), 4767 (unlocked) are all captured by `soc2-wel-security` (Section 1). Pattern-match rules for them follow the same structure as `soc2-cc6-2-user-created-windows` — add as needed for your control catalogue.

#### Linux — Account Management Binary Execution

```yaml
name: soc2-cc6-2-user-mgmt-linux
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
    name: soc2-cc6-2-user-mgmt-linux
    priority: 3
    metadata:
      soc2_criterion: 'CC6.2'
      description: Linux account management binary executed
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - soc2
  - logical-access
comment: 'CC6.2 — Linux user/group management (useradd, usermod, groupadd, ...)'
```

#### macOS — Account Management via dscl

```yaml
name: soc2-cc6-2-user-mgmt-macos
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
    name: soc2-cc6-2-user-mgmt-macos
    priority: 3
    metadata:
      soc2_criterion: 'CC6.2'
      description: macOS account management invocation (dscl / sysadminctl)
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - soc2
  - logical-access
comment: 'CC6.2 — macOS account management via dscl, sysadminctl, dsimport'
```

#### Windows — Special Privileges Assigned

```yaml
name: soc2-cc6-3-special-privilege-logon
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
    name: soc2-cc6-3-special-privilege-logon
    priority: 2
    metadata:
      soc2_criterion: 'CC6.3'
      description: Special privileges assigned to new logon session
      mitre_attack_id: T1078
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-3-special-privilege-logon
tags:
  - soc2
  - logical-access
comment: 'CC6.3 — Windows special privilege assignment (Event ID 4672)'
```

#### Windows — Privileged Service Called

```yaml
name: soc2-cc6-3-privileged-service-windows
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
    name: soc2-cc6-3-privileged-service-windows
    priority: 3
    metadata:
      soc2_criterion: 'CC6.3'
      description: Privileged service or object operation
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-3-privileged-service-windows
tags:
  - soc2
  - logical-access
comment: 'CC6.3 — Windows privileged service call (4673, 4674)'
```

#### Linux — sudo / su / pkexec

```yaml
name: soc2-cc6-3-privilege-escalation-linux
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
    name: soc2-cc6-3-privilege-escalation-linux
    priority: 2
    metadata:
      soc2_criterion: 'CC6.3'
      description: Linux privilege-escalation command executed
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
  - soc2
  - logical-access
comment: 'CC6.3 — Linux sudo/su/pkexec/doas. Suppressed per-user per-hour.'
```

#### macOS — sudo Execution

```yaml
name: soc2-cc6-3-sudo-macos
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
    name: soc2-cc6-3-sudo-macos
    priority: 2
    metadata:
      soc2_criterion: 'CC6.3'
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
  - soc2
  - logical-access
comment: 'CC6.3 — macOS sudo execution'
```

> Windows Event IDs 4740 (account lockout), 4723 (password change), and 4724 (password reset) are captured by `soc2-wel-security` and surface in LCQL queries. Dedicated D&R rules are only needed if you want immediate output notification — follow the same pattern as `soc2-cc6-2-user-created-windows`.

#### Linux — Password Change Utilities

```yaml
name: soc2-cc6-1-password-change-linux
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
    name: soc2-cc6-1-password-change-linux
    priority: 2
    metadata:
      soc2_criterion: 'CC6.1'
      description: Linux password management utility executed
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - soc2
  - logical-access
comment: 'CC6.1 — Linux passwd/chage/chpasswd'
```

### CC6.6 — Protection Against External-Boundary Threats

#### Windows — RDP Logon

```yaml
name: soc2-cc6-6-rdp-logon
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
    name: soc2-cc6-6-rdp-logon
    priority: 2
    metadata:
      soc2_criterion: 'CC6.6, CC6.1'
      description: Remote Desktop logon (LogonType 10)
      mitre_attack_id: T1021.001
      mitre_tactic: lateral-movement
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-6-rdp-logon
tags:
  - soc2
  - logical-access
comment: 'CC6.6 — Windows RDP logon'
```

### CC6.7 — Restriction of Transmission, Movement, and Removal

#### Windows / macOS — Removable Media Mount

```yaml
name: soc2-cc6-7-removable-media-mount
detect:
  event: VOLUME_MOUNT
  op: or
  rules:
    - op: is windows
    - op: is mac
respond:
  - action: report
    name: soc2-cc6-7-removable-media-mount
    priority: 2
    metadata:
      soc2_criterion: 'CC6.7'
      description: Removable media / volume mounted
      mitre_attack_id: T1052
      mitre_tactic: exfiltration
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-7-removable-media-mount
tags:
  - soc2
  - data-movement
comment: 'CC6.7 — Removable media mount tracking (Windows + macOS). Linux does not emit VOLUME_MOUNT — use FIM on /media/* for equivalent signal.'
```

#### All Platforms — Suspicious Outbound Connection

```yaml
name: soc2-cc6-7-suspicious-outbound
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
    name: soc2-cc6-7-suspicious-outbound
    priority: 3
    metadata:
      soc2_criterion: 'CC6.7, CC7.2'
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
  - soc2
  - data-movement
comment: 'CC6.7 / CC7.2 — Outbound from scripting/LOLBin processes'
```

> DNS-tunneling / data-channel indicators are best handled by the Soteria or Sigma managed rule packs — they maintain high-quality DNS anomaly detections. A naive long-label rule produces heavy false positives against modern CDN hostnames. Subscribe to one of those rule packs if CC6.7 DNS-exfil coverage is in scope.

### CC6.8 — Prevention or Detection of Unauthorized/Malicious Software

#### YARA Detection (All Platforms)

```yaml
name: soc2-cc6-8-yara-detection
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: soc2-cc6-8-yara-detection
    priority: 5
    metadata:
      soc2_criterion: 'CC6.8, CC7.2'
      description: YARA rule match — possible malware
      mitre_tactic: execution
tags:
  - soc2
  - malware
comment: 'CC6.8 — All YARA detections on any platform'
```

#### Windows Defender — Threat Detected and RTP Disabled

Two key Defender events — threat detection (1116/1117) and real-time protection disabled (5001). Kept as one D&R rule with branched priority:

```yaml
name: soc2-cc6-8-defender-events
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
        - op: is
          path: event/EVENT/System/EventID
          value: '5001'
respond:
  - action: report
    name: soc2-cc6-8-defender-events
    priority: 5
    metadata:
      soc2_criterion: 'CC6.8, CC7.1'
      description: Windows Defender threat detection (1116/1117) or RTP disable (5001)
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - soc2
  - malware
comment: 'CC6.8 / CC7.1 — Defender threat + RTP disable events'
```

#### Windows — LOLBin Abuse with Network Indicators

```yaml
name: soc2-cc6-8-lolbin-execution-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(mshta|regsvr32|rundll32|certutil|bitsadmin|msiexec|wmic|cmstp)\.exe$'
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)(http|ftp|\\\\)'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)(downloadstring|downloadfile|invoke-expression|iex|invoke-webrequest)'
respond:
  - action: report
    name: soc2-cc6-8-lolbin-execution-windows
    priority: 4
    metadata:
      soc2_criterion: 'CC6.8, CC7.2'
      description: Suspicious LOLBin execution with network or download indicators
      mitre_attack_id: T1218
      mitre_tactic: defense-evasion
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.FILE_PATH }}'
tags:
  - soc2
  - malware
comment: 'CC6.8 / CC7.2 — Windows LOLBin abuse'
```

#### Windows — Encoded PowerShell

```yaml
name: soc2-cc6-8-encoded-powershell
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(powershell(\.exe|_ise\.exe)|pwsh\.exe)$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\s+-(e|en|enc|enco|encod|encode|encoded|encodedc|encodedco|encodedcom|encodedcomm|encodedcomma|encodedcomman|encodedcommand)\s+'
respond:
  - action: report
    name: soc2-cc6-8-encoded-powershell
    priority: 4
    metadata:
      soc2_criterion: 'CC6.8, CC7.2'
      description: PowerShell executed with encoded command — common obfuscation
      mitre_attack_id: T1059.001
      mitre_tactic: execution
tags:
  - soc2
  - malware
comment: 'CC6.8 — Encoded PowerShell on Windows'
```

#### Linux — LOLBin with Download-and-Execute

```yaml
name: soc2-cc6-8-lolbin-execution-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(curl|wget|nc|ncat|socat|python|python3|perl|ruby|php|bash|sh)$'
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)curl\s+.*\|\s*(bash|sh|python)'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)wget\s+.*-O-\s+.*\|\s*(bash|sh)'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)(bash|sh)\s+-c\s+.*base64\s+-d\s+\|\s*(bash|sh)'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)(python[23]?|perl)\s+-c\s+.*(urlopen|socket|exec|eval)'
respond:
  - action: report
    name: soc2-cc6-8-lolbin-execution-linux
    priority: 4
    metadata:
      soc2_criterion: 'CC6.8, CC7.2'
      description: Linux LOLBin with download-and-execute pattern
      mitre_attack_id: T1059.004
      mitre_tactic: execution
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc6-8-lolbin-execution-linux
tags:
  - soc2
  - malware
comment: 'CC6.8 / CC7.2 — Linux download-and-execute patterns'
```

#### macOS — osascript Network Activity

```yaml
name: soc2-cc6-8-osascript-network-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/usr/bin/osascript$'
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)do\s+shell\s+script'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)(curl|wget)\s+'
respond:
  - action: report
    name: soc2-cc6-8-osascript-network-macos
    priority: 4
    metadata:
      soc2_criterion: 'CC6.8, CC7.2'
      description: macOS osascript invoking shell / network
      mitre_attack_id: T1059.002
      mitre_tactic: execution
tags:
  - soc2
  - malware
comment: 'CC6.8 / CC7.2 — macOS osascript shell-out'
```

#### All Platforms — Unsigned Binary in System Path

```yaml
name: soc2-cc6-8-unsigned-binary
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
    name: soc2-cc6-8-unsigned-binary
    priority: 3
    metadata:
      soc2_criterion: 'CC6.8, CC7.1'
      description: Unsigned binary loaded from a system path
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
  - soc2
  - malware
comment: 'CC6.8 — Unsigned binary in trusted system path (Win/macOS)'
```

---

## 7. D&R Rules — CC7: System Operations

### CC7.1 — Detection of Unauthorized Changes

#### FIM Hit (All Platforms)

```yaml
name: soc2-cc7-1-fim-hit
detect:
  event: FIM_HIT
  op: exists
  path: event/FILE_PATH
respond:
  - action: report
    name: soc2-cc7-1-fim-hit
    priority: 3
    metadata:
      soc2_criterion: 'CC7.1, CC8.1'
      description: File integrity change on monitored path
      mitre_attack_id: T1565
      mitre_tactic: impact
tags:
  - soc2
  - change-detection
comment: 'CC7.1 — FIM hit across all platforms'
```

#### Windows — Audit Policy Changed

```yaml
name: soc2-cc7-1-audit-policy-changed
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
    name: soc2-cc7-1-audit-policy-changed
    priority: 5
    metadata:
      soc2_criterion: 'CC7.1, CC8.1'
      description: Audit policy changed — potential tampering with logging
      mitre_attack_id: T1562.002
      mitre_tactic: defense-evasion
tags:
  - soc2
  - change-detection
comment: 'CC7.1 — Windows audit policy change (Event ID 4719)'
```

#### Windows — Security Event Log Cleared

```yaml
name: soc2-cc7-1-event-log-cleared
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
    name: soc2-cc7-1-event-log-cleared
    priority: 5
    metadata:
      soc2_criterion: 'CC7.1'
      description: Security event log was cleared — strong tampering indicator
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: soc2-audit-tamper
    ttl: 86400
tags:
  - soc2
  - change-detection
comment: 'CC7.1 — Security log clearing (Event ID 1102)'
```

#### Windows — Event Log Service Tampering

```yaml
name: soc2-cc7-1-eventlog-service-stop-windows
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
    name: soc2-cc7-1-eventlog-service-stop-windows
    priority: 5
    metadata:
      soc2_criterion: 'CC7.1'
      description: Attempt to stop event log service or clear event logs
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: soc2-audit-tamper
    ttl: 86400
tags:
  - soc2
  - change-detection
comment: 'CC7.1 — Attempt to tamper with Windows event logging'
```

#### Linux — Auditd Tampering

```yaml
name: soc2-cc7-1-auditd-tamper-linux
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
    name: soc2-cc7-1-auditd-tamper-linux
    priority: 5
    metadata:
      soc2_criterion: 'CC7.1'
      description: Attempt to stop or disable Linux auditd
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: soc2-audit-tamper
    ttl: 86400
tags:
  - soc2
  - change-detection
comment: 'CC7.1 — Linux auditd service tampering'
```

#### macOS — Unified Log Tampering

```yaml
name: soc2-cc7-1-log-tamper-macos
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
    name: soc2-cc7-1-log-tamper-macos
    priority: 5
    metadata:
      soc2_criterion: 'CC7.1'
      description: Attempt to erase or disable macOS unified log
      mitre_attack_id: T1070
      mitre_tactic: defense-evasion
  - action: add tag
    tag: soc2-audit-tamper
    ttl: 86400
tags:
  - soc2
  - change-detection
comment: 'CC7.1 — macOS log erase / disable'
```

### CC7.2 — System Component Monitoring for Anomalies

#### Windows — LSASS Access

```yaml
name: soc2-cc7-2-lsass-access
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
    name: soc2-cc7-2-lsass-access
    priority: 5
    metadata:
      soc2_criterion: 'CC7.2, C1.1'
      description: Sensitive handle to LSASS — possible credential dumping
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc7-2-lsass-access
tags:
  - soc2
  - monitoring
  - credential-access
comment: 'CC7.2 / C1.1 — LSASS access (credential dumping)'
```

#### Windows — Suspicious Named Pipe

```yaml
name: soc2-cc7-2-suspicious-named-pipe
detect:
  event: NEW_NAMED_PIPE
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(msagent_|MSSE-|postex_|status_|mypipe-f|mypipe-h|ntsvcs_|scerpc_|DserNamePipe|srvsvc_|wkssvc_|isapi_)'
respond:
  - action: report
    name: soc2-cc7-2-suspicious-named-pipe
    priority: 4
    metadata:
      soc2_criterion: 'CC7.2'
      description: Known malicious named pipe pattern — possible C2
      mitre_attack_id: T1570
      mitre_tactic: lateral-movement
tags:
  - soc2
  - monitoring
comment: 'CC7.2 — Known-bad named pipe patterns'
```

#### Windows — Thread Injection

```yaml
name: soc2-cc7-2-thread-injection
detect:
  event: THREAD_INJECTION
  op: is windows
respond:
  - action: report
    name: soc2-cc7-2-thread-injection
    priority: 4
    metadata:
      soc2_criterion: 'CC7.2'
      description: Thread injection — process injecting code into another
      mitre_attack_id: T1055
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc7-2-thread-injection
tags:
  - soc2
  - monitoring
comment: 'CC7.2 — Thread injection detection'
```

> Windows new-service installation (Event 7045, System channel) and scheduled-task creation (Event 4698, Security channel) are captured by the Section 1 artifact rules. The native `SERVICE_CHANGE` event also covers service additions on all three platforms — see `soc2-cc8-1-service-change` in Section 8. Add channel-specific D&R rules only if you need a distinct tag or priority.

#### Linux — Cron / Systemd Persistence

```yaml
name: soc2-cc7-2-cron-modification-linux
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
    name: soc2-cc7-2-cron-modification-linux
    priority: 3
    metadata:
      soc2_criterion: 'CC7.2, CC8.1'
      description: Linux persistence mechanism modification (cron, systemd)
      mitre_attack_id: T1053.003
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc7-2-cron-modification-linux
tags:
  - soc2
  - monitoring
comment: 'CC7.2 / CC8.1 — Linux crontab / systemctl enable'
```

#### macOS — LaunchAgent / LaunchDaemon Changes

```yaml
name: soc2-cc7-2-launchd-modification-macos
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
    name: soc2-cc7-2-launchd-modification-macos
    priority: 3
    metadata:
      soc2_criterion: 'CC7.2, CC8.1'
      description: macOS launchctl load / bootstrap — persistence indicator
      mitre_attack_id: T1543.001
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc7-2-launchd-modification-macos
tags:
  - soc2
  - monitoring
comment: 'CC7.2 / CC8.1 — macOS launchctl load/bootstrap'
```

### CC7.3 / CC7.4 — Evaluation of Events and Incident Response

The Cases extension provides the evaluation-and-response workflow for CC7.3 and CC7.4. Rules below illustrate response enrichment.

> If ext-cases is set to **all detections** ingestion mode, every `report` action becomes a case automatically. In **tailored** mode (the default for newer orgs), case creation requires detections to meet severity thresholds or rules to explicitly `ingest_detection`.

#### Tag Endpoints on Critical Threat Detection

```yaml
name: soc2-cc7-3-critical-threat-tag
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: soc2-cc7-3-critical-threat-tag
    priority: 5
    metadata:
      soc2_criterion: 'CC7.3, CC7.4'
      description: YARA detection on endpoint — tagged for case triage
  - action: add tag
    tag: soc2-incident
    ttl: 604800
tags:
  - soc2
  - incident-response
comment: 'CC7.3 / CC7.4 — Tag endpoints on YARA detection (7-day tag for case triage)'
```

#### Automated Network Isolation on Credential Dumping (Opt-In)

> Network isolation is disruptive. Deploy only with stakeholder approval for well-tuned, high-confidence detections. Enrol hosts by applying the `isolation-enabled` sensor tag.

```yaml
name: soc2-cc7-4-isolate-on-credential-dump
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
    name: soc2-cc7-4-isolate-on-credential-dump
    priority: 5
    metadata:
      soc2_criterion: 'CC7.4'
      description: LSASS access on isolation-enrolled host — automated containment
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
  - action: isolate network
tags:
  - soc2
  - incident-response
comment: 'CC7.4 — Isolate host on LSASS access. Opt-in via "isolation-enabled" sensor tag.'
```

### CC7.5 — Recovery from Security Incidents

CC7.5 is primarily satisfied through the Cases workflow, Velociraptor forensic collection, and the `rejoin network` response action applied once a host is remediated. See [Section 13](#13-recommended-extensions) for the Velociraptor extension.

---

## 8. D&R Rules — CC8: Change Management

### CC8.1 — Authorized Changes

#### Windows — Autorun Changed

```yaml
name: soc2-cc8-1-autorun-change-windows
detect:
  event: AUTORUN_CHANGE
  op: is windows
respond:
  - action: report
    name: soc2-cc8-1-autorun-change-windows
    priority: 3
    metadata:
      soc2_criterion: 'CC8.1, CC7.1'
      description: Windows autorun persistence change
      mitre_attack_id: T1547.001
      mitre_tactic: persistence
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc8-1-autorun-change-windows
tags:
  - soc2
  - change-management
comment: 'CC8.1 / CC7.1 — Windows autorun change'
```

#### Windows — Driver Change

```yaml
name: soc2-cc8-1-driver-change
detect:
  event: DRIVER_CHANGE
  op: is windows
respond:
  - action: report
    name: soc2-cc8-1-driver-change
    priority: 3
    metadata:
      soc2_criterion: 'CC8.1, CC7.1'
      description: Driver installed or modified
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - soc2
  - change-management
comment: 'CC8.1 / CC7.1 — Driver change detection'
```

#### Service Change (All Platforms)

```yaml
name: soc2-cc8-1-service-change
detect:
  event: SERVICE_CHANGE
  op: exists
  path: event/SVC_NAME
respond:
  - action: report
    name: soc2-cc8-1-service-change
    priority: 2
    metadata:
      soc2_criterion: 'CC8.1, CC7.1'
      description: Service configuration changed
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc8-1-service-change
tags:
  - soc2
  - change-management
comment: 'CC8.1 / CC7.1 — Service change across platforms. Suppressed for patching noise.'
```

#### Windows — Firewall Rule Changed

```yaml
name: soc2-cc8-1-firewall-changed-windows
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
    name: soc2-cc8-1-firewall-changed-windows
    priority: 3
    metadata:
      soc2_criterion: 'CC8.1, CC6.6'
      description: Windows Firewall rule or setting changed
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - soc2
  - change-management
comment: 'CC8.1 / CC6.6 — Windows firewall changes (4946-4950)'
```

#### Linux — iptables / firewalld / ufw Changes

```yaml
name: soc2-cc8-1-firewall-changed-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(iptables|ip6tables|nft|firewall-cmd|ufw)$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)(\s-(A|D|I|F|X|P)\s|--(add|remove|permanent)|\s(allow|deny|disable|enable|reset|delete)\b)'
respond:
  - action: report
    name: soc2-cc8-1-firewall-changed-linux
    priority: 3
    metadata:
      soc2_criterion: 'CC8.1, CC6.6'
      description: Linux firewall modification (iptables / nft / firewall-cmd / ufw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - soc2
  - change-management
comment: 'CC8.1 / CC6.6 — Linux firewall changes'
```

#### macOS — pfctl / Firewall Changes

```yaml
name: soc2-cc8-1-firewall-changed-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(sbin/pfctl|usr/libexec/ApplicationFirewall/socketfilterfw)$'
respond:
  - action: report
    name: soc2-cc8-1-firewall-changed-macos
    priority: 3
    metadata:
      soc2_criterion: 'CC8.1, CC6.6'
      description: macOS firewall modification (pfctl / socketfilterfw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-cc8-1-firewall-changed-macos
tags:
  - soc2
  - change-management
comment: 'CC8.1 / CC6.6 — macOS firewall changes'
```

---

## 9. D&R Rules — CC9: Risk Mitigation

### CC9.1 — Business Disruption Risks (Ransomware / Destruction)

#### Windows — Shadow Copy / Backup Deletion

Ransomware families routinely delete volume shadow copies and backup-recovery entries to impede recovery. This rule detects the canonical deletion commands.

```yaml
name: soc2-cc9-1-shadowcopy-deletion-windows
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
              re: '(?i)\\vssadmin\.exe$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\bdelete\s+shadows?\b'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)\\(wmic|powershell|pwsh)\.exe$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)(shadowcopy\s+delete|Remove-WmiObject.*ShadowCopy|Delete-ShadowCopy)'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)\\bcdedit\.exe$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)(recoveryenabled\s+no|bootstatuspolicy\s+ignoreallfailures)'
respond:
  - action: report
    name: soc2-cc9-1-shadowcopy-deletion-windows
    priority: 5
    metadata:
      soc2_criterion: 'CC9.1, A1.2'
      description: Shadow copy or backup-recovery deletion — ransomware precursor
      mitre_attack_id: T1490
      mitre_tactic: impact
  - action: add tag
    tag: soc2-impact
    ttl: 86400
tags:
  - soc2
  - risk-mitigation
comment: 'CC9.1 / A1.2 — VSS / bcdedit / WMI shadow-copy deletion'
```

#### macOS — Time Machine Deletion

```yaml
name: soc2-cc9-1-timemachine-deletion-macos
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
              re: '(?i)/usr/bin/tmutil$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\b(delete|disable)\b'
        - op: and
          rules:
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/bin/rm$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\.Backups\.backupdb|/Volumes/Time\s?Machine'
respond:
  - action: report
    name: soc2-cc9-1-timemachine-deletion-macos
    priority: 5
    metadata:
      soc2_criterion: 'CC9.1, A1.2'
      description: Time Machine backup destruction — ransomware precursor
      mitre_attack_id: T1490
      mitre_tactic: impact
  - action: add tag
    tag: soc2-impact
    ttl: 86400
tags:
  - soc2
  - risk-mitigation
comment: 'CC9.1 / A1.2 — tmutil delete/disable or rm on backup volumes'
```

#### All Platforms — Ransomware File Extension Creation

```yaml
name: soc2-cc9-1-ransomware-extension
detect:
  event: FILE_CREATE
  op: and
  rules:
    - op: or
      rules:
        - op: is windows
        - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\.(locked|encrypted|crypt|cry|crypted|enc|pay|ryk|ryuk|wncry|wncryt|onion|conti|lockbit|babuk|blackcat|alphv)$'
respond:
  - action: report
    name: soc2-cc9-1-ransomware-extension
    priority: 5
    metadata:
      soc2_criterion: 'CC9.1, A1.2'
      description: File created with known ransomware extension
      mitre_attack_id: T1486
      mitre_tactic: impact
  - action: add tag
    tag: soc2-ransomware
    ttl: 604800
tags:
  - soc2
  - risk-mitigation
comment: 'CC9.1 / A1.2 — File created with known-bad ransomware extension'
```

### CC9.2 — Vendor and Third-Party Risk

#### All Platforms — Third-Party Remote-Support Tool

```yaml
name: soc2-cc9-2-remote-support-tool
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: matches
      path: event/FILE_PATH
      re: '(?i)(anydesk|teamviewer|screenconnect|connectwisecontrol|logmein|splashtop|vnc|gotomypc|beyondtrust|bomgar|ammyy|supremo|dwservice|remoteutilities|radmin|atera|ninjarmm|ngrok)(\.exe)?$'
respond:
  - action: report
    name: soc2-cc9-2-remote-support-tool
    priority: 3
    metadata:
      soc2_criterion: 'CC9.2, CC6.6'
      description: Third-party remote-support tool executed — vendor-risk policy check
      mitre_attack_id: T1219
      mitre_tactic: command-and-control
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.FILE_PATH }}'
tags:
  - soc2
  - risk-mitigation
comment: 'CC9.2 / CC6.6 — Remote-support tools (authorised vendor list should be FP-rule exclusions)'
```

> Maintain the authorised-vendor list for your org as false-positive rules against `soc2-cc9-2-remote-support-tool`. The `/lc-essentials:detection-tuner` skill assists with building these exclusions.

---

## 10. D&R Rules — Availability (A1)

A1 is an optional SOC 2 category. Include these rules only if Availability is in the scope of your report.

### A1.2 — Environmental Protections and Monitoring

#### Windows — Backup / Availability Service Stop

```yaml
name: soc2-a1-2-backup-service-stop
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: or
      rules:
        - op: matches
          path: event/FILE_PATH
          re: '(?i)\\(net|net1|sc|taskkill|powershell|pwsh)\.exe$'
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\b(stop|delete|disable)\s+.*(veeam|backup|acronis|commvault|netbackup|cohesity|rubrik|vss|wbengine|msiserver)'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)stop-service\s+.*(veeam|backup|acronis|vss|wbengine)'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)taskkill\s+.*(veeamagent|rphostd|backupexec)'
respond:
  - action: report
    name: soc2-a1-2-backup-service-stop
    priority: 5
    metadata:
      soc2_criterion: 'A1.2, CC9.1'
      description: Attempt to stop or disable backup / availability service
      mitre_attack_id: T1489
      mitre_tactic: impact
  - action: add tag
    tag: soc2-availability
    ttl: 86400
tags:
  - soc2
  - availability
comment: 'A1.2 — Windows backup-service stop attempts'
```

#### Linux — Critical Service Stop

```yaml
name: soc2-a1-2-critical-service-stop-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(systemctl|service)$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\b(stop|disable|mask)\b.*(sshd|nginx|apache2|httpd|mysql|mariadb|postgresql|mongod|redis|docker|containerd|k3s|kubelet|rsyslog|systemd-journald|auditd)'
respond:
  - action: report
    name: soc2-a1-2-critical-service-stop-linux
    priority: 4
    metadata:
      soc2_criterion: 'A1.2, CC9.1'
      description: Attempt to stop or disable a critical Linux service
      mitre_attack_id: T1489
      mitre_tactic: impact
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-a1-2-critical-service-stop-linux
tags:
  - soc2
  - availability
comment: 'A1.2 — Linux critical-service stop/disable'
```

#### macOS — Critical launchd Unload

```yaml
name: soc2-a1-2-critical-launchd-stop-macos
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
      re: '(?i)\b(unload|disable|bootout)\b.*(com\.apple\.(sshd|syslogd|auditd|mdmclient|security\.agent)|timemachine|backup)'
respond:
  - action: report
    name: soc2-a1-2-critical-launchd-stop-macos
    priority: 4
    metadata:
      soc2_criterion: 'A1.2, CC9.1'
      description: Attempt to unload a critical macOS launchd service
      mitre_attack_id: T1489
      mitre_tactic: impact
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-a1-2-critical-launchd-stop-macos
tags:
  - soc2
  - availability
comment: 'A1.2 — macOS critical launchd service unload'
```

#### All Platforms — Mass Process Termination

```yaml
name: soc2-a1-2-mass-process-termination
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: or
      rules:
        - op: and
          rules:
            - op: is windows
            - op: matches
              path: event/FILE_PATH
              re: '(?i)\\taskkill\.exe$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)/f\s+.*(/im|/pid)'
        - op: and
          rules:
            - op: or
              rules:
                - op: is linux
                - op: is mac
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\bkill(all)?\s+-(9|SIGKILL)\s+'
respond:
  - action: report
    name: soc2-a1-2-mass-process-termination
    priority: 3
    metadata:
      soc2_criterion: 'A1.2, CC9.1'
      description: Forceful process termination command — possible availability attack
      mitre_attack_id: T1489
      mitre_tactic: impact
    suppression:
      max_count: 10
      period: 15m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-a1-2-mass-process-termination
tags:
  - soc2
  - availability
comment: 'A1.2 — taskkill /f or kill -9 patterns'
```

---

## 11. D&R Rules — Confidentiality (C1)

C1 is an optional SOC 2 category. Include these rules only if Confidentiality is in the scope of your report.

### C1.1 — Confidential Information Protection (Credential and Data-Access Indicators)

#### Windows — SAM / SECURITY Hive Access via reg.exe

```yaml
name: soc2-c1-1-sam-hive-access-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\reg\.exe$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\bsave\b.*(HKLM\\SAM|HKLM\\SECURITY|HKLM\\SYSTEM)'
respond:
  - action: report
    name: soc2-c1-1-sam-hive-access-windows
    priority: 5
    metadata:
      soc2_criterion: 'C1.1, CC7.2'
      description: Registry hive save targeting SAM / SECURITY / SYSTEM — credential theft
      mitre_attack_id: T1003.002
      mitre_tactic: credential-access
  - action: add tag
    tag: soc2-credential-access
    ttl: 86400
tags:
  - soc2
  - confidentiality
  - credential-access
comment: 'C1.1 — reg.exe save of credential hives'
```

#### Linux — /etc/shadow Read by Non-Root Pattern

```yaml
name: soc2-c1-1-shadow-access-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)(cat|less|more|head|tail|cp|scp|dd|tar|zip|gzip|base64)\s+.*/etc/shadow'
    - not: true
      op: matches
      path: event/USER_NAME
      re: '^root$'
respond:
  - action: report
    name: soc2-c1-1-shadow-access-linux
    priority: 5
    metadata:
      soc2_criterion: 'C1.1, CC7.2'
      description: Non-root user reading /etc/shadow — credential theft indicator
      mitre_attack_id: T1003.008
      mitre_tactic: credential-access
tags:
  - soc2
  - confidentiality
  - credential-access
comment: 'C1.1 — /etc/shadow access by non-root process'
```

#### macOS — Keychain Database Access

```yaml
name: soc2-c1-1-keychain-access-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)(cat|cp|scp|dd|tar|base64|security)\s+.*((/Users/[^/]+/Library/Keychains/.+\.keychain)|(/Library/Keychains/System\.keychain))'
respond:
  - action: report
    name: soc2-c1-1-keychain-access-macos
    priority: 5
    metadata:
      soc2_criterion: 'C1.1, CC7.2'
      description: Process accessing macOS keychain file — credential theft indicator
      mitre_attack_id: T1555.001
      mitre_tactic: credential-access
tags:
  - soc2
  - confidentiality
  - credential-access
comment: 'C1.1 — macOS keychain file access'
```

#### Windows — NTDS.dit Access

```yaml
name: soc2-c1-1-ntds-access
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)ntdsutil.*ifm'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\\ntds\.dit\b'
respond:
  - action: report
    name: soc2-c1-1-ntds-access
    priority: 5
    metadata:
      soc2_criterion: 'C1.1, CC7.2'
      description: NTDS.dit extraction attempt — domain credential theft
      mitre_attack_id: T1003.003
      mitre_tactic: credential-access
  - action: add tag
    tag: soc2-credential-access
    ttl: 86400
tags:
  - soc2
  - confidentiality
  - credential-access
comment: 'C1.1 — NTDS.dit / ntdsutil extraction'
```

### C1.2 — Disposal of Confidential Information

#### All Platforms — Secure-Delete Tool Execution

```yaml
name: soc2-c1-2-secure-delete
detect:
  event: NEW_PROCESS
  op: matches
  path: event/FILE_PATH
  re: '(?i)\\(sdelete|sdelete64|cipher)\.exe$|/(shred|srm|wipe)$'
respond:
  - action: report
    name: soc2-c1-2-secure-delete
    priority: 2
    metadata:
      soc2_criterion: 'C1.2'
      description: Secure-delete tool executed — evidence of disposal action
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - soc2-c1-2-secure-delete
tags:
  - soc2
  - confidentiality
comment: 'C1.2 — Secure-delete tool invocation (evidence of disposal)'
```

> Confidential-path file deletions are covered by the `soc2-cc7-1-fim-hit` rule when paired with the `soc2-fim-*-confidential` FIM rules (Section 4). A separate `FILE_DELETE` rule is only needed if you want different severity or tagging than the generic FIM-hit detection.

---

## 12. Outputs for Long-Term Evidence Retention

SOC 2 Type II observation periods typically span 12 months. LC Insight provides 90 days of hot retention; for the remaining 9+ months, configure a cold-archive output. Each output below is a separate `ext-output` configuration.

### S3 Cold Archive — All Events

```yaml
name: soc2-s3-archive-events
module: s3
type: event
for_all_tenants: false
dest:
  bucket: your-soc2-bucket
  key_id: AKIAXXXXXXXXXXXXXXXX
  region: us-east-1
  secret_key: 'hive://secret/soc2-s3-secret'
  prefix: events/
is_indexing: true
is_compression: true
```

### S3 Cold Archive — Detections

```yaml
name: soc2-s3-archive-detect
module: s3
type: detect
dest:
  bucket: your-soc2-bucket
  key_id: AKIAXXXXXXXXXXXXXXXX
  region: us-east-1
  secret_key: 'hive://secret/soc2-s3-secret'
  prefix: detect/
is_compression: true
```

### S3 Cold Archive — Audit Stream

The platform audit stream is critical CC8.1 evidence — every LC configuration change with the identity that made it.

```yaml
name: soc2-s3-archive-audit
module: s3
type: audit
dest:
  bucket: your-soc2-bucket
  key_id: AKIAXXXXXXXXXXXXXXXX
  region: us-east-1
  secret_key: 'hive://secret/soc2-s3-secret'
  prefix: audit/
is_compression: true
```

> For GCS, substitute `module: gcs` and use `project:` + `service_account_creds:` fields. Same pattern, one per stream type.

### Slack Notification — Critical Detections

Supports CC2.1 (communication) and CC7.4 (incident response).

```yaml
name: soc2-slack-critical
module: slack
type: detect
dest:
  webhook: 'hive://secret/soc2-slack-webhook'
event_white_list:
  - soc2-cc7-1-event-log-cleared
  - soc2-cc7-2-lsass-access
  - soc2-cc7-4-isolate-on-credential-dump
  - soc2-cc9-1-shadowcopy-deletion-windows
  - soc2-cc9-1-timemachine-deletion-macos
  - soc2-cc9-1-ransomware-extension
  - soc2-a1-2-backup-service-stop
  - soc2-c1-1-ntds-access
```

> Output secrets referenced as `hive://secret/...` are created via the Hive `secret` namespace — not the `lookup` namespace. Create once: `limacharlie hive set --hive secret --name soc2-s3-secret --expr-data '"<value>"'`.

---

## 13. Recommended Extensions

### Required

| Extension | Purpose | SOC 2 Criteria |
|---|---|---|
| **Reliable Tasking** | Prerequisite for Artifact Collection. Ensures tasks reach offline sensors. | CC7.2 (enables WEL/MUL collection) |
| **Artifact Collection (ext-artifact)** | Manages WEL/MUL streaming and file/log retention. | CC6.1, CC7.1, CC7.2 |
| **Exfil Control (ext-exfil)** | Manages which event types flow from sensor to cloud. | CC7.2 |
| **Integrity (ext-integrity)** | FIM / RIM rule management. | CC7.1, CC8.1 |

### Strongly Recommended

| Extension | Purpose | SOC 2 Criteria |
|---|---|---|
| **Cases (ext-cases)** | SOC case management with detection-to-case conversion, SLA tracking, investigation workflows, audit trail. | CC7.3, CC7.4 |
| **EPP (Endpoint Protection)** | Unified Windows Defender management and event collection. Free. | CC6.8 |
| **Soteria EDR Rules** | Managed detection ruleset with MITRE ATT&CK mapping across 14 event types. | CC4.1, CC7.2 |
| **Sigma Rules** | Community and commercial Sigma rule conversion. | CC4.1, CC7.2 |
| **ext-git-sync** | D&R rules, FIM, outputs, extensions managed via git — direct CC8.1 evidence. | CC8.1, CC7.1 |

### Recommended for Enhanced Coverage

| Extension | Purpose | SOC 2 Criteria |
|---|---|---|
| **Strelka** | File analysis engine (YARA, PE analysis, archive extraction) for files transiting endpoints. | CC6.8 |
| **Zeek** | Network monitoring and analysis (Linux sensors). | CC6.6, CC6.7 |
| **Velociraptor** | DFIR hunting and artifact collection — forensic evidence for CC7.5 recovery. | CC7.4, CC7.5 |
| **Playbook** | Python-based automation for custom response workflows. | CC7.4 |
| **AI SOC agents (lean-soc, tiered-soc)** | Automated triage, classification, enrichment of detections. | CC7.3 |

---

## 14. Deployment Notes

### Observation Period and Retention

SOC 2 Type II reports cover an observation period — commonly **12 months** for annual reports, 6 months for initial reports, or the period specified in the service agreement. Auditor expectations:

- Raw telemetry must be retrievable for the full observation window (not just the 90-day Insight hot tier)
- Detections and case records must be available for the full window
- Platform-level configuration change history must be available

**Configuration pattern:**

1. Insight default (90 days) — used for auditor queries of recent evidence, incident investigation
2. S3/GCS outputs (Section 12) — cold archive for the full observation period
3. Cases — persistent narrative evidence of CC7.3 / CC7.4 / CC7.5 operation
4. ext-git-sync — commit history provides CC8.1 evidence of authorised changes

If the auditor requests evidence older than 90 days, queries against the cold-archive bucket (Athena, BigQuery, or direct object retrieval) provide the data. Document this architecture in the SOC 2 system description.

### Tagging Strategy

All D&R rules use the `soc2` tag, enabling:

- Filtering detections by compliance source in the Cases UI
- Routing SOC-2-specific detections to the dedicated S3 output
- Tracking SOC 2 rule coverage separately from operational detections
- Generating audit-ready reports scoped to just SOC 2 evidence

Additional secondary tags by criterion category (`logical-access`, `change-management`, `availability`, `confidentiality`) allow finer-grained reporting.

### Metadata Keys

Every rule in this document sets `metadata.soc2_criterion` identifying the primary criterion (and any secondary criteria). When generating auditor evidence packages, group detections by this metadata key to produce per-criterion evidence exhibits.

### Suppression Tuning

Many rules include starting-point suppression. Tune after deployment:

1. Run for a 7-day burn-in period before the observation window begins
2. Use `/lc-essentials:fp-pattern-finder` to identify systematic noise
3. Author FP rules for known-safe patterns (service accounts, approved admin tools, authorised remote-support tools from `soc2-cc9-2-remote-support-tool`)
4. Document each FP rule with a justification comment — auditors will ask why detections are suppressed

### Windows Audit Policy Prerequisites

Windows endpoints need the **Advanced Audit Policy** configured. Minimum categories for SOC 2 coverage:

| Audit Category | Subcategory | Setting |
|---|---|---|
| Account Logon | Credential Validation | Success, Failure |
| Account Management | User Account Management | Success, Failure |
| Account Management | Security Group Management | Success, Failure |
| Detailed Tracking | Process Creation | Success |
| Logon/Logoff | Logon | Success, Failure |
| Logon/Logoff | Logoff | Success |
| Object Access | File System | Success, Failure |
| Policy Change | Audit Policy Change | Success, Failure |
| Privilege Use | Sensitive Privilege Use | Success, Failure |
| System | Security State Change | Success |
| System | System Integrity | Success, Failure |

Deploy via Group Policy: `Computer Configuration → Windows Settings → Security Settings → Advanced Audit Policy Configuration`.

### Linux Audit Policy Prerequisites

Deploy the auditd rules from Section 3 via Ansible/Puppet/Chef. Verify with `auditctl -l`. Ensure `/var/log/audit/audit.log` rotation is configured to retain at minimum the Insight retention window.

### macOS Audit Policy Prerequisites

macOS Unified Log retention is managed via `log config` policies. Default retention is often shorter than 90 days — validate on a sample endpoint with `log stats --overview`. Adjust predicate patterns (Section 2) to balance visibility with volume.

### Deployment Order

1. Enable **Reliable Tasking**, **Artifact Collection**, **Exfil Control**, **Integrity** extensions
2. Deploy Windows WEL artifact collection rules (Section 1)
3. Deploy macOS MUL artifact collection rules (Section 2)
4. Deploy Linux auditd rules + file adapter or artifact rules (Section 3)
5. Deploy FIM rules per platform (Section 4)
6. Deploy exfil event rules per platform (Section 5)
7. Deploy D&R rules (Sections 6–11) — detections begin firing
8. Configure cold-archive outputs (Section 12) — archival begins immediately, important to enable **before** the observation period starts
9. Enable **Cases (ext-cases)** — detections convert to trackable cases
10. Subscribe to **Soteria** and/or **Sigma** — adds managed detection coverage
11. Burn-in for 7 days before the formal observation period starts, then tune via FP pattern finder

### Mapping Detections to Control Evidence

For each CC-mapped detection, auditors typically request:

1. The rule YAML (detect + respond definitions)
2. A sample of detections fired during the observation period
3. Evidence that detections were triaged (case notes, assignment, resolution)
4. Evidence that high-priority detections met an SLA

LC's detection record structure supports all four:
- Rule YAML is managed via ext-git-sync (commit history) or exportable via `limacharlie dr get`
- Detections are queryable via LCQL (`op: "detect"` filters by rule name)
- Cases carry triage and resolution history
- Case-level SLA metrics are available via the reporting skill

### Validation

Every YAML rule in this document passes `limacharlie dr validate`. New rules specific to SOC 2 coverage (`soc2-cc9-1-shadowcopy-deletion-windows`, `soc2-cc9-1-timemachine-deletion-macos`, `soc2-cc9-1-ransomware-extension`, `soc2-cc9-2-remote-support-tool`, `soc2-a1-2-backup-service-stop`, `soc2-c1-1-shadow-access-linux`, and the removable-media and listener rules) were validated individually.

For end-to-end validation against historical telemetry, use `limacharlie dr replay` against recent data from representative endpoints (one Windows, one Linux, one macOS).

### Scope Trimming

If your SOC 2 scope excludes the optional categories:

- **No Availability (A1):** Skip Section 10 rules
- **No Confidentiality (C1):** Skip Section 11 rules and `soc2-fim-*-confidential` FIM rules in Section 4
- **No Processing Integrity (PI1):** No rules in this doc specifically target PI1 (LC is not a primary PI1 control)
- **No Privacy (P):** No rules in this doc specifically target P (LC is not a primary Privacy control)

If your scope is **Security + all additional categories**, deploy everything in this document.
