---
name: fim
description: File and Registry Integrity Monitoring (FIM/RIM) in LimaCharlie — the Integrity extension for monitoring file system and registry changes with pattern-based rules. Covers rule patterns, platform-specific syntax, FIM_HIT events, Linux eBPF vs inotify limitations, and CLI management. Use when setting up integrity monitoring, writing FIM patterns, or troubleshooting FIM_HIT events.
allowed-tools:
  - Bash
  - Read
---

# File & Registry Integrity Monitoring (FIM)

The Integrity extension (`ext-integrity`) automates integrity checks of file systems and registry values through pattern-based rules. When a monitored file or registry key is modified, a `FIM_HIT` event appears in the sensor timeline.

## Core Concepts

- FIM is consolidated with EDR — no separate agent needed
- Real-time alerts for modifications
- One year of historical FIM data via Insight
- Rules are scoped by **platform** and **sensor tags**

## Enabling

```bash
limacharlie extension subscribe --name ext-integrity --oid <oid>
```

## Managing Rules

```bash
# List rules
limacharlie extension request --name ext-integrity --action list_rules --oid <oid> --output yaml

# Add rule
limacharlie extension request --name ext-integrity --action add_rule --data '{"name":"linux-ssh-configs","patterns":["/root/.ssh/*","/home/*/.ssh/*"],"tags":["server"],"platforms":["linux"]}' --oid <oid> --output yaml

# Remove rule
limacharlie extension request --name ext-integrity --action remove_rule --data '{"name":"linux-ssh-configs"}' --oid <oid> --output yaml
```

## Rule Patterns

Patterns support wildcards: `*` (any characters), `?` (single character), `+` (one or more characters).

### Windows File Patterns

| Pattern | Monitors |
|---------|----------|
| `?:\\Windows\\System32\\drivers` | drivers directory on any drive |
| `C:\\Windows\\System32\\specialfile.exe` | specific file on C: |
| `?:\\inetpub\\wwwroot` | IIS web root on any drive |

**Gotcha**: Windows directory separators (backslash) MUST be escaped with double-backslash `\\` in patterns.

### Windows Registry Patterns

All registry monitoring patterns MUST begin with `\REGISTRY`, followed by the hive and then the path.

| Pattern | Monitors |
|---------|----------|
| `\REGISTRY\MACHINE\Software\Microsoft\Windows\CurrentVersion\Run*` | System Run key (persistence) |
| `\REGISTRY\MACHINE\Software\Microsoft\Windows\CurrentVersion\RunOnce*` | System RunOnce key |
| `\REGISTRY\USER\S-*\Software\Microsoft\Windows\CurrentVersion\Run*` | All users' Run keys |

**Gotcha**: the prefix is `\REGISTRY`, NOT `HKLM` or `HKEY_LOCAL_MACHINE`. This is a common mistake.

### Linux Patterns

| Pattern | Monitors |
|---------|----------|
| `/root/.ssh/authorized_keys` | Root SSH authorized keys |
| `/home/*/.ssh/*` | All users' SSH directories |
| `/etc/passwd` | User account file |
| `/etc/shadow` | Password hash file |
| `/etc/crontab` | System cron |

### macOS Patterns

| Pattern | Monitors |
|---------|----------|
| `/Users/*/Library/Keychains/*` | User keychains |
| `/Library/Keychains` | System keychains |
| `/Library/LaunchDaemons/*` | Launch daemons (persistence) |
| `/Library/LaunchAgents/*` | Launch agents (persistence) |

## Linux Support Differences

### Linux with eBPF Support

On eBPF-capable systems, FIM capabilities are on par with Windows and macOS — full file notification with efficient kernel-level monitoring.

### Legacy Support (inotify)

On systems without eBPF, FIM uses `inotify` (active monitoring, not passive):

- **Paths with wildcards are less efficient** and only support monitoring up to **20 sub-directories** covered by the wildcard
- **Final wildcard `*` required for directory monitoring**: omitting the final `*` results in only the top-level directory being monitored, not its contents
- Example: `/home/*/.ssh/*` works, but `/home/*/.ssh` only monitors the `.ssh` directory entry itself

## FIM_HIT Event Structure

When a monitored path is modified, a `FIM_HIT` event is generated containing:

- The file or registry path that was modified
- Process information (which process made the change)
- Timestamp of the modification

Use `FIM_HIT` events in D&R rules for automated response:

```yaml
# Example: detect FIM hits on critical Windows persistence locations
event: FIM_HIT
op: starts with
path: event/FILE_PATH
value: \REGISTRY\MACHINE\Software\Microsoft\Windows\CurrentVersion\Run
```

## IaC Format

```yaml
extension_config:
  ext-integrity:
    data:
      rules:
        - name: windows-persistence
          patterns:
            - '?\Windows\System32\drivers'
            - '\REGISTRY\MACHINE\Software\Microsoft\Windows\CurrentVersion\Run*'
          tags: [windows-server]
          platforms: [windows]
        - name: linux-ssh
          patterns:
            - '/root/.ssh/*'
            - '/home/*/.ssh/*'
          tags: [linux-server]
          platforms: [linux]
    usr_mtd:
      enabled: true
      expiry: 0
```

## Gotchas Summary

| Gotcha | Detail |
|--------|--------|
| Windows paths need `\\` | Backslash must be escaped as double-backslash |
| Registry prefix is `\REGISTRY` | NOT `HKLM` or `HKEY_LOCAL_MACHINE` |
| Linux inotify: 20 sub-dir limit | Wildcard paths limited on non-eBPF systems |
| Linux inotify: final `*` needed | Omitting final wildcard monitors only directory entry |
| FIM needs ext-integrity subscribed | 403 errors indicate missing subscription |
