# SOC 2 (Trust Services Criteria) — Attribution & Verification

## Authoritative source

| Field | Value |
|---|---|
| **Publisher** | American Institute of Certified Public Accountants (AICPA) — now part of the AICPA & CIMA (Association of International Certified Professional Accountants) |
| **Title** | *TSP Section 100 — 2017 Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy* |
| **Original publication** | 2017 |
| **Most recent update** | 2022 Points of Focus refresh (updated mappings and illustrative examples; no new criteria added) |
| **Canonical URL** | https://www.aicpa-cima.com/topic/trust-services-criteria |
| **Direct download URL** | https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022 |
| **License / access** | Freely downloadable PDF; subject to AICPA terms of use |
| **SSAE standard** | SOC 2 examinations are conducted under *SSAE No. 18, Attestation Standards: Clarification and Recodification* (AICPA) |

## Verification status

**ATTESTATION_ONLY** — the TSC document is a freely-downloadable PDF. Structure (CC / A / C / PI / P category grouping, criterion numbering at `<prefix><group>.<number>`) is well-defined and stable, but we do not machine-extract criterion IDs from the PDF due to (a) licensing restrictions on redistribution and (b) the manageable number of criteria making manual validation tractable.

**Consequence:** Tier 4 validates the *format* of SOC 2 citations (`^(CC|A|C|PI|P)\d+\.\d+$`) but not their existence in the TSC. Content validation is human-attested.

## Criterion structure (for quick reference)

| Category | Prefix | Criteria count (approx.) |
|---|---|---|
| Common Criteria (always applicable) | `CC1.1`–`CC9.2` | 33 across 9 criteria groups (CC1–CC9) |
| Additional — Availability | `A1.1`–`A1.3` | 3 |
| Additional — Confidentiality | `C1.1`–`C1.2` | 2 |
| Additional — Processing Integrity | `PI1.1`–`PI1.5` | 5 |
| Additional — Privacy | `P1`–`P8` (multiple criteria per group) | ~18 |

Our docs reference Common Criteria extensively (CC6 Logical Access, CC7 System Operations, CC8 Change Management, CC9 Risk Mitigation), plus partial coverage of A1.2 and C1.1/C1.2.

## Citation format used in our docs

- Criterion: `CC6.1`, `CC7.2`, `A1.2`
- Written out: "SOC 2 TSC CC6.1"

Stored in D&R rule metadata under `soc2_criterion:` and consumed by the SOC 2 compliance reviewer agent.

## Scope of reliance

Our docs rely on the source for:
- Common Criteria group structure (CC1–CC9)
- Additional criteria prefixes (A, C, PI, P)
- Criterion numbering convention
- Type I vs Type II audit framing (point-in-time vs 12-month observation)
- Points of focus as interpretive aids (2022 refresh)

Our docs do **not** rely on the source for:
- Audit opinion wording (AICPA attestation standards)
- System description format (AICPA *Description Criteria for a Service Organization's System*)
- Subservice-organization carve-out methodology
- Auditor judgment on operating effectiveness of individual controls

## Independent re-verification (manual)

1. Download the TSC PDF from the canonical URL above.
2. For each `soc2_criterion:` citation in our implementation doc, confirm the criterion ID exists in the PDF's table of criteria (Section 100).
3. Confirm the "Points of Focus" for each criterion align with our described LC coverage (points of focus are illustrative, not prescriptive — auditors may consider other equivalent evidence).
4. Re-verify on each TSC update (e.g., future points-of-focus refreshes).

## Auditor engagement note

SOC 2 examinations are performed by licensed CPA firms under AICPA professional standards. This repository's artifacts can support such an examination as evidence of control design and operating effectiveness, but they are not a substitute for the auditor's judgment. The firm's opinion (SOC 2 report) is the only externally-valid attestation of compliance.
