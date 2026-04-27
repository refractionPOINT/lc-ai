# CIS Critical Security Controls v8 Implementation Guide — LimaCharlie

Concrete D&R rules, artifact collection rules, FIM rules, exfil configurations, and extension recommendations to satisfy CIS Critical Security Controls v8 (released 2021) using LimaCharlie EDR on Windows, Linux, and macOS endpoints.

Companion to [cis-v8-limacharlie-mapping.md](cis-v8-limacharlie-mapping.md), which maps safeguards to LC capabilities conceptually. This document provides the deployable configuration.

All D&R rule syntax below has been validated with `limacharlie dr validate`. Event-to-platform coverage reflects actual sensor capability (per the LC EDR events reference), not documentation aspirations.

Rule convention:

- **name:** `cis-<control>-<safeguard>-<desc>` (e.g., `cis-8-2-failed-logon-windows`)
- **metadata.cis_safeguard:** the specific safeguard number, e.g., `'8.2'`
- **tags:** `['cis-v8', '<family>']` — where `<family>` is one of `audit`, `access-control`, `malware`, `integrity`, `incident-response`, `config-management`, `boundary`, `inventory`, `browser-email`, `network-monitoring`, `incident-response`, `pentest`

---

## Table of Contents

1. [Windows Event Log Artifact Collection Rules](#1-windows-event-log-artifact-collection-rules)
2. [macOS Unified Log Artifact Collection Rules](#2-macos-unified-log-artifact-collection-rules)
3. [Linux Auth Log Collection](#3-linux-auth-log-collection)
4. [File Integrity Monitoring (FIM) Rules](#4-file-integrity-monitoring-fim-rules)
5. [Exfil Event Collection Rules](#5-exfil-event-collection-rules)
6. [D&R Rules — Control 1 (Asset Inventory)](#6-dr-rules--control-1-asset-inventory)
7. [D&R Rules — Control 2 (Software Inventory)](#7-dr-rules--control-2-software-inventory)
8. [D&R Rules — Control 3 (Data Protection)](#8-dr-rules--control-3-data-protection)
9. [D&R Rules — Control 4 (Secure Configuration)](#9-dr-rules--control-4-secure-configuration)
10. [D&R Rules — Control 5 (Account Management)](#10-dr-rules--control-5-account-management)
11. [D&R Rules — Control 6 (Access Control)](#11-dr-rules--control-6-access-control)
12. [D&R Rules — Control 7 (Vulnerability Management)](#12-dr-rules--control-7-vulnerability-management)
13. [D&R Rules — Control 8 (Audit Log Management)](#13-dr-rules--control-8-audit-log-management)
14. [D&R Rules — Control 9 (Email & Browser)](#14-dr-rules--control-9-email--browser)
15. [D&R Rules — Control 10 (Malware Defenses)](#15-dr-rules--control-10-malware-defenses)
16. [D&R Rules — Control 13 (Network Monitoring)](#16-dr-rules--control-13-network-monitoring)
17. [D&R Rules — Control 16 (Application Software)](#17-dr-rules--control-16-application-software)
18. [D&R Rules — Control 17 (Incident Response)](#18-dr-rules--control-17-incident-response)
19. [D&R Rules — Control 18 (Pentest Support)](#19-dr-rules--control-18-pentest-support)
20. [Lookups](#20-lookups)
21. [Outputs for Centralisation and Retention (8.9, 8.10)](#21-outputs-for-centralisation-and-retention-89-810)
22. [Recommended Extensions](#22-recommended-extensions)
23. [Deployment Notes](#23-deployment-notes)

---

## 1. Windows Event Log Artifact Collection Rules

CIS Safeguard 8.2 requires the collection of audit logs. The `wel://` pattern streams Windows Event Logs as first-class `WEL` telemetry — preferred over `.evtx` file collection because events are evaluated by D&R rules in real time.

> **Prerequisite:** The **Reliable Tasking** and **Artifact Collection** extensions must be enabled.

Add rule-map entries to `ext-artifact` via the Web UI, CLI (`limacharlie extension config-set --name ext-artifact`), or ext-git-sync.

### Security Log (CIS 8.2, 8.5)

```yaml
cis-wel-security:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Security:*"
```

**Key Event IDs → CIS safeguards:**

| Event ID | Category | CIS Safeguard |
|---|---|---|
| 4624 | Successful logon | 8.2, 8.5 |
| 4625 | Failed logon | 8.2, 8.11 |
| 4634 | Logoff | 8.2 |
| 4647 | User-initiated logoff | 8.2 |
| 4648 | Logon with explicit credentials | 8.2, 6.5 |
| 4672 | Special privileges assigned | 8.2, 5.4, 6.8 |
| 4673 | Privileged service called | 6.8 |
| 4674 | Privileged object operation | 6.8 |
| 4688 | Process creation (advanced audit policy required) | 8.8 |
| 4697 | Service installed | 4.8, 8.2 |
| 4698 | Scheduled task created | 8.2 |
| 4699 | Scheduled task deleted | 8.2 |
| 4700 | Scheduled task enabled | 8.2 |
| 4701 | Scheduled task disabled | 8.2 |
| 4719 | Audit policy changed | 8.2 |
| 4720 | Account created | 5.1 |
| 4722 | Account enabled | 5.1 |
| 4723 | Password change attempted | 5.1, 5.2 |
| 4724 | Password reset attempted | 5.1, 5.2 |
| 4725 | Account disabled | 5.1, 5.3 |
| 4726 | Account deleted | 5.1 |
| 4728 | Added to global security group | 5.1, 6.8 |
| 4732 | Added to local security group | 5.1, 6.8 |
| 4735 | Local security group changed | 5.1, 6.8 |
| 4738 | Account changed | 5.1 |
| 4740 | Account lockout | 8.11 |
| 4756 | Added to universal security group | 5.1, 6.8 |
| 4767 | Account unlocked | 5.1 |
| 4776 | NTLM credential validation | 8.2 |
| 4946–4950 | Firewall rule added/modified/deleted/setting changed | 4.4, 4.5 |
| 1102 | Security log cleared | 8.2, 8.11 |

### System Log

```yaml
cis-wel-system:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://System:*"
```

Key Event IDs: 7034 (service crash), 7036 (service start/stop), 7040 (service start type changed), 7045 (new service installed), 1074 (shutdown/restart), 6005/6006 (event log service lifecycle).

### PowerShell Operational Log (CIS 8.8)

```yaml
cis-wel-powershell:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-PowerShell/Operational:*"
```

Key Event IDs: 4103 (module logging), 4104 (script block logging), 4105/4106 (script start/stop).

### Sysmon (if deployed)

```yaml
cis-wel-sysmon:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Sysmon/Operational:*"
```

### Windows Defender Operational Log (CIS 10.1, 10.2)

```yaml
cis-wel-defender:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Defender/Operational:*"
```

Key Event IDs: 1006/1007 (malware action), 1116/1117 (threat detected/action taken), 2001/2003/2006 (definition update), 5001 (real-time protection disabled), 5007 (Defender configuration changed).

### Task Scheduler Operational Log

```yaml
cis-wel-taskscheduler:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-TaskScheduler/Operational:*"
```

### Windows Firewall Log (CIS 4.4, 4.5)

```yaml
cis-wel-firewall:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-Windows Firewall With Advanced Security/Firewall:*"
```

### BitLocker Management Log (CIS 3.6)

```yaml
cis-wel-bitlocker:
  days_retention: 90
  filters:
    platforms:
      - windows
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - "wel://Microsoft-Windows-BitLocker/BitLocker Management:*"
```

---

## 2. macOS Unified Log Artifact Collection Rules

The `mul://` pattern streams macOS Unified Log entries as real-time `MUL` telemetry. Predicates use standard macOS unified-log predicate syntax.

> **Prerequisite:** `MUL` must be enabled in the Exfil Control rules for macOS (see Section 5).

> **Field path verification:** D&R rules in later sections that match `MUL` events use field paths based on the `log` command keys (`eventMessage`, `processImagePath`, `subsystem`). Verify the exact field paths against your first few `MUL` events in Timeline after deployment — the sensor may flatten or re-key some fields.

### Authentication & Authorization (CIS 8.2, 8.11)

```yaml
cis-mul-auth:
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

### Login & Session Events

```yaml
cis-mul-sessions:
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

### System Configuration & Launch Services (CIS 4.8)

```yaml
cis-mul-system:
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

### Privilege Escalation (CIS 6.8)

```yaml
cis-mul-privilege:
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

### FileVault / Disk Encryption (CIS 3.6)

```yaml
cis-mul-filevault:
  days_retention: 90
  filters:
    platforms:
      - macos
  is_delete_after: false
  is_ignore_cert: false
  patterns:
    - 'mul://subsystem == "com.apple.FDERecoveryAgent"'
    - 'mul://process == "fdesetup"'
```

---

## 3. Linux Auth Log Collection

The LC Linux EDR sensor does **not** emit `USER_LOGIN` / `SSH_LOGIN` events. To satisfy CIS 8.2 for authentication telemetry on Linux, use one of the three approaches below.

### Option A — Artifact Collection (Retention, Not Streaming)

Use when CIS 8.10 retention is the primary goal and real-time detection is not needed:

```yaml
cis-artifact-authlog:
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

Artifacts are retrievable from the Artifacts UI but are not streamed to Timeline.

### Option B — File Adapter (Real-Time Streaming, Separate Stream)

Use when auth events need to be evaluable by D&R rules (CIS 8.11). Deploys a LimaCharlie Adapter binary on each Linux endpoint separate from the EDR sensor.

1. Create an Installation Key for the adapter and download the appropriate binary.
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
4. Persist via systemd unit.

Events arrive as the `text` platform — D&R rules match on `event/raw` with regex patterns.

### Option C — Auditd Rules (Recommended for IG2/IG3)

Deploy auditd rules (via configuration management) that mirror Windows advanced audit policy. Then collect `/var/log/audit/audit.log` via file adapter or artifact collection using Option A / Option B.

Minimum auditd rules for CIS v8 IG2/IG3:

```
# /etc/audit/rules.d/cis-v8.rules
# CIS 5.1, 5.4 — Identity
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k identity
-w /etc/sudoers.d/ -p wa -k identity

# CIS 4.9 — Authentication config
-w /etc/pam.d/ -p wa -k auth-config
-w /etc/ssh/sshd_config -p wa -k sshd-config
-w /etc/resolv.conf -p wa -k dns-config

# CIS 6.8 — Privilege escalation
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation
-a always,exit -F arch=b32 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k privilege-escalation

# CIS 8.4 — Time changes
-a always,exit -F arch=b64 -S settimeofday,clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# CIS 8.2, 8.11 — Audit subsystem integrity
-w /etc/audit/ -p wa -k audit-config
-w /etc/libaudit.conf -p wa -k audit-config
-e 2
```

Deploy via Ansible, Puppet, Chef, or cloud-init; verify with `auditctl -l`.

---

## 4. File Integrity Monitoring (FIM) Rules

CIS 8.5 (detailed audit logs), CIS 4.x (secure configuration), and CIS 10.3 (disable autorun) call for monitoring sensitive files. FIM produces `FIM_HIT` events on monitored paths across all three platforms.

> Linux FIM works with `inotify` (active monitoring) or eBPF (on supported kernels). Windows and macOS use passive kernel monitoring.

### Windows

```yaml
cis-fim-windows-system:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\drivers\etc\hosts
    - ?:\Windows\System32\config\SAM
    - ?:\Windows\System32\config\SYSTEM
    - ?:\Windows\System32\config\SECURITY

cis-fim-windows-boot:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\boot\bcd
    - ?:\Windows\System32\boot\winload.exe

cis-fim-windows-grouppolicy:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\GroupPolicy\*
    - ?:\Windows\SYSVOL\*

cis-fim-windows-powershell-profiles:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    - ?:\Users\*\Documents\WindowsPowerShell\profile.ps1

cis-fim-windows-registry-persistence:
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

# CIS 10.3 — Autorun / Autoplay registry policy
cis-fim-windows-autorun-policy:
  filters:
    platforms:
      - windows
  patterns:
    - \REGISTRY\MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\*
    - \REGISTRY\USER\S-*\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\*

# CIS 9.4 — Browser extensions
cis-fim-windows-browser-extensions:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Users\*\AppData\Local\Google\Chrome\User Data\*\Extensions\*
    - ?:\Users\*\AppData\Local\Microsoft\Edge\User Data\*\Extensions\*
    - ?:\Users\*\AppData\Roaming\Mozilla\Firefox\Profiles\*\extensions\*
```

### Linux

```yaml
cis-fim-linux-identity:
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

cis-fim-linux-auth:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/pam.d/*
    - /etc/ssh/sshd_config
    - /etc/ssh/ssh_config
    - /etc/security/*

cis-fim-linux-dns:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/resolv.conf
    - /etc/nsswitch.conf
    - /etc/systemd/resolved.conf

cis-fim-linux-ssh-keys:
  filters:
    platforms:
      - linux
  patterns:
    - /root/.ssh/authorized_keys
    - /root/.ssh/*
    - /home/*/.ssh/*

cis-fim-linux-persistence:
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

cis-fim-linux-boot:
  filters:
    platforms:
      - linux
  patterns:
    - /boot/grub/grub.cfg
    - /boot/grub2/grub.cfg
    - /etc/default/grub
    - /etc/fstab

cis-fim-linux-audit:
  filters:
    platforms:
      - linux
  patterns:
    - /etc/audit/*
    - /etc/libaudit.conf

cis-fim-linux-browser-extensions:
  filters:
    platforms:
      - linux
  patterns:
    - /home/*/.config/google-chrome/*/Extensions/*
    - /home/*/.config/chromium/*/Extensions/*
    - /home/*/.mozilla/firefox/*/extensions/*
```

### macOS

```yaml
cis-fim-macos-identity:
  filters:
    platforms:
      - macos
  patterns:
    - /etc/sudoers
    - /etc/sudoers.d/*
    - /etc/pam.d/*

cis-fim-macos-dns:
  filters:
    platforms:
      - macos
  patterns:
    - /etc/resolv.conf
    - /etc/resolver/*

cis-fim-macos-ssh-keys:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/.ssh/*
    - /var/root/.ssh/*

cis-fim-macos-launch-daemons:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/LaunchDaemons/*
    - /Library/LaunchAgents/*
    - /System/Library/LaunchDaemons/*
    - /System/Library/LaunchAgents/*
    - /Users/*/Library/LaunchAgents/*

cis-fim-macos-keychains:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/Library/Keychains/*
    - /Library/Keychains/*

cis-fim-macos-boot:
  filters:
    platforms:
      - macos
  patterns:
    - /System/Library/CoreServices/boot.efi
    - /Library/Preferences/SystemConfiguration/*

cis-fim-macos-kernel-extensions:
  filters:
    platforms:
      - macos
  patterns:
    - /Library/Extensions/*
    - /System/Library/Extensions/*

cis-fim-macos-browser-extensions:
  filters:
    platforms:
      - macos
  patterns:
    - /Users/*/Library/Application Support/Google/Chrome/*/Extensions/*
    - /Users/*/Library/Application Support/Microsoft Edge/*/Extensions/*
    - /Users/*/Library/Application Support/Firefox/Profiles/*/extensions/*
```

---

## 5. Exfil Event Collection Rules

These ensure the event types required by CIS 8.2, 8.5, 8.6, 8.8 stream to the cloud even if default exfil rules change. Additive to defaults.

### Windows

```yaml
cis-windows-events:
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
    - NETWORK_CONNECTIONS
  filters:
    platforms:
      - windows
```

### Linux

```yaml
cis-linux-events:
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
cis-macos-events:
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
    - NETWORK_CONNECTIONS
  filters:
    platforms:
      - macos
```

---

## 6. D&R Rules — Control 1 (Asset Inventory)

### 1.1 (IG1) — Sensor Enrollment Record

LC sensor enrollment itself is the asset-inventory signal. The rule below records `CODE_IDENTITY` first-seen events per sensor as an ongoing liveness signal — useful when feeding an external CMDB.

```yaml
name: cis-1-1-sensor-asset-record
detect:
  event: CODE_IDENTITY
  op: exists
  path: event/HASH
respond:
  - action: report
    name: cis-1-1-sensor-asset-record
    priority: 1
    metadata:
      cis_safeguard: '1.1'
      description: Asset inventory signal — CODE_IDENTITY first-seen per sensor
    suppression:
      max_count: 1
      period: 24h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-1-1-sensor-asset-record
tags:
  - cis-v8
  - inventory
comment: 'CIS 1.1 (IG1) — One inventory signal per sensor per day from CODE_IDENTITY. Route to CMDB output.'
```

### 1.2 (IG1) — Sensor Going Offline (Unauthorized Asset Disconnect)

Detection of a previously-enrolled sensor going offline can surface unauthorized decommissioning. Use the `deployment` output stream in an external monitor rather than a D&R rule — D&R rules run on telemetry events, not sensor liveness.

**Alternative (LCQL):** schedule a query such as `SELECT sid, hostname FROM sensors WHERE last_seen < NOW() - INTERVAL '7 days'` and route results to the CMDB.

---

## 7. D&R Rules — Control 2 (Software Inventory)

### 2.3 (IG1) — Unauthorised Binary via CODE_IDENTITY + Allowlist Lookup

Requires a lookup named `software-allowlist` keyed by SHA-256 hash. Create per Section 20.

```yaml
name: cis-2-3-unauthorized-binary
detect:
  event: CODE_IDENTITY
  op: and
  rules:
    - op: exists
      path: event/HASH
    - op: lookup
      not: true
      resource: 'lcr://lookup/software-allowlist'
      path: event/HASH
respond:
  - action: report
    name: cis-2-3-unauthorized-binary
    priority: 3
    metadata:
      cis_safeguard: '2.3'
      description: Binary hash not in approved software allowlist
      mitre_attack_id: T1204.002
      mitre_tactic: execution
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.HASH }}'
tags:
  - cis-v8
  - inventory
comment: 'CIS 2.3 (IG1) — Detection-only allowlist. Enforcement is WDAC/AppLocker/Gatekeeper.'
```

### 2.5 (IG2) — Unsigned Binary Loaded from System Path

```yaml
name: cis-2-5-unsigned-in-system-path
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
    name: cis-2-5-unsigned-in-system-path
    priority: 3
    metadata:
      cis_safeguard: '2.5'
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
  - cis-v8
  - inventory
comment: 'CIS 2.5 (IG2) — Unsigned binaries in trusted paths on Windows/macOS.'
```

### 2.7 (IG3) — Unauthorized Script Interpreter Execution

```yaml
name: cis-2-7-script-interpreter-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(wscript|cscript|mshta)\.exe$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\.(js|jse|vbs|vbe|wsf|wsh)\b'
respond:
  - action: report
    name: cis-2-7-script-interpreter-windows
    priority: 3
    metadata:
      cis_safeguard: '2.7'
      description: Windows script host invocation with script file argument
      mitre_attack_id: T1059.005
      mitre_tactic: execution
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-2-7-script-interpreter-windows
tags:
  - cis-v8
  - inventory
comment: 'CIS 2.7 (IG3) — wscript/cscript/mshta executing scripts.'
```

```yaml
name: cis-2-7-script-interpreter-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(python|python3|perl|ruby|php|bash|sh|ksh|zsh)$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\s(-c|-e)\s+'
respond:
  - action: report
    name: cis-2-7-script-interpreter-linux
    priority: 2
    metadata:
      cis_safeguard: '2.7'
      description: Linux interpreter with inline code — potential unauthorised script
      mitre_attack_id: T1059
      mitre_tactic: execution
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-2-7-script-interpreter-linux
tags:
  - cis-v8
  - inventory
comment: 'CIS 2.7 (IG3) — Linux inline-code interpreter invocations.'
```

```yaml
name: cis-2-7-script-interpreter-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(osascript|python|python3|perl|ruby|bash|sh|zsh)$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\s(-e|-c)\s+'
respond:
  - action: report
    name: cis-2-7-script-interpreter-macos
    priority: 2
    metadata:
      cis_safeguard: '2.7'
      description: macOS interpreter with inline code
      mitre_attack_id: T1059
      mitre_tactic: execution
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-2-7-script-interpreter-macos
tags:
  - cis-v8
  - inventory
comment: 'CIS 2.7 (IG3) — macOS inline-code interpreter invocations.'
```

---

## 8. D&R Rules — Control 3 (Data Protection)

### 3.13 (IG3) — Cloud-Storage CLI (Potential Exfil)

```yaml
name: cis-3-13-cloud-exfil-cli
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: matches
      path: event/FILE_PATH
      re: '(?i)[/\\](aws|gsutil|azcopy|rclone|mega-cli|megaget|megasync|dropbox-uploader)(\.exe)?$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\b(cp|sync|put|upload|push|copy)\b'
respond:
  - action: report
    name: cis-3-13-cloud-exfil-cli
    priority: 3
    metadata:
      cis_safeguard: '3.13'
      description: Cloud-storage CLI invocation with upload/sync verb
      mitre_attack_id: T1567.002
      mitre_tactic: exfiltration
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.USER_NAME }}'
tags:
  - cis-v8
  - integrity
comment: 'CIS 3.13 (IG3) — Cloud-storage CLI with upload verb across all platforms.'
```

### 3.13 (IG3) — Archive Creation Before Network Egress

A narrow indicator — archive tools spawning in temp/Download directories. Tune aggressively.

```yaml
name: cis-3-13-archive-staging
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: matches
      path: event/FILE_PATH
      re: '(?i)[/\\](7z|7za|rar|zip|tar|gzip)(\.exe)?$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)(-p[^\s]+|--password|--encrypt)'
respond:
  - action: report
    name: cis-3-13-archive-staging
    priority: 3
    metadata:
      cis_safeguard: '3.13'
      description: Password-protected archive created — potential exfil staging
      mitre_attack_id: T1560.001
      mitre_tactic: collection
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-3-13-archive-staging
tags:
  - cis-v8
  - integrity
comment: 'CIS 3.13 (IG3) — Password-protected archive creation — exfil staging indicator.'
```

### 3.14 (IG3) — LSASS Access (Credential Dumping)

```yaml
name: cis-3-14-lsass-access
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
    name: cis-3-14-lsass-access
    priority: 5
    metadata:
      cis_safeguard: '3.14'
      description: Sensitive handle to LSASS — credential-dumping indicator
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-3-14-lsass-access
tags:
  - cis-v8
  - integrity
comment: 'CIS 3.14 (IG3) — LSASS access on Windows.'
```

### 3.14 (IG3) — Shadow File Read (Linux)

```yaml
name: cis-3-14-shadow-read-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)(cat|less|more|head|tail|strings|grep|awk|sed)\s+.*/etc/(shadow|gshadow)\b'
respond:
  - action: report
    name: cis-3-14-shadow-read-linux
    priority: 4
    metadata:
      cis_safeguard: '3.14'
      description: Read of /etc/shadow or /etc/gshadow
      mitre_attack_id: T1003.008
      mitre_tactic: credential-access
tags:
  - cis-v8
  - integrity
comment: 'CIS 3.14 (IG3) — Shadow file read via common utilities.'
```

### 3.14 (IG3) — Credential-Dumping Tool (Linux)

```yaml
name: cis-3-14-credential-tool-linux
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is linux
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(mimipenguin|laZagne|pypykatz|procdump)$'
respond:
  - action: report
    name: cis-3-14-credential-tool-linux
    priority: 5
    metadata:
      cis_safeguard: '3.14'
      description: Credential-dumping tool executed on Linux
      mitre_attack_id: T1003
      mitre_tactic: credential-access
tags:
  - cis-v8
  - integrity
comment: 'CIS 3.14 (IG3) — Known credential-dumping binary execution on Linux.'
```

### 3.14 (IG3) — Keychain Access (macOS)

```yaml
name: cis-3-14-keychain-access-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/usr/bin/security$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\b(dump-keychain|find-generic-password|find-internet-password)\b'
respond:
  - action: report
    name: cis-3-14-keychain-access-macos
    priority: 4
    metadata:
      cis_safeguard: '3.14'
      description: macOS security CLI used to dump or read keychain items
      mitre_attack_id: T1555.001
      mitre_tactic: credential-access
tags:
  - cis-v8
  - integrity
comment: 'CIS 3.14 (IG3) — security CLI with dump/find-password verbs.'
```

---

## 9. D&R Rules — Control 4 (Secure Configuration)

### 4.4 / 4.5 (IG1) — Firewall Changed (Windows)

```yaml
name: cis-4-4-firewall-changed-windows
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
    name: cis-4-4-firewall-changed-windows
    priority: 3
    metadata:
      cis_safeguard: '4.4, 4.5'
      description: Windows Firewall rule or setting changed
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - config-management
comment: 'CIS 4.4 / 4.5 (IG1) — Windows firewall changes (4946-4950).'
```

### 4.4 / 4.5 (IG1) — Firewall Changed (Linux)

```yaml
name: cis-4-4-firewall-changed-linux
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
    name: cis-4-4-firewall-changed-linux
    priority: 3
    metadata:
      cis_safeguard: '4.4, 4.5'
      description: Linux firewall modification (iptables / nft / firewall-cmd / ufw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - config-management
comment: 'CIS 4.4 / 4.5 (IG1) — Linux firewall changes.'
```

### 4.4 / 4.5 (IG1) — Firewall Changed (macOS)

```yaml
name: cis-4-4-firewall-changed-macos
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
    name: cis-4-4-firewall-changed-macos
    priority: 3
    metadata:
      cis_safeguard: '4.4, 4.5'
      description: macOS firewall modification (pfctl / socketfilterfw)
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - config-management
comment: 'CIS 4.4 / 4.5 (IG1) — macOS firewall changes.'
```

### 4.7 (IG1) — Default / Guest Account Enabled

```yaml
name: cis-4-7-default-account-enabled-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4722'
    - op: matches
      path: event/EVENT/EventData/TargetUserName
      re: '(?i)^(guest|administrator|defaultaccount|wdagutilityaccount)$'
respond:
  - action: report
    name: cis-4-7-default-account-enabled-windows
    priority: 4
    metadata:
      cis_safeguard: '4.7'
      description: Built-in / default account enabled on Windows
      mitre_attack_id: T1078.001
      mitre_tactic: persistence
tags:
  - cis-v8
  - config-management
comment: 'CIS 4.7 (IG1) — Default Windows account enabled (Guest/Administrator/DefaultAccount/WDAGUtilityAccount).'
```

### 4.8 (IG2) — Service Change

```yaml
name: cis-4-8-service-change
detect:
  event: SERVICE_CHANGE
  op: exists
  path: event/SVC_NAME
respond:
  - action: report
    name: cis-4-8-service-change
    priority: 2
    metadata:
      cis_safeguard: '4.8'
      description: Service configuration changed — review for unnecessary service
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-4-8-service-change
tags:
  - cis-v8
  - config-management
comment: 'CIS 4.8 (IG2) — Service changes on all platforms.'
```

### 4.9 (IG2) — DNS Resolver Configuration Change

```yaml
name: cis-4-9-dns-config-change
detect:
  event: FIM_HIT
  op: matches
  path: event/FILE_PATH
  re: '(?i)(/etc/resolv\.conf|/etc/resolver/.*|/etc/systemd/resolved\.conf|\\system32\\drivers\\etc\\hosts$)'
respond:
  - action: report
    name: cis-4-9-dns-config-change
    priority: 3
    metadata:
      cis_safeguard: '4.9'
      description: DNS resolver configuration changed
      mitre_attack_id: T1565.001
      mitre_tactic: impact
tags:
  - cis-v8
  - config-management
comment: 'CIS 4.9 (IG2) — DNS config drift. Requires FIM rules from Section 4.'
```

---

## 10. D&R Rules — Control 5 (Account Management)

### 5.1 (IG1) — Windows User Account Created

```yaml
name: cis-5-1-user-created-windows
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
    name: cis-5-1-user-created-windows
    priority: 3
    metadata:
      cis_safeguard: '5.1'
      description: Windows user account created
      mitre_attack_id: T1136.001
      mitre_tactic: persistence
tags:
  - cis-v8
  - access-control
comment: 'CIS 5.1 (IG1) — Windows local user creation (Event ID 4720).'
```

### 5.1 (IG1) — Windows Account Deleted

```yaml
name: cis-5-1-user-deleted-windows
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
    name: cis-5-1-user-deleted-windows
    priority: 3
    metadata:
      cis_safeguard: '5.1'
      description: Windows user account deleted
tags:
  - cis-v8
  - access-control
comment: 'CIS 5.1 (IG1) — Windows account deletion (Event ID 4726).'
```

### 5.1 (IG1) — Linux Account Management Binary

```yaml
name: cis-5-1-user-mgmt-linux
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
    name: cis-5-1-user-mgmt-linux
    priority: 3
    metadata:
      cis_safeguard: '5.1'
      description: Linux account management binary executed
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - cis-v8
  - access-control
comment: 'CIS 5.1 (IG1) — Linux user/group management (useradd, usermod, groupadd, ...).'
```

### 5.1 (IG1) — macOS Account Management via dscl / sysadminctl

```yaml
name: cis-5-1-user-mgmt-macos
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
    name: cis-5-1-user-mgmt-macos
    priority: 3
    metadata:
      cis_safeguard: '5.1'
      description: macOS account management invocation (dscl / sysadminctl)
      mitre_attack_id: T1136
      mitre_tactic: persistence
tags:
  - cis-v8
  - access-control
comment: 'CIS 5.1 (IG1) — macOS account management via dscl, sysadminctl, dsimport.'
```

### 5.3 (IG1) — Dormant Account Awakening (Windows)

Detect a first login after a long silence. Implemented via scheduled LCQL job comparing `WEL 4624` logon users per sensor against a per-sensor last-seen-user baseline. The D&R rule below captures the signal for review; the dormancy calculation lives in a scheduled job.

```yaml
name: cis-5-3-interactive-logon-windows
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
    - op: or
      rules:
        - op: is
          path: event/EVENT/EventData/LogonType
          value: '2'
        - op: is
          path: event/EVENT/EventData/LogonType
          value: '10'
respond:
  - action: report
    name: cis-5-3-interactive-logon-windows
    priority: 1
    metadata:
      cis_safeguard: '5.3'
      description: Interactive or RemoteInteractive logon — feeds dormancy analytics
    suppression:
      max_count: 1
      period: 24h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.EVENT.EventData.TargetUserName }}'
tags:
  - cis-v8
  - access-control
comment: 'CIS 5.3 (IG1) — One record per user per sensor per day. Feeds dormancy analytics.'
```

### 5.4 (IG1) — Privileged Logon

```yaml
name: cis-5-4-privileged-logon-windows
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
    name: cis-5-4-privileged-logon-windows
    priority: 2
    metadata:
      cis_safeguard: '5.4'
      description: Special privileges assigned to new logon session
      mitre_attack_id: T1078
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-5-4-privileged-logon-windows
tags:
  - cis-v8
  - access-control
comment: 'CIS 5.4 (IG1) — Windows privileged logon (Event ID 4672).'
```

---

## 11. D&R Rules — Control 6 (Access Control)

### 6.8 (IG3) — User Added to Privileged Group (Windows)

```yaml
name: cis-6-8-user-added-to-group-windows
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
    name: cis-6-8-user-added-to-group-windows
    priority: 4
    metadata:
      cis_safeguard: '6.8'
      description: User added to a Windows security-enabled group
      mitre_attack_id: T1098
      mitre_tactic: persistence
tags:
  - cis-v8
  - access-control
comment: 'CIS 6.8 (IG3) — Windows group membership addition (4728, 4732, 4756).'
```

### 6.8 (IG3) — Linux sudo / su / pkexec

```yaml
name: cis-6-8-privilege-escalation-linux
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
    name: cis-6-8-privilege-escalation-linux
    priority: 2
    metadata:
      cis_safeguard: '6.8'
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
  - cis-v8
  - access-control
comment: 'CIS 6.8 (IG3) — Linux sudo/su/pkexec/doas, per-user per-hour.'
```

### 6.8 (IG3) — macOS sudo

```yaml
name: cis-6-8-sudo-macos
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
    name: cis-6-8-sudo-macos
    priority: 2
    metadata:
      cis_safeguard: '6.8'
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
  - cis-v8
  - access-control
comment: 'CIS 6.8 (IG3) — macOS sudo execution.'
```

---

## 12. D&R Rules — Control 7 (Vulnerability Management)

CIS Control 7 is primarily operational — run `os_packages` and `os_version` against the fleet, join against a CVE feed lookup, report on matches. No D&R rule captures this directly because the join happens post-hoc; the LCQL workflow below is preferred.

### 7.5 (IG2) — Scheduled `os_packages` Collection

A scheduled payload (pushed via reliable tasking) on each platform:

- **Windows:** `os_packages`
- **Linux:** task with payload running `dpkg-query -W -f='${Package} ${Version}\n'` or `rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}\n'`
- **macOS:** task with payload running `pkgutil --pkgs` + per-pkg `pkgutil --pkg-info <pkg>`

Invoke weekly via `limacharlie-iac` schedule or a cron-driven API caller.

### 7.5 (IG2) — CVE-Match via Lookup

Assumes a lookup `cve-feed` keyed `<product>:<version>` with a JSON value holding CVE IDs.

```yaml
name: cis-7-5-vulnerable-binary-load
detect:
  event: CODE_IDENTITY
  op: and
  rules:
    - op: exists
      path: event/HASH
    - op: lookup
      path: event/HASH
      resource: 'lcr://lookup/cve-feed-hashes'
respond:
  - action: report
    name: cis-7-5-vulnerable-binary-load
    priority: 3
    metadata:
      cis_safeguard: '7.5'
      description: Loaded binary hash matches a hash in the CVE feed lookup
    suppression:
      max_count: 5
      period: 24h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.HASH }}'
tags:
  - cis-v8
  - inventory
comment: 'CIS 7.5 (IG2) — Vulnerable-binary match via lookup keyed on hash. Populate the lookup from your vulnerability intel source.'
```

---

## 13. D&R Rules — Control 8 (Audit Log Management)

### 8.2 / 8.11 (IG1) — Windows Failed Logon

```yaml
name: cis-8-2-failed-logon-windows
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
    name: cis-8-2-failed-logon-windows
    priority: 3
    metadata:
      cis_safeguard: '8.2, 8.11'
      description: Failed Windows logon attempt
      mitre_attack_id: T1078
      mitre_tactic: initial-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-8-2-failed-logon-windows
tags:
  - cis-v8
  - audit
comment: 'CIS 8.2 / 8.11 (IG1) — Failed Windows logon (Event ID 4625).'
```

### 8.2 / 8.11 (IG1) — Windows Brute-Force Threshold

```yaml
name: cis-8-11-brute-force-windows
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
    name: cis-8-11-brute-force-windows
    priority: 4
    metadata:
      cis_safeguard: '8.11'
      description: Threshold — 10 failed Windows logons within 10 minutes
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      min_count: 10
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-8-11-brute-force-windows
tags:
  - cis-v8
  - audit
comment: 'CIS 8.11 (IG2) — Windows brute-force threshold.'
```

### 8.2 / 8.11 (IG1) — macOS Failed Auth via MUL

The native `SSH_LOGIN` event fires only on successful login and has no failure field. Failed SSH and authentication attempts on macOS must be matched on the Unified Log stream.

```yaml
name: cis-8-2-auth-failed-macos
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
    name: cis-8-2-auth-failed-macos
    priority: 3
    metadata:
      cis_safeguard: '8.2, 8.11'
      description: macOS authentication failure from Unified Log
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-8-2-auth-failed-macos
tags:
  - cis-v8
  - audit
comment: 'CIS 8.2 / 8.11 (IG1) — macOS authentication failures. Requires cis-mul-auth (Section 2).'
```

### 8.2 / 8.11 — Linux Failed Auth

LC Linux sensor does not emit `SSH_LOGIN`. Detection of failed auth on Linux relies on (a) auditd + file adapter (Section 3) or (b) the `/var/log/auth.log` file adapter. If the adapter is deployed, author D&R rules on the adapter event stream (the `text` platform) matching regex against `event/raw`.

Example adapter-stream rule:

```yaml
name: cis-8-2-failed-ssh-linux-adapter
detect:
  target: lctext
  op: and
  rules:
    - op: matches
      path: event/raw
      re: '(?i)sshd\[.*\]:\s+(Failed password|Invalid user|authentication failure)'
respond:
  - action: report
    name: cis-8-2-failed-ssh-linux-adapter
    priority: 3
    metadata:
      cis_safeguard: '8.2, 8.11'
      description: Failed SSH auth on Linux from auth.log adapter
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.hostname }}'
        - cis-8-2-failed-ssh-linux-adapter
tags:
  - cis-v8
  - audit
comment: 'CIS 8.2 / 8.11 — Linux failed SSH via file adapter on auth.log. Target is lctext because adapter events come from the text platform.'
```

### 8.2 / 8.11 (IG2) — Windows Account Lockout

```yaml
name: cis-8-11-account-lockout-windows
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
    name: cis-8-11-account-lockout-windows
    priority: 4
    metadata:
      cis_safeguard: '8.11'
      description: Windows account lockout — review for brute force / legitimate issue
      mitre_attack_id: T1110
      mitre_tactic: credential-access
tags:
  - cis-v8
  - audit
comment: 'CIS 8.11 (IG2) — Windows account lockout (Event ID 4740).'
```

### 8.2 / 8.11 — Security Event Log Cleared (Windows)

```yaml
name: cis-8-2-event-log-cleared
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
    name: cis-8-2-event-log-cleared
    priority: 5
    metadata:
      cis_safeguard: '8.2, 8.11'
      description: Windows Security event log was cleared — strong tampering indicator
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - cis-v8
  - audit
comment: 'CIS 8.2 (IG1) — Security log clearing (Event ID 1102).'
```

### 8.2 — Event Log Service Tampering (Windows)

```yaml
name: cis-8-2-eventlog-service-stop-windows
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
    name: cis-8-2-eventlog-service-stop-windows
    priority: 5
    metadata:
      cis_safeguard: '8.2'
      description: Attempt to stop event log service or clear event logs
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - cis-v8
  - audit
comment: 'CIS 8.2 (IG1) — Event log service tampering.'
```

### 8.2 — Linux Auditd Tampering

```yaml
name: cis-8-2-auditd-tamper-linux
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
    name: cis-8-2-auditd-tamper-linux
    priority: 5
    metadata:
      cis_safeguard: '8.2'
      description: Attempt to stop or disable Linux auditd
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - cis-v8
  - audit
comment: 'CIS 8.2 (IG1) — Linux auditd tampering.'
```

### 8.2 — macOS Unified Log Tampering

```yaml
name: cis-8-2-log-tamper-macos
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
    name: cis-8-2-log-tamper-macos
    priority: 5
    metadata:
      cis_safeguard: '8.2'
      description: Attempt to erase or disable macOS unified log
      mitre_attack_id: T1070
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - cis-v8
  - audit
comment: 'CIS 8.2 (IG1) — macOS log erase / disable.'
```

### 8.4 (IG2) — Time Change Detection

```yaml
name: cis-8-4-time-change-windows
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Security
    - op: is
      path: event/EVENT/System/EventID
      value: '4616'
respond:
  - action: report
    name: cis-8-4-time-change-windows
    priority: 3
    metadata:
      cis_safeguard: '8.4'
      description: System time was changed — possible anti-forensics
      mitre_attack_id: T1070.006
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - audit
comment: 'CIS 8.4 (IG2) — Windows time change (Event ID 4616).'
```

```yaml
name: cis-8-4-time-change-unix
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: or
      rules:
        - op: is linux
        - op: is mac
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(date|timedatectl|systemsetup)$'
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\s(-s|set-time|set-ntp|setdate|settimezone)\b'
respond:
  - action: report
    name: cis-8-4-time-change-unix
    priority: 3
    metadata:
      cis_safeguard: '8.4'
      description: System time/timezone change (Linux/macOS)
      mitre_attack_id: T1070.006
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - audit
comment: 'CIS 8.4 (IG2) — Linux/macOS time change via date / timedatectl / systemsetup.'
```

### 8.6 (IG2) — DNS Query Telemetry (All Platforms)

```yaml
name: cis-8-6-dns-telemetry
detect:
  event: DNS_REQUEST
  op: exists
  path: event/DOMAIN_NAME
respond:
  - action: report
    name: cis-8-6-dns-telemetry
    priority: 1
    metadata:
      cis_safeguard: '8.6'
      description: DNS query telemetry signal — review routed to SIEM, not alerted
    suppression:
      max_count: 1
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-8-6-dns-telemetry
tags:
  - cis-v8
  - audit
comment: 'CIS 8.6 (IG2) — DNS coverage proof. Low priority — this is a liveness signal, not an alert. Pair with SIEM output for full DNS history.'
```

### 8.8 (IG2) — Command-Line Audit (PowerShell Script Block Logging)

```yaml
name: cis-8-8-powershell-scriptblock
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Microsoft-Windows-PowerShell/Operational
    - op: is
      path: event/EVENT/System/EventID
      value: '4104'
respond:
  - action: report
    name: cis-8-8-powershell-scriptblock
    priority: 1
    metadata:
      cis_safeguard: '8.8'
      description: PowerShell script block logging event — command-line audit coverage
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-8-8-powershell-scriptblock
tags:
  - cis-v8
  - audit
comment: 'CIS 8.8 (IG2) — PowerShell 4104 coverage signal. Route to SIEM.'
```

### 8.11 — Audit Policy Changed (Windows)

```yaml
name: cis-8-11-audit-policy-changed
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
    name: cis-8-11-audit-policy-changed
    priority: 5
    metadata:
      cis_safeguard: '8.11'
      description: Audit policy changed — potential tampering with logging
      mitre_attack_id: T1562.002
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - audit
comment: 'CIS 8.11 (IG2) — Windows audit policy change (Event ID 4719).'
```

---

## 14. D&R Rules — Control 9 (Email & Browser)

### 9.1 (IG1) — Unsupported Browser (via Allowlist Lookup)

```yaml
name: cis-9-1-unsupported-browser
detect:
  event: CODE_IDENTITY
  op: and
  rules:
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(chrome|msedge|firefox|brave|opera|iexplore)\.exe$|/Applications/(Google Chrome|Firefox|Microsoft Edge|Safari|Brave Browser)\.app/Contents/MacOS/'
    - op: lookup
      not: true
      resource: 'lcr://lookup/supported-browsers'
      path: event/HASH
respond:
  - action: report
    name: cis-9-1-unsupported-browser
    priority: 2
    metadata:
      cis_safeguard: '9.1'
      description: Browser binary hash not in supported-version lookup
    suppression:
      max_count: 5
      period: 24h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - '{{ .event.HASH }}'
tags:
  - cis-v8
  - browser-email
comment: 'CIS 9.1 (IG1) — Browser hash not in supported-browsers lookup. Populate the lookup from your browser-management source.'
```

### 9.2 (IG1) — Malicious Domain via DNS Lookup

```yaml
name: cis-9-2-malicious-domain-dns
detect:
  event: DNS_REQUEST
  op: lookup
  path: event/DOMAIN_NAME
  resource: 'lcr://lookup/malicious-domains'
respond:
  - action: report
    name: cis-9-2-malicious-domain-dns
    priority: 4
    metadata:
      cis_safeguard: '9.2'
      description: DNS request to a domain present in the malicious-domains lookup
      mitre_attack_id: T1071.004
      mitre_tactic: command-and-control
tags:
  - cis-v8
  - browser-email
comment: 'CIS 9.2 (IG1) — Malicious domain DNS match. Populate the lookup from your threat intel feed.'
```

### 9.3 (IG2) — Browser Spawning Shell / Interpreter (Windows)

```yaml
name: cis-9-3-browser-spawning-shell-windows
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/PARENT/FILE_PATH
      re: '(?i)\\(chrome|msedge|firefox|brave|opera)\.exe$'
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(cmd|powershell|pwsh|wscript|cscript|mshta)\.exe$'
respond:
  - action: report
    name: cis-9-3-browser-spawning-shell-windows
    priority: 4
    metadata:
      cis_safeguard: '9.3'
      description: Browser spawning command-line interpreter — browser-exploit indicator
      mitre_attack_id: T1204
      mitre_tactic: execution
tags:
  - cis-v8
  - browser-email
comment: 'CIS 9.3 (IG2) — Windows browser -> shell parent-child.'
```

### 9.3 (IG2) — Browser Spawning Shell (macOS)

```yaml
name: cis-9-3-browser-spawning-shell-macos
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is mac
    - op: matches
      path: event/PARENT/FILE_PATH
      re: '(?i)/(Google Chrome|Firefox|Microsoft Edge|Safari|Brave Browser)\.app/Contents/MacOS/'
    - op: matches
      path: event/FILE_PATH
      re: '(?i)/(bash|sh|zsh|osascript|python|python3)$'
respond:
  - action: report
    name: cis-9-3-browser-spawning-shell-macos
    priority: 4
    metadata:
      cis_safeguard: '9.3'
      description: macOS browser spawning shell or scripting host
      mitre_attack_id: T1204
      mitre_tactic: execution
tags:
  - cis-v8
  - browser-email
comment: 'CIS 9.3 (IG2) — macOS browser -> shell parent-child.'
```

### 9.4 (IG2) — Browser Extension Change

```yaml
name: cis-9-4-browser-extension-change
detect:
  event: FIM_HIT
  op: matches
  path: event/FILE_PATH
  re: '(?i)(\\AppData\\.*\\Extensions\\|/Library/Application Support/.*(Chrome|Firefox|Edge).*/Extensions/|/\.config/.*(chrome|chromium)/.*/Extensions/|/\.mozilla/firefox/.*/extensions/)'
respond:
  - action: report
    name: cis-9-4-browser-extension-change
    priority: 3
    metadata:
      cis_safeguard: '9.4'
      description: Browser extension directory change
      mitre_attack_id: T1176
      mitre_tactic: persistence
tags:
  - cis-v8
  - browser-email
comment: 'CIS 9.4 (IG2) — Browser extension dir changes. Requires FIM rules from Section 4.'
```

### 9.6 (IG2) — Blocked File-Type Download via Browser

```yaml
name: cis-9-6-disallowed-filetype-download
detect:
  event: FILE_CREATE
  op: and
  rules:
    - op: or
      rules:
        - op: is windows
        - op: is mac
    - op: matches
      path: event/CREATING_PROCESS/FILE_PATH
      re: '(?i)\\(chrome|msedge|firefox|brave|opera)\.exe$|/(Google Chrome|Firefox|Microsoft Edge|Safari|Brave Browser)\.app/'
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\.(scr|pif|hta|vbs|vbe|js|jse|wsf|wsh|ps1|lnk|iso|img|vhd|vhdx)$'
respond:
  - action: report
    name: cis-9-6-disallowed-filetype-download
    priority: 3
    metadata:
      cis_safeguard: '9.6'
      description: Disallowed filetype downloaded by browser
      mitre_attack_id: T1204.002
      mitre_tactic: execution
tags:
  - cis-v8
  - browser-email
comment: 'CIS 9.6 (IG2) — Browser download of high-risk extensions on Windows/macOS.'
```

---

## 15. D&R Rules — Control 10 (Malware Defenses)

### 10.1 (IG1) — YARA Detection (All Platforms)

```yaml
name: cis-10-1-yara-detection
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: cis-10-1-yara-detection
    priority: 5
    metadata:
      cis_safeguard: '10.1'
      description: YARA rule match — possible malware
      mitre_tactic: execution
tags:
  - cis-v8
  - malware
comment: 'CIS 10.1 (IG1) — YARA detection on any platform.'
```

### 10.1 (IG1) — Defender Threat Detected

```yaml
name: cis-10-1-defender-threat
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
    name: cis-10-1-defender-threat
    priority: 4
    metadata:
      cis_safeguard: '10.1'
      description: Windows Defender detected or acted on a threat
      mitre_tactic: execution
tags:
  - cis-v8
  - malware
comment: 'CIS 10.1 (IG1) — Defender threat alerts (1116, 1117).'
```

### 10.1 (IG1) — Defender Config Change

```yaml
name: cis-10-1-defender-config-change
detect:
  event: WEL
  op: and
  rules:
    - op: is
      path: event/EVENT/System/Channel
      value: Microsoft-Windows-Windows Defender/Operational
    - op: is
      path: event/EVENT/System/EventID
      value: '5007'
respond:
  - action: report
    name: cis-10-1-defender-config-change
    priority: 4
    metadata:
      cis_safeguard: '10.1'
      description: Windows Defender configuration changed
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - malware
comment: 'CIS 10.1 (IG1) — Defender configuration drift (Event ID 5007).'
```

### 10.2 (IG1) — Defender Real-Time Protection Disabled

```yaml
name: cis-10-2-defender-rtp-disabled
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
    name: cis-10-2-defender-rtp-disabled
    priority: 5
    metadata:
      cis_safeguard: '10.2'
      description: Windows Defender real-time protection disabled
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - malware
comment: 'CIS 10.2 (IG1) — Defender RTP disabled (Event ID 5001).'
```

### 10.3 (IG1) — Removable Media Mount

```yaml
name: cis-10-3-volume-mount
detect:
  event: VOLUME_MOUNT
  op: or
  rules:
    - op: is windows
    - op: is mac
respond:
  - action: report
    name: cis-10-3-volume-mount
    priority: 2
    metadata:
      cis_safeguard: '10.3, 10.4'
      description: Volume mount — removable media attach
      mitre_attack_id: T1091
      mitre_tactic: lateral-movement
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-10-3-volume-mount
tags:
  - cis-v8
  - malware
comment: 'CIS 10.3 / 10.4 (IG1/IG2) — Volume mount on Win/macOS. No Linux equivalent event.'
```

### 10.5 (IG2) — Thread Injection (Windows)

```yaml
name: cis-10-5-thread-injection
detect:
  event: THREAD_INJECTION
  op: is windows
respond:
  - action: report
    name: cis-10-5-thread-injection
    priority: 4
    metadata:
      cis_safeguard: '10.5'
      description: Thread injection — process injecting code into another
      mitre_attack_id: T1055
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-10-5-thread-injection
tags:
  - cis-v8
  - malware
comment: 'CIS 10.5 (IG2) — Thread injection detection.'
```

### 10.5 (IG2) — Module Memory/Disk Mismatch (All Platforms)

```yaml
name: cis-10-5-module-mem-disk-mismatch
detect:
  event: MODULE_MEM_DISK_MISMATCH
  op: exists
  path: event/FILE_PATH
respond:
  - action: report
    name: cis-10-5-module-mem-disk-mismatch
    priority: 4
    metadata:
      cis_safeguard: '10.5'
      description: In-memory module differs from its on-disk copy — injection indicator
      mitre_attack_id: T1055.002
      mitre_tactic: defense-evasion
tags:
  - cis-v8
  - malware
comment: 'CIS 10.5 (IG2) — Module mem/disk drift across platforms.'
```

### 10.7 (IG3) — LOLBin Abuse with Network Indicators (Windows)

```yaml
name: cis-10-7-lolbin-execution-windows
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
    name: cis-10-7-lolbin-execution-windows
    priority: 4
    metadata:
      cis_safeguard: '10.7'
      description: LOLBin execution with network or download indicators
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
  - cis-v8
  - malware
comment: 'CIS 10.7 (IG3) — Windows LOLBin behavioural detection.'
```

### 10.7 (IG3) — Encoded PowerShell (Windows)

```yaml
name: cis-10-7-encoded-powershell
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
    name: cis-10-7-encoded-powershell
    priority: 4
    metadata:
      cis_safeguard: '10.7'
      description: PowerShell executed with encoded command — common obfuscation
      mitre_attack_id: T1059.001
      mitre_tactic: execution
tags:
  - cis-v8
  - malware
comment: 'CIS 10.7 (IG3) — Encoded PowerShell behavioural detection.'
```

### 10.7 (IG3) — Linux LOLBin Download-and-Execute

```yaml
name: cis-10-7-lolbin-execution-linux
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
    name: cis-10-7-lolbin-execution-linux
    priority: 4
    metadata:
      cis_safeguard: '10.7'
      description: Linux download-and-execute pattern
      mitre_attack_id: T1059.004
      mitre_tactic: execution
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-10-7-lolbin-execution-linux
tags:
  - cis-v8
  - malware
comment: 'CIS 10.7 (IG3) — Linux download-and-execute behavioural pattern.'
```

### 10.7 (IG3) — macOS osascript Shell-Out

```yaml
name: cis-10-7-osascript-network-macos
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
    name: cis-10-7-osascript-network-macos
    priority: 4
    metadata:
      cis_safeguard: '10.7'
      description: macOS osascript invoking shell or network utility
      mitre_attack_id: T1059.002
      mitre_tactic: execution
tags:
  - cis-v8
  - malware
comment: 'CIS 10.7 (IG3) — macOS osascript shell-out behavioural detection.'
```

### 10.7 (IG3) — Suspicious Named Pipe (Windows C2)

```yaml
name: cis-10-7-suspicious-named-pipe
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
    name: cis-10-7-suspicious-named-pipe
    priority: 4
    metadata:
      cis_safeguard: '10.7'
      description: Known-bad named pipe pattern — possible C2 framework
      mitre_attack_id: T1570
      mitre_tactic: lateral-movement
tags:
  - cis-v8
  - malware
comment: 'CIS 10.7 (IG3) — C2 named pipe patterns (Cobalt Strike, Meterpreter, etc.).'
```

### 10.7 (IG3) — Shadow Copy Deletion (Ransomware Indicator)

```yaml
name: cis-10-7-shadow-copy-delete
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: or
      rules:
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\bvssadmin(\.exe)?\s+delete\s+shadows'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\bwmic(\.exe)?\s+.*shadowcopy\s+delete'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\bbcdedit(\.exe)?\s+.*recoveryenabled\s+no'
        - op: matches
          path: event/COMMAND_LINE
          re: '(?i)\bwbadmin(\.exe)?\s+delete\s+catalog'
respond:
  - action: report
    name: cis-10-7-shadow-copy-delete
    priority: 5
    metadata:
      cis_safeguard: '10.7'
      description: Shadow copy / recovery deletion — ransomware pre-encryption indicator
      mitre_attack_id: T1490
      mitre_tactic: impact
  - action: add tag
    tag: ransomware-indicator
    ttl: 604800
tags:
  - cis-v8
  - malware
comment: 'CIS 10.7 (IG3) — Shadow copy / recovery data deletion, strong ransomware signal.'
```

---

## 16. D&R Rules — Control 13 (Network Monitoring)

### 13.1 (IG2) — Central Alerting Signal (Generic)

Centralised alerting is delivered by routing the `detect` output stream to the SIEM/chat sink (see Section 21). No single D&R rule represents 13.1 — it is an output configuration.

### 13.2 (IG2) — Host-Based IDS Coverage Signal

The presence of `YARA_DETECTION`, `THREAD_INJECTION`, `SENSITIVE_PROCESS_ACCESS`, `HIDDEN_MODULE_DETECTED`, and `MODULE_MEM_DISK_MISMATCH` in the exfil configuration (Section 5) satisfies 13.2.

### 13.6 (IG2) — Outbound Connection to Public IP from Scripting Tool

```yaml
name: cis-13-6-suspicious-outbound
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
    name: cis-13-6-suspicious-outbound
    priority: 3
    metadata:
      cis_safeguard: '13.6'
      description: Outbound public-IP connection from command-line or scripting utility
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
  - cis-v8
  - network-monitoring
comment: 'CIS 13.6 (IG2) — Outbound from scripting/LOLBin processes.'
```

### 13.6 (IG2) — Non-Standard SSH Destination Port

```yaml
name: cis-13-6-nonstandard-ssh-port
detect:
  event: NEW_TCP4_CONNECTION
  op: and
  rules:
    - op: matches
      path: event/PROCESS/FILE_PATH
      re: '(?i)(/ssh$|\\ssh\.exe$)'
    - op: is
      not: true
      path: event/NETWORK_ACTIVITY/DESTINATION/PORT
      value: '22'
    - op: is public address
      path: event/NETWORK_ACTIVITY/DESTINATION/IP_ADDRESS
respond:
  - action: report
    name: cis-13-6-nonstandard-ssh-port
    priority: 3
    metadata:
      cis_safeguard: '13.6'
      description: SSH client connecting on non-standard public port — possible C2/tunnel
      mitre_attack_id: T1021.004
      mitre_tactic: lateral-movement
tags:
  - cis-v8
  - network-monitoring
comment: 'CIS 13.6 (IG2) — Non-standard SSH port usage.'
```

### 13.7 (IG3) — Host Isolation on Critical Malware Detection (opt-in)

> Network isolation is disruptive. Deploy only with stakeholder approval for well-tuned, high-confidence detections. Uses the `isolate network` response action. Opt-in via sensor tag `isolation-enabled`.

```yaml
name: cis-13-7-isolate-on-credential-dump
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
    name: cis-13-7-isolate-on-credential-dump
    priority: 5
    metadata:
      cis_safeguard: '13.7'
      description: LSASS access on isolation-enabled host — automated containment
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
  - action: isolate network
tags:
  - cis-v8
  - network-monitoring
  - incident-response
comment: 'CIS 13.7 (IG3) — Opt-in HIPS-style isolation on credential dump.'
```

```yaml
name: cis-13-7-isolate-on-ransomware-indicator
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: is tagged
      tag: isolation-enabled
    - op: matches
      path: event/COMMAND_LINE
      re: '(?i)\bvssadmin(\.exe)?\s+delete\s+shadows'
respond:
  - action: report
    name: cis-13-7-isolate-on-ransomware-indicator
    priority: 5
    metadata:
      cis_safeguard: '13.7'
      description: Shadow-copy deletion on isolation-enabled host — ransomware signal
      mitre_attack_id: T1490
      mitre_tactic: impact
  - action: isolate network
  - action: add tag
    tag: ransomware-indicator
    ttl: 604800
tags:
  - cis-v8
  - network-monitoring
  - incident-response
comment: 'CIS 13.7 (IG3) — Isolate on ransomware pre-encryption indicator.'
```

### 13.11 (IG3) — Suppression Tuning Signal

Rule suppression (`max_count`, `period`, `min_count`) is the in-platform mechanism. Pair with:

- `/lc-essentials:fp-pattern-finder` for systematic FP analysis
- `/lc-essentials:detection-tuner` for manual tuning
- FP rules authored in the FP Rules section of the Web UI

---

## 17. D&R Rules — Control 16 (Application Software)

### 16.7 (IG2) — Office Macro Spawning Scripting / LOLBin

```yaml
name: cis-16-7-office-macro-spawn
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/PARENT/FILE_PATH
      re: '(?i)\\(winword|excel|powerpnt|outlook|msaccess)\.exe$'
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(cmd|powershell|pwsh|wscript|cscript|mshta|rundll32|regsvr32|certutil)\.exe$'
respond:
  - action: report
    name: cis-16-7-office-macro-spawn
    priority: 4
    metadata:
      cis_safeguard: '16.7'
      description: Office application spawning scripting/LOLBin child — macro indicator
      mitre_attack_id: T1204.002
      mitre_tactic: execution
tags:
  - cis-v8
  - browser-email
  - malware
comment: 'CIS 16.7 (IG2) — Office macro child-process detection on Windows.'
```

### 16.7 (IG2) — Office Application Spawning NEW_DOCUMENT from Temp

```yaml
name: cis-16-7-office-temp-document
detect:
  event: NEW_DOCUMENT
  op: and
  rules:
    - op: is windows
    - op: matches
      path: event/PROCESS/FILE_PATH
      re: '(?i)\\(winword|excel|powerpnt|outlook)\.exe$'
    - op: matches
      path: event/FILE_PATH
      re: '(?i)\\(Temp|AppData\\Local\\Temp|Downloads)\\'
respond:
  - action: report
    name: cis-16-7-office-temp-document
    priority: 2
    metadata:
      cis_safeguard: '16.7'
      description: Office application touched document in temp / downloads path
      mitre_attack_id: T1204.002
      mitre_tactic: execution
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-16-7-office-temp-document
tags:
  - cis-v8
  - browser-email
comment: 'CIS 16.7 (IG2) — Office document in temp — lure indicator.'
```

---

## 18. D&R Rules — Control 17 (Incident Response)

The Cases extension provides the incident-handling workflow end to end. The rules below are response-enrichment patterns that improve triage quality.

### 17.3 (IG1) — Critical-Severity Case Escalation

In ext-cases, detections with `priority >= 4` can be configured to auto-escalate to a case. The rule below explicitly tags critical events.

```yaml
name: cis-17-3-critical-tag
detect:
  event: YARA_DETECTION
  op: exists
  path: event/RULE_NAME
respond:
  - action: report
    name: cis-17-3-critical-tag
    priority: 5
    metadata:
      cis_safeguard: '17.3, 17.4'
      description: Critical YARA detection — tag for case triage
  - action: add tag
    tag: cis-incident
    ttl: 604800
tags:
  - cis-v8
  - incident-response
comment: 'CIS 17.3 / 17.4 (IG1/IG2) — Tag endpoints on critical detection (7-day TTL).'
```

### 17.4 (IG2) — Auto-Case on Audit-Tamper Tag

```yaml
name: cis-17-4-audit-tamper-to-case
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is tagged
      tag: audit-tamper
respond:
  - action: report
    name: cis-17-4-audit-tamper-to-case
    priority: 4
    metadata:
      cis_safeguard: '17.4'
      description: Post-tamper activity on host — correlation signal for incident case
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-17-4-audit-tamper-to-case
tags:
  - cis-v8
  - incident-response
comment: 'CIS 17.4 (IG2) — Correlates post-tamper activity for case enrichment.'
```

### 17.6 (IG2) — Notification Routing

Notification routing is an output configuration, not a D&R rule. Configure an output of type `slack` / `teams` / `pagerduty` / `email` filtered to the `detect` stream with `event_white_list` including the `cis-v8` tag. See Section 21.

### 17.9 (IG3) — Severity Threshold

D&R rule `priority` values set the implicit severity threshold. Convention used in this document:

- `1` — telemetry coverage signal (not an alert)
- `2` — informational (ok to batch review)
- `3` — notable, review within 24h
- `4` — suspicious, review within 4h
- `5` — critical, page on-call

---

## 19. D&R Rules — Control 18 (Pentest Support)

### 18.1 (IG2) — Tagged-Pentest Activity Record

Scope pentests by applying the `pentest-engagement-<id>` tag to participating endpoints before the engagement and removing after.

```yaml
name: cis-18-1-pentest-activity
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: is tagged
      tag: pentest
    - op: matches
      path: event/FILE_PATH
      re: '.*'
respond:
  - action: report
    name: cis-18-1-pentest-activity
    priority: 1
    metadata:
      cis_safeguard: '18.1'
      description: Activity on a pentest-tagged endpoint — recorded for scope tracking
    suppression:
      max_count: 100
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cis-18-1-pentest-activity
tags:
  - cis-v8
  - pentest
comment: 'CIS 18.1 (IG2) — Records process activity on pentest-tagged hosts. Priority 1 — informational only.'
```

### 18.4 (IG3) — Pentest Detection-Coverage Review

Post-engagement, query the detection stream filtered to the `pentest` sensor tag and the engagement window:

```
SELECT rule_name, COUNT(*) FROM detections
WHERE sensor_tag = 'pentest' AND ts BETWEEN <start> AND <end>
GROUP BY rule_name ORDER BY COUNT(*) DESC
```

Produce a coverage report comparing:
- MITRE ATT&CK techniques attempted by the pentester (recorded in their report)
- Techniques detected by LC rules during the window

Gaps inform 18.4 findings.

---

## 20. Lookups

Several rules depend on lookups. Create them via:

```
limacharlie hive add --hive-name lookup --name <name> --file <file.json>
```

### `software-allowlist`

Approved-software hash list, keyed on SHA-256.

```json
{
  "keys": ["sha256"],
  "expected_keys": ["sha256"],
  "data": {
    "aaaa...bbbb": {"name": "notepad.exe", "version": "10.0.19041"}
  }
}
```

### `supported-browsers`

Approved browser hashes, keyed on SHA-256. Updated via scheduled job that diffs vendor release feeds against deployed hashes.

### `malicious-domains`

Threat intel feed — blocklist of domains. Populate from internal feeds (MISP, commercial IoC provider, DNS-RPZ export).

### `cve-feed-hashes`

Map of known-vulnerable binary hashes to CVE IDs. Populate from vulnerability management tool export or public sources (e.g., LOLBAS project for living-off-the-land utilities).

> Lookups are not validated by `limacharlie dr validate` replay (the validator flags `external resources like lookup and api are not currently supported in replay`) — the rule passes validation, but runtime matches require the lookup to exist in the org.

---

## 21. Outputs for Centralisation and Retention (8.9, 8.10)

### Central SIEM (CIS 8.9)

Route detections and events to the organisation's SIEM. Example — Splunk HEC:

```yaml
cis-output-splunk-detect:
  module: splunk
  type: detect
  dest_host: splunk.corp.example:8088
  dest_token: <hec-token>
  is_compression: true
  tag: cis-v8
```

Substitute `module: elastic`, `chronicle`, `sentinel`, or `syslog` to match the enterprise SIEM.

### Cold Archival (CIS 8.10 Beyond 90 Days)

```yaml
cis-output-s3-archive:
  module: s3
  type: event
  bucket: cis-audit-archive
  access_key: <access-key>
  secret_key: <secret-key>
  region: us-east-1
  is_compression: true
```

For multi-year retention (HIPAA 6 yr, PCI 1 yr, SOX 7 yr, FedRAMP High), apply S3 Object Lock in governance or compliance mode and a retention lifecycle rule. Typical cost profile: ~$0.023/GB/mo for S3 Standard, ~$0.004/GB/mo for Glacier Instant Retrieval, and ~$0.00099/GB/mo for Glacier Deep Archive (check AWS pricing for current rates).

### Chat/Ticketing Alert Routing (CIS 13.1, 17.6)

```yaml
cis-output-slack:
  module: slack
  type: detect
  webhook_url: https://hooks.slack.com/services/XXX
  event_white_list:
    - tag == "cis-v8"
  custom_transform:
    channel: '#secops-alerts'
    username: LimaCharlie
    text: '{{ .event.detect.name }} — {{ .routing.hostname }}'
```

---

## 22. Recommended Extensions

### Required

| Extension | Purpose | CIS Safeguards |
|---|---|---|
| **Reliable Tasking** | Prerequisite for Artifact Collection. Ensures tasks reach offline sensors. | 8.2 (enables WEL / MUL / file collection) |
| **Artifact Collection (ext-artifact)** | Manages WEL/MUL streaming and file/log retention. | 8.2, 8.3, 8.5, 8.10 |
| **Exfil Control (ext-exfil)** | Manages which event types flow from sensor to cloud. | 8.2, 8.5, 8.6, 8.8 |
| **Integrity (ext-integrity)** | FIM / RIM rule management. | 3.14, 4.9, 8.5, 9.4, 10.3 |

### Strongly Recommended

| Extension | Purpose | CIS Safeguards |
|---|---|---|
| **Cases (ext-cases)** | SOC case management — detection-to-case conversion, SLA tracking, investigation workflows, audit trail. | 17.3, 17.4, 17.5, 17.7, 17.8, 17.9 |
| **EPP (Endpoint Protection)** | Unified Windows Defender management and event collection. Free. | 10.1, 10.2, 10.6 |
| **Soteria EDR Rules** | Managed detection ruleset with MITRE ATT&CK mapping across 14 event types. | 10.7, 13.2, 13.11 |
| **Sigma Rules** | Community and commercial Sigma rule conversion. | 10.7, 13.2 |

### Recommended for Enhanced Coverage

| Extension | Purpose | CIS Safeguards |
|---|---|---|
| **Strelka** | File analysis engine (YARA, PE analysis, archive extraction) for files transiting endpoints. | 10.1, 10.7, 16.4 |
| **Zeek** | Network monitoring and analysis on a Linux network-monitor sensor. | 13.3, 13.6, 1.5 |
| **Velociraptor** | DFIR hunting and artifact collection for incident response. | 17.4, 17.8 |
| **Playbook** | Python-based automation for custom response workflows. | 17.4, 17.6, 13.7 |
| **ext-git-sync** | Infrastructure as Code — D&R rules, FIM, outputs, extensions managed via git. | 4.1, 8.1, 8.11, 16.1 |

---

## 23. Deployment Notes

### Retention (CIS 8.10)

CIS Safeguard 8.10 requires **at least 90 days** of audit-log retention. Insight default meets this minimum. Extend via S3/GCS output for:

- IG3 organisations
- Any organisation with a regulatory overlay (HIPAA 6 yr, PCI 1 yr, SOX 7 yr, FedRAMP High multi-year)
- Organisations requiring long-window historical search — pair with a SIEM output (Splunk, Chronicle, Elastic, Sentinel)

All artifact collection rules in this document use `days_retention: 90` to match the 8.10 baseline. Tune per your retention policy.

### Tagging Strategy

All D&R rules use the `cis-v8` tag plus a family tag (`audit`, `access-control`, `malware`, `integrity`, `network-monitoring`, `incident-response`, `config-management`, `inventory`, `browser-email`, `pentest`). This enables:

- Filtering detections by framework in the Cases UI
- Routing CIS-specific detections to a dedicated output
- Separating CIS rule coverage from operational / custom detections in metrics
- Per-family dashboarding (e.g., all `audit` detections across all sensors)

### Suppression Tuning

Many rules include starting-point suppression. Tune after deployment:

1. Run for a 7-day burn-in period
2. Use `/lc-essentials:fp-pattern-finder` to identify systematic noise
3. Author FP rules for known-safe patterns (service accounts, approved admin tools, patching windows, scheduled scans)

### Windows Audit Policy Prerequisites

Windows endpoints need the **Advanced Audit Policy** configured. Minimum categories for the rules in this document:

| Audit Category | Subcategory | Setting |
|---|---|---|
| Account Logon | Credential Validation | Success, Failure |
| Account Management | User Account Management | Success, Failure |
| Account Management | Security Group Management | Success, Failure |
| Detailed Tracking | Process Creation | Success |
| Logon/Logoff | Logon | Success, Failure |
| Logon/Logoff | Logoff | Success |
| Object Access | File System | Success, Failure |
| Object Access | Removable Storage | Success, Failure |
| Policy Change | Audit Policy Change | Success, Failure |
| Privilege Use | Sensitive Privilege Use | Success, Failure |
| System | Security State Change | Success |
| System | System Integrity | Success, Failure |

Deploy via Group Policy: `Computer Configuration → Windows Settings → Security Settings → Advanced Audit Policy Configuration`.

Also enable:
- **PowerShell Script Block Logging** — `Computer Configuration → Administrative Templates → Windows Components → Windows PowerShell → Turn on PowerShell Script Block Logging`
- **Process Command Line Auditing** — `Include command line in process creation events` (enables full `COMMAND_LINE` in Event ID 4688; LC `NEW_PROCESS` has this natively, but the WEL version is useful for non-LC workflows)

### Linux Audit Policy Prerequisites

Deploy the auditd rules from Section 3 via Ansible / Puppet / Chef / cloud-init. Verify with `auditctl -l`. Ensure `/var/log/audit/audit.log` rotation retains at minimum the Insight retention window (default 90 days) — tune `max_log_file_action` and `max_log_file` in `/etc/audit/auditd.conf`.

For CIS 8.6 (DNS query audit logs) on Linux, the LC sensor's native `DNS_REQUEST` event is sufficient. If systemd-resolved is in use, augment with the systemd-resolved log via file adapter on `/var/log/syslog` filtered for `systemd-resolved`.

### macOS Audit Policy Prerequisites

macOS Unified Log retention is managed via `log config` policies. Default retention is often shorter than 90 days — validate on a sample endpoint with `log stats --overview`. Adjust predicate patterns (Section 2) to balance visibility with volume.

For MUL rules to fire, MUL must be listed in the exfil rule for macOS (Section 5).

### Deployment Order

1. Enable **Reliable Tasking**, **Artifact Collection**, **Exfil Control**, **Integrity** extensions
2. Deploy Windows WEL artifact collection rules (Section 1)
3. Deploy macOS MUL artifact collection rules (Section 2)
4. Deploy Linux auditd rules + file adapter or artifact rules (Section 3)
5. Deploy FIM rules per platform (Section 4)
6. Deploy exfil event rules per platform (Section 5)
7. Populate lookups from Section 20 (at minimum `malicious-domains`)
8. Deploy D&R rules (Sections 6–19) — detections begin firing
9. Configure outputs (Section 21) — SIEM + Slack/PagerDuty for 13.1 and 17.6 alerting
10. Configure S3/GCS output (Section 21) — needed for 8.10 beyond Insight default
11. Enable **Cases (ext-cases)** — detections convert to trackable cases for Control 17
12. Subscribe to **Soteria** and/or **Sigma** — adds managed detection coverage for 10.7
13. Burn-in for 7 days, then tune via `/lc-essentials:fp-pattern-finder`
14. Validate coverage against a tabletop exercise (Control 17.7) before declaring IG2/IG3 compliance

### Implementation-Group Phased Rollout

| Phase | Target | Sections | Safeguards Covered |
|---|---|---|---|
| IG1 Foundation | Small org minimum | 1, 3, 4, 5 (Windows+macOS), 6 (1.1), 7 (2.1, 2.3), 8 (3.14 LSASS), 9 (4.4, 4.5, 4.7), 10 (5.1, 5.4), 13 (8.2, 8.11 core), 14 (9.1, 9.2), 15 (10.1, 10.2, 10.3) | 1.1, 2.1–2.3, 4.4–4.7, 5.1, 5.3, 5.4, 8.1–8.3, 9.1–9.2, 10.1–10.3, 17.3 |
| IG2 Essential | Medium org | + 7 (2.4–2.6), 9 (4.8, 4.9), 11 (6.6, 6.8), 12 (7.5), 13 (8.4–8.8, 8.11 extra), 14 (9.3, 9.4, 9.6), 15 (10.4–10.6), 16 (13.1–13.3, 13.6, 13.11), 17 (16.4–16.7), 18 (17.4–17.7, 17.9) | All of IG1 + 2.4–2.6, 4.8–4.9, 6.8, 7.5, 8.4–8.11, 9.3–9.6, 10.4–10.6, 13.1–13.6, 13.11, 16.4–16.7, 17.4–17.7, 17.9, 18.1 |
| IG3 Advanced | Large/regulated org | + 7 (2.7), 8 (3.13, 3.14 full), 12 (7.5 hash-match), 13 (8.12), 15 (10.7), 16 (13.7), 19 (18.4) | All of IG2 + 2.7, 3.13, 3.14, 8.12, 10.7, 13.7, 17.8, 18.4 |

### Validation

Every YAML rule in this document passes `limacharlie dr validate`. For end-to-end validation against historical telemetry, use `limacharlie dr replay` against recent data from representative endpoints (one Windows, one Linux, one macOS). Rules using `lookup` operators report `external resources like lookup and api are not currently supported in replay` during replay — this is expected; runtime behaviour is correct once the lookup is populated.

### Cross-Framework Savings

Because the 800-53 and CIS v8 detections share underlying mechanisms, organisations running both frameworks can author a single rule set tagged with both `nist-800-53` and `cis-v8` tags. The rule `metadata.cis_safeguard` and `metadata.nist_control` fields can be set independently. See [../nist-800-53/nist-800-53-limacharlie-implementation.md](../nist-800-53/nist-800-53-limacharlie-implementation.md) for the NIST-flavoured rule names and metadata.
