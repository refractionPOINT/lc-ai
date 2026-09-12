---
name: hive-data
description: "Manage typed Hive configuration, lookups and secret references while preserving metadata and unrelated records."
---

# Hive, lookups and secrets

Hive is typed configuration, not a free-form database. Identify hive, partition, key, data schema and metadata before writing. Prefer the dedicated command for a known resource. Read current data and metadata and distinguish full replacement from partial-merge semantics. Preserve unrelated fields, enabled state, tags and expiry; use enable/disable operations for that isolated change. If concurrent writes are possible, use supported preconditions or reread and reconcile rather than assuming last-write wins is harmless.

Read lookup type and consumer requirements before changing values; a string lookup and structured lookup do not have interchangeable shapes. Use lookup-manager for managed external feeds when appropriate and verify refresh status as well as record content.

Use secret metadata and references. This harness blocks secret value get/export operations so credentials do not enter model tool results. If a task requires entering, inspecting or rotating a value, use the secure user interface for that step and continue configuration with its stored reference; do not bypass the restriction through Hive, API, shell or SDK calls. Never place credentials in transcripts, logs or test fixtures. Use `hive://secret/<name>` or the consuming feature's documented secret-reference format; references are not interchangeable across every API. For deletion or rotation, inspect dependent adapters, outputs, extensions and agents and verify the consumer after the change. Do not claim a secret is unused solely because one resource list has no reference.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `7-administration/config-hive/index.md`
- `7-administration/config-hive/lookups.md`
- `7-administration/config-hive/secrets.md`
- `5-integrations/extensions/limacharlie/lookup-manager.md`
