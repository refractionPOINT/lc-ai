---
name: sensors-tasking
description: "Deploy and manage sensors, discover supported endpoint commands, task selected fleets and track asynchronous or partial results."
---

# Sensors and endpoint tasking

Before tasking, identify real sensor IDs, platform, version, last-seen time, and supported command. An adapter sensor is not necessarily an EDR endpoint; do not send native endpoint commands to an unsupported platform. Read the endpoint command reference for command spelling, arguments, platform support and response event. The CLI is a transport; `task --ai-help` does not enumerate endpoint commands.

Preview a selector with sensor listing and record selected count and IDs. Sensor selectors use bexpr, not LCQL. Avoid implicit `*`. For fleet work, use the platform's aggregate facility (`spotcheck run`) when it fits; otherwise bounded batches with a per-sensor outcome ledger. Group by supported platform and distinguish selected, eligible, offline and excluded targets. Never spawn one agent per sensor.

`task request` waits for a response with a bounded timeout. `task send` only submits; acceptance is not execution success. `task reliable-send` persists offline delivery with a TTL, and `task reliable-list` shows pending delivery. A task disappearing from that queue establishes acknowledgement, not the command's semantic success. Correlate returned task/investigation identifiers to actual response evidence. Use a bounded overall deadline and report pending, failed, expired and completed sensors separately. Retry only failures known safe to retry; an ambiguous timeout on a mutating command must be reconciled before resubmission.

For isolation/sealing, inspect current and desired state and verify enforcement separately from the accepted request. Plan installation keys, platform/architecture and supported release versions for deployment; read platform installation documentation before generating installation commands. Never equate deleting a sensor record with uninstalling the endpoint software.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `8-reference/endpoint-commands.md`
- `8-reference/sensor-selector-expressions.md`
- `2-sensors-deployment/installation-keys.md`
- `2-sensors-deployment/endpoint-agent/versioning-upgrades.md`
- `5-integrations/extensions/limacharlie/reliable-tasking.md`
- `2-sensors-deployment/troubleshooting/non-responding-sensors.md`
- `2-sensors-deployment/endpoint-agent/chrome/installation.md`
- `2-sensors-deployment/endpoint-agent/docker/installation.md`
- `2-sensors-deployment/endpoint-agent/edge/installation.md`
- `2-sensors-deployment/endpoint-agent/linux/installation.md`
- `2-sensors-deployment/endpoint-agent/macos/installation.md`
- `2-sensors-deployment/endpoint-agent/windows/installation.md`
- `2-sensors-deployment/sensor-tags.md`
- `2-sensors-deployment/connectivity.md`
