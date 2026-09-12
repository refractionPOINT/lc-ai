---
name: cloud-security
description: "Configure cloud posture providers and policies; operate findings, inventory, graph, identity, data security and asset coverage."
---

# Cloud Security

Cloud Security requires `ext-cloud-security` subscription independently of `cloudsec.get`/`cloudsec.set`. Provider connections are `cloudsec_provider` and policies are `cloudsec_policy` Hive records. Read provider-specific setup and preflight documentation; verify credential scope, provider coverage and collection status before interpreting the absence of inventory or findings. A stale/partial collection cannot establish a healthy estate.

Use native `cloudsec` finding, inventory, resource, graph, ciem, data-security and caasm commands for the requested operation. Discover filters and pagination in current help. A resource URN, sensor SID, finding ID and provider key are different identifiers. Prefer native aggregates/topology and bounded graph expansion over downloading the entire estate. Read original finding evidence and current resource state before changing disposition, owner or ticket; resolving a finding is not cloud-side remediation. Verify updated disposition and distinguish it from subsequent collector evidence.

Posture rules are `policy_type: rules` records in `cloudsec_policy`, not ordinary `dr-general` rules. Read custom-rules.md before authoring: detect sees normalized `event/` resource properties, supports a restricted operator set and no sensor responses. Match observed bad state rather than missing data. Use scoped conditions for a single list element; scalar lists use the documented `/v` representation. Respect custom identifiers, resource types, finding classes and pack budgets. Preview supported policy matchers with `cloudsec simulate`; this does not establish every custom rule's correctness. Verify write-time validation, next collection/projection, reported rule rejections and resulting finding volume.

Code scanning has its own prerequisites and procedures: load code-security. Built-in assessments and query packs are first-level operations; designing a compliance program or a broad hunting methodology is outside this package.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `cloud-security/getting-started.md`
- `cloud-security/configuration.md`
- `cloud-security/findings.md`
- `cloud-security/graph.md`
- `cloud-security/custom-rules.md`
- `cloud-security/caasm.md`
- `cloud-security/cli.md`
- `8-reference/cloud-security-api-iac.md`
- `cloud-security/provider-setup/anthropic.md`
- `cloud-security/provider-setup/auth0.md`
- `cloud-security/provider-setup/aws.md`
- `cloud-security/provider-setup/azure.md`
- `cloud-security/provider-setup/cloudflare.md`
- `cloud-security/provider-setup/entra.md`
- `cloud-security/provider-setup/gcp.md`
- `cloud-security/provider-setup/github.md`
- `cloud-security/provider-setup/google-workspace.md`
- `cloud-security/provider-setup/index.md`
- `cloud-security/provider-setup/limacharlie.md`
- `cloud-security/provider-setup/okta.md`
- `cloud-security/provider-setup/onepassword.md`
- `cloud-security/provider-setup/openai.md`
- `cloud-security/api-reference.md`
- `cloud-security/automation.md`
- `cloud-security/code-scanning.md`
- `cloud-security/compliance.md`
- `cloud-security/index.md`
- `cloud-security/mcp.md`
- `cloud-security/providers.md`
- `cloud-security/remediation-sla.md`
