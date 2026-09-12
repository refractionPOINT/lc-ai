---
name: platform-configuration
description: "Manage infrastructure-as-code, apps, playbooks and reusable platform configuration with scoped diffs and verified execution."
---

# Platform configuration, apps and IaC

Use `sync` for versioned organization configuration through the infrastructure extension. Read actual pull/push flags and choose resource types explicitly. Pull the current scoped configuration and prepare the intended diff with `sync push --dry-run`. This harness blocks direct bulk `sync push` because it could bypass per-resource validation. Translate the reviewed diff into individual prepared resource changes, using the mandatory artifact workflow for standard D&R rules. If the diff contains a resource with no supported individual operation, report that item as blocked rather than applying an incomplete configuration as success. D&R and FP are Hive resources in current sync. Avoid treating an incomplete export as authoritative desired state; inspect deletion behavior and secret redaction before pushing. Preserve a rollback artifact with secrets protected.

Apps are configured LC UI resources; inspect existing app schema and referenced queries, actions and permissions. Validate data sources and resulting user-visible behavior with the intended user's access. An app rendering for an administrator does not prove its audience can use it.

Playbooks are executable serverless code with a documented entrypoint and environment. Read playbook runtime documentation before authoring; discover invocation action via extension schema. Storing the Python source does not run or validate its external effects. Test with controlled input, bounded runtime and appropriate credentials, then verify the result and any service job. Dependencies on lookups, secrets and extensions must exist; read only the relevant capability packages for those prerequisites.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `5-integrations/extensions/limacharlie/infrastructure.md`
- `5-integrations/extensions/limacharlie/git-sync.md`
- `apps/reference.md`
- `apps/creating-and-managing-apps.md`
- `5-integrations/extensions/limacharlie/playbook.md`
