# NIST SP 800-53 Rev 5 Compliance Implementation Guide — LimaCharlie

Concrete D&R rules, artifact collection rules, FIM rules, and extension recommendations to satisfy NIST SP 800-53 Rev 5 controls using LimaCharlie EDR on Windows, Linux, and macOS endpoints.

Companion to [nist-800-53-limacharlie-mapping.md](nist-800-53-limacharlie-mapping.md), which maps controls to LC capabilities conceptually. This document provides the deployable configuration.

All D&R rule syntax in this document has been validated against `limacharlie dr validate` / `limacharlie dr test`. Event-to-platform coverage reflects actual sensor capability (per the LC EDR events reference), not documentation aspirations.

---

## Table of Contents

1. [Windows Event Log Artifact Collection Rules](#1-windows-event-log-artifact-collection-rules)
2. [macOS Unified Log Artifact Collection Rules](#2-macos-unified-log-artifact-collection-rules)
3. [Linux Audit Log Collection](#3-linux-audit-log-collection)
4. [File Integrity Monitoring (FIM) Rules](#4-file-integrity-monitoring-fim-rules)
5. [Exfil Event Collection Rules](#5-exfil-event-collection-rules)
6. [D&R Rules — Audit & Accountability (AU)](#6-dr-rules--audit--accountability-au)
7. [D&R Rules — Access Control (AC)](#7-dr-rules--access-control-ac)
8. [D&R Rules — Identification & Authentication (IA)](#8-dr-rules--identification--authentication-ia)
9. [D&R Rules — System & Information Integrity (SI)](#9-dr-rules--system--information-integrity-si)
10. [D&R Rules — Incident Response (IR)](#10-dr-rules--incident-response-ir)
11. [D&R Rules — Configuration Management (CM)](#11-dr-rules--configuration-management-cm)
12. [D&R Rules — System & Communications Protection (SC)](#12-dr-rules--system--communications-protection-sc)
13. [Recommended Extensions](#13-recommended-extensions)
14. [Deployment Notes](#14-deployment-notes)

---

## 1. Windows Event Log Artifact Collection Rules

The `wel://` pattern streams Windows Event Logs as first-class `WEL` telemetry — preferred over `.evtx` file collection because events are evaluated by D&R rules in real time.

> **Prerequisite:** The **Reliable Tasking** and **Artifact Collection** extensions must be enabled.

Rule map entries are added to `ext-artifact` configuration (web UI Artifact Collection section, `limacharlie extension config-set --name ext-artifact`, or ext-git-sync).

### Security Log

```yaml
nist-wel-security:
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

| Event ID | Category | NIST Control |
|---|---|---|
| 4624 | Successful logon | AU-2, AU-3, IA-2 |
| 4625 | Failed logon | AU-2, AC-7 |
| 4634 | Logoff | AU-2 |
| 4647 | User-initiated logoff | AU-2 |
| 4648 | Logon with explicit credentials | AU-2, AC-6 |
| 4672 | Special privileges assigned to new logon | AU-2, AC-6 |
| 4673 | Privileged service called | AC-6 |
| 4674 | Operation attempted on privileged object | AC-6 |
| 4688 | Process creation (if audit enabled) | AU-2 |
| 4689 | Process termination | AU-2 |
| 4697 | Service installed on the system | CM-5, SI-4 |
| 4698 | Scheduled task created | SI-4 |
| 4699 | Scheduled task deleted | CM-5 |
| 4700 | Scheduled task enabled | SI-4 |
| 4701 | Scheduled task disabled | CM-5 |
| 4719 | Audit policy changed | AU-9, CM-5 |
| 4720 | User account created | AC-2 |
| 4722 | User account enabled | AC-2 |
| 4723 | Password change attempted | IA-5 |
| 4724 | Password reset attempted | IA-5 |
| 4725 | User account disabled | AC-2 |
| 4726 | User account deleted | AC-2 |
| 4728 | Member added to security-enabled global group | AC-2 |
| 4732 | Member added to security-enabled local group | AC-2 |
| 4735 | Security-enabled local group changed | AC-2 |
| 4738 | User account changed | AC-2 |
| 4740 | User account locked out | AC-7 |
| 4756 | Member added to universal security group | AC-2 |
| 4767 | User account unlocked | AC-2 |
| 4776 | Credential validation (NTLM) | IA-2 |
| 4946 | Firewall rule added | CM-5, SC-7 |
| 4947 | Firewall rule modified | CM-5, SC-7 |
| 4948 | Firewall rule deleted | CM-5, SC-7 |
| 4950 | Firewall setting changed | CM-5, SC-7 |
| 1102 | Security log cleared | AU-9 |

### System Log

```yaml
nist-wel-system:
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
nist-wel-powershell:
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

### Sysmon (if deployed)

```yaml
nist-wel-sysmon:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Sysmon/Operational:*"
```

### Windows Defender Operational Log

```yaml
nist-wel-defender:
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

### Task Scheduler Operational Log

```yaml
nist-wel-taskscheduler:
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
nist-wel-firewall:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Firewall With Advanced Security/Firewall:*"
```

---

## 2. macOS Unified Log Artifact Collection Rules

The `mul://` pattern streams macOS Unified Log entries as real-time `MUL` telemetry. Predicates use standard macOS unified-log predicate syntax.

> **Prerequisite:** `MUL` must be enabled in the Exfil Control rules for macOS (see Section 5).

> **Field path verification:** D&R rules in Section 6 that match `MUL` events use field paths based on macOS `log` command keys (`eventMessage`, `processImagePath`, `subsystem`). Verify the exact field paths against your first few `MUL` events in Timeline after deployment — the sensor may flatten or re-key some fields. Adjust `path:` values accordingly.

### Authentication & Authorization

```yaml
nist-mul-auth:
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

Covers: IA-2, AC-7 (authentication failures), IA-5 (authenticator changes via `dscl`, `passwd`).

### Login & Session Events

```yaml
nist-mul-sessions:
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

Complements native `USER_LOGIN` / `SSH_LOGIN` events.

### System Configuration & Launch Services

```yaml
nist-mul-system:
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

Covers: CM-3, CM-5, SI-4 (launch agent / daemon changes).

### Privilege Escalation

```yaml
nist-mul-privilege:
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

Covers: AC-6, AC-6(9).

---

## 3. Linux Audit Log Collection

The LC Linux EDR sensor does **not** emit `USER_LOGIN` / `SSH_LOGIN` events. Linux authentication telemetry requires one of the three approaches below.

### Option A — Artifact Collection (Retention, Not Streaming)

Use when compliance requires **retention** of the raw auth log but real-time detection is not needed:

```yaml
nist-artifact-authlog:
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
2. Deploy on each Linux endpoint with this config:

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

### Option C — Auditd Rules (Recommended for High-Security Systems)

Deploy auditd rules on Linux endpoints (via configuration management) that mirror Windows advanced audit policy. Then collect `/var/log/audit/audit.log` via file adapter or artifact collection using the same approach as Options A/B.

Minimum auditd rules for NIST 800-53 Moderate/High:

```
# /etc/audit/rules.d/nist-800-53.rules
# Identity changes (AC-2, IA-5)
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k identity
-w /etc/sudoers.d/ -p wa -k identity

# Authentication config (AC-7)
-w /etc/pam.d/ -p wa -k auth-config
-w /etc/ssh/sshd_config -p wa -k sshd-config

# Privilege escalation (AC-6)
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation
-a always,exit -F arch=b32 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation

# Time changes (AU-8)
-a always,exit -F arch=b64 -S settimeofday,clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Audit subsystem integrity (AU-9)
-w /etc/audit/ -p wa -k audit-config
-w /etc/libaudit.conf -p wa -k audit-config
-e 2
```

Deploy via Ansible, Puppet, or similar; verify with `auditctl -l`.

---

## 4. File Integrity Monitoring (FIM) Rules

FIM generates `FIM_HIT` events on monitored files, directories, and Windows registry keys across all three platforms.

> Linux FIM works with `inotify` (active monitoring) or eBPF (on supported kernels). Windows and macOS use passive kernel monitoring.

### Windows

```yaml
nist-fim-windows-system:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\drivers\etc\hosts
    - ?:\Windows\System32\config\SAM
    - ?:\Windows\System32\config\SYSTEM
    - ?:\Windows\System32\config\SECURITY

nist-fim-windows-boot:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\boot\bcd
    - ?:\Windows\System32\boot\winload.exe

nist-fim-windows-grouppolicy:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\GroupPolicy\*
    - ?:\Windows\SYSVOL\*

nist-fim-windows-powershell-profiles:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    - ?:\Users\*\Documents\WindowsPowerShell\profile.ps1

nist-fim-windows-registry-persistence:
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
nist-fim-linux-identity:
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

nist-fim-linux-auth:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/pam.d/*
    - /etc/ssh/sshd_config
    - /etc/ssh/ssh_config
    - /etc/security/*

nist-fim-linux-ssh-keys:
  filters:
    platforms:
      - linux
  patterns:
    - /root/.ssh/authorized_keys
    - /root/.ssh/*
    - /home/*/.ssh/*

nist-fim-linux-persistence:
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

nist-fim-linux-boot:
  filters:
    platforms:
      - linux
  patterns:
    - /boot/grub/grub.cfg
    - /boot/grub2/grub.cfg
    - /etc/default/grub
    - /etc/fstab

nist-fim-linux-audit:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/audit/*
    - /etc/libaudit.conf
```

### macOS

```yaml
nist-fim-macos-identity:
  filters:
    platforms:
      - macos
  patterns:
    - /etc/sudoers
    - /etc/sudoers.d/*
    - /etc/pam.d/*

nist-fim-macos-ssh-keys:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/.ssh/*
    - /var/root/.ssh/*

nist-fim-macos-launch-daemons:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/LaunchDaemons/*
    - /Library/LaunchAgents/*
    - /System/Library/LaunchDaemons/*
    - /System/Library/LaunchAgents/*
    - /Users/*/Library/LaunchAgents/*

nist-fim-macos-keychains:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/Library/Keychains/*
    - /Library/Keychains/*

nist-fim-macos-boot:
  filters:
    platforms:
      - macos
  patterns:
    - /System/Library/CoreServices/boot.efi
    - /Library/Preferences/SystemConfiguration/*

nist-fim-macos-kernel-extensions:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/Extensions/*
    - /System/Library/Extensions/*
```

---

## 5. Exfil Event Collection Rules

Additive to default exfil rules — ensures required event types stream to the cloud even if defaults change.

### Windows

```yaml
nist-windows-events:
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
  filters:
    platforms:
      - windows
```

### Linux

```yaml
nist-linux-events:
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
nist-macos-events:
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
  filters:
    platforms:
      - macos
```

---

## 6. D&R Rules — Audit & Accountability (AU)

### AU-2 — Event Logging / AU-12 — Audit Record Generation

#### Windows — Failed Logon Detection (AC-7 / AU-2)

```yaml
name: nist-au-failed-logon-windows
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
    name: nist-au-failed-logon-windows
    priority: 3
    metadata:
      nist_control: AU-2, AC-7
      description: Failed logon attempt detected
      mitre_attack_id: T1078
      mitre_tactic: initial-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-au-failed-logon-windows
tags:
  - nist-800-53
  - audit
comment: 'AU-2 / AC-7 — Failed Windows logon (Event ID 4625)'
```

#### Windows — Brute Force Detection

```yaml
name: nist-au-brute-force-windows
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
    name: nist-au-brute-force-windows
    priority: 4
    metadata:
      nist_control: AU-2, AC-7
      description: Possible brute force — 10+ failed logons within 10 min
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      min_count: 10
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-au-brute-force-windows
tags:
  - nist-800-53
  - audit
comment: 'AU-2 / AC-7 — Threshold-based brute force on Windows'
```

#### macOS — Failed Authentication via Unified Log

The native `SSH_LOGIN` event fires only on successful login and has no failure field. Failed SSH / authentication attempts on macOS must be collected from the Unified Log. Deploy the `nist-mul-auth` artifact rule (Section 2), then match the MUL stream:

```yaml
name: nist-au-auth-failed-macos
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
    name: nist-au-auth-failed-macos
    priority: 3
    metadata:
      nist_control: AU-2, AC-7
      description: Authentication failure logged to macOS Unified Log
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-au-auth-failed-macos
tags:
  - nist-800-53
  - audit
comment: 'AU-2 / AC-7 — macOS authentication failures from Unified Log. Requires nist-mul-auth (Section 2).'
```

#### Linux — Failed SSH via Process Context

LC Linux sensor does not emit `SSH_LOGIN`. Detection of failed auth on Linux relies on (a) auditd integration via the file adapter or (b) scanning `NEW_PROCESS` for `sshd` child `exec`s followed by early termination — a weaker signal. If auditd is collected via adapter (Section 3), author rules on the adapter event stream.

### AU-9 — Protection of Audit Information

#### Windows — Audit Policy Changed

```yaml
name: nist-au-audit-policy-changed
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
    name: nist-au-audit-policy-changed
    priority: 5
    metadata:
      nist_control: AU-9, CM-5
      description: Audit policy changed — potential tampering with logging
      mitre_attack_id: T1562.002
      mitre_tactic: defense-evasion
tags:
  - nist-800-53
  - audit
comment: 'AU-9 — Windows audit policy change (Event ID 4719)'
```

#### Windows — Security Event Log Cleared

```yaml
name: nist-au-event-log-cleared
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
    name: nist-au-event-log-cleared
    priority: 5
    metadata:
      nist_control: AU-9
      description: Security event log was cleared — strong tampering indicator
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - nist-800-53
  - audit
comment: 'AU-9 — Security log clearing (Event ID 1102)'
```

#### Windows — Event Log Service Tampering

```yaml
name: nist-au-eventlog-service-stop-windows
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
    name: nist-au-eventlog-service-stop-windows
    priority: 5
    metadata:
      nist_control: AU-9
      description: Attempt to stop event log service or clear event logs
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - nist-800-53
  - audit
comment: 'AU-9 — Attempt to tamper with Windows event logging'
```

#### Linux — Auditd Tampering

```yaml
name: nist-au-auditd-tamper-linux
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
    name: nist-au-auditd-tamper-linux
    priority: 5
    metadata:
      nist_control: AU-9
      description: Attempt to stop or disable Linux auditd
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - nist-800-53
  - audit
comment: 'AU-9 — Linux auditd service tampering'
```

#### macOS — Unified Log Tampering

```yaml
name: nist-au-log-tamper-macos
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
    name: nist-au-log-tamper-macos
    priority: 5
    metadata:
      nist_control: AU-9
      description: Attempt to erase or disable macOS unified log
      mitre_attack_id: T1070
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - nist-800-53
  - audit
comment: 'AU-9 — macOS log erase / disable'
```

#### Windows Defender Real-Time Protection Disabled

```yaml
name: nist-au-defender-rtp-disabled
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
    name: nist-au-defender-rtp-disabled
    priority: 5
    metadata:
      nist_control: SI-3, AU-9
      description: Windows Defender real-time protection disabled
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - nist-800-53
  - audit
  - defense-evasion
comment: 'SI-3 / AU-9 — Defender RTP disabled (Event ID 5001)'
```

---

## 7. D&R Rules — Access Control (AC)

### AC-2 — Account Management

#### Windows — User Account Created

```yaml
name: nist-ac-user-created-windows
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
    name: nist-ac-user-created-windows
    priority: 3
    metadata:
      nist_control: AC-2
      description: New Windows user account created
      mitre_attack_id: T1136.001
      mitre_tactic: persistence
tags:
  - nist-800-53
  - access-control
comment: 'AC-2 — Windows local user creation (Event ID 4720)'
```

#### Windows — User Added to Privileged Group

```yaml
name: nist-ac-user-added-to-group-windows
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
    name: nist-ac-user-added-to-group-windows
    priority: 4
    metadata:
      nist_control: AC-2, AC-6
      description: User added to a Windows security-enabled group
      mitre_attack_id: T1098
      mitre_tactic: persistence
tags:
  - nist-800-53
  - access-control
comment: 'AC-2 — Windows group membership addition (4728, 4732, 4756)'
```

#### Windows — User Account Deleted

```yaml
name: nist-ac-user-deleted-windows
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
    name: nist-ac-user-deleted-windows
    priority: 3
    metadata:
      nist_control: AC-2
      description: Windows user account deleted
tags:
  - nist-800-53
  - access-control
comment: 'AC-2 — Windows user deletion (Event ID 4726)'
```

#### Linux — Account Management Binary Execution

```yaml
name: nist-ac-user-mgmt-linux
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
    name: nist-ac-user-mgmt-linux
    priority: 3
    metadata:
      nist_control: AC-2
      description: Linux account management binary executed
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - nist-800-53
  - access-control
comment: 'AC-2 — Linux user/group management (useradd, usermod, groupadd, ...)'
```

#### macOS — Account Management via dscl

```yaml
name: nist-ac-user-mgmt-macos
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
    name: nist-ac-user-mgmt-macos
    priority: 3
    metadata:
      nist_control: AC-2
      description: macOS account management invocation (dscl / sysadminctl)
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - nist-800-53
  - access-control
comment: 'AC-2 — macOS account management via dscl, sysadminctl, dsimport'
```

### AC-6 — Least Privilege

#### Windows — Special Privileges Assigned

```yaml
name: nist-ac-special-privilege-logon
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
    name: nist-ac-special-privilege-logon
    priority: 2
    metadata:
      nist_control: AC-6, AC-6(9)
      description: Special privileges assigned to new logon session
      mitre_attack_id: T1078
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-ac-special-privilege-logon
tags:
  - nist-800-53
  - access-control
comment: 'AC-6 — Windows special privilege assignment (Event ID 4672)'
```

#### Windows — Privileged Service Called

```yaml
name: nist-ac-privileged-service-windows
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
    name: nist-ac-privileged-service-windows
    priority: 3
    metadata:
      nist_control: AC-6
      description: Privileged service or object operation
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-ac-privileged-service-windows
tags:
  - nist-800-53
  - access-control
comment: 'AC-6 — Windows privileged service call (4673, 4674)'
```

#### Linux — sudo / su / pkexec

```yaml
name: nist-ac-privilege-escalation-linux
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
    name: nist-ac-privilege-escalation-linux
    priority: 2
    metadata:
      nist_control: AC-6, AC-6(9)
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
  - nist-800-53
  - access-control
comment: 'AC-6 — Linux sudo/su/pkexec/doas. Suppressed per-user per-hour.'
```

#### macOS — sudo Execution

```yaml
name: nist-ac-sudo-macos
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
    name: nist-ac-sudo-macos
    priority: 2
    metadata:
      nist_control: AC-6, AC-6(9)
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
  - nist-800-53
  - access-control
comment: 'AC-6 — macOS sudo execution'
```

### AC-7 — Unsuccessful Logon Attempts / Lockout

#### Windows — Account Lockout

```yaml
name: nist-ac-account-lockout-windows
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
    name: nist-ac-account-lockout-windows
    priority: 4
    metadata:
      nist_control: AC-7
      description: Windows account locked due to failed logons
      mitre_attack_id: T1110
      mitre_tactic: credential-access
tags:
  - nist-800-53
  - access-control
comment: 'AC-7 — Windows account lockout (Event ID 4740)'
```

### AC-17 — Remote Access

#### Windows — RDP Logon

```yaml
name: nist-ac-rdp-logon
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
    name: nist-ac-rdp-logon
    priority: 2
    metadata:
      nist_control: AC-17
      description: Remote Desktop logon (LogonType 10)
      mitre_attack_id: T1021.001
      mitre_tactic: lateral-movement
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-ac-rdp-logon
tags:
  - nist-800-53
  - access-control
comment: 'AC-17 — Windows RDP logon'
```

#### macOS — SSH Login

```yaml
name: nist-ac-ssh-login-macos
detect:
  event: SSH_LOGIN
  op: is mac
respond:
  - action: report
    name: nist-ac-ssh-login-macos
    priority: 2
    metadata:
      nist_control: AC-17
      description: macOS SSH session established
      mitre_attack_id: T1021.004
      mitre_tactic: lateral-movement
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-ac-ssh-login-macos
tags:
  - nist-800-53
  - access-control
comment: 'AC-17 — macOS SSH login'
```

---

## 8. D&R Rules — Identification & Authentication (IA)

### IA-5 — Authenticator Management

#### Windows — Password Change / Reset

```yaml
name: nist-ia-password-change-windows
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
    name: nist-ia-password-change-windows
    priority: 2
    metadata:
      nist_control: IA-5
      description: Windows password change or reset attempted
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-ia-password-change-windows
tags:
  - nist-800-53
  - authentication
comment: 'IA-5 — Windows password change (4723) / reset (4724)'
```

#### Linux — Password Change Utilities

```yaml
name: nist-ia-password-change-linux
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
    name: nist-ia-password-change-linux
    priority: 2
    metadata:
      nist_control: IA-5
      description: Linux password management utility executed
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - nist-800-53
  - authentication
comment: 'IA-5 — Linux passwd/chage/chpasswd'
```

### IA-2 — NTLM Authentication Tracking

```yaml
name: nist-ia-ntlm-auth
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
    name: nist-ia-ntlm-auth
    priority: 1
    metadata:
      nist_control: IA-2
      description: NTLM credential validation
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-ia-ntlm-auth
tags:
  - nist-800-53
  - authentication
comment: 'IA-2 — NTLM auth tracking. High suppression — noisy in AD.'
```

---

## 9. D&R Rules — System & Information Integrity (SI)

### SI-3 — Malicious Code Protection

#### YARA Detection (All Platforms)

```yaml
name: nist-si-yara-detection
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: nist-si-yara-detection
    priority: 5
    metadata:
      nist_control: SI-3
      description: YARA rule match — possible malware
      mitre_tactic: execution
tags:
  - nist-800-53
  - malware
comment: 'SI-3 — All YARA detections on any platform'
```

#### Defender Threat Detected

```yaml
name: nist-si-defender-threat
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
    name: nist-si-defender-threat
    priority: 4
    metadata:
      nist_control: SI-3
      description: Windows Defender detected or acted on a threat
      mitre_tactic: execution
tags:
  - nist-800-53
  - malware
comment: 'SI-3 — Defender threat alerts (1116, 1117)'
```

### SI-4 — System Monitoring

#### Windows — LOLBin Abuse with Network Indicators

```yaml
name: nist-si-lolbin-execution-windows
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
    name: nist-si-lolbin-execution-windows
    priority: 4
    metadata:
      nist_control: SI-4, CM-7
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
  - nist-800-53
  - integrity
comment: 'SI-4 / CM-7 — Windows LOLBin abuse'
```

#### Windows — Encoded PowerShell

```yaml
name: nist-si-encoded-powershell
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
    name: nist-si-encoded-powershell
    priority: 4
    metadata:
      nist_control: SI-4, SC-18
      description: PowerShell executed with encoded command — common obfuscation
      mitre_attack_id: T1059.001
      mitre_tactic: execution
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 — Encoded PowerShell on Windows'
```

#### Windows — LSASS Access

```yaml
name: nist-si-lsass-access
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
    name: nist-si-lsass-access
    priority: 5
    metadata:
      nist_control: SI-4, SI-4(24)
      description: Sensitive handle to LSASS — possible credential dumping
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-si-lsass-access
tags:
  - nist-800-53
  - integrity
  - credential-access
comment: 'SI-4 — LSASS access (credential dumping)'
```

#### Windows — Suspicious Named Pipe

```yaml
name: nist-si-suspicious-named-pipe
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
    name: nist-si-suspicious-named-pipe
    priority: 4
    metadata:
      nist_control: SI-4, SI-4(24)
      description: Known malicious named pipe pattern — possible C2
      mitre_attack_id: T1570
      mitre_tactic: lateral-movement
tags:
  - nist-800-53
  - integrity
comment: 'SI-4(24) — Known-bad named pipe patterns'
```

#### Windows — Thread Injection

```yaml
name: nist-si-thread-injection
detect:
  event: THREAD_INJECTION
  op: is windows
respond:
  - action: report
    name: nist-si-thread-injection
    priority: 4
    metadata:
      nist_control: SI-4
      description: Thread injection — process injecting code into another
      mitre_attack_id: T1055
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-si-thread-injection
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 — Thread injection detection'
```

#### Linux — LOLBin with Suspicious Arguments

```yaml
name: nist-si-lolbin-execution-linux
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
    name: nist-si-lolbin-execution-linux
    priority: 4
    metadata:
      nist_control: SI-4, CM-7
      description: Linux LOLBin with download-and-execute pattern
      mitre_attack_id: T1059.004
      mitre_tactic: execution
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-si-lolbin-execution-linux
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 / CM-7 — Linux download-and-execute patterns'
```

#### macOS — osascript Network Activity

```yaml
name: nist-si-osascript-network-macos
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
    name: nist-si-osascript-network-macos
    priority: 4
    metadata:
      nist_control: SI-4, CM-7
      description: macOS osascript invoking shell / network
      mitre_attack_id: T1059.002
      mitre_tactic: execution
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 / CM-7 — macOS osascript shell-out'
```

#### All Platforms — CODE_IDENTITY Unsigned Binary

```yaml
name: nist-si-unsigned-binary
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
    name: nist-si-unsigned-binary
    priority: 3
    metadata:
      nist_control: SI-7, SI-4
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
  - nist-800-53
  - integrity
comment: 'SI-7 — Unsigned binary in trusted system path (Win/macOS)'
```

### SI-7 — Integrity Verification

#### FIM Hit (All Platforms)

```yaml
name: nist-si-fim-hit
detect:
  event: FIM_HIT
  op: exists
  path: event/FILE_PATH
respond:
  - action: report
    name: nist-si-fim-hit
    priority: 3
    metadata:
      nist_control: SI-7, SI-7(1), CM-3
      description: File integrity change on monitored path
      mitre_attack_id: T1565
      mitre_tactic: impact
tags:
  - nist-800-53
  - integrity
comment: 'SI-7(1) — FIM hit across all platforms'
```

#### Windows — New Service Installed

```yaml
name: nist-si-new-service-windows
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
    name: nist-si-new-service-windows
    priority: 3
    metadata:
      nist_control: SI-4, CM-5
      description: New Windows service installed
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 / CM-5 — Windows new service (Event ID 7045)'
```

#### Windows — Scheduled Task Created

```yaml
name: nist-si-scheduled-task-windows
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
    name: nist-si-scheduled-task-windows
    priority: 3
    metadata:
      nist_control: SI-4
      description: Scheduled task created
      mitre_attack_id: T1053.005
      mitre_tactic: persistence
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 — Windows scheduled task created (Event ID 4698)'
```

#### Linux — Cron / Systemd Persistence via NEW_PROCESS

```yaml
name: nist-si-cron-modification-linux
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
    name: nist-si-cron-modification-linux
    priority: 3
    metadata:
      nist_control: SI-4, CM-5
      description: Linux persistence mechanism modification (cron, systemd)
      mitre_attack_id: T1053.003
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-si-cron-modification-linux
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 / CM-5 — Linux crontab / systemctl enable'
```

#### macOS — LaunchAgent / LaunchDaemon Changes

```yaml
name: nist-si-launchd-modification-macos
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
    name: nist-si-launchd-modification-macos
    priority: 3
    metadata:
      nist_control: SI-4, CM-5
      description: macOS launchctl load / bootstrap — persistence indicator
      mitre_attack_id: T1543.001
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-si-launchd-modification-macos
tags:
  - nist-800-53
  - integrity
comment: 'SI-4 / CM-5 — macOS launchctl load/bootstrap'
```

---

## 10. D&R Rules — Incident Response (IR)

The Cases extension provides the incident-handling workflow. Rules below illustrate response enrichment for IR-4 / IR-5 / IR-6.

> If ext-cases is set to **all detections** ingestion mode, every `report` action becomes a case automatically. In **tailored** mode (the default for newer orgs), case creation requires detections to meet severity thresholds or rules to explicitly `ingest_detection`.

### IR-4 — Tag Endpoints on Critical Threats

```yaml
name: nist-ir-critical-threat-tag
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: nist-ir-critical-threat-tag
    priority: 5
    metadata:
      nist_control: IR-4, IR-5
      description: YARA detection on endpoint — tagged for case triage
  - action: add tag
    tag: nist-incident
    ttl: 604800
tags:
  - nist-800-53
  - incident-response
comment: 'IR-4 — Tag endpoints on YARA detection (7-day tag for case triage)'
```

### IR-4(2) — Automated Network Isolation (optional / opt-in)

> Network isolation is disruptive. Deploy only with stakeholder approval for well-tuned, high-confidence detections.

```yaml
name: nist-ir-isolate-on-credential-dump
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
    name: nist-ir-isolate-on-credential-dump
    priority: 5
    metadata:
      nist_control: IR-4, IR-4(2)
      description: LSASS access on isolation-enrolled host — automated containment
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
  - action: isolate network
tags:
  - nist-800-53
  - incident-response
comment: 'IR-4(2) — Isolate host on LSASS access. Opt-in via "isolation-enabled" sensor tag.'
```

---

## 11. D&R Rules — Configuration Management (CM)

### CM-3 / CM-5 — Configuration Change Detection

#### Windows — Autorun Changed

```yaml
name: nist-cm-autorun-change-windows
detect:
  event: AUTORUN_CHANGE
  op: is windows
respond:
  - action: report
    name: nist-cm-autorun-change-windows
    priority: 3
    metadata:
      nist_control: CM-3, CM-5
      description: Windows autorun persistence change
      mitre_attack_id: T1547.001
      mitre_tactic: persistence
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-cm-autorun-change-windows
tags:
  - nist-800-53
  - config-management
comment: 'CM-3 / CM-5 — Windows autorun change'
```

#### Windows — Driver Change

```yaml
name: nist-cm-driver-change
detect:
  event: DRIVER_CHANGE
  op: is windows
respond:
  - action: report
    name: nist-cm-driver-change
    priority: 3
    metadata:
      nist_control: CM-3, CM-5
      description: Driver installed or modified
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - nist-800-53
  - config-management
comment: 'CM-3 / CM-5 — Driver change detection'
```

#### Service Change (All Platforms)

```yaml
name: nist-cm-service-change
detect:
  event: SERVICE_CHANGE
  op: exists
  path: event/SVC_NAME
respond:
  - action: report
    name: nist-cm-service-change
    priority: 2
    metadata:
      nist_control: CM-3, CM-5
      description: Service configuration changed
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - nist-cm-service-change
tags:
  - nist-800-53
  - config-management
comment: 'CM-3 / CM-5 — Service change across platforms. Suppressed for patching noise.'
```

#### Windows — Firewall Rule Changed

```yaml
name: nist-cm-firewall-changed-windows
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
    name: nist-cm-firewall-changed-windows
    priority: 3
    metadata:
      nist_control: CM-5, SC-7
      description: Windows Firewall rule or setting changed
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - nist-800-53
  - config-management
comment: 'CM-5 / SC-7 — Windows firewall changes (4946-4950)'
```

#### Linux — iptables / firewalld Changes

```yaml
name: nist-cm-firewall-changed-linux
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
    name: nist-cm-firewall-changed-linux
    priority: 3
    metadata:
      nist_control: CM-5, SC-7
      description: Linux firewall modification (iptables / nft / firewall-cmd / ufw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - nist-800-53
  - config-management
comment: 'CM-5 / SC-7 — Linux firewall changes'
```

#### macOS — pfctl / Firewall Changes

```yaml
name: nist-cm-firewall-changed-macos
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
    name: nist-cm-firewall-changed-macos
    priority: 3
    metadata:
      nist_control: CM-5, SC-7
      description: macOS firewall modification (pfctl / socketfilterfw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - nist-800-53
  - config-management
comment: 'CM-5 / SC-7 — macOS firewall changes'
```

---

## 12. D&R Rules — System & Communications Protection (SC)

### SC-7 — Boundary Protection Detection

#### Outbound Connection to Private-to-Public IP from Unusual Process

```yaml
name: nist-sc-suspicious-outbound
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
    name: nist-sc-suspicious-outbound
    priority: 3
    metadata:
      nist_control: SC-7, SI-4(4)
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
  - nist-800-53
  - boundary
comment: 'SC-7 / SI-4(4) — Outbound from scripting/LOLBin processes'
```

---

## 13. Recommended Extensions

### Required

| Extension | Purpose | NIST Controls |
|---|---|---|
| **Reliable Tasking** | Prerequisite for Artifact Collection. Ensures tasks reach offline sensors. | AU-2, AU-12 (enables WEL/MUL collection) |
| **Artifact Collection (ext-artifact)** | Manages WEL/MUL streaming and file/log retention. | AU-2, AU-3, AU-11, AU-12 |
| **Exfil Control (ext-exfil)** | Manages which event types flow from sensor to cloud. | AU-2, AU-12, SI-4 |
| **Integrity (ext-integrity)** | FIM / RIM rule management. | SI-7, SI-7(1), CM-3 |

### Strongly Recommended

| Extension | Purpose | NIST Controls |
|---|---|---|
| **Cases (ext-cases)** | SOC case management with detection-to-case conversion, SLA tracking, investigation workflows, audit trail. | IR-4, IR-5 |
| **EPP (Endpoint Protection)** | Unified Windows Defender management and event collection. Free. | SI-3 |
| **Soteria EDR Rules** | Managed detection ruleset with MITRE ATT&CK mapping across 14 event types. | SI-4, SI-4(2), SI-4(24) |
| **Sigma Rules** | Community and commercial Sigma rule conversion. | SI-4, SI-4(2), SI-4(24) |

### Recommended for Enhanced Coverage

| Extension | Purpose | NIST Controls |
|---|---|---|
| **Strelka** | File analysis engine (YARA, PE analysis, archive extraction) for files transiting endpoints. | SI-3 |
| **Zeek** | Network monitoring and analysis (Linux sensors). | SI-4(4), SC-7 |
| **Velociraptor** | DFIR hunting and artifact collection for incident response. | IR-4, SI-4(24) |
| **Playbook** | Python-based automation for custom response workflows. | IR-4, IR-6 |
| **ext-git-sync** | Infrastructure as Code — D&R rules, FIM, outputs, extensions managed via git. | CM-3, CM-5, AU-9 |

---

## 14. Deployment Notes

### Retention

- **Low baseline:** Insight default (90 days) is typically sufficient for AU-11.
- **Moderate baseline:** Configure an S3/GCS output for cold archival if the org-defined retention exceeds 90 days.
- **High baseline:** Multi-year cold archival is mandatory.

All artifact collection rules in this doc use `days_retention: 90`. Tune per your retention policy.

### Tagging Strategy

All D&R rules use the `nist-800-53` tag, enabling:

- Filtering detections by compliance source in the Cases UI
- Routing NIST-specific detections to a dedicated output
- Tracking NIST rule coverage separately from operational detections

### Suppression Tuning

Many rules include starting-point suppression. Tune after deployment:

1. Run for a 7-day burn-in period
2. Use `/lc-essentials:fp-pattern-finder` to identify systematic noise
3. Author FP rules for known-safe patterns (service accounts, approved admin tools)

### Windows Audit Policy Prerequisites

Windows endpoints need the **Advanced Audit Policy** configured. Minimum categories:

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

Deploy the auditd rules from Section 3 via Ansible/Puppet/Chef. Verify with `auditctl -l`. Ensure `/var/log/audit/audit.log` rotation is configured to retain at minimum the Insight retention window (default 90 days).

### macOS Audit Policy Prerequisites

macOS Unified Log retention is managed via `log config` policies. Default retention is often shorter than 90 days — validate on a sample endpoint with `log stats --overview`. Adjust predicate patterns (Section 2) to balance visibility with volume.

### Deployment Order

1. Enable **Reliable Tasking**, **Artifact Collection**, **Exfil Control**, **Integrity** extensions
2. Deploy Windows WEL artifact collection rules (Section 1)
3. Deploy macOS MUL artifact collection rules (Section 2)
4. Deploy Linux auditd rules + file adapter or artifact rules (Section 3)
5. Deploy FIM rules per platform (Section 4)
6. Deploy exfil event rules per platform (Section 5)
7. Deploy D&R rules (Sections 6–12) — detections begin firing
8. Enable **Cases (ext-cases)** — detections convert to trackable cases
9. Subscribe to **Soteria** and/or **Sigma** — adds managed detection coverage
10. Burn-in for 7 days, then tune via FP pattern finder

### Validation

Every YAML rule in this document passes `limacharlie dr validate`. For end-to-end validation against historical telemetry, use `limacharlie dr replay` against recent data from representative endpoints (one Windows, one Linux, one macOS).
