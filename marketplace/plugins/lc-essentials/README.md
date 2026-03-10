# LimaCharlie Essentials Plugin

Core LimaCharlie skills for CLI-based API access, sensor management, detection engineering, and security operations.

## OID is a UUID, not an Organization Name

Most skills require an **Organization ID (OID)** — a UUID like `c1ffedc0-ffee-4a1e-b1a5-abc123def456`. Use `limacharlie org list --output yaml` to discover orgs and OIDs.

**Skills that don't require an OID:** `list-user-orgs`, `create-org`, `get-platform-names`.

## EDR Agent Platform Limitation

LimaCharlie EDR agents only run on **Windows, Linux, macOS, and Chrome OS**. Cloud sensors, external adapters, and USP adapters provide log ingestion only — do not attempt system-level queries (processes, registry, file system) against them.

## Skills

- **lookup-lc-doc** - Search LimaCharlie documentation
- **investigation-creation** - Investigate security cases (SOC triage, incident response)
- **detection-engineering** - Create and test D&R rules
- **detection-tuner** - Tune noisy alerts with FP rules
- **sensor-tasking** - Send live response commands to sensors
- **sensor-health** - Fleet-wide sensor health reports
- **fleet-payload-tasking** - Deploy commands fleet-wide with reliable tasking
- **velociraptor** - Velociraptor DFIR integration
- **web-ui-link** - Generate LimaCharlie web UI URLs

## CLI Usage

All operations use the `limacharlie` CLI via Bash. Use `--output yaml` and `--ai-help` for command discovery. See AUTOINIT.md for full rules.
