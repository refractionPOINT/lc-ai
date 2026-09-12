---
name: extensions
description: "Discover, subscribe, configure and invoke Extensions using their live schemas and monitor asynchronous service jobs."
---

# Extensions and service jobs

Use `extension list-available` and `extension list` to distinguish supported capabilities from subscribed ones. Subscription, configuration, credential access and caller permission are separate prerequisites. Read the extension's live `schema` and specific bundled documentation before constructing config or request payloads.

Use `extension config-get` and `config-set` for settings and `extension request` for actions. Do not guess action names or reuse another extension's schema. Confirm impersonation semantics and external effects for the selected action. Subscription can grant permissions and incur usage; keep it within the user's requested setup scope.

A response containing a job ID is pending work. Record the ID, inspect `job get` or bounded `job wait`, and evaluate terminal success, failure, cancellation or timeout, including errors inside an otherwise successful HTTP response. Do not blindly retry an external action after a timeout. Reconcile its status first. A feedback request remaining unanswered is pending, not user approval.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `5-integrations/extensions/index.md`
- `5-integrations/extensions/using-extensions.md`
- `6-developer-guide/extensions/schema-data-types.md`
- `5-integrations/extensions/limacharlie/feedback.md`
