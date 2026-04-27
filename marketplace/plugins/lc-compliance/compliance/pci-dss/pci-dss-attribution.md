# PCI DSS v4.0 — Attribution & Verification

## Authoritative source

| Field | Value |
|---|---|
| **Publisher** | PCI Security Standards Council, LLC (PCI SSC) |
| **Title** | *Payment Card Industry Data Security Standard — Requirements and Testing Procedures* |
| **Version** | v4.0 (originally March 2022); v4.0.1 released June 2024 |
| **Canonical URL** | https://www.pcisecuritystandards.org/document_library/ |
| **Direct download (registration required, free)** | Document library, "PCI DSS v4.0.1" |
| **License / access** | Freely downloadable after accepting a registration agreement at pcisecuritystandards.org; no purchase required but the PDF is subject to PCI SSC terms of use |
| **Transition timeline** | PCI DSS v3.2.1 retired 2024-03-31. v4.0 requirements future-dated to 2025-03-31 are now effective. |

## Verification status

**ATTESTATION_ONLY** — the PCI DSS v4.0.1 PDF is not machine-parseable in a repeatable automated pipeline without redistributing the document (which PCI SSC's terms of use restrict). Citations in our docs use requirement numbers that follow the v4.0 tree (e.g., 10.2.1.1, 11.5.2, 12.10.x). These IDs are publicly referenced in the PCI SSC *Summary of Changes* and Quick Reference Guide, but the full control catalog requires downloading the PDF.

**Consequence:** Tier 4 does not validate PCI citations against an automatically-extracted authoritative list. Citations should be human-verified against the PCI DSS v4.0.1 PDF before external (QSA, ROC) reliance.

**Partial machine-verification available:** requirement-number *format* can be validated (regex: `^\d+(\.\d+){0,3}$`), ensuring no fabricated formats. This is implemented in Tier 4 as a format check, not a content check.

## Citation format used in our docs

- Top-level requirement: `Req 10` (Logging & Monitoring)
- Sub-requirement: `Req 10.2.1.1` (specific testing procedure)
- Written out: "PCI DSS v4.0 Req 10.2.1.1"

Stored in D&R rule metadata under `pci_dss_req:` and consumed by the PCI compliance reviewer agent.

## Scope of reliance

Our docs rely on the source for:
- Requirement tree numbering (Reqs 1–12; sub-requirements at 2–4 levels of depth)
- CDE (Cardholder Data Environment) scope concept
- Retention: Req 10.5.1 — at least 12 months retention, 3 months immediately available
- Req 11.5.1 — change-detection mechanism deployment
- Testing-procedure taxonomy

Our docs do **not** rely on the source for:
- QSA assessment methodology (PCI SSC *Report on Compliance (ROC) Reporting Template*)
- SAQ (Self-Assessment Questionnaire) applicability mapping
- Compensating controls worksheet
- Attestation of Compliance (AOC) format

## Independent re-verification (manual)

1. Register (free) at https://www.pcisecuritystandards.org and accept the document-library terms of use.
2. Download PCI DSS v4.0.1 (or the current version).
3. For each `pci_dss_req:` citation in our implementation doc, confirm the requirement ID exists in the PDF's Requirement and Testing Procedure table.
4. When PCI DSS is amended (typically every 3 years major + interim errata), re-verify citations.

## Related PCI SSC supporting documents

- *PCI DSS v4.0 Summary of Changes* — useful for identifying v3.2.1 → v4.0 migration deltas
- *PCI DSS v4.0 Quick Reference Guide* — public summary suitable for orientation, not for assessment
- *PCI DSS v4.0 Prioritized Approach* — risk-ranked implementation guidance

All available (with registration) at the PCI SSC document library.

## CDE scope concept

PCI DSS applies only to systems that store, process, or transmit cardholder data (CHD) or sensitive authentication data (SAD), plus connected systems that can affect CDE security. Our PCI agent's scope check validates this via sensor tags (`cde`, `pci-scope`, `card-data`, `pci-dss`). QSAs use a formal scoping exercise that our agent does not substitute for.
