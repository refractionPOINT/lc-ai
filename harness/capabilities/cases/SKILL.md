---
name: cases
description: "Manage Case lifecycle, notes, entities, detections, telemetry and artifacts with verified links and scoped bulk updates."
---

# Cases and evidence records

Inspect the case and its current lifecycle, assignee and evidence before updating. Discover accepted values with `case --ai-help` and specific command help; do not invent statuses. Use entity, detection, telemetry and artifact subcommands to attach typed evidence and preserve source identifiers. Notes should distinguish observations, interpretation and outstanding work.

Read before adding to avoid duplicate evidence on retries. For bulk updates and merges, enumerate exact case IDs and inspect the proposed scope; a merge is not just a reversible status change. Verify final case fields and evidence links after mutation. A case closure records workflow state, not proof that endpoint or mailbox remediation completed. Keep report exports scoped to intended recipients and omit secret values and unsupported conclusions.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `5-integrations/extensions/limacharlie/cases.md`
