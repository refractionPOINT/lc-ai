---
name: sensors
description: Working with LimaCharlie sensors — listing, filtering, info, tags, installation keys, and sensor selectors. Covers both EDR agents and adapter sensors at the inventory level. Use when managing sensor inventory, checking sensor status, working with tags, creating installation keys, or building sensor selectors.
allowed-tools:
  - Bash
  - Read
---

# Sensors

How to work with sensors as objects in LimaCharlie. This covers inventory operations — listing, filtering, inspecting, tagging, and managing installation keys. For sending commands to sensors, see the `sensor-tasking` skill. For configuring adapter data sources, see the `adapters` skill.

## Sensor Types

All telemetry sources in LimaCharlie are "sensors" with a Sensor ID (SID, UUID). Two main categories:

| Type | Description | Taskable |
|------|-------------|----------|
| **EDR Agent** | Endpoint sensor (Windows, Linux, macOS, ChromeOS) | Yes |
| **Adapter** | Third-party telemetry source (cloud or on-prem) | No |

To distinguish: EDR agents have a platform of `windows`, `linux`, `macos`, or `chrome` with architecture NOT `usp_adapter`. Adapters have either a non-EDR platform or `arch=usp_adapter`.

## CLI Commands

### List Sensors

```bash
# All sensors in an org
limacharlie sensor list --oid <oid> --output yaml

# Only online sensors
limacharlie sensor list --online --oid <oid> --output yaml

# With selector filter
limacharlie sensor list --selector "plat==windows" --oid <oid> --output yaml

# With tag filter
limacharlie sensor list --tag production --oid <oid> --output yaml

# Reduce output with JMESPath filter
limacharlie sensor list --oid <oid> --filter "[].{sid:sid,hostname:hostname,plat:plat}" --output yaml
```

### Get Sensor Info

```bash
limacharlie sensor get --sid <sid> --oid <oid> --output yaml
```

Key fields in response: `sid`, `hostname`, `plat` (platform), `arch` (architecture), `alive` (last seen timestamp), `ext_ip`, `int_ip`, `tags`.

### Manage Tags

```bash
# Add a tag (with optional auto-expiry TTL in seconds)
limacharlie tag add --sid <sid> --tag <tag> --oid <oid> --output yaml
limacharlie tag add --sid <sid> --tag <tag> --ttl 604800 --oid <oid> --output yaml

# Remove a tag
limacharlie tag remove --sid <sid> --tag <tag> --oid <oid> --output yaml

# List tags on a sensor
limacharlie tag list --sid <sid> --oid <oid> --output yaml

# Find sensors by tag
limacharlie tag find --tag <tag> --oid <oid> --output yaml

# Mass-add a tag to sensors matching a selector
limacharlie tag mass-add --selector "plat==windows" --tag <tag> --oid <oid> --output yaml

# Mass-remove a tag from sensors matching a selector
limacharlie tag mass-remove --selector "plat==windows" --tag <tag> --oid <oid> --output yaml
```

Tags can also be added/removed via D&R rule response actions.

### Delete a Sensor

```bash
limacharlie sensor delete --sid <sid> --confirm --oid <oid>
```

### Installation Keys

Installation keys register new sensors/adapters with an org. Each key has an Installer ID (IID, UUID).

```bash
# List installation keys
limacharlie installation-key list --oid <oid> --output yaml

# Create an installation key
limacharlie installation-key create --description "Windows servers" --tags server,windows --oid <oid> --output yaml
```

When deploying adapters, use the IID (UUID format) not the full base64 installation key string.

### Find Sensors by Installation Key

```bash
limacharlie sensor list --selector "iid == \`<iid-uuid>\`" --oid <oid> --output yaml
```

## Sensor Selectors

Sensor selectors use [bexpr](https://github.com/hashicorp/go-bexpr) syntax to filter sensors. Used in CLI commands (`--selector`), D&R rules, and fleet operations.

### Selector Examples

| Selector | Description |
|----------|-------------|
| `*` | All sensors |
| `plat==windows` | Windows sensors |
| `plat==linux` | Linux sensors |
| `plat==macos` | macOS sensors |
| `production in tags` | Sensors tagged "production" |
| `hostname matches '^web-'` | Hostname starts with "web-" |
| `sid=='<uuid>'` | Specific sensor by SID |
| `iid=='\`<uuid>\`'` | Sensors from specific installation key |
| `plat==windows and production in tags` | Windows + production tag |
| `(plat==windows or plat==linux) and arch!=usp_adapter` | EDR agents only (no adapters) |

### Available Selector Fields

| Field | Type | Description |
|-------|------|-------------|
| `sid` | string | Sensor ID (UUID) |
| `iid` | string | Installer ID (UUID) |
| `plat` | string | Platform name (`windows`, `linux`, `macos`, `chrome`, `json`, `text`, etc.) |
| `arch` | string | Architecture (`x86`, `x64`, `arm64`, `usp_adapter`, etc.) |
| `hostname` | string | Sensor hostname |
| `tags` | list | Sensor tags |
| `ext_ip` | string | External IP |
| `int_ip` | string | Internal IP |

## EDR vs Adapter Identification

To filter only EDR agents (taskable sensors), combine platform and architecture:

```bash
limacharlie sensor list --selector "(plat==windows or plat==linux or plat==macos) and arch!=usp_adapter" --oid <oid> --output yaml
```

Non-EDR platforms include: `json`, `text`, `gcp`, `aws`, `office365`, `okta`, `crowdstrike`, `carbon_black`, `sophos`, and many others. A sensor with `plat==linux` but `arch==usp_adapter` is an adapter running on Linux, not an EDR agent.

## Platform Reference

### EDR Platforms

| Platform | Selector | Decimal ID |
|----------|----------|-----------|
| Windows | `plat==windows` | 268435456 |
| Linux | `plat==linux` | 536870912 |
| macOS | `plat==macos` | 805306368 |
| ChromeOS | `plat==chrome` | 1610612736 |

### Common Adapter Platforms

| Platform | Selector | Source Type |
|----------|----------|------------|
| `json` | `plat==json` | JSON telemetry |
| `text` | `plat==text` | Text/syslog telemetry |
| `gcp` | `plat==gcp` | Google Cloud |
| `aws` | `plat==aws` | Amazon Web Services |
| `office365` | `plat==office365` | Microsoft 365 |
| `okta` | `plat==okta` | Okta |
| `crowdstrike` | `plat==crowdstrike` | CrowdStrike |

## System Tags

LimaCharlie provides system-level tags that control sensor behavior:

| Tag | Effect |
|-----|--------|
| `lc:latest` | Forces latest sensor version (ignores org-assigned version). Use to test-deploy on a representative set. |
| `lc:stable` | Forces stable sensor version. Use to hold specific sensors back during an org-wide upgrade. |
| `lc:experimental` | Runs experimental sensor version. Used when troubleshooting with the LimaCharlie team. |
| `lc:no_kernel` | Kernel component will not load on the host. |
| `lc:debug` | Uses debug version of sensor. |
| `lc:limit-update` | Sensor won't update version at runtime — only changes on restart/reboot. |
| `lc:sleeper` | Disables all functionality except cloud connection. Minimal system impact ($0.10/30d). |

### Sleeper Mode

Sleeper mode lets you pre-deploy sensors at near-zero cost ($0.10/30 days per sensor) and activate them on-demand:

1. Create an installation key with the `lc:sleeper` tag
2. Deploy sensors fleet-wide — they enter sleeper mode within ~10 minutes
3. To activate: remove the `lc:sleeper` tag and ensure org quota accommodates the sensor count
4. Sensors resume full EDR within ~10 minutes

**Requirements**: org must have billing enabled (quota >= 3). No binary change or reboot needed.

**Gotcha**: there is a ~10-minute delay when applying or removing `lc:sleeper`. It is not instant.

## Device ID vs Sensor ID

- **SID** (Sensor ID): unique per sensor installation. Changes if the sensor is reinstalled.
- **DID** (Device ID): hardware-derived identifier in `routing/did`. Persists across reinstalls on the same machine.

Use DID to track a device across sensor reinstalls. The `entire_device: true` parameter on tag actions applies tags to ALL sensors sharing a Device ID.

## Tag Gotchas

- **Tag TTL is per-application**: each `add tag` creates its own TTL timer. Reapplying a tag with a new TTL does not extend the original — it creates a new entry.
- **`entire_device: true`**: applies the tag to ALL sensors sharing the same Device ID, not just the targeted sensor.
- **Tags appear in every event**: tags are included in `routing/tags` of every event from the sensor, so they can be used in D&R rule detection logic via the `is tagged` operator.

## Checking Sensor Health

### Online Status

The `alive` field in sensor info shows the last seen timestamp. Compare with current time to determine if a sensor is stale.

```bash
# List online sensors only
limacharlie sensor list --online --oid <oid> --output yaml
```

### Event Retention Check

Verify a sensor has data within a time range:

```bash
limacharlie event retention --sid <sid> --start <epoch_seconds> --end <epoch_seconds> --oid <oid> --output yaml
```

### Event Listing

List recent events from a specific sensor:

```bash
start=$(date -d '1 hour ago' +%s) && end=$(date +%s)
limacharlie event list --sid <sid> --start $start --end $end --oid <oid> --output yaml
```
