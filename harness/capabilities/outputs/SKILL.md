---
name: outputs
description: "Configure event, detection or audit Outputs and verify external delivery and forwarding errors."
---

# Outputs and delivery

Determine destination module, data stream (`event`, `detect`, or `audit`), filtering and credential reference. Read the matching document under `5-integrations/outputs/destinations/`; field names and authentication differ between destinations. Distinguish event forwarding from retention and ingestion.

Read existing output configuration, preserve unrelated filters and routing, then use the documented `output` operation. The CLI may expose create without an update verb; inspect its help and the documented API escape hatch rather than guessing `output update` or deleting a working destination first. Do not expose a destination token while inspecting config.

Verify saved configuration and delivery separately. Inspect `org errors` for `outputs/<name>` and confirm receipt at the destination when that access is available. A controlled audit event can test transport, but switching a production stream to audit interrupts its intended forwarding: use a separately authorized test output or the requested stream. Outputs can temporarily disable after failures and retry later. Report configuration acceptance, observed delivery and any inaccessible destination verification distinctly.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `5-integrations/outputs/index.md`
- `5-integrations/outputs/stream-structures.md`
- `5-integrations/outputs/testing.md`
- `5-integrations/outputs/allowlisting.md`
- `5-integrations/outputs/destinations/amazon-s3.md`
- `5-integrations/outputs/destinations/apache-kafka.md`
- `5-integrations/outputs/destinations/azure-event-hub.md`
- `5-integrations/outputs/destinations/azure-storage-blob.md`
- `5-integrations/outputs/destinations/bigquery.md`
- `5-integrations/outputs/destinations/elastic.md`
- `5-integrations/outputs/destinations/google-cloud-storage.md`
- `5-integrations/outputs/destinations/google-pubsub.md`
- `5-integrations/outputs/destinations/humio.md`
- `5-integrations/outputs/destinations/ms-teams.md`
- `5-integrations/outputs/destinations/opensearch.md`
- `5-integrations/outputs/destinations/scp.md`
- `5-integrations/outputs/destinations/sftp.md`
- `5-integrations/outputs/destinations/slack.md`
- `5-integrations/outputs/destinations/smtp.md`
- `5-integrations/outputs/destinations/splunk.md`
- `5-integrations/outputs/destinations/syslog.md`
- `5-integrations/outputs/destinations/telegram.md`
- `5-integrations/outputs/destinations/tines.md`
- `5-integrations/outputs/destinations/webhook-bulk.md`
- `5-integrations/outputs/destinations/webhook.md`
