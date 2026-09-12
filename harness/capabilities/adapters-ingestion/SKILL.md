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
- `2-sensors-deployment/adapters/types/1password.md`
- `2-sensors-deployment/adapters/types/atlassian.md`
- `2-sensors-deployment/adapters/types/aws-cloudtrail.md`
- `2-sensors-deployment/adapters/types/aws-guardduty.md`
- `2-sensors-deployment/adapters/types/azure/key-vault.md`
- `2-sensors-deployment/adapters/types/azure/kubernetes-service.md`
- `2-sensors-deployment/adapters/types/azure/monitor.md`
- `2-sensors-deployment/adapters/types/azure/network-security-group.md`
- `2-sensors-deployment/adapters/types/azure/sql-audit-logs.md`
- `2-sensors-deployment/adapters/types/azure-event-hub.md`
- `2-sensors-deployment/adapters/types/canarytokens.md`
- `2-sensors-deployment/adapters/types/carbon-black.md`
- `2-sensors-deployment/adapters/types/cato.md`
- `2-sensors-deployment/adapters/types/checkpoint-harmony.md`
- `2-sensors-deployment/adapters/types/crowdstrike.md`
- `2-sensors-deployment/adapters/types/duo.md`
- `2-sensors-deployment/adapters/types/evtx.md`
- `2-sensors-deployment/adapters/types/file.md`
- `2-sensors-deployment/adapters/types/gmail.md`
- `2-sensors-deployment/adapters/types/google-cloud-pubsub.md`
- `2-sensors-deployment/adapters/types/google-cloud-storage.md`
- `2-sensors-deployment/adapters/types/google-workspace.md`
- `2-sensors-deployment/adapters/types/hubspot.md`
- `2-sensors-deployment/adapters/types/iis.md`
- `2-sensors-deployment/adapters/types/imap.md`
- `2-sensors-deployment/adapters/types/it-glue.md`
- `2-sensors-deployment/adapters/types/json.md`
- `2-sensors-deployment/adapters/types/kubernetes-pods.md`
- `2-sensors-deployment/adapters/types/mac-unified-logging.md`
- `2-sensors-deployment/adapters/types/microsoft-365.md`
- `2-sensors-deployment/adapters/types/microsoft-defender.md`
- `2-sensors-deployment/adapters/types/microsoft-entra-id.md`
- `2-sensors-deployment/adapters/types/mimecast.md`
- `2-sensors-deployment/adapters/types/okta.md`
- `2-sensors-deployment/adapters/types/pandadoc.md`
- `2-sensors-deployment/adapters/types/s3.md`
- `2-sensors-deployment/adapters/types/sentinelone.md`
- `2-sensors-deployment/adapters/types/servicenow.md`
- `2-sensors-deployment/adapters/types/slack-audit-logs.md`
- `2-sensors-deployment/adapters/types/sophos.md`
- `2-sensors-deployment/adapters/types/sqs.md`
- `2-sensors-deployment/adapters/types/stdin.md`
- `2-sensors-deployment/adapters/types/sublime-security.md`
- `2-sensors-deployment/adapters/types/syslog.md`
- `2-sensors-deployment/adapters/types/tailscale.md`
- `2-sensors-deployment/adapters/types/threatlocker.md`
- `2-sensors-deployment/adapters/types/windows-event-log.md`
- `2-sensors-deployment/adapters/types/zendesk.md`
