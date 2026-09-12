---
name: adapters-ingestion
description: "Configure cloud or self-hosted adapters, ingestion credentials, schemas, mappings and ingestion health."
---

# Adapters and ingestion

Choose cloud-hosted versus self-hosted ingestion based on source reachability and supported deployment mode. A SaaS log adapter and a Cloud Security posture provider are different resources; route inventory/posture work to cloud-security.

Use `cloud-adapter list-types` or `external-adapter list-types`, then the corresponding `schema` for the exact type before authoring configuration. Read the matching `2-sensors-deployment/adapters/types/` document. Respect nested fields such as `client_options`; never derive the schema by analogy to another adapter. Use `usp` validation where applicable, with the correct hosted/self-hosted envelope.

Inspect an existing record before updating, preserve metadata and reference secrets without exposing values. Configuration being accepted does not prove ingestion: use adapter `sensors`, last-seen status, organization errors, and a bounded recent event sample to confirm expected schema and source timestamps. Distinguish polling cadence, credentials, upstream permissions, parse/mapping errors, and lack of source activity. Do not deploy a second collector to fix a mapping issue without checking duplicate ingestion.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `2-sensors-deployment/adapters/index.md`
- `2-sensors-deployment/adapters/as-a-service.md`
- `2-sensors-deployment/adapters/deployment.md`
- `2-sensors-deployment/adapters/usage.md`
- `7-administration/config-hive/cloud-sensors.md`
