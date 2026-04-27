# CIS Critical Security Controls v8 — Attribution & Verification

## Authoritative source

| Field | Value |
|---|---|
| **Publisher** | Center for Internet Security, Inc. (CIS) |
| **Title** | *CIS Critical Security Controls, Version 8* |
| **Publication date** | May 2021 (v8.0); minor updates in v8.1 (2024) |
| **Canonical URL** | https://www.cisecurity.org/controls/v8 |
| **Direct download (registration required, free)** | https://www.cisecurity.org/controls/cis-controls-list (email registration then PDF) |
| **License / access** | Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 (CC BY-NC-ND 4.0). Free use for non-commercial purposes; attribution required; no modification of the controls document itself. |
| **Governance** | The CIS Controls are maintained by a community of practitioners under CIS's stewardship. |

## Verification status

**ATTESTATION_ONLY** — the CIS Controls v8 PDF is freely downloadable after registration but subject to the CC BY-NC-ND license. We do not redistribute or machine-extract the document in this repository.

**Consequence:** Tier 4 does not validate individual CIS Safeguard IDs against an automatically-extracted authoritative list. Citations should be human-verified against the CIS Controls v8 PDF before external reliance.

**Partial machine-verification available:** Tier 4 validates the *format* of CIS citations (`^\d+\.\d+$`, e.g., `8.2`) and confirms the control number (left of the dot) is in the range 1–18.

## Structure (public knowledge)

CIS Controls v8 is organized into:

| Control | Title | Public safeguard count (advertised) |
|---|---|---|
| 1 | Inventory and Control of Enterprise Assets | 5 |
| 2 | Inventory and Control of Software Assets | 7 |
| 3 | Data Protection | 14 |
| 4 | Secure Configuration of Enterprise Assets and Software | 12 |
| 5 | Account Management | 6 |
| 6 | Access Control Management | 8 |
| 7 | Continuous Vulnerability Management | 7 |
| 8 | Audit Log Management | 12 |
| 9 | Email and Web Browser Protections | 7 |
| 10 | Malware Defenses | 7 |
| 11 | Data Recovery | 5 |
| 12 | Network Infrastructure Management | 8 |
| 13 | Network Monitoring and Defense | 11 |
| 14 | Security Awareness and Skill Training | 9 |
| 15 | Service Provider Management | 7 |
| 16 | Application Software Security | 14 |
| 17 | Incident Response Management | 9 |
| 18 | Penetration Testing | 5 |

**Advertised total: ~153 Safeguards.** Individual safeguard IDs (e.g., `8.1`, `8.2`, …) must be verified against the official PDF.

## Implementation Groups (IG1 / IG2 / IG3)

Each safeguard is tagged with one of three Implementation Groups:
- **IG1** (foundational) — small-org minimum; ~56 safeguards
- **IG2** (essential) — medium-org baseline; adds ~74 more to IG1
- **IG3** (advanced) — large/regulated-org advanced; adds the remaining to IG2

The CIS v8 agent in this repo reads `cis-ig1`/`cis-ig2`/`cis-ig3` sensor/org tags to identify the org's committed tier.

## Citation format used in our docs

- Safeguard: `8.2`, `10.7`, `17.1`
- Written out: "CIS v8 Safeguard 8.2"

Stored in D&R rule metadata under `cis_safeguard:` and consumed by the CIS v8 compliance reviewer agent.

## Scope of reliance

Our docs rely on the source for:
- 18-Control organizational structure
- Safeguard numbering convention (`<control>.<safeguard>`)
- IG1/IG2/IG3 tiering concept
- Retention guidance in Safeguard 8.10 (at least 90 days)
- Cross-walks to other frameworks (documented in CIS Community mappings)

Our docs do **not** rely on the source for:
- Exact normative text of each Safeguard
- CIS Benchmarks (separate product — benchmark hardening guides)
- CIS Hardened Images (separate product)
- CIS-CAT Pro Assessor (assessment tooling)

## Independent re-verification (manual)

1. Visit the canonical URL and register (free, email).
2. Download the CIS Controls v8 PDF.
3. For each `cis_safeguard:` citation in our implementation doc, confirm the safeguard ID exists in the PDF and the safeguard text aligns with our described LC coverage.
4. Confirm IG tier assignments per safeguard.
5. Re-verify when CIS publishes updated versions (v8.1 most recent; major versions typically every 2–3 years).

## Related CIS publications (not a substitute for v8)

- CIS Controls v8 Companion Guides (IG-specific)
- CIS Controls Self-Assessment Tool (CSAT) — scoring tool
- CIS Community Defense Model (CDM) — threat-to-control mappings
- CIS Mappings to NIST CSF / NIST 800-53 / HIPAA / PCI / ISO 27001 — community-maintained

These are interpretive aids; the controls document itself is authoritative.
