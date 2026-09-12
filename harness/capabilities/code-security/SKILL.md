---
name: code-security
description: "Configure repository scanning, inspect code findings and SBOMs, ingest scan results, rescan and operate authorized dependency fixes."
---

# Code Security

Code is the `cloudsec code` lane, sharing Cloud Security findings; it is not a separate `codesec` command. Check `ext-cloud-security` subscription, `cloudsec.get` and write permission when needed. Repository inventory access does not imply `Contents: Read-only`; inspect collection and per-repository scan status for missing permission or skipped scan reasons.

Scanning is opt-in through a `code_scanning` policy in `cloudsec_policy`. Select repository include/exclude scope explicitly: an empty include can mean every visible repository. Choose actual scanner booleans and schedule; at least one scanner must be enabled. A severity floor discards findings below it rather than only filtering the UI. Read the policy schema before changes and verify selected repositories and scan completion afterward.

Use `cloudsec code repos` and `status`; a repository-triggered rescan is reflected in that repository's row and need not update estate-wide status. Findings are in `cloudsec finding list` with repository filtering. Record commit/ref, scan time, engines that ran and partial failures. An accepted rescan is pending until the repository result changes. SBOM links may expire; keep metadata and protected artifact references rather than sharing signed URLs broadly.

For `code ingest`, identify SARIF, CycloneDX or native report format, repository and commit. Assert scanner success only from the actual scan exit/status evidence; an incomplete report must not close prior findings. Pushed credential findings have special restrictions: read the documentation before promising import. Local `code scan` needs an available scanner runtime; do not assume the session contains Docker.

PR checks and dependency AutoFix require a separate opted-in write App; the inventory connection stays read-only. Verify the exact finding and repository before requesting AutoFix: `--repo` is a search hint, not an authorization boundary. Distinguish PR creation from merged remediation and subsequent successful scan. Never reveal detected secret values; remediation may require rotation even after a file was deleted.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `cloud-security/code-scanning.md`
- `cloud-security/provider-setup/github.md`
- `cloud-security/findings.md`
- `cloud-security/cli.md`
