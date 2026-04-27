# ISO/IEC 27001:2022 / ISO/IEC 27002:2022 — Attribution & Verification

## Authoritative sources

| Field | Value |
|---|---|
| **Publisher** | International Organization for Standardization (ISO) jointly with the International Electrotechnical Commission (IEC) |
| **Primary standard** | *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements* |
| **Annex A control source** | *ISO/IEC 27002:2022 — Information security, cybersecurity and privacy protection — Information security controls* |
| **Publication date** | 2022-10-25 (27001), 2022-02-15 (27002) |
| **Canonical URL (ISO Browsing Platform)** | https://www.iso.org/standard/27001 and https://www.iso.org/standard/75652.html |
| **License / access** | **Paywalled.** ISO/IEC 27001:2022 — approx. USD 180. ISO/IEC 27002:2022 — approx. USD 215. Prices vary by region and ISO member distributor. |

## Verification status

# ⚠️ UNVERIFIED ⚠️

**The ISO/IEC 27002:2022 control wording and Annex A control list have NOT been machine-verified against the authoritative source.** ISO standards are distributed commercially and we cannot redistribute them. Our control citations (e.g., `A.8.15`) are based on publicly-available summaries, vendor mappings, and training materials — none of which are authoritative.

**This means:**
- An Annex A control ID cited in our docs *may* not exist in the published standard.
- The *wording* of controls we paraphrase *may* differ from the normative text.
- The 2022↔2013 mapping noted in our docs is illustrative, not normative.

**To achieve machine-verified status**, one of:

1. A licensed user of ISO/IEC 27002:2022 extracts the full Annex A control ID list (e.g., `A.5.1`, `A.5.2`, …, `A.8.34`) and stages it at `compliance/testing/attribution_sources/iso-27002-2022-controls.json`. Tier 4 will then validate every `iso_27001_control:` citation against this list.
2. Acquire the ISO standards via https://www.iso.org/ (or a national ISO member — ANSI for US, BSI for UK, DIN for Germany, etc.) for your organization.

Until one of these is done, **treat all ISO/IEC 27001 content in this repository as draft guidance**, not a compliance artifact.

## What we can say with confidence

The 2022 edition of ISO/IEC 27002 **publicly advertised** the reorganization of Annex A into **4 themes** (down from 14 categories in the 2013 edition):

| Theme | Prefix | Advertised count |
|---|---|---|
| Organizational controls | A.5 | 37 |
| People controls | A.6 | 8 |
| Physical controls | A.7 | 14 |
| Technological controls | A.8 | 34 |

**Total: 93 controls.** These counts are referenced in public ISO and vendor material but the individual IDs must be cross-checked against the purchased standard.

## Citation format used in our docs

- Annex A control: `A.8.15`, `A.5.26`
- Written out: "ISO/IEC 27001:2022 Annex A.8.15"

Stored in D&R rule metadata under `iso_27001_control:` and consumed by the ISO compliance reviewer agent.

## Scope of reliance (with UNVERIFIED caveat)

Our docs rely on publicly-available summaries for:
- 4-theme organization (A.5 / A.6 / A.7 / A.8)
- Approximate control counts per theme
- Citation format convention
- 2022↔2013 equivalence table structure

Our docs do **not** rely on the source for:
- Exact normative text of individual controls
- Control implementation guidance
- Application of risk assessment methodology (ISO 27005)
- ISMS scope definition methodology
- Statement of Applicability (SoA) content

## Independent re-verification (mandatory before external use)

1. Purchase ISO/IEC 27002:2022 via the canonical URL or a national ISO member.
2. Extract all Annex A control IDs (A.5.x, A.6.x, A.7.x, A.8.x) to a JSON or text file.
3. Place at `compliance/testing/attribution_sources/iso-27002-2022-controls.json`.
4. Run `compliance/testing/tier4_citations.py --framework iso-27001` — the verifier will auto-detect the staged file and switch verification status to MACHINE_VERIFIED.
5. Re-verify every `iso_27001_control:` citation in the implementation doc against the purchased standard's normative text before external reliance.

## Certification context

ISO/IEC 27001 certification is performed by accredited third-party certification bodies through stage 1 (documentation review) and stage 2 (implementation assessment) audits, followed by annual surveillance audits and a recertification audit every 3 years. Our docs and agent support such an audit by providing technical control evidence — they do not substitute for the certification body's judgment.
