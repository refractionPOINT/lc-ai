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
- `5-integrations/extensions/cloud-cli/1password.md`
- `5-integrations/extensions/cloud-cli/aws.md`
- `5-integrations/extensions/cloud-cli/azure.md`
- `5-integrations/extensions/cloud-cli/digitalocean.md`
- `5-integrations/extensions/cloud-cli/github.md`
- `5-integrations/extensions/cloud-cli/google-cloud.md`
- `5-integrations/extensions/cloud-cli/index.md`
- `5-integrations/extensions/cloud-cli/microsoft365.md`
- `5-integrations/extensions/cloud-cli/okta.md`
- `5-integrations/extensions/cloud-cli/sdm.md`
- `5-integrations/extensions/cloud-cli/sublime.md`
- `5-integrations/extensions/cloud-cli/tailscale.md`
- `5-integrations/extensions/cloud-cli/vultr.md`
- `5-integrations/extensions/limacharlie/artifact.md`
- `5-integrations/extensions/limacharlie/binlib.md`
- `5-integrations/extensions/limacharlie/cases.md`
- `5-integrations/extensions/limacharlie/dlp.md`
- `5-integrations/extensions/limacharlie/dumper.md`
- `5-integrations/extensions/limacharlie/epp.md`
- `5-integrations/extensions/limacharlie/exfil.md`
- `5-integrations/extensions/limacharlie/git-sync.md`
- `5-integrations/extensions/limacharlie/index.md`
- `5-integrations/extensions/limacharlie/infrastructure.md`
- `5-integrations/extensions/limacharlie/integrity.md`
- `5-integrations/extensions/limacharlie/lookup-manager.md`
- `5-integrations/extensions/limacharlie/payload-manager.md`
- `5-integrations/extensions/limacharlie/playbook.md`
- `5-integrations/extensions/limacharlie/reliable-tasking.md`
- `5-integrations/extensions/limacharlie/sensor-cull.md`
- `5-integrations/extensions/limacharlie/usage-alerts.md`
- `5-integrations/extensions/limacharlie/vulnerability-reporting.md`
- `5-integrations/extensions/limacharlie/yara-manager.md`
- `5-integrations/extensions/third-party/atomic-red-team.md`
- `5-integrations/extensions/third-party/cloudflare.md`
- `5-integrations/extensions/third-party/govee.md`
- `5-integrations/extensions/third-party/halopsa.md`
- `5-integrations/extensions/third-party/hayabusa.md`
- `5-integrations/extensions/third-party/index.md`
- `5-integrations/extensions/third-party/microsoft-response.md`
- `5-integrations/extensions/third-party/nims.md`
- `5-integrations/extensions/third-party/okta.md`
- `5-integrations/extensions/third-party/otx.md`
- `5-integrations/extensions/third-party/pagerduty.md`
- `5-integrations/extensions/third-party/plaso.md`
- `5-integrations/extensions/third-party/renigma.md`
- `5-integrations/extensions/third-party/secureannex.md`
- `5-integrations/extensions/third-party/sentinelone.md`
- `5-integrations/extensions/third-party/servicenow.md`
- `5-integrations/extensions/third-party/strelka.md`
- `5-integrations/extensions/third-party/threatlocker.md`
- `5-integrations/extensions/third-party/twilio.md`
- `5-integrations/extensions/third-party/velociraptor.md`
- `5-integrations/extensions/third-party/yara.md`
- `5-integrations/extensions/third-party/zeek.md`
