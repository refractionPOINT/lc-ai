# CMMC v2 — Attribution & Verification

## Authoritative source

| Field | Value |
|---|---|
| **Publisher** | U.S. Department of Defense, Office of the Chief Information Officer (DoD CIO) |
| **Program** | Cybersecurity Maturity Model Certification (CMMC) 2.0 |
| **Canonical URL** | https://dodcio.defense.gov/CMMC/ |
| **Rule of law** | 32 CFR Part 170 (CMMC Program Rule), effective 2024-12-16 |
| **Federal Register notice** | https://www.federalregister.gov/documents/2024/10/15/2024-22905/cybersecurity-maturity-model-certification-cmmc-program |
| **License / access** | Public — U.S. government program |

## Foundational controls

CMMC v2 incorporates by reference:

- **CMMC Level 1** — 15 practices from FAR 52.204-21 *Basic Safeguarding of Covered Contractor Information Systems*
- **CMMC Level 2** — 110 practices from **NIST SP 800-171 Revision 2** (February 2020)
- **CMMC Level 3** — CMMC Level 2 + a subset of **NIST SP 800-172** (February 2021)

| Practice source | URL |
|---|---|
| NIST SP 800-171 Rev 2 | https://csrc.nist.gov/publications/detail/sp/800-171/rev-2/final |
| NIST SP 800-172 | https://csrc.nist.gov/publications/detail/sp/800-172/final |
| FAR 52.204-21 | https://www.acquisition.gov/far/52.204-21 |

## Verification status

**ATTESTATION_ONLY** (machine verification pending a machine-readable NIST SP 800-171 Rev 2 source)

**Why not machine-verified:** NIST's OSCAL repository (`usnistgov/oscal-content`) currently hosts SP 800-171 **Rev 3** (the 2024 revision with 130 controls) but not Rev 2 (the 110-control version CMMC actually uses). CMMC's own machine-readable control list is not publicly distributed in a convenient format.

**Consequence:** Tier 4 does not automatically validate individual CMMC practice IDs against an authoritative list. Citations should be human-reviewed against the NIST SP 800-171 Rev 2 PDF before any external (auditor, C3PAO) reliance.

**Partial mitigation:** NIST SP 800-171 Rev 3 OSCAL is staged at `compliance/testing/attribution_sources/nist-800-171-rev3-catalog.json` for reference, with the understanding that Rev 3 has a different practice-ID scheme (e.g., `03.01.01` vs Rev 2's `3.1.1`).

## Citation format used in our docs

- Practice ID: `AU.L2-3.3.1` — family (AU) . level (L2) - NIST 800-171 control (3.3.1)
- Written out: "CMMC v2 Practice AU.L2-3.3.1"

Stored in D&R rule metadata under `cmmc_control:` and consumed by the CMMC compliance reviewer agent.

## Scope of reliance

Our docs rely on the source for:
- Practice ID format (`<family>.<level>-<800-171 control>`)
- Level structure (L1 / L2 / L3)
- Families assessed (AU, AC, IA, SI, IR, CM, SC, MP, PE, PS, RA, CA, CP, SA, SR)
- Certification tier requirements (C3PAO for L2+, self-attestation for L1)

Our docs do **not** rely on the source for:
- Exact normative text of each practice (see NIST SP 800-171 Rev 2 PDF)
- Assessment objectives (see NIST SP 800-171A)
- CMMC Assessment Guide content (see DoD CIO guidance documents)

## Independent re-verification (manual)

1. Obtain NIST SP 800-171 Rev 2 PDF from the URL above.
2. For each CMMC citation in our implementation doc, confirm the practice ID appears in the 800-171 Rev 2 Appendix D or the corresponding family section.
3. For Level 3 practices, cross-reference against NIST SP 800-172.
4. For CMMC-specific procedural requirements (C3PAO assessments, POA&M limits), cross-reference against the current CMMC Assessment Guide on the DoD CIO site.

## DFARS interaction

CMMC implementation is separate from but related to **DFARS 252.204-7012** (*Safeguarding Covered Defense Information and Cyber Incident Reporting*). The CMMC agent flags suspected CUI spillage with a 72-hour DoD reporting requirement — that obligation derives from DFARS 252.204-7012, not CMMC itself. See the clause text at https://www.acquisition.gov/dfars/252.204-7012-safeguarding-covered-defense-information-and-cyber-incident-reporting.
