# CMMC Compliance Implementation Guide — LimaCharlie on Windows

Concrete D&R rules, artifact collection rules, FIM rules, and extension recommendations to satisfy CMMC Level 2 (NIST 800-171) and Level 3 (NIST 800-172) controls using LimaCharlie EDR on Windows endpoints.

This guide is a companion to [cmmc-limacharlie-mapping.md](cmmc-limacharlie-mapping.md), which maps CMMC controls to LimaCharlie capabilities at a conceptual level. This document provides the deployable configuration.

---

## Table of Contents

1. [Windows Event Log Artifact Collection Rules](#1-windows-event-log-artifact-collection-rules)
2. [File Integrity Monitoring (FIM) Rules](#2-file-integrity-monitoring-fim-rules)
3. [Exfil Event Collection Rules](#3-exfil-event-collection-rules)
4. [D&R Rules — Audit & Accountability (AU)](#4-dr-rules--audit--accountability-au)
5. [D&R Rules — Access Control (AC)](#5-dr-rules--access-control-ac)
6. [D&R Rules — System & Information Integrity (SI)](#6-dr-rules--system--information-integrity-si)
7. [D&R Rules — Incident Response (IR)](#7-dr-rules--incident-response-ir)
8. [D&R Rules — Configuration Management (CM)](#8-dr-rules--configuration-management-cm)
9. [D&R Rules — Identification & Authentication (IA)](#9-dr-rules--identification--authentication-ia)
10. [Recommended Extensions](#10-recommended-extensions)
11. [Deployment Notes](#11-deployment-notes)

---

## 1. Windows Event Log Artifact Collection Rules

These artifact collection rules use the `wel://` pattern to stream Windows Event Logs as first-class telemetry alongside native EDR events. This is the recommended approach over `.evtx` file collection because it produces real-time `WEL` events that D&R rules can evaluate immediately.

> **Prerequisite:** The **Reliable Tasking** extension must be enabled before configuring artifact collection rules.

The rules below use the extension configuration format (for `ext-artifact`). The `patterns` field uses `wel://ChannelName:*` syntax where `:*` collects all events from that channel. Deploy via the web UI (Artifact Collection section), the CLI (`limacharlie extension config-set`), or via ext-git-sync IaC.

### Security Log

The Windows Security log is the primary source for authentication, privilege use, account management, and object access auditing.

```yaml
cmmc-wel-security:
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

| Event ID | Category | CMMC Control |
|----------|----------|--------------|
| 4624 | Successful logon | AU.L2-3.3.1, AU.L2-3.3.2 |
| 4625 | Failed logon | AU.L2-3.3.1, AC.L2-3.1.8 |
| 4634 | Logoff | AU.L2-3.3.1 |
| 4647 | User-initiated logoff | AU.L2-3.3.1 |
| 4648 | Logon with explicit credentials | AU.L2-3.3.1, AC.L2-3.1.7 |
| 4672 | Special privileges assigned to new logon | AU.L2-3.3.1, AC.L2-3.1.7 |
| 4673 | Privileged service called | AC.L2-3.1.7 |
| 4674 | Operation attempted on privileged object | AC.L2-3.1.7 |
| 4688 | Process creation (if audit enabled) | AU.L2-3.3.1 |
| 4689 | Process termination | AU.L2-3.3.1 |
| 4697 | Service installed on the system | CM.L2-3.4.5, SI.L2-3.14.6 |
| 4698 | Scheduled task created | SI.L2-3.14.6 |
| 4699 | Scheduled task deleted | CM.L2-3.4.5 |
| 4700 | Scheduled task enabled | SI.L2-3.14.6 |
| 4701 | Scheduled task disabled | CM.L2-3.4.5 |
| 4719 | Audit policy changed | AU.L2-3.3.4, CM.L2-3.4.5 |
| 4720 | User account created | AC.L2-3.1.1 |
| 4722 | User account enabled | AC.L2-3.1.1 |
| 4723 | Password change attempted | IA.L2-3.5.7 |
| 4724 | Password reset attempted | IA.L2-3.5.7 |
| 4725 | User account disabled | AC.L2-3.1.1 |
| 4726 | User account deleted | AC.L2-3.1.1 |
| 4728 | Member added to security-enabled global group | AC.L2-3.1.1 |
| 4732 | Member added to security-enabled local group | AC.L2-3.1.1 |
| 4735 | Security-enabled local group changed | AC.L2-3.1.1 |
| 4738 | User account changed | AC.L2-3.1.1 |
| 4740 | User account locked out | AC.L2-3.1.8 |
| 4756 | Member added to universal security group | AC.L2-3.1.1 |
| 4767 | User account unlocked | AC.L2-3.1.1 |
| 4776 | Credential validation (NTLM) | IA.L2-3.5.1 |
| 4946 | Firewall rule added | CM.L2-3.4.5 |
| 4947 | Firewall rule modified | CM.L2-3.4.5 |
| 4948 | Firewall rule deleted | CM.L2-3.4.5 |
| 4950 | Firewall setting changed | CM.L2-3.4.5 |

### System Log

Captures service state changes, driver loads, and system integrity events.

```yaml
cmmc-wel-system:
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

Captures PowerShell script execution — critical for detecting living-off-the-land attacks.

```yaml
cmmc-wel-powershell:
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

If Sysmon is installed on endpoints, collect its log channel for enriched process, network, and file telemetry.

```yaml
cmmc-wel-sysmon:
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

Captures antimalware scan results, threat detections, and definition updates.

```yaml
cmmc-wel-defender:
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

Captures scheduled task execution — important for detecting persistence mechanisms.

```yaml
cmmc-wel-taskscheduler:
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

Captures firewall rule changes and connection filtering.

```yaml
cmmc-wel-firewall:
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

## 2. File Integrity Monitoring (FIM) Rules

FIM rules generate `FIM_HIT` events when monitored files, directories, or registry keys are modified. These directly support CM.L2-3.4.1 (baseline configurations) and SI.L2-3.14.6 (monitor systems for attacks).

```yaml
# Critical Windows system files
cmmc-fim-system-files:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\drivers\etc\hosts
    - ?:\Windows\System32\config\SAM
    - ?:\Windows\System32\config\SYSTEM
    - ?:\Windows\System32\config\SECURITY

# Boot configuration
cmmc-fim-boot:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\boot\bcd
    - ?:\Windows\System32\boot\winload.exe

# Group Policy templates
cmmc-fim-group-policy:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\GroupPolicy\*
    - ?:\Windows\SYSVOL\*

# PowerShell profiles (persistence vector)
cmmc-fim-powershell-profiles:
  filters:
    platforms:
      - windows
  patterns:
    - ?:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    - ?:\Users\*\Documents\WindowsPowerShell\profile.ps1

# Registry-based persistence and security settings
cmmc-fim-registry-security:
  filters:
    platforms:
      - windows
  patterns:
    - hklm\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
    - hklm\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce
    - hklm\SYSTEM\CurrentControlSet\Services
    - hklm\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon
    - hklm\SOFTWARE\Policies\Microsoft\Windows
```

---

## 3. Exfil Event Collection Rules

The LC EDR sensor collects many event types by default. The following exfil event rule ensures all CMMC-relevant event types are explicitly enabled for Windows sensors. This is a safety net — if default collection changes, these rules guarantee the required telemetry continues to flow.

> **Note:** This rule is additive to the default exfil rules. It does not replace them. Any event types already collected by default will continue to be collected.

```yaml
cmmc-windows-events:
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
    - USER_LOGIN
    - USER_LOGOUT
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

---

## 4. D&R Rules — Audit & Accountability (AU)

### AU.L2-3.3.1 — System Auditing

The WEL artifact collection rules in Section 1 satisfy the data collection requirement. The D&R rules below create detections for the most critical audit events.

#### Failed Logon Detection

```yaml
name: cmmc-au-failed-logon
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
    name: cmmc-au-failed-logon
    priority: 3
    metadata:
      cmmc_control: AU.L2-3.3.1
      description: Failed logon attempt detected
      mitre_attack_id: T1078
      mitre_tactic: initial-access
    suppression:
      max_count: 10
      period: 5m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-au-failed-logon
tags:
  - cmmc
  - audit
comment: 'CMMC AU.L2-3.3.1 — Detect failed logon attempts (Event ID 4625)'
```

#### Brute Force Detection (Multiple Failed Logons)

> This rule uses the same detect block as the failed logon rule above. The difference is in the response: `min_count: 10` means this detection only fires after the 10th matching event within the period, acting as a threshold-based brute force alert.

```yaml
name: cmmc-au-brute-force
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
    name: cmmc-au-brute-force
    priority: 4
    metadata:
      cmmc_control: AU.L2-3.3.1
      description: Possible brute force — high volume of failed logons from single host
      mitre_attack_id: T1110
      mitre_tactic: credential-access
    suppression:
      min_count: 10
      period: 10m
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-au-brute-force
tags:
  - cmmc
  - audit
comment: 'CMMC AU.L2-3.3.1 — Alert on 10+ failed logons within 10 minutes (brute force indicator)'
```

#### Remote Desktop Logon Detection

```yaml
name: cmmc-au-rdp-logon
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
    name: cmmc-au-rdp-logon
    priority: 2
    metadata:
      cmmc_control: AU.L2-3.3.1
      description: Remote Desktop logon detected
      mitre_attack_id: T1021.001
      mitre_tactic: lateral-movement
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-au-rdp-logon
tags:
  - cmmc
  - audit
comment: 'CMMC AU.L2-3.3.1 — Detect RDP logons (Logon Type 10) for lateral movement awareness'
```

### AU.L2-3.3.4 — Alert on Audit Logging Process Failure

#### Audit Policy Changed

```yaml
name: cmmc-au-audit-policy-changed
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
    name: cmmc-au-audit-policy-changed
    priority: 5
    metadata:
      cmmc_control: AU.L2-3.3.4
      description: Audit policy was changed — potential tampering with logging
      mitre_attack_id: T1562.002
      mitre_tactic: defense-evasion
tags:
  - cmmc
  - audit
comment: 'CMMC AU.L2-3.3.4 — Detect audit policy changes (Event ID 4719)'
```

#### Event Log Cleared

```yaml
name: cmmc-au-event-log-cleared
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
    name: cmmc-au-event-log-cleared
    priority: 5
    metadata:
      cmmc_control: AU.L2-3.3.4
      description: Security event log was cleared — strong indicator of tampering
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - cmmc
  - audit
comment: 'CMMC AU.L2-3.3.4 — Detect security log clearing (Event ID 1102)'
```

#### Windows Defender Real-Time Protection Disabled

```yaml
name: cmmc-au-defender-rtp-disabled
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
    name: cmmc-au-defender-rtp-disabled
    priority: 5
    metadata:
      cmmc_control: AU.L2-3.3.4
      description: Windows Defender real-time protection was disabled
      mitre_attack_id: T1562.001
      mitre_tactic: defense-evasion
tags:
  - cmmc
  - audit
  - defense-evasion
comment: 'CMMC AU.L2-3.3.4 — Detect Defender real-time protection being disabled (Event ID 5001)'
```

### AU.L2-3.3.8 — Protect Audit Information

#### Attempt to Stop Windows Event Log Service

```yaml
name: cmmc-au-eventlog-service-stop
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
    name: cmmc-au-eventlog-service-stop
    priority: 5
    metadata:
      cmmc_control: AU.L2-3.3.8
      description: Attempt to stop event log service or clear event logs
      mitre_attack_id: T1070.001
      mitre_tactic: defense-evasion
  - action: add tag
    tag: audit-tamper
    ttl: 86400
tags:
  - cmmc
  - audit
comment: 'CMMC AU.L2-3.3.8 — Detect attempts to stop event logging or clear logs'
```

---

## 5. D&R Rules — Access Control (AC)

### AC.L2-3.1.1 — Account Management

#### New User Account Created

```yaml
name: cmmc-ac-user-created
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
    name: cmmc-ac-user-created
    priority: 3
    metadata:
      cmmc_control: AC.L2-3.1.1
      description: New user account created
      mitre_attack_id: T1136.001
      mitre_tactic: persistence
tags:
  - cmmc
  - access-control
comment: 'CMMC AC.L2-3.1.1 — Detect local user account creation (Event ID 4720)'
```

#### User Added to Privileged Group

```yaml
name: cmmc-ac-user-added-to-admin-group
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
    name: cmmc-ac-user-added-to-admin-group
    priority: 4
    metadata:
      cmmc_control: AC.L2-3.1.1
      description: User added to a security-enabled group
      mitre_attack_id: T1098
      mitre_tactic: persistence
tags:
  - cmmc
  - access-control
comment: 'CMMC AC.L2-3.1.1 — Detect user additions to security groups (Event IDs 4728, 4732, 4756)'
```

#### User Account Deleted

```yaml
name: cmmc-ac-user-deleted
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
    name: cmmc-ac-user-deleted
    priority: 3
    metadata:
      cmmc_control: AC.L2-3.1.1
      description: User account deleted
tags:
  - cmmc
  - access-control
comment: 'CMMC AC.L2-3.1.1 — Detect user account deletion (Event ID 4726)'
```

### AC.L2-3.1.7 — Privileged Function Execution

#### Special Privileges Assigned to New Logon

```yaml
name: cmmc-ac-special-privilege-logon
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
    name: cmmc-ac-special-privilege-logon
    priority: 2
    metadata:
      cmmc_control: AC.L2-3.1.7
      description: Special privileges assigned to new logon session
      mitre_attack_id: T1078
      mitre_tactic: privilege-escalation
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-ac-special-privilege-logon
tags:
  - cmmc
  - access-control
comment: 'CMMC AC.L2-3.1.7 — Track special privilege assignment (Event ID 4672). Suppressed to reduce noise from service accounts.'
```

#### Privileged Service Called

```yaml
name: cmmc-ac-privileged-service
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
    name: cmmc-ac-privileged-service
    priority: 3
    metadata:
      cmmc_control: AC.L2-3.1.7
      description: Privileged service or object operation attempted
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-ac-privileged-service
tags:
  - cmmc
  - access-control
comment: 'CMMC AC.L2-3.1.7 — Detect privileged service calls (Event IDs 4673, 4674)'
```

### AC.L2-3.1.8 — Unsuccessful Logon Attempts

#### Account Lockout

```yaml
name: cmmc-ac-account-lockout
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
    name: cmmc-ac-account-lockout
    priority: 4
    metadata:
      cmmc_control: AC.L2-3.1.8
      description: User account locked out due to failed logon attempts
      mitre_attack_id: T1110
      mitre_tactic: credential-access
tags:
  - cmmc
  - access-control
comment: 'CMMC AC.L2-3.1.8 — Detect account lockouts (Event ID 4740)'
```

---

## 6. D&R Rules — System & Information Integrity (SI)

### SI.L2-3.14.2 — Malicious Code Protection

#### YARA Detection Alert

```yaml
name: cmmc-si-yara-detection
detect:
  event: YARA_DETECTION
  op: is windows
respond:
  - action: report
    name: cmmc-si-yara-detection
    priority: 5
    metadata:
      cmmc_control: SI.L2-3.14.2
      description: YARA rule match — possible malware detected
      mitre_tactic: execution
tags:
  - cmmc
  - malware
comment: 'CMMC SI.L2-3.14.2 — Alert on all YARA detections'
```

#### Defender Threat Detected

```yaml
name: cmmc-si-defender-threat
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
    name: cmmc-si-defender-threat
    priority: 4
    metadata:
      cmmc_control: SI.L2-3.14.2
      description: Windows Defender detected or took action against a threat
      mitre_tactic: execution
tags:
  - cmmc
  - malware
comment: 'CMMC SI.L2-3.14.2 — Detect Defender threat alerts (Event IDs 1116, 1117)'
```

### SI.L2-3.14.6 — Monitor Systems for Attacks

#### New Service Installed

```yaml
name: cmmc-si-new-service-installed
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
    name: cmmc-si-new-service-installed
    priority: 3
    metadata:
      cmmc_control: SI.L2-3.14.6
      description: New service installed on system
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - cmmc
  - integrity
comment: 'CMMC SI.L2-3.14.6 — Detect new service installations (Event ID 7045)'
```

#### Scheduled Task Created

```yaml
name: cmmc-si-scheduled-task-created
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
    name: cmmc-si-scheduled-task-created
    priority: 3
    metadata:
      cmmc_control: SI.L2-3.14.6
      description: Scheduled task created
      mitre_attack_id: T1053.005
      mitre_tactic: persistence
tags:
  - cmmc
  - integrity
comment: 'CMMC SI.L2-3.14.6 — Detect scheduled task creation (Event ID 4698)'
```

#### Suspicious Process Execution — Living Off the Land

```yaml
name: cmmc-si-lolbin-execution
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
    name: cmmc-si-lolbin-execution
    priority: 4
    metadata:
      cmmc_control: SI.L2-3.14.6
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
  - cmmc
  - integrity
comment: 'CMMC SI.L2-3.14.6 — Detect LOLBin abuse with network/download indicators'
```

#### Encoded PowerShell Execution

```yaml
name: cmmc-si-encoded-powershell
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
    name: cmmc-si-encoded-powershell
    priority: 4
    metadata:
      cmmc_control: SI.L2-3.14.6
      description: PowerShell executed with encoded command — common evasion technique
      mitre_attack_id: T1059.001
      mitre_tactic: execution
tags:
  - cmmc
  - integrity
comment: 'CMMC SI.L2-3.14.6 — Detect encoded PowerShell commands (common obfuscation)'
```

#### Credential Access — LSASS Access

```yaml
name: cmmc-si-lsass-access
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
    name: cmmc-si-lsass-access
    priority: 5
    metadata:
      cmmc_control: SI.L2-3.14.6
      description: Sensitive process access to LSASS — possible credential dumping
      mitre_attack_id: T1003.001
      mitre_tactic: credential-access
    suppression:
      max_count: 3
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-si-lsass-access
tags:
  - cmmc
  - integrity
  - credential-access
comment: 'CMMC SI.L2-3.14.6 — Detect LSASS memory access (credential dumping indicator)'
```

#### Named Pipe Creation (Lateral Movement Indicator)

```yaml
name: cmmc-si-suspicious-named-pipe
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
    name: cmmc-si-suspicious-named-pipe
    priority: 4
    metadata:
      cmmc_control: SI.L2-3.14.6
      description: Suspicious named pipe creation — possible C2 or lateral movement
      mitre_attack_id: T1570
      mitre_tactic: lateral-movement
tags:
  - cmmc
  - integrity
comment: 'CMMC SI.L2-3.14.6 — Detect known malicious named pipe patterns'
```

#### Thread Injection Detection

```yaml
name: cmmc-si-thread-injection
detect:
  event: THREAD_INJECTION
  op: is windows
respond:
  - action: report
    name: cmmc-si-thread-injection
    priority: 4
    metadata:
      cmmc_control: SI.L2-3.14.6
      description: Thread injection detected — process injecting code into another process
      mitre_attack_id: T1055
      mitre_tactic: defense-evasion
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-si-thread-injection
tags:
  - cmmc
  - integrity
comment: 'CMMC SI.L2-3.14.6 — Detect process injection via thread injection'
```

### SI.L2-3.14.7 — Identify Unauthorized Use

#### Logon Outside Business Hours

```yaml
name: cmmc-si-after-hours-logon
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
        - op: is
          path: event/EVENT/EventData/LogonType
          value: '11'
respond:
  - action: report
    name: cmmc-si-after-hours-logon
    priority: 2
    metadata:
      cmmc_control: SI.L2-3.14.7
      description: Interactive logon detected — review for after-hours or unauthorized access
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-si-after-hours-logon
tags:
  - cmmc
  - integrity
comment: 'CMMC SI.L2-3.14.7 — Track interactive logons (Types 2, 10, 11). Use downstream SIEM time-of-day filtering to flag after-hours activity.'
```

---

## 7. D&R Rules — Incident Response (IR)

### IR.L2-3.6.1 — Incident Handling

The Cases extension (ext-cases) provides the incident handling workflow. These rules ensure high-severity detections automatically create cases.

> **Note:** If ext-cases is configured in **all detections** ingestion mode, every detection above automatically creates a case. If using **tailored** mode, add an `ingest_detection` response action to high-priority rules. The rules below illustrate explicit case-relevant tagging.

#### Network Isolation on Critical Threat

```yaml
name: cmmc-ir-critical-threat-isolate
detect:
  event: YARA_DETECTION
  op: is windows
respond:
  - action: report
    name: cmmc-ir-critical-threat-isolate
    priority: 5
    metadata:
      cmmc_control: IR.L2-3.6.1
      description: YARA detection triggered network isolation
  - action: add tag
    tag: cmmc-incident
    ttl: 604800
tags:
  - cmmc
  - incident-response
comment: 'CMMC IR.L2-3.6.1 — Tag endpoint for case management on YARA detection. Add "isolate network" action if automated containment is desired.'
```

---

## 8. D&R Rules — Configuration Management (CM)

### CM.L2-3.4.1 — Baseline Configurations / CM.L2-3.4.5 — Access Restrictions for Change

#### FIM Hit on Critical Files

```yaml
name: cmmc-cm-fim-critical-change
detect:
  event: FIM_HIT
  op: is windows
respond:
  - action: report
    name: cmmc-cm-fim-critical-change
    priority: 3
    metadata:
      cmmc_control: CM.L2-3.4.1
      description: File integrity change detected on monitored path
      mitre_attack_id: T1565
      mitre_tactic: impact
tags:
  - cmmc
  - config-management
comment: 'CMMC CM.L2-3.4.1 — Alert on all FIM hits on Windows. Monitored paths defined in FIM rules (Section 2).'
```

#### Autorun Change Detection (Persistence)

```yaml
name: cmmc-cm-autorun-change
detect:
  event: AUTORUN_CHANGE
  op: is windows
respond:
  - action: report
    name: cmmc-cm-autorun-change
    priority: 3
    metadata:
      cmmc_control: CM.L2-3.4.5
      description: Autorun persistence mechanism changed
      mitre_attack_id: T1547.001
      mitre_tactic: persistence
    suppression:
      max_count: 10
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-cm-autorun-change
tags:
  - cmmc
  - config-management
comment: 'CMMC CM.L2-3.4.5 — Detect autorun/startup persistence changes'
```

#### Driver Change Detection

```yaml
name: cmmc-cm-driver-change
detect:
  event: DRIVER_CHANGE
  op: is windows
respond:
  - action: report
    name: cmmc-cm-driver-change
    priority: 3
    metadata:
      cmmc_control: CM.L2-3.4.5
      description: Driver installation or modification detected
      mitre_attack_id: T1543.003
      mitre_tactic: persistence
tags:
  - cmmc
  - config-management
comment: 'CMMC CM.L2-3.4.5 — Detect driver changes'
```

#### Service Configuration Change Detection

```yaml
name: cmmc-cm-service-change
detect:
  event: SERVICE_CHANGE
  op: is windows
respond:
  - action: report
    name: cmmc-cm-service-change
    priority: 2
    metadata:
      cmmc_control: CM.L2-3.4.5
      description: Windows service configuration changed
    suppression:
      max_count: 20
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-cm-service-change
tags:
  - cmmc
  - config-management
comment: 'CMMC CM.L2-3.4.5 — Detect service configuration changes. Suppressed to reduce noise during patching.'
```

#### Firewall Rule Changed

```yaml
name: cmmc-cm-firewall-changed
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
    name: cmmc-cm-firewall-changed
    priority: 3
    metadata:
      cmmc_control: CM.L2-3.4.5
      description: Windows Firewall rule or setting changed
      mitre_attack_id: T1562.004
      mitre_tactic: defense-evasion
tags:
  - cmmc
  - config-management
comment: 'CMMC CM.L2-3.4.5 — Detect firewall configuration changes (Event IDs 4946-4950)'
```

---

## 9. D&R Rules — Identification & Authentication (IA)

### IA.L2-3.5.7 — Password Management

#### Password Change Attempts

```yaml
name: cmmc-ia-password-change
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
    name: cmmc-ia-password-change
    priority: 2
    metadata:
      cmmc_control: IA.L2-3.5.7
      description: Password change or reset attempted
    suppression:
      max_count: 5
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-ia-password-change
tags:
  - cmmc
  - authentication
comment: 'CMMC IA.L2-3.5.7 — Track password change (4723) and reset (4724) attempts'
```

### IA.L2-3.5.1 — Identification

#### NTLM Authentication

```yaml
name: cmmc-ia-ntlm-auth
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
    name: cmmc-ia-ntlm-auth
    priority: 1
    metadata:
      cmmc_control: IA.L2-3.5.1
      description: NTLM credential validation event
    suppression:
      max_count: 50
      period: 1h
      is_global: false
      keys:
        - '{{ .routing.sid }}'
        - cmmc-ia-ntlm-auth
tags:
  - cmmc
  - authentication
comment: 'CMMC IA.L2-3.5.1 — Track NTLM authentication events. High suppression threshold — these are high-volume in AD environments.'
```

---

## 10. Recommended Extensions

Subscribe to these extensions to maximize CMMC coverage.

### Required

| Extension | Purpose | CMMC Controls |
|-----------|---------|---------------|
| **Reliable Tasking** | Prerequisite for artifact collection rules. Ensures tasks (including WEL collection configs) reach sensors even when offline. | All AU controls (enables WEL collection) |
| **Artifact Collection** | Manages WEL streaming rules and log file collection. | AU.L2-3.3.1 through AU.L2-3.3.9 |
| **Exfil Control** | Manages which EDR event types flow from sensor to cloud. Ensures required telemetry is collected. | AU.L2-3.3.1, SI.L2-3.14.6 |

### Strongly Recommended

| Extension | Purpose | CMMC Controls |
|-----------|---------|---------------|
| **ext-cases** (Cases) | SOC case management with detection-to-case conversion, SLA tracking, investigation workflows, and audit trail. | IR.L2-3.6.1, IR.L2-3.6.2 |
| **EPP (Endpoint Protection)** | Unified Windows Defender management, event collection, and alerting. Free extension. | SI.L2-3.14.2, SI.L2-3.14.3 |
| **Soteria EDR Rules** | Managed detection ruleset with MITRE ATT&CK mapping across 14 event types. Provides broad behavioral detection coverage without manual rule authoring. | SI.L2-3.14.6, 3.3.2e |
| **Sigma Rules** | Community and commercial Sigma rule conversion. Provides wide coverage of known attack patterns from the open-source Sigma repository. | SI.L2-3.14.6, 3.3.2e |

### Recommended for Enhanced Coverage

| Extension | Purpose | CMMC Controls |
|-----------|---------|---------------|
| **Strelka** | File analysis engine for scanning files transiting endpoints. Supports YARA, PE analysis, document analysis, and archive extraction. | SI.L2-3.14.2 |
| **Playbook** | Python-based automation for custom response workflows — enrichment, notification, remediation orchestration. | IR.L2-3.6.1, 3.3.2e |
| **ext-git-sync** | Infrastructure as Code — manage D&R rules, FIM, artifact collection, outputs, and extensions across orgs via git. | CM.L2-3.4.1, CM.L2-3.4.5, AU.L2-3.3.9 |

---

## 11. Deployment Notes

### Retention

- Set Insight retention to **90+ days** to meet Level 2 active retention requirements.
- Add an S3 or GCS output for long-term archival beyond the Insight window.
- All artifact collection rules above use `days_retention: 90` to match.

### Tagging Strategy

All D&R rules in this document use the `cmmc` tag. This enables:
- Filtering detections by compliance source in the Cases UI
- Routing CMMC-specific detections to a dedicated output
- Tracking CMMC rule coverage separately from operational detections

### Suppression Tuning

Many rules include suppression settings to reduce noise from high-volume events (e.g., Event ID 4672 on service accounts, Event ID 4776 NTLM in AD). These values are starting points:
- Review suppression thresholds after initial deployment
- Create FP rules for known-safe patterns (e.g., specific service accounts triggering 4672)
- Use the `/lc-essentials:fp-pattern-finder` skill to identify systematic noise after a burn-in period

### Windows Audit Policy Prerequisites

The D&R rules in this document depend on the Windows endpoints having the correct **Advanced Audit Policy** configured. At minimum, enable:

| Audit Category | Subcategory | Setting |
|----------------|-------------|---------|
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

### Deployment Order

1. Enable **Reliable Tasking**, **Artifact Collection**, and **Exfil Control** extensions
2. Deploy artifact collection rules (Section 1) — WEL streaming begins
3. Deploy FIM rules (Section 2) — integrity monitoring begins
4. Deploy exfil event rules (Section 3) — ensures all event types are collected
5. Deploy D&R rules (Sections 4–9) — detections begin firing
6. Enable **ext-cases** — detections convert to trackable cases
7. Subscribe to **Soteria** and/or **Sigma** — adds managed detection coverage
8. Tune: run for 7 days, then use FP pattern finder to suppress noise
