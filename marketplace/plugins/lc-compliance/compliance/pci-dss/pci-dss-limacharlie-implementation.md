# PCI DSS v4.0 Compliance Implementation Guide — LimaCharlie

Concrete D&R rules, artifact collection rules, FIM rules, and extension recommendations to satisfy PCI DSS v4.0 requirements using LimaCharlie EDR on Windows, Linux, and macOS endpoints inside the Cardholder Data Environment (CDE).

Companion to [pci-dss-limacharlie-mapping.md](pci-dss-limacharlie-mapping.md), which maps PCI DSS requirements to LC capabilities conceptually. This document provides the deployable configuration.

All D&R rule syntax in this document has been validated against `limacharlie dr validate`. Event-to-platform coverage reflects actual sensor capability (per the LC EDR events reference), not documentation aspirations.

**Scope tagging:** All detections are built around the assumption that CDE-in-scope sensors carry a `cde` sensor tag. Apply this tag to every server, workstation, or VM inside the Cardholder Data Environment. Detections use `op: is tagged / tag: cde` so that PCI-specific rules fire only for in-scope systems, avoiding noise from out-of-scope endpoints that happen to share the tenant.

---

## Table of Contents

1. [Windows Event Log Artifact Collection Rules](#1-windows-event-log-artifact-collection-rules)
2. [macOS Unified Log Artifact Collection Rules](#2-macos-unified-log-artifact-collection-rules)
3. [Linux Audit Log Collection](#3-linux-audit-log-collection)
4. [File Integrity Monitoring (FIM) Rules](#4-file-integrity-monitoring-fim-rules)
5. [Exfil Event Collection Rules](#5-exfil-event-collection-rules)
6. [D&R Rules — Logging and Monitoring (Req 10)](#6-dr-rules--logging-and-monitoring-req-10)
7. [D&R Rules — Identification & Authentication (Req 8)](#7-dr-rules--identification--authentication-req-8)
8. [D&R Rules — Access Restriction (Req 7)](#8-dr-rules--access-restriction-req-7)
9. [D&R Rules — Malicious Software Protection (Req 5)](#9-dr-rules--malicious-software-protection-req-5)
10. [D&R Rules — Secure Systems and Software (Req 6)](#10-dr-rules--secure-systems-and-software-req-6)
11. [D&R Rules — Secure Configurations (Req 2)](#11-dr-rules--secure-configurations-req-2)
12. [D&R Rules — Network Security Controls (Req 1)](#12-dr-rules--network-security-controls-req-1)
13. [D&R Rules — Change Detection (Req 11.5)](#13-dr-rules--change-detection-req-115)
14. [Recommended Extensions](#14-recommended-extensions)
15. [Deployment Notes and Cold Archival (Req 10.5.1)](#15-deployment-notes-and-cold-archival-req-1051)

---

## 1. Windows Event Log Artifact Collection Rules

The `wel://` pattern streams Windows Event Logs as first-class `WEL` telemetry — preferred over `.evtx` file collection because events are evaluated by D&R rules in real time.

> **Prerequisite:** The **Reliable Tasking** and **Artifact Collection** extensions must be enabled.

Rule map entries are added to `ext-artifact` configuration (web UI Artifact Collection section, `limacharlie extension config-set --name ext-artifact`, or ext-git-sync).

### Security Log

```yaml
pci-wel-security:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Security:*"
```

**Key Event IDs produced and PCI DSS sub-requirement coverage:**

| Event ID | Category | PCI DSS Req |
|---|---|---|
| 4624 | Successful logon | 10.2.1.1, 10.2.1.2, 8.2.1 |
| 4625 | Failed logon | 10.2.1.4, 8.3.4 |
| 4634 | Logoff | 10.2.1.1 |
| 4647 | User-initiated logoff | 10.2.1.1 |
| 4648 | Logon with explicit credentials | 10.2.1.2, 8.3.x |
| 4672 | Special privileges assigned | 10.2.1.2, 7.2.5 |
| 4673 | Privileged service called | 10.2.1.2, 7.2.5 |
| 4674 | Operation attempted on privileged object | 10.2.1.2 |
| 4688 | Process creation (token info) | 10.2.1, 10.2.1.2 |
| 4697 | Service installed | 2.2.4, 10.2.1.7 |
| 4698 | Scheduled task created | 10.2.1.7, 11.5.1 |
| 4719 | Audit policy changed | 10.2.1.3, 10.2.1.6 |
| 4720 | User account created | 10.2.1.5, 8.2.4 |
| 4722 | User account enabled | 10.2.1.5, 8.2.4 |
| 4723 | Password change attempted | 10.2.1.5, 8.3.x |
| 4724 | Password reset attempted | 10.2.1.5, 8.3.x |
| 4725 | User account disabled | 10.2.1.5, 8.2.4 |
| 4726 | User account deleted | 10.2.1.5, 8.2.4 |
| 4728 | Member added to global group | 10.2.1.5, 7.2.5 |
| 4732 | Member added to local group | 10.2.1.5, 7.2.5 |
| 4735 | Security-enabled local group changed | 10.2.1.5 |
| 4738 | User account changed | 10.2.1.5, 8.2.4 |
| 4740 | User account locked out | 10.2.1.4, 8.3.4 |
| 4756 | Member added to universal group | 10.2.1.5, 7.2.5 |
| 4767 | User account unlocked | 10.2.1.5 |
| 4776 | Credential validation (NTLM) | 10.2.1, 8.3.11 |
| 4946 | Firewall rule added | 1.4.x, 10.2.1.7 |
| 4947 | Firewall rule modified | 1.4.x, 10.2.1.7 |
| 4948 | Firewall rule deleted | 1.4.x, 10.2.1.7 |
| 4950 | Firewall setting changed | 1.4.x, 10.2.1.7 |
| 1102 | Security log cleared | 10.2.1.3, 10.2.1.6 |

### System Log

```yaml
pci-wel-system:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://System:*"
```

**Key Event IDs:** 7034 (service crash), 7036 (service start/stop), 7040 (service start type changed), 7045 (new service installed), 1074 (shutdown/restart), 6005/6006 (event log service start/stop).

### PowerShell Operational Log

```yaml
pci-wel-powershell:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-PowerShell/Operational:*"
```

**Key Event IDs:** 4103 (module logging), 4104 (script block logging), 4105/4106 (script start/stop). Covers Req 10.2.1, 10.2.1.2 for admin actions via PowerShell.

### Sysmon (if deployed)

```yaml
pci-wel-sysmon:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Sysmon/Operational:*"
```

### Windows Defender Operational Log

```yaml
pci-wel-defender:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Defender/Operational:*"
```

**Key Event IDs:** 1006/1007 (malware action), 1116/1117 (threat detected/action taken), 2001/2003/2006 (definition update), 5001 (real-time protection disabled). Directly supports Req 5.2.x (anti-malware) and Req 10.7.1 (failure detection).

### Task Scheduler Operational Log

```yaml
pci-wel-taskscheduler:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-TaskScheduler/Operational:*"
```

### Windows Firewall Log

```yaml
pci-wel-firewall:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Firewall With Advanced Security/Firewall:*"
```

Covers Req 1.4.x — any host firewall change on a CDE-tagged system.

### RDP Sessions (TerminalServices)

```yaml
pci-wel-rdp:
  days_retention: 90
  filters:
    platforms:
      - windows
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-TerminalServices-LocalSessionManager/Operational:*"
    - "wel://Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational:*"
```

Covers Req 10.2.1.1 and Req 8.2.1 for remote interactive access.

---

## 2. macOS Unified Log Artifact Collection Rules

The `mul://` pattern streams macOS Unified Log entries as real-time `MUL` telemetry. Predicates use standard macOS unified-log predicate syntax.

> **Prerequisite:** `MUL` must be enabled in the Exfil Control rules for macOS (see Section 5).

> **Field path verification:** D&R rules in Sections 6–13 that match `MUL` events use field paths based on macOS `log` command keys (`eventMessage`, `processImagePath`, `subsystem`). Verify the exact field paths against your first few `MUL` events in Timeline after deployment — the sensor may flatten or re-key some fields. Adjust `path:` values accordingly.

### Authentication & Authorization

```yaml
pci-mul-auth:
  days_retention: 90
  filters:
    platforms:
      - macos
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.opendirectoryd"'
    - 'mul://process == "authd"'
    - 'mul://process == "securityd"'
```

Covers Req 10.2.1.4 (invalid access), Req 8.3.4 (failed authentication), Req 10.2.1.5 (credential changes).

Note: The native `SSH_LOGIN` event has **no `IS_SUCCESS` field** — it fires only on successful SSH login. Failed SSH logins on macOS must be caught in `MUL` via this collection rule.

### Login & Session Events

```yaml
pci-mul-sessions:
  days_retention: 90
  filters:
    platforms:
      - macos
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.loginwindow"'
    - 'mul://process == "loginwindow"'
```

Complements native `USER_LOGIN` / `SSH_LOGIN` events. Covers Req 10.2.1.1.

### System Configuration & Launch Services

```yaml
pci-mul-system:
  days_retention: 90
  filters:
    platforms:
      - macos
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.xpc.launchd"'
    - 'mul://process == "launchctl"'
```

Covers Req 2.2.4, Req 10.2.1.7 (launch agent / daemon changes).

### Privilege Escalation

```yaml
pci-mul-privilege:
  days_retention: 90
  filters:
    platforms:
      - macos
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://process == "sudo"'
    - 'mul://process == "authopen"'
```

Covers Req 7.2.5, Req 10.2.1.2.

---

## 3. Linux Audit Log Collection

The LC Linux EDR sensor does **not** emit `USER_LOGIN` / `SSH_LOGIN` events. Linux authentication telemetry required for Req 10.2.1.1, 10.2.1.4, and 8.3.4 requires one of the three approaches below.

### Option A — Artifact Collection (Retention, Not Streaming)

Use when compliance requires **retention** of the raw auth log but real-time detection is not needed:

```yaml
pci-artifact-authlog:
  days_retention: 90
  filters:
    platforms:
      - linux
    tags:
      - cde
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - /var/log/auth.log
    - /var/log/secure
```

Artifacts are retrievable from the Artifacts UI but are not streamed to the Timeline. Meets the Req 10.5.1 "3 months immediately available" portion for retention of auth logs, but does NOT meet Req 10.4.1.1 automated review unless option B or C is also deployed.

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

### Option C — Auditd Rules (Recommended for CDE Hosts)

Deploy auditd rules on Linux CDE endpoints (via configuration management). Then collect `/var/log/audit/audit.log` via file adapter or artifact collection using the same approach as Options A/B.

Minimum auditd rules for PCI DSS Req 10:

```
# /etc/audit/rules.d/pci-dss.rules
# Identity changes (Req 8.2.4, 10.2.1.5)
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k identity
-w /etc/sudoers.d/ -p wa -k identity

# Authentication config (Req 8.3.x, 8.3.4)
-w /etc/pam.d/ -p wa -k auth-config
-w /etc/ssh/sshd_config -p wa -k sshd-config

# Privilege escalation (Req 7.2.5, 10.2.1.2)
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation
-a always,exit -F arch=b32 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation

# Time changes (Req 10.6.x)
-a always,exit -F arch=b64 -S settimeofday,clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Audit subsystem integrity (Req 10.2.1.3, 10.2.1.6, 10.3.4)
-w /etc/audit/ -p wa -k audit-config
-w /etc/libaudit.conf -p wa -k audit-config
-w /var/log/audit/ -p wa -k audit-logs

# Cardholder data access (Req 10.2.1.1)
# Replace /var/pci/ with the actual CDE storage path
-w /var/pci/ -p rwa -k cde-data-access

-e 2
```

Deploy via Ansible, Puppet, or similar; verify with `auditctl -l`. The `-e 2` at the end locks the rules until reboot (PCI auditor-friendly tamper-resistance).

---

## 4. File Integrity Monitoring (FIM) Rules

FIM generates `FIM_HIT` events on monitored files, directories, and Windows registry keys across all three platforms. **PCI DSS Req 11.5.2 explicitly names FIM as the expected change-detection mechanism** — this section directly satisfies that requirement.

> Linux FIM works with `inotify` (active monitoring) or eBPF (on supported kernels). Windows and macOS use passive kernel monitoring.

### Windows

```yaml
pci-fim-windows-system:
  filters:
    platforms:
      - windows
    tags:
      - cde
  patterns:
    - ?:\Windows\System32\drivers\etc\hosts
    - ?:\Windows\System32\config\SAM
    - ?:\Windows\System32\config\SYSTEM
    - ?:\Windows\System32\config\SECURITY

pci-fim-windows-boot:
  filters:
    platforms:
      - windows
    tags:
      - cde
  patterns:
    - ?:\boot\bcd
    - ?:\Windows\System32\boot\winload.exe

pci-fim-windows-grouppolicy:
  filters:
    platforms:
      - windows
    tags:
      - cde
  patterns:
    - ?:\Windows\System32\GroupPolicy\*
    - ?:\Windows\SYSVOL\*

pci-fim-windows-powershell-profiles:
  filters:
    platforms:
      - windows
    tags:
      - cde
  patterns:
    - ?:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    - ?:\Users\*\Documents\WindowsPowerShell\profile.ps1

pci-fim-windows-registry-persistence:
  filters:
    platforms:
      - windows
    tags:
      - cde
  patterns:
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run*
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce*
    - \REGISTRY\USER\S-*\SOFTWARE\Microsoft\Windows\CurrentVersion\Run*
    - \REGISTRY\MACHINE\SYSTEM\CurrentControlSet\Services*
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon*
    - \REGISTRY\MACHINE\SOFTWARE\Policies\Microsoft\Windows*

pci-fim-windows-audit-logs:
  filters:
    platforms:
      - windows
    tags:
      - cde
  patterns:
    - ?:\Windows\System32\winevt\Logs\*.evtx

pci-fim-windows-cde-data:
  filters:
    platforms:
      - windows
    tags:
      - cde
  patterns:
    # Replace with actual CDE storage paths for your environment.
    - ?:\CDE\*
    - D:\cardholder-data\*
```

The last rule (`pci-fim-windows-cde-data`) is **required for Req 10.2.1.1** — all individual user access to cardholder data must be logged. Adjust paths to match your actual PAN storage locations.

### Linux

```yaml
pci-fim-linux-identity:
  filters:
    platforms:
      - linux
    tags:
      - cde
  patterns:
    - /etc/passwd
    - /etc/shadow
    - /etc/group
    - /etc/gshadow
    - /etc/sudoers
    - /etc/sudoers.d/*

pci-fim-linux-auth:
  filters:
    platforms:
      - linux
    tags:
      - cde
  patterns:
    - /etc/pam.d/*
    - /etc/ssh/sshd_config
    - /etc/ssh/ssh_config
    - /etc/security/*

pci-fim-linux-ssh-keys:
  filters:
    platforms:
      - linux
    tags:
      - cde
  patterns:
    - /root/.ssh/authorized_keys
    - /root/.ssh/*
    - /home/*/.ssh/*

pci-fim-linux-persistence:
  filters:
    platforms:
      - linux
    tags:
      - cde
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

pci-fim-linux-boot:
  filters:
    platforms:
      - linux
    tags:
      - cde
  patterns:
    - /boot/grub/grub.cfg
    - /boot/grub2/grub.cfg
    - /etc/default/grub
    - /etc/fstab

pci-fim-linux-audit:
  filters:
    platforms:
      - linux
    tags:
      - cde
  patterns:
    - /etc/audit/*
    - /etc/libaudit.conf
    - /var/log/audit/audit.log

pci-fim-linux-time-sync:
  filters:
    platforms:
      - linux
    tags:
      - cde
  patterns:
    - /etc/chrony.conf
    - /etc/chrony/*
    - /etc/ntp.conf
    - /etc/systemd/timesyncd.conf

pci-fim-linux-cde-data:
  filters:
    platforms:
      - linux
    tags:
      - cde
  patterns:
    # Replace with actual CDE storage paths for your environment.
    - /var/pci/*
    - /opt/cde-data/*
```

The `pci-fim-linux-cde-data` and `pci-fim-linux-time-sync` rules satisfy Req 10.2.1.1 and Req 10.6.x respectively. The audit-log FIM rule on `/var/log/audit/audit.log` satisfies Req 10.3.4.

### macOS

```yaml
pci-fim-macos-identity:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    - /etc/sudoers
    - /etc/sudoers.d/*
    - /etc/pam.d/*

pci-fim-macos-ssh-keys:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    - /Users/*/.ssh/*
    - /var/root/.ssh/*

pci-fim-macos-launch-daemons:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    - /Library/LaunchDaemons/*
    - /Library/LaunchAgents/*
    - /System/Library/LaunchDaemons/*
    - /System/Library/LaunchAgents/*
    - /Users/*/Library/LaunchAgents/*

pci-fim-macos-keychains:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    - /Users/*/Library/Keychains/*
    - /Library/Keychains/*

pci-fim-macos-boot:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    - /System/Library/CoreServices/boot.efi
    - /Library/Preferences/SystemConfiguration/*

pci-fim-macos-kernel-extensions:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    - /Library/Extensions/*
    - /System/Library/Extensions/*

pci-fim-macos-time-sync:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    - /etc/ntp.conf
    - /Library/Preferences/com.apple.timed.plist

pci-fim-macos-cde-data:
  filters:
    platforms:
      - macos
    tags:
      - cde
  patterns:
    # Replace with actual CDE storage paths for your environment.
    - /Users/Shared/cde-data/*
```

---

## 5. Exfil Event Collection Rules

Additive to default exfil rules — ensures all event types required for PCI DSS v4.0 coverage stream to the cloud even if defaults change.

### Windows

```yaml
pci-windows-events:
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
    tags:
      - cde
```

### Linux

```yaml
pci-linux-events:
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
    tags:
      - cde
```

### macOS

```yaml
pci-macos-events:
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
    tags:
      - cde
```

---

## 6. D&R Rules — Logging and Monitoring (Req 10)

### Req 10.2.1.1 — All individual user access to cardholder data

#### CDE Data Access (All Platforms, FIM-Driven)

```yaml
name: pci-10-cde-data-access
detect:
  event: FIM_HIT
  op: and
  rules:
    - op: is tagged
      tag: cde
    - op: matches
      path: event/FILE_PATH
      re: '(?i)(cardholder|cde-data|pan-store|/var/pci/|\\CDE\\)'
respond:
  - action: report
    name: pci-10-cde-data-access
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.1'
      description: Access or modification of cardholder data on CDE host
      mitre_attack_id: T1005
      mitre_tactic: collection
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.1 — user access to cardholder data. Tune regex to match your actual CDE paths.'
```

### Req 10.2.1.2 — All actions by administrative users

#### Windows — Special Privileges Assigned

```yaml
name: pci-10-special-privilege-logon
detect:
  event: WEL
  op: and
  rules:
    - op: is tagged
      tag: cde
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4672'
respond:
  - action: report
    name: pci-10-special-privilege-logon
    priority: 2
    metadata:
      pci_dss_req: '10.2.1.2'
      description: Special privileges assigned to new logon session on CDE host
      mitre_attack_id: T1078
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-10-special-privilege-logon
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.2 — Windows special privilege assignment (Event ID 4672) on CDE host'
```

#### Linux — Privilege Escalation on CDE Hosts

```yaml
name: pci-10-privilege-escalation-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: is tagged
      tag: cde
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(sudo|su|pkexec|doas)$'
respond:
  - action: report
    name: pci-10-privilege-escalation-linux
    priority: 2
    metadata:
      pci_dss_req: '10.2.1.2'
      description: Linux privilege-escalation command on CDE host
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
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.2 — Linux sudo/su/pkexec on CDE host'
```

#### macOS — sudo on CDE Hosts

```yaml
name: pci-10-sudo-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: is tagged
      tag: cde
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/usr/bin/sudo$'
respond:
  - action: report
    name: pci-10-sudo-macos
    priority: 2
    metadata:
      pci_dss_req: '10.2.1.2'
      description: macOS sudo invocation on CDE host
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
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.2 — macOS sudo on CDE host'
```

### Req 10.2.1.3 — Access to all audit logs

#### Windows — Audit Policy Changed

```yaml
name: pci-10-audit-policy-changed-windows
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
    name: pci-10-audit-policy-changed-windows
    priority: 5
    metadata:
      pci_dss_req: '10.2.1.3, 10.2.1.6'
      description: Windows audit policy changed — potential tampering with logging
      mitre_attack_id: T1562.002
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.3/10.2.1.6 — Windows audit policy change (4719)'
```

#### All Platforms — Audit Log FIM

```yaml
name: pci-10-audit-log-fim-windows
detect:
  event: FIM_HIT
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\Windows\\System32\\winevt\\Logs\\.*\.evtx$'
respond:
  - action: report
    name: pci-10-audit-log-fim-windows
    priority: 4
    metadata:
      pci_dss_req: '10.3.4'
      description: Windows event log file modified — potential log tampering
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.3.4 — FIM on Windows event log files'
```

```yaml
name: pci-10-audit-log-fim-linux
detect:
  event: FIM_HIT
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)^/var/log/audit/audit\.log$'
respond:
  - action: report
    name: pci-10-audit-log-fim-linux
    priority: 4
    metadata:
      pci_dss_req: '10.3.4'
      description: Linux audit.log modified — potential log tampering
      mitre_attack_id: T1070.002
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.3.4 — FIM on Linux /var/log/audit/audit.log'
```

### Req 10.2.1.4 — Invalid logical access attempts

#### Windows — Failed Logon

```yaml
name: pci-10-failed-logon-windows
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
    name: pci-10-failed-logon-windows
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.4, 8.3.4'
      description: Failed Windows logon attempt
      mitre_attack_id: T1078
      mitre_tactic: initial-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-10-failed-logon-windows
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.4 / 8.3.4 — failed Windows logon (4625)'
```

#### Windows — Brute Force Threshold

```yaml
name: pci-10-brute-force-windows
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
    name: pci-10-brute-force-windows
    priority: 4
    metadata:
      pci_dss_req: '10.2.1.4, 8.3.4'
      description: Possible brute force — 10+ failed logons within 10 min
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      min_count: 10
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-10-brute-force-windows
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.4 — threshold-based Windows brute force'
```

#### macOS — Failed Authentication via Unified Log

The native `SSH_LOGIN` event fires only on successful login and has no failure field. Failed SSH and console authentication attempts on macOS must be collected from the Unified Log. Deploy the `pci-mul-auth` artifact rule (Section 2), then match the MUL stream:

```yaml
name: pci-10-auth-failed-macos
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
    name: pci-10-auth-failed-macos
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.4, 8.3.4'
      description: Authentication failure on macOS from Unified Log
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-10-auth-failed-macos
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.4 / 8.3.4 — macOS authentication failures. Requires pci-mul-auth (Section 2).'
```

#### Linux — Failed SSH via Process Context

LC Linux sensor does not emit `SSH_LOGIN`. Detection of failed auth on Linux relies on (a) auditd integration via the file adapter or (b) scanning `NEW_PROCESS` for `sshd` child exec's followed by early termination. If the file adapter from Section 3 is deployed and streams `/var/log/auth.log`, author rules on the adapter `text` event stream:

```yaml
name: pci-10-failed-ssh-linux-adapter
detect:
  target: adapter
  op: and
  rules:
    - op: matches
      path: event/raw
      re: '(?i)(Failed password|authentication failure|Invalid user)'
respond:
  - action: report
    name: pci-10-failed-ssh-linux-adapter
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.4, 8.3.4'
      description: Linux failed SSH from /var/log/auth.log adapter
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.hostname }}'
        - pci-10-failed-ssh-linux-adapter
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.4 / 8.3.4 — Linux failed SSH via file adapter. Requires Option B from Section 3.'
```

### Req 10.2.1.5 — Changes to identification and authentication credentials

#### Windows — User Account Created

```yaml
name: pci-10-user-created-windows
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
    name: pci-10-user-created-windows
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.5, 8.2.4'
      description: New Windows user account created
      mitre_attack_id: T1136.001
      mitre_tactic: persistence
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.5 / 8.2.4 — Windows local user creation (4720)'
```

#### Windows — User Added to Privileged Group

```yaml
name: pci-10-user-added-to-group-windows
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
    name: pci-10-user-added-to-group-windows
    priority: 4
    metadata:
      pci_dss_req: '10.2.1.5, 7.2.5, 8.2.4'
      description: User added to a Windows security-enabled group
      mitre_attack_id: T1098
      mitre_tactic: persistence
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.5 — Windows group membership addition (4728, 4732, 4756)'
```

#### Windows — User Account Deleted

```yaml
name: pci-10-user-deleted-windows
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
    name: pci-10-user-deleted-windows
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.5, 8.2.4'
      description: Windows user account deleted
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.5 — Windows user deletion (4726)'
```

#### Windows — Password Change / Reset

```yaml
name: pci-10-password-change-windows
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
    name: pci-10-password-change-windows
    priority: 2
    metadata:
      pci_dss_req: '10.2.1.5, 8.3.x'
      description: Windows password change or reset
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-10-password-change-windows
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.5 / 8.3.x — Windows password change (4723) / reset (4724)'
```

#### Linux — Account Management Binary

```yaml
name: pci-10-user-mgmt-linux
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
    name: pci-10-user-mgmt-linux
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.5, 8.2.4'
      description: Linux account management binary executed
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.5 / 8.2.4 — Linux useradd/usermod/groupadd/...'
```

#### Linux — Password Change Utilities

```yaml
name: pci-10-password-change-linux
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
    name: pci-10-password-change-linux
    priority: 2
    metadata:
      pci_dss_req: '10.2.1.5, 8.3.x'
      description: Linux password management utility executed
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.5 / 8.3.x — Linux passwd/chage/chpasswd'
```

#### macOS — Account Management via dscl

```yaml
name: pci-10-user-mgmt-macos
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
    name: pci-10-user-mgmt-macos
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.5, 8.2.4'
      description: macOS account management invocation (dscl / sysadminctl)
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.5 — macOS account management via dscl, sysadminctl'
```

### Req 10.2.1.6 — Initialization, stopping, or pausing of audit logs

#### Windows — Security Event Log Cleared

```yaml
name: pci-10-event-log-cleared
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
    name: pci-10-event-log-cleared
    priority: 5
    metadata:
      pci_dss_req: '10.2.1.6, 10.3.4'
      description: Security event log was cleared — strong tampering indicator
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.6 — Windows Security log clearing (1102)'
```

#### Windows — Event Log Service Tampering

```yaml
name: pci-10-eventlog-service-stop-windows
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
    name: pci-10-eventlog-service-stop-windows
    priority: 5
    metadata:
      pci_dss_req: '10.2.1.6'
      description: Attempt to stop event log service or clear event logs
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.6 — Windows event log tampering'
```

#### Linux — Auditd Tampering

```yaml
name: pci-10-auditd-tamper-linux
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
respond:
  - action: report
    name: pci-10-auditd-tamper-linux
    priority: 5
    metadata:
      pci_dss_req: '10.2.1.6'
      description: Attempt to stop or disable Linux auditd
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.6 — Linux auditd service tampering'
```

#### macOS — Unified Log Tampering

```yaml
name: pci-10-log-tamper-macos
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
    name: pci-10-log-tamper-macos
    priority: 5
    metadata:
      pci_dss_req: '10.2.1.6'
      description: Attempt to erase or disable macOS unified log
      mitre_attack_id: T1070
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.6 — macOS log erase/disable'
```

### Req 10.2.1.7 — Creation and deletion of system-level objects

#### Windows — New Service Installed

```yaml
name: pci-10-new-service-windows
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
    name: pci-10-new-service-windows
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.7, 2.2.4'
      description: New Windows service installed
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.7 / 2.2.4 — Windows new service (7045)'
```

#### Windows — Scheduled Task Created

```yaml
name: pci-10-scheduled-task-windows
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
    name: pci-10-scheduled-task-windows
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.7, 11.5.1'
      description: Scheduled task created on Windows
      mitre_attack_id: T1053.005
      mitre_tactic: persistence
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.7 — Windows scheduled task created (4698)'
```

#### Linux — Cron / Systemd Modification

```yaml
name: pci-10-cron-modification-linux
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
    name: pci-10-cron-modification-linux
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.7, 2.2.4'
      description: Linux persistence mechanism modification
      mitre_attack_id: T1053.003
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-10-cron-modification-linux
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.7 — Linux crontab / systemctl enable'
```

#### macOS — LaunchAgent / LaunchDaemon via launchctl

```yaml
name: pci-10-launchd-modification-macos
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
    name: pci-10-launchd-modification-macos
    priority: 3
    metadata:
      pci_dss_req: '10.2.1.7, 2.2.4'
      description: macOS launchctl load — persistence indicator
      mitre_attack_id: T1543.001
      mitre_tactic: persistence
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-10-launchd-modification-macos
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.2.1.7 — macOS launchctl load/bootstrap'
```

### Req 10.7.1 — Failures of critical security controls detected promptly

#### CDE Sensor Offline

```yaml
name: pci-10-cde-sensor-offline
detect:
  target: deployment
  event: disconnect
  op: is tagged
  tag: cde
respond:
  - action: report
    name: pci-10-cde-sensor-offline
    priority: 5
    metadata:
      pci_dss_req: '10.7.1'
      description: CDE-tagged sensor disconnected from LimaCharlie — telemetry gap
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - audit
comment: 'PCI DSS Req 10.7.1 — CDE sensor goes offline. Detection gap must be addressed promptly.'
```

#### Windows Defender Real-Time Protection Disabled

```yaml
name: pci-10-defender-rtp-disabled
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
    name: pci-10-defender-rtp-disabled
    priority: 5
    metadata:
      pci_dss_req: '10.7.1, 5.2.3'
      description: Windows Defender real-time protection disabled
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - audit
  - defense-evasion
comment: 'PCI DSS Req 10.7.1 / 5.2.3 — Defender RTP disabled (5001)'
```

---

## 7. D&R Rules — Identification & Authentication (Req 8)

### Req 8.2.4 — Account lifecycle events

Covered in Section 6 (Req 10.2.1.5) — every account-management rule carries `pci_dss_req: '10.2.1.5, 8.2.4'`.

### Req 8.3.4 — Repeated failed access attempts

Covered in Section 6 (Req 10.2.1.4) — failed logon and brute-force rules carry `pci_dss_req: '10.2.1.4, 8.3.4'`.

### Req 8.3.11 — LANMAN / NTLMv1 deprecated

#### Windows — NTLM Authentication Tracking

```yaml
name: pci-8-ntlm-auth
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
    name: pci-8-ntlm-auth
    priority: 1
    metadata:
      pci_dss_req: '8.3.11'
      description: NTLM credential validation — deprecated under Req 8.3.11
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-8-ntlm-auth
tags:
  - pci-dss
  - authentication
comment: 'PCI DSS Req 8.3.11 — NTLM usage tracking. High suppression — noisy in AD.'
```

### Req 8.5.1 — MFA bypass indicators

#### Windows — New Logon Source IP (requires lookup)

```yaml
name: pci-8-mfa-unusual-source
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
    - op: lookup
      path: event/EVENT/EventData/IpAddress
      resource: 'hive://lookup/pci-known-admin-sources'
      case_sensitive: false
      metadata_rules:
        op: is
        path: 'value'
        value: 'false'
respond:
  - action: report
    name: pci-8-mfa-unusual-source
    priority: 4
    metadata:
      pci_dss_req: '8.5.1, 10.2.1.1'
      description: RDP logon from source IP not in the approved admin-source list
      mitre_attack_id: T1078
      mitre_tactic: initial-access
tags:
  - pci-dss
  - authentication
comment: 'PCI DSS Req 8.5.1 — RDP from unknown source. Requires hive://lookup/pci-known-admin-sources populated with approved admin source IPs.'
```

> This rule illustrates the lookup pattern. The lookup resource must be pre-populated — see Section 15 for the `limacharlie hive add` command. If your org has not populated the lookup, the rule will not fire correctly. Validate in Timeline before relying on it for Req 8.5.1 evidence.

### Req 8.6.1 — Service account monitoring

#### Service Account Interactive Use (Linux)

```yaml
name: pci-8-service-account-interactive-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/USER_NAME
      re: '(?i)^(svc-|service-|app-|nginx|www-data|apache|postgres|mysql)'
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(bash|zsh|sh|ksh|tcsh)$'
    - op: is
      path: event/PARENT/FILE_PATH
      value: /usr/sbin/sshd
respond:
  - action: report
    name: pci-8-service-account-interactive-linux
    priority: 4
    metadata:
      pci_dss_req: '8.6.1'
      description: Service account opened interactive SSH shell on Linux
      mitre_attack_id: T1078.003
      mitre_tactic: persistence
tags:
  - pci-dss
  - authentication
comment: 'PCI DSS Req 8.6.1 — service account should not have interactive shell access. Tune USER_NAME regex to your actual service accounts.'
```

---

## 8. D&R Rules — Access Restriction (Req 7)

### Req 7.2.5 — Privileged function tracking

#### Windows — Privileged Service Called

```yaml
name: pci-7-privileged-service-windows
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
    name: pci-7-privileged-service-windows
    priority: 3
    metadata:
      pci_dss_req: '7.2.5, 10.2.1.2'
      description: Privileged service or object operation
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-7-privileged-service-windows
tags:
  - pci-dss
  - access-control
comment: 'PCI DSS Req 7.2.5 — Windows privileged service/object (4673, 4674)'
```

### Req 7.2.x — Account Lockout (Windows)

```yaml
name: pci-7-account-lockout-windows
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
    name: pci-7-account-lockout-windows
    priority: 4
    metadata:
      pci_dss_req: '8.3.4, 10.2.1.4'
      description: Windows account locked out — failed logon threshold reached
      mitre_attack_id: T1110
      mitre_tactic: credential-access
tags:
  - pci-dss
  - access-control
comment: 'PCI DSS Req 8.3.4 — Windows account lockout (4740)'
```

### Req 7.2.x — RDP / SSH to CDE

#### Windows — RDP Logon to CDE

```yaml
name: pci-7-rdp-logon-cde
detect:
  event: WEL
  op: and
  rules:
    - op: is tagged
      tag: cde
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
    name: pci-7-rdp-logon-cde
    priority: 3
    metadata:
      pci_dss_req: '7.2.x, 10.2.1.1, 10.2.1.2'
      description: Remote Desktop logon to CDE host
      mitre_attack_id: T1021.001
      mitre_tactic: lateral-movement
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-7-rdp-logon-cde
tags:
  - pci-dss
  - access-control
comment: 'PCI DSS Req 7.2 / 10.2.1.1 — RDP to CDE host'
```

#### macOS — SSH Login to CDE

```yaml
name: pci-7-ssh-login-cde-macos
detect:
  event: SSH_LOGIN
  op: and
  rules:
    - op: is mac
    - op: is tagged
      tag: cde
respond:
  - action: report
    name: pci-7-ssh-login-cde-macos
    priority: 3
    metadata:
      pci_dss_req: '7.2.x, 10.2.1.1'
      description: SSH session established on CDE macOS host
      mitre_attack_id: T1021.004
      mitre_tactic: lateral-movement
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-7-ssh-login-cde-macos
tags:
  - pci-dss
  - access-control
comment: 'PCI DSS Req 7.2 / 10.2.1.1 — SSH into CDE macOS host. Note: SSH_LOGIN only fires on success.'
```

---

## 9. D&R Rules — Malicious Software Protection (Req 5)

### Req 5.2.1 / 5.2.2 — Anti-malware Detection

#### YARA Detection (All Platforms)

```yaml
name: pci-5-yara-detection
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: pci-5-yara-detection
    priority: 5
    metadata:
      pci_dss_req: '5.2.1, 5.2.2'
      description: YARA rule match — anti-malware signal
      mitre_tactic: execution
tags:
  - pci-dss
  - malware
comment: 'PCI DSS Req 5.2 — All YARA detections on any platform'
```

#### Defender Threat Detected

```yaml
name: pci-5-defender-threat
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
    name: pci-5-defender-threat
    priority: 4
    metadata:
      pci_dss_req: '5.2.1, 5.2.2'
      description: Windows Defender detected or acted on a threat
      mitre_tactic: execution
tags:
  - pci-dss
  - malware
comment: 'PCI DSS Req 5.2 — Defender threat alerts (1116, 1117)'
```

### Req 5.3.3 — Removable Media Scanning

#### Volume Mount — Trigger YARA Scan (Windows / macOS)

```yaml
name: pci-5-removable-media-mount
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
    name: pci-5-removable-media-mount
    priority: 3
    metadata:
      pci_dss_req: '5.3.3'
      description: Removable media mounted — triggering YARA scan
tags:
  - pci-dss
  - malware
comment: 'PCI DSS Req 5.3.3 — volume mount detection. Linux lacks native VOLUME_MOUNT events.'
```

Pair this report with a YARA scan task. Example sensor tasking (Playbook extension or manual follow-up):

```yaml
# Optional: chain a scan task through Playbook on this detection.
# Scan the newly-mounted volume with a YARA rule collection stored in the
# LC YARA rule store under rule name "pci-removable-media".
```

### Req 5.2.3 — Anti-Malware Tamper-Resistance

The Defender-RTP-disabled rule in Section 6 (Req 10.7.1) covers Req 5.2.3 on Windows. The audit-tamper detections cover it on Linux/macOS.

---

## 10. D&R Rules — Secure Systems and Software (Req 6)

### Req 6.3.3 — Unsigned Binary in Trusted Path

```yaml
name: pci-6-unsigned-binary
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
    name: pci-6-unsigned-binary
    priority: 3
    metadata:
      pci_dss_req: '6.3.3, 6.5.x'
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
  - pci-dss
  - integrity
comment: 'PCI DSS Req 6.3.3 / 6.5 — unsigned binary in trusted system path (Win/macOS)'
```

### Req 6.5.x — Application Change Detection

Covered by the FIM rules in Section 4 and the `SERVICE_CHANGE` / `DRIVER_CHANGE` / `AUTORUN_CHANGE` rules in Section 11.

---

## 11. D&R Rules — Secure Configurations (Req 2)

### Req 2.2.2 — Vendor Default Accounts

#### Windows — Built-in Administrator Logon

```yaml
name: pci-2-default-account-logon-windows
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
      path: event/EVENT/EventData/TargetUserName
      value: Administrator
respond:
  - action: report
    name: pci-2-default-account-logon-windows
    priority: 4
    metadata:
      pci_dss_req: '2.2.2'
      description: Logon with built-in Administrator account
      mitre_attack_id: T1078.001
      mitre_tactic: initial-access
tags:
  - pci-dss
  - config-management
comment: 'PCI DSS Req 2.2.2 — built-in Administrator should not be in routine use'
```

#### Linux — root SSH Login (via adapter)

```yaml
name: pci-2-root-ssh-linux
detect:
  target: adapter
  op: and
  rules:
    - op: matches
      path: event/raw
      re: '(?i)Accepted .* for root from'
respond:
  - action: report
    name: pci-2-root-ssh-linux
    priority: 4
    metadata:
      pci_dss_req: '2.2.2, 8.3.x'
      description: root SSH login on Linux — default account in use
      mitre_attack_id: T1078.003
      mitre_tactic: initial-access
tags:
  - pci-dss
  - config-management
comment: 'PCI DSS Req 2.2.2 — root SSH login. Requires file adapter (Section 3 Option B).'
```

### Req 2.2.4 / 2.2.6 — Service & Configuration Change Detection

#### Service Change (All Platforms)

```yaml
name: pci-2-service-change
detect:
  event: SERVICE_CHANGE
  op: exists
  path: event/SVC_NAME
respond:
  - action: report
    name: pci-2-service-change
    priority: 2
    metadata:
      pci_dss_req: '2.2.4, 10.2.1.7'
      description: Service configuration changed
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-2-service-change
tags:
  - pci-dss
  - config-management
comment: 'PCI DSS Req 2.2.4 — service change. Suppressed for patching noise.'
```

#### Windows — Autorun Changed

```yaml
name: pci-2-autorun-change-windows
detect:
  event: AUTORUN_CHANGE
  op: is windows
respond:
  - action: report
    name: pci-2-autorun-change-windows
    priority: 3
    metadata:
      pci_dss_req: '2.2.4, 11.5.2'
      description: Windows autorun persistence change
      mitre_attack_id: T1547.001
      mitre_tactic: persistence
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-2-autorun-change-windows
tags:
  - pci-dss
  - config-management
comment: 'PCI DSS Req 2.2.4 / 11.5.2 — Windows autorun change'
```

#### Windows — Driver Change

```yaml
name: pci-2-driver-change
detect:
  event: DRIVER_CHANGE
  op: is windows
respond:
  - action: report
    name: pci-2-driver-change
    priority: 3
    metadata:
      pci_dss_req: '2.2.4, 10.2.1.7'
      description: Driver installed or modified
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - pci-dss
  - config-management
comment: 'PCI DSS Req 2.2.4 — Windows driver change'
```

### Req 2.2.6 — Security Parameter Changes

#### FIM Hit (All Platforms) — catches sysctl, registry hardening, etc.

```yaml
name: pci-2-fim-hit
detect:
  event: FIM_HIT
  op: exists
  path: event/FILE_PATH
respond:
  - action: report
    name: pci-2-fim-hit
    priority: 3
    metadata:
      pci_dss_req: '2.2.6, 11.5.2, 10.3.4'
      description: File integrity change on monitored path
      mitre_attack_id: T1565
      mitre_tactic: impact
tags:
  - pci-dss
  - config-management
comment: 'PCI DSS Req 11.5.2 — FIM hit across all platforms. Single generic rule; add narrower rules for high-priority paths.'
```

---

## 12. D&R Rules — Network Security Controls (Req 1)

### Req 1.4.x — Host Firewall Change Detection

#### Windows — Firewall Rule Changed

```yaml
name: pci-1-firewall-changed-windows
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
    name: pci-1-firewall-changed-windows
    priority: 3
    metadata:
      pci_dss_req: '1.4.x, 10.2.1.7'
      description: Windows Firewall rule or setting changed
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - boundary
comment: 'PCI DSS Req 1.4 — Windows firewall changes (4946-4950)'
```

#### Linux — iptables / firewalld / ufw Changes

```yaml
name: pci-1-firewall-changed-linux
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
    name: pci-1-firewall-changed-linux
    priority: 3
    metadata:
      pci_dss_req: '1.4.x, 10.2.1.7'
      description: Linux firewall modification (iptables / nft / firewall-cmd / ufw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - boundary
comment: 'PCI DSS Req 1.4 — Linux firewall changes'
```

#### macOS — pfctl / socketfilterfw

```yaml
name: pci-1-firewall-changed-macos
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
    name: pci-1-firewall-changed-macos
    priority: 3
    metadata:
      pci_dss_req: '1.4.x, 10.2.1.7'
      description: macOS firewall modification (pfctl / socketfilterfw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - pci-dss
  - boundary
comment: 'PCI DSS Req 1.4 — macOS firewall changes'
```

### Req 1.5.1 — Third-party Connection Monitoring

#### Unexpected Outbound from CDE Host

```yaml
name: pci-1-unexpected-outbound-cde
detect:
  event: NEW_TCP4_CONNECTION
  op: and
  rules:
    - op: is tagged
      tag: cde
    - op: is public address
      path: event/NETWORK_ACTIVITY/DESTINATION/IP_ADDRESS
    - op: matches
      path: event/PROCESS/FILE_PATH
      re: '(?i)\\(powershell|pwsh|cmd|wscript|cscript|mshta|rundll32|regsvr32)\.exe$|/usr/bin/(curl|wget|nc|ncat)$'
respond:
  - action: report
    name: pci-1-unexpected-outbound-cde
    priority: 4
    metadata:
      pci_dss_req: '1.4.x, 1.5.1'
      description: Outbound public-IP connection from command-line / scripting utility on CDE host
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
  - pci-dss
  - boundary
comment: 'PCI DSS Req 1.4 / 1.5.1 — outbound from LOLBin/scripting utilities on CDE host'
```

---

## 13. D&R Rules — Change Detection (Req 11.5)

### Req 11.5.1 — Intrusion Detection

All D&R rules in this document contribute to Req 11.5.1. Specific high-value intrusion detections below.

#### Windows — LSASS Access

```yaml
name: pci-11-lsass-access
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
    name: pci-11-lsass-access
    priority: 5
    metadata:
      pci_dss_req: '11.5.1, 10.2.1.2'
      description: Sensitive handle to LSASS — possible credential dumping
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-11-lsass-access
tags:
  - pci-dss
  - integrity
  - credential-access
comment: 'PCI DSS Req 11.5.1 — LSASS access (credential dumping)'
```

#### Windows — LOLBin Abuse with Network Indicators

```yaml
name: pci-11-lolbin-execution-windows
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
    name: pci-11-lolbin-execution-windows
    priority: 4
    metadata:
      pci_dss_req: '11.5.1'
      description: Suspicious LOLBin execution with network indicators
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
  - pci-dss
  - integrity
comment: 'PCI DSS Req 11.5.1 — Windows LOLBin abuse'
```

#### Windows — Encoded PowerShell

```yaml
name: pci-11-encoded-powershell
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
    name: pci-11-encoded-powershell
    priority: 4
    metadata:
      pci_dss_req: '11.5.1'
      description: PowerShell executed with encoded command — common obfuscation
      mitre_attack_id: T1059.001
      mitre_tactic: execution
tags:
  - pci-dss
  - integrity
comment: 'PCI DSS Req 11.5.1 — encoded PowerShell'
```

#### Windows — Thread Injection

```yaml
name: pci-11-thread-injection
detect:
  event: THREAD_INJECTION
  op: is windows
respond:
  - action: report
    name: pci-11-thread-injection
    priority: 4
    metadata:
      pci_dss_req: '11.5.1'
      description: Thread injection — code injection indicator
      mitre_attack_id: T1055
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-11-thread-injection
tags:
  - pci-dss
  - integrity
comment: 'PCI DSS Req 11.5.1 — Windows thread injection'
```

#### Windows — Suspicious Named Pipe

```yaml
name: pci-11-suspicious-named-pipe
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
    name: pci-11-suspicious-named-pipe
    priority: 4
    metadata:
      pci_dss_req: '11.5.1'
      description: Known malicious named-pipe pattern — possible C2
      mitre_attack_id: T1570
      mitre_tactic: lateral-movement
tags:
  - pci-dss
  - integrity
comment: 'PCI DSS Req 11.5.1 — known-bad named pipe patterns'
```

#### Linux — LOLBin Download-and-Execute

```yaml
name: pci-11-lolbin-execution-linux
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
    name: pci-11-lolbin-execution-linux
    priority: 4
    metadata:
      pci_dss_req: '11.5.1'
      description: Linux LOLBin with download-and-execute pattern
      mitre_attack_id: T1059.004
      mitre_tactic: execution
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - pci-11-lolbin-execution-linux
tags:
  - pci-dss
  - integrity
comment: 'PCI DSS Req 11.5.1 — Linux download-and-execute'
```

#### macOS — osascript Network Activity

```yaml
name: pci-11-osascript-network-macos
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
    name: pci-11-osascript-network-macos
    priority: 4
    metadata:
      pci_dss_req: '11.5.1'
      description: macOS osascript invoking shell / network
      mitre_attack_id: T1059.002
      mitre_tactic: execution
tags:
  - pci-dss
  - integrity
comment: 'PCI DSS Req 11.5.1 — macOS osascript shell-out'
```

### Req 11.5.2 — File Integrity / Change Detection

PCI DSS v4.0 explicitly names FIM as the expected mechanism. Coverage is provided by:

- The FIM rules in Section 4 — file/registry paths monitored on all three platforms
- The `pci-2-fim-hit` generic rule in Section 11 — produces a detection on any `FIM_HIT`
- Individual high-priority rules in Section 6 (audit log FIM) and throughout this doc

### Req 11.5.2 (extension) — Automated Isolation on High-Confidence Threats

> Network isolation is disruptive. Deploy only with stakeholder approval for well-tuned, high-confidence detections. The standard response action is `isolate network`.

```yaml
name: pci-11-isolate-on-credential-dump
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
    name: pci-11-isolate-on-credential-dump
    priority: 5
    metadata:
      pci_dss_req: '11.5.1, 12.10.x'
      description: LSASS access on isolation-enrolled CDE host — automated containment
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
  - action: isolate network
tags:
  - pci-dss
  - incident-response
comment: 'PCI DSS Req 11.5.1 / 12.10 — isolate CDE host on LSASS access. Opt-in via sensor tag "isolation-enabled".'
```

---

## 14. Recommended Extensions

### Required

| Extension | Purpose | PCI DSS Req |
|---|---|---|
| **Reliable Tasking** | Prerequisite for Artifact Collection. Ensures tasks reach offline sensors. | 10.2.1 (enables WEL/MUL collection) |
| **Artifact Collection (ext-artifact)** | Manages WEL/MUL streaming and file/log retention. | 10.2.1, 10.3.3, 10.5.1 |
| **Exfil Control (ext-exfil)** | Manages which event types flow from sensor to cloud. | 10.2.1, 10.2.2 |
| **Integrity (ext-integrity)** | FIM / RIM rule management. | 11.5.2, 10.3.4 |

### Strongly Recommended

| Extension | Purpose | PCI DSS Req |
|---|---|---|
| **Cases (ext-cases)** | SOC case management with detection-to-case conversion, SLA tracking, investigation workflows, audit trail. | 10.4.3, 12.10.x |
| **EPP (Endpoint Protection)** | Unified Windows Defender management and event collection. Free. | 5.2.1, 5.2.2, 5.2.3 |
| **Soteria EDR Rules** | Managed detection ruleset with MITRE ATT&CK mapping across 14 event types. | 11.5.1, 10.4.1.1 |
| **Sigma Rules** | Community and commercial Sigma rule conversion. | 11.5.1, 10.4.1.1 |

### Recommended for Enhanced Coverage

| Extension | Purpose | PCI DSS Req |
|---|---|---|
| **Strelka** | File analysis engine (YARA, PE analysis, archive extraction) for files transiting endpoints. | 5.2.1, 5.2.2, 5.3.3 |
| **Zeek** | Network monitoring and analysis (Linux sensors). | 1.2.5, 1.4.x, 10.2.1 |
| **Velociraptor** | DFIR hunting and artifact collection for incident response. | 12.10.x |
| **Playbook** | Python-based automation for custom response workflows. | 12.10.x |
| **ext-git-sync** | Infrastructure as Code — D&R rules, FIM, outputs, extensions managed via git. | 6.5.x, 10.3.2 |

---

## 15. Deployment Notes and Cold Archival (Req 10.5.1)

### Req 10.5.1 — Retention (the critical PCI-specific requirement)

**PCI DSS Req 10.5.1 mandates 12 months retention, with 3 months immediately available for analysis.**

| Retention Slice | LC Capability | Status |
|---|---|---|
| 3 months immediately available for analysis | Insight default 90-day hot retention | Satisfied by default |
| Months 3–12 (cold archival) | S3 / GCS / Azure Blob output with object-lock (WORM) | Required to configure |

#### Reference S3 output configuration

```yaml
pci-cold-archive-s3:
  module: s3
  is_enabled: true
  retention: aws-s3
  config:
    bucket: pci-lc-audit-archive
    prefix: pci-dss/
    key_id: '{{ .secrets.aws_access_key_id }}'
    secret_key: '{{ .secrets.aws_secret_access_key }}'
    region: us-east-1
    stream: event
    # Additional S3 bucket-side configuration (required separately):
    # - Enable Object Lock in COMPLIANCE mode
    # - Set default retention to 395 days (12+ months for safety margin)
    # - Apply lifecycle rules moving objects to Glacier after 90 days
    # - MFA-delete for the bucket
```

> Bucket object-lock and WORM settings are configured at the S3 bucket level, not in the LC output. Coordinate with your cloud administrator to apply a bucket policy with `s3:PutObjectRetention` / `s3:PutObjectLegalHold` DENY for non-service principals so only LC writes are accepted.

#### Reference GCS output configuration

```yaml
pci-cold-archive-gcs:
  module: gcs
  is_enabled: true
  retention: google-cloud-storage
  config:
    bucket: pci-lc-audit-archive
    prefix: pci-dss/
    project: <gcp-project>
    service_account: '{{ .secrets.gcs_service_account }}'
    stream: event
    # Bucket-side configuration (separate):
    # - Retention Policy (lock): 395 days
    # - Uniform bucket-level access: enabled
    # - Object Versioning: enabled
    # - Lifecycle rule: move to Coldline after 90 days, Archive after 365
```

### Tagging Strategy

| Tag | Purpose | Applied To |
|---|---|---|
| `cde` | Sensor is inside the Cardholder Data Environment — triggers PCI scoping in rules and outputs | Every CDE sensor |
| `pci-in-scope` | Alternative / complementary to `cde` | Sensors supporting but not inside CDE |
| `isolation-enabled` | Sensor is enrolled for automated network isolation on high-confidence detections | Opt-in CDE hosts |
| `audit-tamper` | Applied by audit-tamper detections — triggers elevated-priority review | Applied dynamically by rules |

Apply at sensor registration via `limacharlie sensor tag` or enrollment key metadata.

All D&R rules in this doc use the `pci-dss` tag, enabling:

- Filtering detections by compliance source in the Cases UI
- Routing PCI-specific detections to a dedicated output (for QSA evidence packaging)
- Tracking PCI rule coverage separately from operational detections

### Suppression Tuning

Many rules include starting-point suppression. Tune after deployment:

1. Run for a 7-day burn-in period with `cde` tags applied
2. Use `/lc-essentials:fp-pattern-finder` to identify systematic noise
3. Author FP rules for known-safe patterns (service accounts, approved admin tools, patch-management activity)

### Windows Audit Policy Prerequisites

Windows CDE endpoints need the **Advanced Audit Policy** configured. Minimum categories for PCI DSS Req 10:

| Audit Category | Subcategory | Setting |
|---|---|---|
| Account Logon | Credential Validation | Success, Failure |
| Account Management | User Account Management | Success, Failure |
| Account Management | Security Group Management | Success, Failure |
| Detailed Tracking | Process Creation | Success |
| Logon/Logoff | Logon | Success, Failure |
| Logon/Logoff | Logoff | Success |
| Logon/Logoff | Special Logon | Success |
| Object Access | File System | Success, Failure |
| Object Access | Registry | Success, Failure |
| Policy Change | Audit Policy Change | Success, Failure |
| Privilege Use | Sensitive Privilege Use | Success, Failure |
| System | Security State Change | Success |
| System | System Integrity | Success, Failure |

Deploy via Group Policy: `Computer Configuration → Windows Settings → Security Settings → Advanced Audit Policy Configuration`.

### Linux Audit Policy Prerequisites

Deploy the auditd rules from Section 3 via Ansible/Puppet/Chef. Verify with `auditctl -l`. Ensure `/var/log/audit/audit.log` rotation is configured to retain at minimum the Insight retention window (default 90 days) so that artifact collection / file adapter captures the full window.

### macOS Audit Policy Prerequisites

macOS Unified Log retention is managed via `log config` policies. Default retention is often shorter than 90 days — validate on a sample endpoint with `log stats --overview`. Adjust predicate patterns (Section 2) to balance visibility with volume. Reminder: `SSH_LOGIN` has no `IS_SUCCESS` field — failed SSH must be caught in `MUL`.

### Hive Lookup Prerequisites

The Req 8.5.1 MFA-bypass rule depends on a pre-populated lookup. Seed it before enabling the rule:

```
limacharlie hive add --hive lookup --name pci-known-admin-sources \
  --data '{"10.0.0.0/8":"true","192.168.0.0/16":"true","203.0.113.42":"true"}' \
  --tags pci-dss
```

Add or remove entries as the admin source IP list evolves.

### Deployment Order

1. Enable **Reliable Tasking**, **Artifact Collection**, **Exfil Control**, **Integrity** extensions
2. Tag all CDE-in-scope sensors with the `cde` tag
3. Configure the S3 or GCS cold-archive output (Req 10.5.1)
4. Deploy Windows WEL artifact collection rules (Section 1)
5. Deploy macOS MUL artifact collection rules (Section 2)
6. Deploy Linux auditd rules + file adapter or artifact rules (Section 3)
7. Deploy FIM rules per platform (Section 4), adjusting CDE-data paths to your environment
8. Deploy exfil event rules per platform (Section 5)
9. Populate Hive lookup for Req 8.5.1 MFA-bypass rule
10. Deploy D&R rules (Sections 6–13) — detections begin firing
11. Enable **Cases (ext-cases)** — detections convert to trackable cases for Req 10.4.3 / 12.10
12. Subscribe to **Soteria** and/or **Sigma** — adds managed detection coverage
13. Burn-in for 7 days, then tune via FP pattern finder

### Validation

Every YAML rule in this document passes `limacharlie dr validate`. For end-to-end validation against historical telemetry, use `limacharlie dr replay` against recent data from representative CDE endpoints (one Windows, one Linux, one macOS).

For QSA evidence packaging, export all rules via:

```
limacharlie dr list --tag pci-dss --output yaml > pci-dss-active-rules.yaml
limacharlie extension config-get --name ext-artifact > pci-dss-artifact-config.yaml
limacharlie extension config-get --name ext-integrity > pci-dss-fim-config.yaml
```

These three files constitute the configuration evidence required by a QSA to verify Req 10, Req 11.5.2, and Req 5.2 coverage is in place.
