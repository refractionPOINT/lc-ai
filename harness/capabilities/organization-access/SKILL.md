---
name: organization-access
description: "Resolve organizations, inspect identity and permissions, manage users, groups, API keys, quotas and billing."
---

# Organization and access

Resolve organization names to UUIDs using `org list`; pass the intended `--oid` explicitly. Check `auth whoami` and distinguish the authenticated identity, its permissions, and organization availability. A denied operation does not mean the resource is absent. Do not change identities or widen permissions to circumvent denial.

Read existing membership and direct/group permissions before an access change. Grant only the requested scope and preserve unrelated grants; a user API key and organization API key have different identity semantics. Verify the resulting membership or key metadata after the change. Keep key values out of transcripts and artifacts; use the secret capability when storage is required.

Use `org info`, `org config-get`, `org stats`, `org errors`, and `audit list` to inspect settings and operational errors. Read command-specific help before `org config-set`: distinguish platform settings from local CLI `config`. Billing status and plans are observations, not authority to change subscriptions or invent a cost estimate. Confirm exact organization and irreversible implications when deletion is requested. Report which permission or owner action is missing when blocked.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `7-administration/access/api-keys.md`
- `7-administration/access/user-access.md`
- `8-reference/permissions.md`
- `7-administration/billing/options.md`
