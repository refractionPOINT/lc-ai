---
name: exfil-event-collection
description: Managing which events EDR sensors send to LimaCharlie — event collection rules, watch rules, performance rules, throughput management, Afterburner mode, and IR mode. Use when configuring which events sensors collect, troubleshooting throughput issues, managing high-volume sensors, or understanding why events are missing.
allowed-tools:
  - Bash
  - Read
---

# Exfil (Event Collection)

The Exfil extension (`ext-exfil`) manages which real-time events EDR sensors send to LimaCharlie. By default, sensors send events based on a standard profile. This extension lets you customize what gets collected.

## Core Concept

Event collection determines what data reaches LimaCharlie — and therefore what D&R rules can see. If an event type isn't collected, no D&R rule can detect it and no output will receive it. This is the most fundamental knob for balancing visibility vs throughput.

**Gotcha**: event collection rule changes sync with sensors every few minutes, NOT instantly. After changing rules, wait several minutes before expecting new behavior.

## Three Rule Types

### Event Collection Rules

Control which event types are sent per platform and tag combination.

```json
{
  "action": "add_event_rule",
  "name": "windows-vip",
  "events": ["NEW_TCP4_CONNECTION", "NEW_TCP6_CONNECTION"],
  "tags": ["vip"],
  "platforms": ["windows"]
}
```

This means: for Windows sensors tagged `vip`, also collect TCP connection events.

### Watch Rules

Conditional operators on events — only send events matching specific field values. Used to manage high-volume events by filtering at the sensor.

```json
{
  "action": "add_watch",
  "name": "wininet-loading",
  "event": "MODULE_LOAD",
  "operator": "ends with",
  "value": "wininet.dll",
  "path": ["FILE_PATH"],
  "tags": ["server"],
  "platforms": ["windows"]
}
```

This means: for Windows sensors tagged `server`, only send `MODULE_LOAD` events where `FILE_PATH` ends with `wininet.dll`. All other MODULE_LOAD events are dropped at the sensor.

### Performance Rules

For high I/O servers (Windows only). May impact event accuracy. Applied via tag to sensor sets.

```json
{
  "action": "add_perf_rule",
  "name": "sql-servers",
  "tags": ["sql"],
  "platforms": ["windows"]
}
```

## Throughput Management

Enabling ALL events via exfil can produce massive traffic. LimaCharlie processes events in real-time, but if the rate exceeds capacity, events are enqueued up to a limit. If that limit is reached, the queue is dropped and a **DATA_DROPPED** error is emitted to platform logs.

**Seeing event collection errors means you need to**:

1. Reduce the population of events collected
2. Reduce D&R rule count or complexity
3. Use Watch Rules to filter high-volume events at the sensor
4. Enable IR mode

### Afterburner Mode

Before dropping a backlogged queue, LimaCharlie enters "Afterburner" mode automatically. This addresses the common scenario of spammy processes (e.g., `devenv.exe` or `git` called hundreds of times per second during builds):

1. De-duplicates spammy processes
2. Processes each unique process through D&R rules only once

Afterburner is automatic — no configuration needed.

### IR Mode

For users who want to record a very large number of events but don't need D&R rules on all of them. Enable by tagging a sensor with `ir`.

When IR mode is enabled:
- Events are NOT de-duplicated (full fidelity recording)
- D&R rules ONLY run on these 4 event types:
  1. `CODE_IDENTITY`
  2. `DNS_REQUEST`
  3. `NETWORK_CONNECTIONS`
  4. `NEW_PROCESS`

**Gotcha**: IR mode means most D&R rules won't fire. Only use it when you explicitly need full event recording with limited detection. This affects managed rulesets too — Soteria rules that depend on other event types won't fire.

## CLI Operations

The exfil extension is managed via extension requests:

```bash
# List all exfil rules
limacharlie extension request --name ext-exfil --action list_rules --oid <oid> --output yaml

# Add event collection rule
limacharlie extension request --name ext-exfil --action add_event_rule --data '{"name":"windows-extra","events":["NEW_TCP4_CONNECTION"],"tags":["monitor"],"platforms":["windows"]}' --oid <oid> --output yaml

# Remove event collection rule
limacharlie extension request --name ext-exfil --action remove_event_rule --data '{"name":"windows-extra"}' --oid <oid> --output yaml

# Add watch rule
limacharlie extension request --name ext-exfil --action add_watch --data '{"name":"wininet-only","event":"MODULE_LOAD","operator":"ends with","value":"wininet.dll","path":["FILE_PATH"],"tags":["server"],"platforms":["windows"]}' --oid <oid> --output yaml

# Remove watch rule
limacharlie extension request --name ext-exfil --action remove_watch --data '{"name":"wininet-only"}' --oid <oid> --output yaml
```

## Gotchas Summary

| Gotcha | Detail |
|--------|--------|
| Changes are not instant | Sync with sensors every few minutes |
| IR mode limits D&R | Only 4 event types get D&R rule evaluation |
| DATA_DROPPED means overloaded | Reduce collection, add watch rules, or enable IR mode |
| Afterburner is automatic | No configuration needed, activates before queue drop |
| Performance rules Windows only | Only applies to Windows sensors |
