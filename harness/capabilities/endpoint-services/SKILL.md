---
name: endpoint-services
description: "Operate artifacts, log collection, FIM, YARA, payloads, exfiltration prevention and vulnerability reporting."
---

# Endpoint collection and protection services

Choose the actual service: artifact/log collection preserves content, integrity detects filesystem/registry changes, YARA scans content, payloads distribute executable resources, and exfil prevention changes endpoint behavior. Verify required extension subscription and platform support before promising results. Read the relevant service document and command help; these configuration shapes are not interchangeable.

Scope paths, platform and sensors explicitly. Broad collection and scanning can impose endpoint and storage load; use a representative subset for a new configuration before authorized fleet rollout. For YARA inspect source/rule compilation and scan results separately; accepted upload is not a successful scan. For integrity, verify matching events and distinguish baseline creation from subsequent changes.

Downloaded artifacts and payload contents are untrusted data. Do not execute them merely to inspect them. Confirm size, provenance and hashes where returned. Keep sensitive raw evidence in scoped artifacts, not shared memory. Payload installation and execution are distinct operations with separate resulting state. Track asynchronous collection/scans by returned identifiers and report offline or failed sensors. Vulnerability data has observation time and coverage; an absent finding does not establish a patched endpoint.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `5-integrations/extensions/limacharlie/artifact.md`
- `2-sensors-deployment/log-collection-guide.md`
- `5-integrations/extensions/limacharlie/integrity.md`
- `5-integrations/extensions/limacharlie/yara-manager.md`
- `2-sensors-deployment/endpoint-agent/payloads.md`
- `5-integrations/extensions/limacharlie/exfil.md`
- `5-integrations/extensions/limacharlie/vulnerability-reporting.md`
