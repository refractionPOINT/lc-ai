# ISO/IEC 27001:2022 Compliance Implementation Guide — LimaCharlie

Concrete D&R rules, artifact collection rules, FIM rules, and extension recommendations to satisfy ISO/IEC 27001:2022 Annex A controls (derived from ISO/IEC 27002:2022) using LimaCharlie EDR on Windows, Linux, and macOS endpoints.

Companion to [iso-27001-limacharlie-mapping.md](iso-27001-limacharlie-mapping.md), which maps Annex A controls to LimaCharlie capabilities at a conceptual level. This document provides the deployable configuration.

All D&R rule syntax in this document has been validated against `limacharlie dr validate`. Event-to-platform coverage reflects actual sensor capability (per the LC EDR events reference), not documentation aspirations.

Rule naming convention: `iso-<control-id>-<desc>` (e.g., `iso-8-15-failed-logon-windows`). All rules carry the `iso-27001` tag plus one or more category tags. Metadata includes `iso_27001_control: 'A.8.15'` for compliance-report filtering.

---

## Table of Contents

1. [Windows Event Log Artifact Collection Rules](#1-windows-event-log-artifact-collection-rules)
2. [macOS Unified Log Artifact Collection Rules](#2-macos-unified-log-artifact-collection-rules)
3. [Linux Audit Log Collection](#3-linux-audit-log-collection)
4. [File Integrity Monitoring (FIM) Rules](#4-file-integrity-monitoring-fim-rules)
5. [Exfil Event Collection Rules](#5-exfil-event-collection-rules)
6. [D&R Rules — A.8.15 Logging / A.8.16 Monitoring](#6-dr-rules--a815-logging--a816-monitoring)
7. [D&R Rules — A.8.2 Privileged Access / A.8.5 Secure Authentication](#7-dr-rules--a82-privileged-access--a85-secure-authentication)
8. [D&R Rules — A.8.7 Protection Against Malware](#8-dr-rules--a87-protection-against-malware)
9. [D&R Rules — A.8.9 Configuration Management / A.8.32 Change Management](#9-dr-rules--a89-configuration-management--a832-change-management)
10. [D&R Rules — A.8.10 Information Deletion / A.8.12 Data Leakage Prevention](#10-dr-rules--a810-information-deletion--a812-data-leakage-prevention)
11. [D&R Rules — A.8.17 Clock Synchronization](#11-dr-rules--a817-clock-synchronization)
12. [D&R Rules — A.8.18 Privileged Utility Programs / A.8.19 Installation of Software](#12-dr-rules--a818-privileged-utility-programs--a819-installation-of-software)
13. [D&R Rules — A.8.20 Network Security / A.8.22 Segregation / A.8.23 Web Filtering](#13-dr-rules--a820-network-security--a822-segregation--a823-web-filtering)
14. [D&R Rules — A.5.24–A.5.28 Incident Management](#14-dr-rules--a524a528-incident-management)
15. [Recommended Extensions](#15-recommended-extensions)
16. [Deployment Notes](#16-deployment-notes)

---

## 1. Windows Event Log Artifact Collection Rules

The `wel://` pattern streams Windows Event Logs as first-class `WEL` telemetry — preferred over `.evtx` file collection because events are evaluated by D&R rules in real time.

> **Prerequisite:** The **Reliable Tasking** and **Artifact Collection** extensions must be enabled.

Rule map entries are added to `ext-artifact` configuration (web UI Artifact Collection section, `limacharlie extension config-set --name ext-artifact`, or ext-git-sync).

### Security Log

```yaml
iso-wel-security:
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

| Event ID | Category | ISO 27001 Control |
|---|---|---|
| 4624 | Successful logon | A.8.15, A.8.5 |
| 4625 | Failed logon | A.8.15, A.8.5 |
| 4634 | Logoff | A.8.15 |
| 4647 | User-initiated logoff | A.8.15 |
| 4648 | Logon with explicit credentials | A.8.15, A.8.2 |
| 4672 | Special privileges assigned to new logon | A.8.2 |
| 4673 | Privileged service called | A.8.2 |
| 4674 | Operation attempted on privileged object | A.8.2 |
| 4688 | Process creation (if audit enabled) | A.8.15 |
| 4689 | Process termination | A.8.15 |
| 4697 | Service installed on the system | A.8.9, A.8.16 |
| 4698 | Scheduled task created | A.8.16 |
| 4699 | Scheduled task deleted | A.8.9 |
| 4700 | Scheduled task enabled | A.8.16 |
| 4701 | Scheduled task disabled | A.8.9 |
| 4719 | Audit policy changed | A.8.15, A.8.9 |
| 4720 | User account created | A.8.2 |
| 4722 | User account enabled | A.8.2 |
| 4723 | Password change attempted | A.8.5 |
| 4724 | Password reset attempted | A.8.5 |
| 4725 | User account disabled | A.8.2 |
| 4726 | User account deleted | A.8.2 |
| 4728 | Member added to security-enabled global group | A.8.2 |
| 4732 | Member added to security-enabled local group | A.8.2 |
| 4735 | Security-enabled local group changed | A.8.2 |
| 4738 | User account changed | A.8.2 |
| 4740 | User account locked out | A.8.5 |
| 4756 | Member added to universal security group | A.8.2 |
| 4767 | User account unlocked | A.8.2 |
| 4776 | Credential validation (NTLM) | A.8.5 |
| 4946 | Firewall rule added | A.8.9, A.8.20 |
| 4947 | Firewall rule modified | A.8.9, A.8.20 |
| 4948 | Firewall rule deleted | A.8.9, A.8.20 |
| 4950 | Firewall setting changed | A.8.9, A.8.20 |
| 1102 | Security log cleared | A.8.15 |

### System Log

```yaml
iso-wel-system:
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
iso-wel-powershell:
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
iso-wel-sysmon:
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
iso-wel-defender:
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
iso-wel-taskscheduler:
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
iso-wel-firewall:
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

> **Field path verification:** D&R rules in Sections 6+ that match `MUL` events use field paths based on macOS `log` command keys (`eventMessage`, `processImagePath`, `subsystem`). Verify the exact field paths against your first few `MUL` events in Timeline after deployment — the sensor may flatten or re-key some fields. Adjust `path:` values accordingly.

### Authentication & Authorization

```yaml
iso-mul-auth:
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

Covers: A.8.5 (authentication failures), A.8.2 (authorization decisions).

### Login & Session Events

```yaml
iso-mul-sessions:
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
iso-mul-system:
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

Covers: A.8.9 (configuration management), A.8.32 (change management).

### Privilege Escalation

```yaml
iso-mul-privilege:
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

Covers: A.8.2 (privileged access rights), A.8.18 (privileged utilities).

---

## 3. Linux Audit Log Collection

The LC Linux EDR sensor does **not** emit `USER_LOGIN` / `SSH_LOGIN` events. Linux authentication telemetry requires one of the three approaches below.

### Option A — Artifact Collection (Retention, Not Streaming)

Use when compliance requires **retention** of the raw auth log but real-time detection is not needed:

```yaml
iso-artifact-authlog:
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

### Option C — Auditd Rules (Recommended for Stricter ISMS Postures)

Deploy auditd rules on Linux endpoints (via configuration management). Then collect `/var/log/audit/audit.log` via file adapter or artifact collection using the same approach as Options A/B.

Minimum auditd rules aligned to the Annex A technological controls:

```
# /etc/audit/rules.d/iso-27001.rules

# A.8.2 Privileged access / A.8.5 Secure authentication — identity changes
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k identity
-w /etc/sudoers.d/ -p wa -k identity

# A.8.5 Secure authentication config
-w /etc/pam.d/ -p wa -k auth-config
-w /etc/ssh/sshd_config -p wa -k sshd-config

# A.8.2 Privilege escalation
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation
-a always,exit -F arch=b32 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation

# A.8.17 Clock synchronization
-a always,exit -F arch=b64 -S settimeofday,clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# A.8.15 Logging — audit subsystem integrity
-w /etc/audit/ -p wa -k audit-config
-w /etc/libaudit.conf -p wa -k audit-config
-e 2
```

Deploy via Ansible, Puppet, or similar; verify with `auditctl -l`.

---

## 4. File Integrity Monitoring (FIM) Rules

FIM generates `FIM_HIT` events on monitored files, directories, and Windows registry keys across all three platforms. Supports A.8.9 (configuration management), A.8.15 (log protection), A.8.32 (change management), and A.5.28 (evidence collection).

> Linux FIM works with `inotify` (active monitoring) or eBPF (on supported kernels). Windows and macOS use passive kernel monitoring.

### Windows

```yaml
iso-fim-windows-system:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\drivers\etc\hosts
    - ?:\Windows\System32\config\SAM
    - ?:\Windows\System32\config\SYSTEM
    - ?:\Windows\System32\config\SECURITY

iso-fim-windows-boot:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\boot\bcd
    - ?:\Windows\System32\boot\winload.exe

iso-fim-windows-grouppolicy:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\GroupPolicy\*
    - ?:\Windows\SYSVOL\*

iso-fim-windows-powershell-profiles:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    - ?:\Users\*\Documents\WindowsPowerShell\profile.ps1

iso-fim-windows-registry-persistence:
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
iso-fim-linux-identity:
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

iso-fim-linux-auth:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/pam.d/*
    - /etc/ssh/sshd_config
    - /etc/ssh/ssh_config
    - /etc/security/*

iso-fim-linux-ssh-keys:
  filters:
    platforms:
      - linux
  patterns:
    - /root/.ssh/authorized_keys
    - /root/.ssh/*
    - /home/*/.ssh/*

iso-fim-linux-persistence:
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

iso-fim-linux-boot:
  filters:
    platforms:
      - linux
  patterns:
    - /boot/grub/grub.cfg
    - /boot/grub2/grub.cfg
    - /etc/default/grub
    - /etc/fstab

iso-fim-linux-audit:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/audit/*
    - /etc/libaudit.conf
```

### macOS

```yaml
iso-fim-macos-identity:
  filters:
    platforms:
      - macos
  patterns:
    - /etc/sudoers
    - /etc/sudoers.d/*
    - /etc/pam.d/*

iso-fim-macos-ssh-keys:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/.ssh/*
    - /var/root/.ssh/*

iso-fim-macos-launch-daemons:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/LaunchDaemons/*
    - /Library/LaunchAgents/*
    - /System/Library/LaunchDaemons/*
    - /System/Library/LaunchAgents/*
    - /Users/*/Library/LaunchAgents/*

iso-fim-macos-keychains:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/Library/Keychains/*
    - /Library/Keychains/*

iso-fim-macos-boot:
  filters:
    platforms:
      - macos
  patterns:
    - /System/Library/CoreServices/boot.efi
    - /Library/Preferences/SystemConfiguration/*

iso-fim-macos-kernel-extensions:
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
iso-windows-events:
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
iso-linux-events:
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
iso-macos-events:
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

## 6. D&R Rules — A.8.15 Logging / A.8.16 Monitoring

### A.8.15 / A.8.5 — Failed Logon (Windows)

```yaml
name: iso-8-15-failed-logon-windows
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
    name: iso-8-15-failed-logon-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.15
      description: Failed logon attempt (Windows Security 4625)
      mitre_attack_id: T1078
      mitre_tactic: initial-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-15-failed-logon-windows
tags:
  - iso-27001
  - logging
comment: 'A.8.15 / A.8.5 — Windows failed logon (Event ID 4625)'
```

### A.8.16 / A.8.5 — Brute-Force Threshold (Windows)

```yaml
name: iso-8-16-brute-force-windows
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
    name: iso-8-16-brute-force-windows
    priority: 4
    metadata:
      iso_27001_control: A.8.16
      description: Possible brute force — 10+ failed logons within 10 min
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      min_count: 10
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-16-brute-force-windows
tags:
  - iso-27001
  - monitoring
comment: 'A.8.16 / A.8.5 — Threshold-based brute force on Windows'
```

### A.8.15 / A.8.5 — Failed Authentication (macOS)

The native `SSH_LOGIN` event fires only on successful login and has no failure field. Failed SSH / authentication attempts on macOS must be collected from the Unified Log. Deploy the `iso-mul-auth` artifact rule (Section 2), then match the MUL stream:

```yaml
name: iso-8-15-failed-auth-macos
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
    name: iso-8-15-failed-auth-macos
    priority: 3
    metadata:
      iso_27001_control: A.8.15
      description: Authentication failure logged to macOS Unified Log
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-15-failed-auth-macos
tags:
  - iso-27001
  - logging
comment: 'A.8.15 / A.8.5 — macOS authentication failures from Unified Log. Requires iso-mul-auth (Section 2).'
```

### A.8.15 — Log Tampering: Audit Policy Changed (Windows)

```yaml
name: iso-8-15-audit-policy-changed
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
    name: iso-8-15-audit-policy-changed
    priority: 5
    metadata:
      iso_27001_control: A.8.15
      description: Audit policy changed — potential tampering with logging
      mitre_attack_id: T1562.002
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - logging
comment: 'A.8.15 — Windows audit policy change (Event ID 4719)'
```

### A.8.15 — Log Tampering: Security Event Log Cleared (Windows)

```yaml
name: iso-8-15-event-log-cleared
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
    name: iso-8-15-event-log-cleared
    priority: 5
    metadata:
      iso_27001_control: A.8.15
      description: Security event log was cleared — strong tampering indicator
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: iso-log-tamper
    ttl: 86400
tags:
  - iso-27001
  - logging
comment: 'A.8.15 — Security log clearing (Event ID 1102)'
```

### A.8.15 — Log Tampering: Event Log Service Stopped (Windows)

```yaml
name: iso-8-15-eventlog-service-stop-windows
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
    name: iso-8-15-eventlog-service-stop-windows
    priority: 5
    metadata:
      iso_27001_control: A.8.15
      description: Attempt to stop event log service or clear event logs
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: iso-log-tamper
    ttl: 86400
tags:
  - iso-27001
  - logging
comment: 'A.8.15 — Attempt to tamper with Windows event logging'
```

### A.8.15 — Log Tampering: Auditd (Linux)

```yaml
name: iso-8-15-auditd-tamper-linux
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
    name: iso-8-15-auditd-tamper-linux
    priority: 5
    metadata:
      iso_27001_control: A.8.15
      description: Attempt to stop or disable Linux auditd
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: iso-log-tamper
    ttl: 86400
tags:
  - iso-27001
  - logging
comment: 'A.8.15 — Linux auditd service tampering'
```

### A.8.15 — Log Tampering: Unified Log (macOS)

```yaml
name: iso-8-15-log-tamper-macos
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
    name: iso-8-15-log-tamper-macos
    priority: 5
    metadata:
      iso_27001_control: A.8.15
      description: Attempt to erase or disable macOS unified log
      mitre_attack_id: T1070
      mitre_tactic: defense-evasion
  - action: add tag
    tag: iso-log-tamper
    ttl: 86400
tags:
  - iso-27001
  - logging
comment: 'A.8.15 — macOS log erase / disable'
```

---

## 7. D&R Rules — A.8.2 Privileged Access / A.8.5 Secure Authentication

### A.8.2 — User Account Created (Windows)

```yaml
name: iso-8-2-user-created-windows
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
    name: iso-8-2-user-created-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.2
      description: New Windows user account created
      mitre_attack_id: T1136.001
      mitre_tactic: persistence
tags:
  - iso-27001
  - access-control
comment: 'A.8.2 — Windows local user creation (Event ID 4720)'
```

### A.8.2 — User Added to Privileged Group (Windows)

```yaml
name: iso-8-2-user-added-to-group-windows
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
    name: iso-8-2-user-added-to-group-windows
    priority: 4
    metadata:
      iso_27001_control: A.8.2
      description: User added to a Windows security-enabled group
      mitre_attack_id: T1098
      mitre_tactic: persistence
tags:
  - iso-27001
  - access-control
comment: 'A.8.2 — Windows group membership addition (4728, 4732, 4756)'
```

### A.8.2 — User Account Deleted (Windows)

```yaml
name: iso-8-2-user-deleted-windows
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
    name: iso-8-2-user-deleted-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.2
      description: Windows user account deleted
tags:
  - iso-27001
  - access-control
comment: 'A.8.2 — Windows user deletion (Event ID 4726)'
```

### A.8.2 — Account Management (Linux)

```yaml
name: iso-8-2-user-mgmt-linux
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
    name: iso-8-2-user-mgmt-linux
    priority: 3
    metadata:
      iso_27001_control: A.8.2
      description: Linux account management binary executed
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - iso-27001
  - access-control
comment: 'A.8.2 — Linux user/group management (useradd, usermod, groupadd, ...)'
```

### A.8.2 — Account Management via dscl (macOS)

```yaml
name: iso-8-2-user-mgmt-macos
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
    name: iso-8-2-user-mgmt-macos
    priority: 3
    metadata:
      iso_27001_control: A.8.2
      description: macOS account management invocation (dscl / sysadminctl)
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - iso-27001
  - access-control
comment: 'A.8.2 — macOS account management via dscl, sysadminctl, dsimport'
```

### A.8.2 — Special Privileges Assigned (Windows)

```yaml
name: iso-8-2-special-privilege-logon
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
    name: iso-8-2-special-privilege-logon
    priority: 2
    metadata:
      iso_27001_control: A.8.2
      description: Special privileges assigned to new logon session
      mitre_attack_id: T1078
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-2-special-privilege-logon
tags:
  - iso-27001
  - access-control
comment: 'A.8.2 — Windows special privilege assignment (Event ID 4672)'
```

### A.8.2 — Privileged Service Called (Windows)

```yaml
name: iso-8-2-privileged-service-windows
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
    name: iso-8-2-privileged-service-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.2
      description: Privileged service or object operation
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-2-privileged-service-windows
tags:
  - iso-27001
  - access-control
comment: 'A.8.2 — Windows privileged service call (4673, 4674)'
```

### A.8.2 — sudo / su / pkexec (Linux)

```yaml
name: iso-8-2-privilege-escalation-linux
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
    name: iso-8-2-privilege-escalation-linux
    priority: 2
    metadata:
      iso_27001_control: A.8.2
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
  - iso-27001
  - access-control
comment: 'A.8.2 — Linux sudo/su/pkexec/doas. Suppressed per-user per-hour.'
```

### A.8.2 — sudo Execution (macOS)

```yaml
name: iso-8-2-sudo-macos
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
    name: iso-8-2-sudo-macos
    priority: 2
    metadata:
      iso_27001_control: A.8.2
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
  - iso-27001
  - access-control
comment: 'A.8.2 — macOS sudo execution'
```

### A.8.5 — Account Lockout (Windows)

```yaml
name: iso-8-5-account-lockout-windows
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
    name: iso-8-5-account-lockout-windows
    priority: 4
    metadata:
      iso_27001_control: A.8.5
      description: Windows account locked due to failed logons
      mitre_attack_id: T1110
      mitre_tactic: credential-access
tags:
  - iso-27001
  - authentication
comment: 'A.8.5 — Windows account lockout (Event ID 4740)'
```

### A.8.5 — Password Change / Reset (Windows)

```yaml
name: iso-8-5-password-change-windows
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
    name: iso-8-5-password-change-windows
    priority: 2
    metadata:
      iso_27001_control: A.8.5
      description: Windows password change or reset attempted
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-5-password-change-windows
tags:
  - iso-27001
  - authentication
comment: 'A.8.5 — Windows password change (4723) / reset (4724)'
```

### A.8.5 — Password Utilities (Linux)

```yaml
name: iso-8-5-password-change-linux
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
    name: iso-8-5-password-change-linux
    priority: 2
    metadata:
      iso_27001_control: A.8.5
      description: Linux password management utility executed
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - iso-27001
  - authentication
comment: 'A.8.5 — Linux passwd/chage/chpasswd'
```

### A.8.5 — NTLM Authentication Tracking (Windows)

```yaml
name: iso-8-5-ntlm-auth
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
    name: iso-8-5-ntlm-auth
    priority: 1
    metadata:
      iso_27001_control: A.8.5
      description: NTLM credential validation
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-5-ntlm-auth
tags:
  - iso-27001
  - authentication
comment: 'A.8.5 — NTLM auth tracking. High suppression — noisy in AD.'
```

### A.8.5 — Remote Desktop Logon (Windows)

```yaml
name: iso-8-5-rdp-logon
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
    name: iso-8-5-rdp-logon
    priority: 2
    metadata:
      iso_27001_control: A.8.5
      description: Remote Desktop logon (LogonType 10)
      mitre_attack_id: T1021.001
      mitre_tactic: lateral-movement
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-5-rdp-logon
tags:
  - iso-27001
  - authentication
comment: 'A.8.5 — Windows RDP logon'
```

### A.8.5 — SSH Login (macOS)

```yaml
name: iso-8-5-ssh-login-macos
detect:
  event: SSH_LOGIN
  op: is mac
respond:
  - action: report
    name: iso-8-5-ssh-login-macos
    priority: 2
    metadata:
      iso_27001_control: A.8.5
      description: macOS SSH session established
      mitre_attack_id: T1021.004
      mitre_tactic: lateral-movement
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-5-ssh-login-macos
tags:
  - iso-27001
  - authentication
comment: 'A.8.5 — macOS SSH login (SSH_LOGIN fires on success only; see iso-8-15-failed-auth-macos for failures)'
```

---

## 8. D&R Rules — A.8.7 Protection Against Malware

### A.8.7 — YARA Detection (All Platforms)

```yaml
name: iso-8-7-yara-detection
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: iso-8-7-yara-detection
    priority: 5
    metadata:
      iso_27001_control: A.8.7
      description: YARA rule match — possible malware
      mitre_tactic: execution
tags:
  - iso-27001
  - malware
comment: 'A.8.7 — All YARA detections on any platform'
```

### A.8.7 — Defender Threat Detected (Windows)

```yaml
name: iso-8-7-defender-threat
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
    name: iso-8-7-defender-threat
    priority: 4
    metadata:
      iso_27001_control: A.8.7
      description: Windows Defender detected or acted on a threat
      mitre_tactic: execution
tags:
  - iso-27001
  - malware
comment: 'A.8.7 — Defender threat alerts (1116, 1117)'
```

### A.8.7 — Defender Real-Time Protection Disabled (Windows)

```yaml
name: iso-8-7-defender-rtp-disabled
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
    name: iso-8-7-defender-rtp-disabled
    priority: 5
    metadata:
      iso_27001_control: A.8.7
      description: Windows Defender real-time protection disabled
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - malware
  - defense-evasion
comment: 'A.8.7 — Defender RTP disabled (Event ID 5001)'
```

### A.8.7 — LSASS Access (Windows)

```yaml
name: iso-8-7-lsass-access
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
    name: iso-8-7-lsass-access
    priority: 5
    metadata:
      iso_27001_control: A.8.7
      description: Sensitive handle to LSASS — possible credential dumping
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-7-lsass-access
tags:
  - iso-27001
  - malware
  - credential-access
comment: 'A.8.7 — LSASS access (credential dumping)'
```

### A.8.7 — Thread Injection (Windows)

```yaml
name: iso-8-7-thread-injection
detect:
  event: THREAD_INJECTION
  op: is windows
respond:
  - action: report
    name: iso-8-7-thread-injection
    priority: 4
    metadata:
      iso_27001_control: A.8.7
      description: Thread injection — process injecting code into another
      mitre_attack_id: T1055
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-7-thread-injection
tags:
  - iso-27001
  - malware
comment: 'A.8.7 — Thread injection detection'
```

### A.8.7 — Suspicious Named Pipe (Windows)

```yaml
name: iso-8-7-suspicious-named-pipe
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
    name: iso-8-7-suspicious-named-pipe
    priority: 4
    metadata:
      iso_27001_control: A.8.7
      description: Known malicious named pipe pattern — possible C2
      mitre_attack_id: T1570
      mitre_tactic: lateral-movement
tags:
  - iso-27001
  - malware
comment: 'A.8.7 — Known-bad named pipe patterns'
```

### A.8.7 — Unsigned Binary in System Path (Windows / macOS)

```yaml
name: iso-8-7-unsigned-binary
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
    name: iso-8-7-unsigned-binary
    priority: 3
    metadata:
      iso_27001_control: A.8.7
      description: Unsigned binary loaded from a trusted system path
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
  - iso-27001
  - malware
comment: 'A.8.7 — Unsigned binary in trusted system path (Win/macOS)'
```

---

## 9. D&R Rules — A.8.9 Configuration Management / A.8.32 Change Management

### A.8.9 — FIM Hit (All Platforms)

```yaml
name: iso-8-9-fim-hit
detect:
  event: FIM_HIT
  op: exists
  path: event/FILE_PATH
respond:
  - action: report
    name: iso-8-9-fim-hit
    priority: 3
    metadata:
      iso_27001_control: A.8.9
      description: File integrity change on monitored path
      mitre_attack_id: T1565
      mitre_tactic: impact
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 / A.8.32 — FIM hit across all platforms'
```

### A.8.9 — Autorun Changed (Windows)

```yaml
name: iso-8-9-autorun-change-windows
detect:
  event: AUTORUN_CHANGE
  op: is windows
respond:
  - action: report
    name: iso-8-9-autorun-change-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.9
      description: Windows autorun persistence change
      mitre_attack_id: T1547.001
      mitre_tactic: persistence
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-9-autorun-change-windows
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 — Windows autorun change'
```

### A.8.9 — Driver Change (Windows)

```yaml
name: iso-8-9-driver-change
detect:
  event: DRIVER_CHANGE
  op: is windows
respond:
  - action: report
    name: iso-8-9-driver-change
    priority: 3
    metadata:
      iso_27001_control: A.8.9
      description: Driver installed or modified
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 — Driver change detection'
```

### A.8.9 — Service Change (All Platforms)

```yaml
name: iso-8-9-service-change
detect:
  event: SERVICE_CHANGE
  op: exists
  path: event/SVC_NAME
respond:
  - action: report
    name: iso-8-9-service-change
    priority: 2
    metadata:
      iso_27001_control: A.8.9
      description: Service configuration changed
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-9-service-change
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 — Service change across platforms. Suppressed for patching noise.'
```

### A.8.9 — New Service Installed (Windows)

```yaml
name: iso-8-9-new-service-windows
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
    name: iso-8-9-new-service-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.9
      description: New Windows service installed
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 — Windows new service (Event ID 7045)'
```

### A.8.9 — Scheduled Task Created (Windows)

```yaml
name: iso-8-9-scheduled-task-windows
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
    name: iso-8-9-scheduled-task-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.9
      description: Scheduled task created
      mitre_attack_id: T1053.005
      mitre_tactic: persistence
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 — Windows scheduled task created (Event ID 4698)'
```

### A.8.9 — Cron / Systemd Modification (Linux)

```yaml
name: iso-8-9-cron-modification-linux
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
    name: iso-8-9-cron-modification-linux
    priority: 3
    metadata:
      iso_27001_control: A.8.9
      description: Linux persistence mechanism modification (cron, systemd)
      mitre_attack_id: T1053.003
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-9-cron-modification-linux
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 — Linux crontab / systemctl enable'
```

### A.8.9 — LaunchAgent / LaunchDaemon Changes (macOS)

```yaml
name: iso-8-9-launchd-modification-macos
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
    name: iso-8-9-launchd-modification-macos
    priority: 3
    metadata:
      iso_27001_control: A.8.9
      description: macOS launchctl load / bootstrap — persistence indicator
      mitre_attack_id: T1543.001
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-9-launchd-modification-macos
tags:
  - iso-27001
  - configuration
comment: 'A.8.9 — macOS launchctl load/bootstrap'
```

---

## 10. D&R Rules — A.8.10 Information Deletion / A.8.12 Data Leakage Prevention

### A.8.10 — Secure-Deletion Utility Invocation (All Platforms)

Secure-deletion utilities are legitimate for data hygiene **and** used by adversaries to remove evidence. Alerting provides evidence of both and enables review against change-management tickets.

```yaml
name: iso-8-10-secure-delete-tool
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: or
      rules:
        - op: and
          rules:
            - op: is windows
            - op: or
              rules:
                - op: matches
                  path: event/FILE_PATH
                  re: '(?i)\\(sdelete|cipher)\.exe$'
                - op: matches
                  path: event/COMMAND_LINE
                  re: '(?i)cipher\s+.*/w:'
        - op: and
          rules:
            - op: is linux
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/(shred|wipe)$'
        - op: and
          rules:
            - op: is mac
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\brm\s+-[rfRP]*P[rfRP]*\b'
respond:
  - action: report
    name: iso-8-10-secure-delete-tool
    priority: 3
    metadata:
      iso_27001_control: A.8.10
      description: Secure-deletion utility invoked (sdelete / cipher /w / shred / rm -P)
      mitre_attack_id: T1070.004
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - deletion
comment: 'A.8.10 — Secure-delete invocation. Expected during media retirement; alert enables review against change ticket.'
```

### A.8.10 — Mass File Deletion (Windows / macOS)

```yaml
name: iso-8-10-mass-file-delete
detect:
  event: FILE_DELETE
  op: and
  rules:
    - op: or
      rules:
        - op: is windows
        - op: is mac
respond:
  - action: report
    name: iso-8-10-mass-file-delete
    priority: 3
    metadata:
      iso_27001_control: A.8.10
      description: High-volume file deletion — possible destructive activity or mass cleanup
      mitre_attack_id: T1485
      mitre_tactic: impact
    suppression:
      min_count: 100
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-10-mass-file-delete
tags:
  - iso-27001
  - deletion
comment: 'A.8.10 — 100+ file deletions in 5 min on Win/macOS'
```

### A.8.12 — Removable Media Mount (Windows / macOS)

```yaml
name: iso-8-12-removable-media-mount
detect:
  event: VOLUME_MOUNT
  op: and
  rules:
    - op: or
      rules:
        - op: is windows
        - op: is mac
respond:
  - action: report
    name: iso-8-12-removable-media-mount
    priority: 3
    metadata:
      iso_27001_control: A.8.12
      description: Removable-media volume mounted — possible data exfiltration vector
      mitre_attack_id: T1052.001
      mitre_tactic: exfiltration
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-12-removable-media-mount
tags:
  - iso-27001
  - dlp
comment: 'A.8.12 — USB / removable-media mount on Win/macOS (Linux not supported by VOLUME_MOUNT).'
```

### A.8.12 — DNS Exfiltration (Long Subdomains)

```yaml
name: iso-8-12-dns-exfil
detect:
  event: DNS_REQUEST
  op: matches
  path: event/DOMAIN_NAME
  re: '^[a-z0-9+/=]{50,}\.'
respond:
  - action: report
    name: iso-8-12-dns-exfil
    priority: 4
    metadata:
      iso_27001_control: A.8.12
      description: DNS query with long encoded subdomain — possible DNS exfiltration
      mitre_attack_id: T1048.003
      mitre_tactic: exfiltration
    suppression:
      max_count: 5
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-12-dns-exfil
tags:
  - iso-27001
  - dlp
comment: 'A.8.12 — DNS exfil pattern (subdomain ≥50 chars, base64-alphabet).'
```

### A.8.12 — Cloud-Storage CLI Upload (All Platforms)

```yaml
name: iso-8-12-cloud-upload-cli
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: or
      rules:
        - op: matches
          path: event/FILE_PATH
          re: '(?i)\\(aws|az|gcloud|gsutil|rclone|mega(cmd|put))\.exe$'
        - op: matches
          path: event/FILE_PATH
          re: '(?i)/(aws|az|gcloud|gsutil|rclone|megaput|megacmd)$'
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\b(s3\s+cp|s3\s+sync|storage\s+cp|copy|upload|put-object|put\s+)'
respond:
  - action: report
    name: iso-8-12-cloud-upload-cli
    priority: 3
    metadata:
      iso_27001_control: A.8.12
      description: Cloud-storage CLI upload command — possible data exfiltration
      mitre_attack_id: T1567.002
      mitre_tactic: exfiltration
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-12-cloud-upload-cli
tags:
  - iso-27001
  - dlp
comment: 'A.8.12 — aws/az/gcloud/rclone upload commands. Whitelist via FP rules for authorized backup paths.'
```

---

## 11. D&R Rules — A.8.17 Clock Synchronization

### A.8.17 — Time-Source Change (All Platforms)

```yaml
name: iso-8-17-time-source-change
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
              re: '(?i)\\w32tm\.exe$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)/config\s'
        - op: and
          rules:
            - op: is linux
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/(ntpdate|timedatectl|chronyc|hwclock)$'
        - op: and
          rules:
            - op: is mac
            - op: matches
              path: event/FILE_PATH
              re: '(?i)/usr/sbin/systemsetup$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)-set(networktimeserver|usingnetworktime)'
respond:
  - action: report
    name: iso-8-17-time-source-change
    priority: 3
    metadata:
      iso_27001_control: A.8.17
      description: System time source or clock configuration modified
      mitre_attack_id: T1070.006
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - time-sync
comment: 'A.8.17 — Time-source configuration change. Validate against change ticket.'
```

---

## 12. D&R Rules — A.8.18 Privileged Utility Programs / A.8.19 Installation of Software

### A.8.18 — High-Risk Privileged Utility (Windows)

```yaml
name: iso-8-18-privileged-util-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(psexec|procdump|procexp|sdelete|fsutil|bcdedit|takeown|cipher)\.exe$'
respond:
  - action: report
    name: iso-8-18-privileged-util-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.18
      description: High-risk Windows privileged utility executed
      mitre_attack_id: T1569
      mitre_tactic: execution
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.FILE_PATH }}'
tags:
  - iso-27001
  - privileged-utility
comment: 'A.8.18 — Windows Sysinternals / system utilities with override potential.'
```

### A.8.18 — High-Risk Privileged Utility (Linux)

```yaml
name: iso-8-18-privileged-util-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(strace|ltrace|gdb|nmap|tcpdump|socat|dd|shred)$'
respond:
  - action: report
    name: iso-8-18-privileged-util-linux
    priority: 3
    metadata:
      iso_27001_control: A.8.18
      description: High-risk Linux privileged utility executed
      mitre_attack_id: T1059
      mitre_tactic: execution
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.FILE_PATH }}'
tags:
  - iso-27001
  - privileged-utility
comment: 'A.8.18 — Linux debug/network/system utilities.'
```

### A.8.18 — High-Risk Privileged Utility (macOS)

```yaml
name: iso-8-18-privileged-util-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(dtruss|csrutil|spctl|nvram|pfctl)$'
respond:
  - action: report
    name: iso-8-18-privileged-util-macos
    priority: 3
    metadata:
      iso_27001_control: A.8.18
      description: High-risk macOS privileged utility executed
      mitre_attack_id: T1562
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.FILE_PATH }}'
tags:
  - iso-27001
  - privileged-utility
comment: 'A.8.18 — macOS system-integrity / network utilities.'
```

### A.8.19 — MSI Install from User-Writable Path (Windows)

```yaml
name: iso-8-19-msi-install-user-path
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\msiexec\.exe$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)/i\s+.*(\\users\\|\\appdata\\|\\temp\\|\\programdata\\)'
respond:
  - action: report
    name: iso-8-19-msi-install-user-path
    priority: 4
    metadata:
      iso_27001_control: A.8.19
      description: MSI installation from user-writable path — possible unauthorized install
      mitre_attack_id: T1218.007
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - software-install
comment: 'A.8.19 — msiexec /i from user temp/appdata/programdata.'
```

### A.8.19 — Package Manager Invocation (Linux)

```yaml
name: iso-8-19-package-install-linux
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
              re: '(?i)/(apt|apt-get|dnf|yum|zypper|pacman)$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\b(install|upgrade|update)\b'
        - op: matches
          path: event/FILE_PATH
          re: '(?i)/dpkg$'
respond:
  - action: report
    name: iso-8-19-package-install-linux
    priority: 2
    metadata:
      iso_27001_control: A.8.19
      description: Linux package install/upgrade command
      mitre_tactic: execution
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-19-package-install-linux
tags:
  - iso-27001
  - software-install
comment: 'A.8.19 — apt/dnf/yum install. Correlate with change-management tickets.'
```

### A.8.19 — Homebrew / pkg Install (macOS)

```yaml
name: iso-8-19-package-install-macos
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
              re: '(?i)/(brew|port)$'
            - op: matches
              path: event/COMMAND_LINE
              re: '(?i)\b(install|upgrade|cask\s+install)\b'
        - op: matches
          path: event/FILE_PATH
          re: '(?i)/usr/sbin/installer$'
respond:
  - action: report
    name: iso-8-19-package-install-macos
    priority: 2
    metadata:
      iso_27001_control: A.8.19
      description: macOS package install (brew / port / installer)
      mitre_tactic: execution
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-19-package-install-macos
tags:
  - iso-27001
  - software-install
comment: 'A.8.19 — macOS brew/port/installer invocations.'
```

---

## 13. D&R Rules — A.8.20 Network Security / A.8.22 Segregation / A.8.23 Web Filtering

### A.8.20 — Suspicious Outbound from Scripting Interpreters

```yaml
name: iso-8-20-suspicious-outbound
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
    name: iso-8-20-suspicious-outbound
    priority: 3
    metadata:
      iso_27001_control: A.8.20
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
  - iso-27001
  - network
comment: 'A.8.20 — Outbound from scripting/LOLBin processes.'
```

### A.8.20 — Firewall Change (Windows)

```yaml
name: iso-8-20-firewall-changed-windows
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
    name: iso-8-20-firewall-changed-windows
    priority: 3
    metadata:
      iso_27001_control: A.8.20
      description: Windows Firewall rule or setting changed
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - network
comment: 'A.8.20 — Windows firewall changes (4946-4950)'
```

### A.8.20 — Firewall Change (Linux)

```yaml
name: iso-8-20-firewall-changed-linux
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
    name: iso-8-20-firewall-changed-linux
    priority: 3
    metadata:
      iso_27001_control: A.8.20
      description: Linux firewall modification (iptables / nft / firewall-cmd / ufw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - network
comment: 'A.8.20 — Linux firewall changes'
```

### A.8.20 — Firewall Change (macOS)

```yaml
name: iso-8-20-firewall-changed-macos
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
    name: iso-8-20-firewall-changed-macos
    priority: 3
    metadata:
      iso_27001_control: A.8.20
      description: macOS firewall modification (pfctl / socketfilterfw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - iso-27001
  - network
comment: 'A.8.20 — macOS firewall changes'
```

### A.8.22 — Private-to-Private Lateral Movement Indicator

```yaml
name: iso-8-22-internal-lateral
detect:
  event: NEW_TCP4_CONNECTION
  op: and
  rules:
    - op: is private address
      path: event/NETWORK_ACTIVITY/DESTINATION/IP_ADDRESS
    - op: is
      path: event/NETWORK_ACTIVITY/DESTINATION/PORT
      value: '3389'
respond:
  - action: report
    name: iso-8-22-internal-lateral
    priority: 3
    metadata:
      iso_27001_control: A.8.22
      description: Internal RDP connection — candidate lateral-movement signal
      mitre_attack_id: T1021.001
      mitre_tactic: lateral-movement
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-22-internal-lateral
tags:
  - iso-27001
  - network
comment: 'A.8.22 — Internal RDP (3389) connections. Tune for admin workstations.'
```

### A.8.23 — DNS Lookup to Known-Malicious Domain

Requires a populated hive lookup named `ti-malicious-domains`. Use `limacharlie hive set --name lookup --hive_name ti-malicious-domains --data <file>` or manage via ext-git-sync.

```yaml
name: iso-8-23-malicious-domain
detect:
  event: DNS_REQUEST
  op: and
  rules:
    - op: lookup
      path: event/DOMAIN_NAME
      resource: hive://lookup/ti-malicious-domains
respond:
  - action: report
    name: iso-8-23-malicious-domain
    priority: 4
    metadata:
      iso_27001_control: A.8.23
      description: DNS query resolved to known-malicious domain (threat-intel lookup match)
      mitre_attack_id: T1071.004
      mitre_tactic: command-and-control
tags:
  - iso-27001
  - web-filtering
comment: 'A.8.23 — TI-feed match on DNS query domain.'
```

### A.8.23 — Download-and-Execute Pattern (Linux)

```yaml
name: iso-8-23-download-execute-linux
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
respond:
  - action: report
    name: iso-8-23-download-execute-linux
    priority: 4
    metadata:
      iso_27001_control: A.8.23
      description: Linux download-and-execute pattern (curl/wget piped to shell)
      mitre_attack_id: T1059.004
      mitre_tactic: execution
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - iso-8-23-download-execute-linux
tags:
  - iso-27001
  - web-filtering
comment: 'A.8.23 — Curl/wget piped to interpreter (drive-by install indicator).'
```

### A.8.23 — Encoded PowerShell (Windows)

```yaml
name: iso-8-23-encoded-powershell
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
    name: iso-8-23-encoded-powershell
    priority: 4
    metadata:
      iso_27001_control: A.8.23
      description: PowerShell executed with encoded command — common obfuscation
      mitre_attack_id: T1059.001
      mitre_tactic: execution
tags:
  - iso-27001
  - web-filtering
comment: 'A.8.23 — Encoded PowerShell on Windows.'
```

### A.8.23 — LOLBin with Download Indicators (Windows)

```yaml
name: iso-8-23-lolbin-download-windows
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
    name: iso-8-23-lolbin-download-windows
    priority: 4
    metadata:
      iso_27001_control: A.8.23
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
  - iso-27001
  - web-filtering
comment: 'A.8.23 — Windows LOLBin abuse with HTTP / download keywords.'
```

### A.8.23 — osascript Shell/Network (macOS)

```yaml
name: iso-8-23-osascript-network-macos
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
    name: iso-8-23-osascript-network-macos
    priority: 4
    metadata:
      iso_27001_control: A.8.23
      description: macOS osascript invoking shell / network
      mitre_attack_id: T1059.002
      mitre_tactic: execution
tags:
  - iso-27001
  - web-filtering
comment: 'A.8.23 — macOS osascript shell-out.'
```

---

## 14. D&R Rules — A.5.24–A.5.28 Incident Management

The Cases extension provides the incident-handling workflow. Rules below illustrate response enrichment for A.5.24 (planning), A.5.25 (event assessment), A.5.26 (response), A.5.27 (learning), and A.5.28 (evidence).

> If ext-cases is set to **all detections** ingestion mode, every `report` action becomes a case automatically. In **tailored** mode (the default for newer orgs), case creation requires detections to meet severity thresholds or rules to explicitly `ingest_detection`.

### A.5.26 — Tag Endpoints on Critical Threats

```yaml
name: iso-5-26-critical-threat-tag
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: iso-5-26-critical-threat-tag
    priority: 5
    metadata:
      iso_27001_control: A.5.26
      description: YARA detection on endpoint — tagged for case triage
  - action: add tag
    tag: iso-incident
    ttl: 604800
tags:
  - iso-27001
  - incident-response
comment: 'A.5.26 — Tag endpoints on YARA detection (7-day tag for case triage).'
```

### A.5.26 — Automated Network Isolation on Credential Dumping

> Network isolation is disruptive. Deploy only with stakeholder approval for well-tuned, high-confidence detections. Opt-in via the `isolation-enabled` sensor tag.

```yaml
name: iso-5-26-isolate-on-credential-dump
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
    name: iso-5-26-isolate-on-credential-dump
    priority: 5
    metadata:
      iso_27001_control: A.5.26
      description: LSASS access on isolation-enrolled host — automated containment
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
  - action: isolate network
tags:
  - iso-27001
  - incident-response
comment: 'A.5.26 — Isolate host on LSASS access. Opt-in via "isolation-enabled" sensor tag.'
```

### A.5.28 — Evidence Preservation on Detonation

Tag endpoints with a unique incident identifier so subsequent analyst investigation captures downstream events against the same case.

```yaml
name: iso-5-28-evidence-tag
detect:
  event: YARA_DETECTION
  op: and
  rules:
    - op: matches
      path: event/RULE_NAME
      re: '(?i)(ransomware|credential.dump|wiper|backdoor)'
respond:
  - action: report
    name: iso-5-28-evidence-tag
    priority: 5
    metadata:
      iso_27001_control: A.5.28
      description: High-severity YARA hit — endpoint tagged for evidence preservation
  - action: add tag
    tag: iso-evidence-hold
    ttl: 2592000
tags:
  - iso-27001
  - incident-response
comment: 'A.5.28 — 30-day evidence-preservation tag on high-severity YARA categories.'
```

---

## 15. Recommended Extensions

### Required

| Extension | Purpose | ISO Controls |
|---|---|---|
| **Reliable Tasking** | Prerequisite for Artifact Collection. Ensures tasks reach offline sensors. | A.8.15 (enables WEL/MUL collection) |
| **Artifact Collection (ext-artifact)** | Manages WEL/MUL streaming and file/log retention. | A.8.15, A.5.28 |
| **Exfil Control (ext-exfil)** | Manages which event types flow from sensor to cloud. | A.8.15, A.8.16 |
| **Integrity (ext-integrity)** | FIM / RIM rule management. | A.8.9, A.8.32 |

### Strongly Recommended

| Extension | Purpose | ISO Controls |
|---|---|---|
| **Cases (ext-cases)** | SOC case management with detection-to-case conversion, SLA tracking, investigation workflows, audit trail. | A.5.24, A.5.25, A.5.26, A.5.27 |
| **EPP (Endpoint Protection)** | Unified Windows Defender management and event collection. Free. | A.8.7 |
| **Soteria EDR Rules** | Managed detection ruleset with MITRE ATT&CK mapping across 14 event types. | A.5.7, A.8.16 |
| **Sigma Rules** | Community and commercial Sigma rule conversion. | A.5.7, A.8.16 |

### Recommended for Enhanced Coverage

| Extension | Purpose | ISO Controls |
|---|---|---|
| **Strelka** | File analysis engine (YARA, PE analysis, archive extraction) for files transiting endpoints. | A.8.7 |
| **Zeek** | Network monitoring and analysis (Linux sensors). | A.8.20, A.8.22 |
| **Velociraptor** | DFIR hunting and artifact collection for incident response. | A.5.26, A.5.28 |
| **Playbook** | Python-based automation for custom response workflows. | A.5.26 |
| **ext-git-sync** | Infrastructure as Code — D&R rules, FIM, outputs, extensions managed via git. | A.8.9, A.8.32 |

---

## 16. Deployment Notes

### Retention

ISO 27001 does **not** prescribe a specific retention period — retention is org-defined based on risk assessment (referenced by A.8.15). Three years is common industry practice.

LimaCharlie retention model:
- **Insight** provides 90 days of hot retention (default)
- **S3/GCS output** provides unlimited cold storage with no LC-side expiration

For a 3-year retention policy: configure both the 90-day Insight window and an S3/GCS output with object-lock for the remainder. All artifact collection rules in this doc use `days_retention: 90` — tune per your Statement of Applicability.

### Tagging Strategy

All D&R rules use the `iso-27001` tag, enabling:

- Filtering detections by compliance source in the Cases UI
- Routing ISO-specific detections to a dedicated output
- Tracking ISO control coverage separately from operational detections

Rule metadata includes `iso_27001_control: 'A.X.Y'` for per-control coverage reporting:

```
limacharlie dr list --output json | jq '[.[] | select(.metadata.iso_27001_control)] | group_by(.metadata.iso_27001_control) | map({control: .[0].metadata.iso_27001_control, rule_count: length})'
```

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
7. Populate threat-intel lookup (`hive://lookup/ti-malicious-domains`) for Section 13 rules
8. Deploy D&R rules (Sections 6–14) — detections begin firing
9. Enable **Cases (ext-cases)** — detections convert to trackable cases
10. Subscribe to **Soteria** and/or **Sigma** — adds managed detection coverage
11. Burn-in for 7 days, then tune via FP pattern finder

### Validation

Every YAML rule in this document passes `limacharlie dr validate`. For end-to-end validation against historical telemetry, use `limacharlie dr replay` against recent data from representative endpoints (one Windows, one Linux, one macOS).

### Statement of Applicability (SoA) Mapping

The ISO 27001 SoA enumerates each Annex A control and records whether it applies plus the implementation method. Use the rule metadata `iso_27001_control` field to generate SoA coverage tables directly from the LC control plane:

```
limacharlie dr list --output json \
  | jq '[.[] | select(.metadata.iso_27001_control) | {control: .metadata.iso_27001_control, rule: .name, tags: .tags}]'
```

Export the result to the Statement of Applicability column for "implementation method" — it provides traceable evidence that each applicable control has a corresponding detection or collection artifact in the platform.
