# HIPAA Security Rule — Attribution & Verification

## Authoritative source

| Field | Value |
|---|---|
| **Publisher** | U.S. Department of Health and Human Services (HHS), Office for Civil Rights (OCR) |
| **Regulation** | 45 CFR Part 164 — Security and Privacy |
| **Subparts in scope** | Subpart A (General Provisions), Subpart C (Security Standards), Subpart D (Breach Notification) |
| **Enabling legislation** | Health Insurance Portability and Accountability Act of 1996 (HIPAA), as amended by HITECH Act (2009) and the HIPAA Omnibus Rule (2013) |
| **Canonical URL** | https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164 |
| **Source of normative text** | Electronic Code of Federal Regulations (eCFR), maintained by the Office of the Federal Register (OFR) and the Government Publishing Office (GPO) |
| **License / access** | Public domain — U.S. government regulation |

## Machine-readable source (eCFR API)

| Field | Value |
|---|---|
| **Source format** | eCFR XML full-text |
| **API endpoint** | `https://www.ecfr.gov/api/versioner/v1/full/{date}/title-45.xml?part=164` |
| **As-of date** | 2025-01-01 (stable snapshot) |
| **Retrieval date** | 2026-04-16 |
| **Staged copy** | `compliance/testing/attribution_sources/hipaa-45cfr-164-subsections.json` (997 extracted subsection IDs) |

## Verification status

**MACHINE_VERIFIED** — Every HIPAA citation in our docs is validated by Tier 4 against the eCFR-derived subsection ID list.

**Known parser limitation:** The CFR uses a compound-marker paragraph style (e.g., `(a)(1)` in a single paragraph vs nested `(a)` then `(1)`). Our parser handles this and resolves nested hierarchy with context-aware kind disambiguation (single lowercase letters like `i` are ambiguous between alpha `(i)` and roman numeral level; resolved by examining the current stack). Verified against 18 spot-check citations from our docs including `§164.312(b)`, `§164.312(a)(2)(iii)`, `§164.308(a)(5)(ii)(B/C/D)`, `§164.308(a)(6)(ii)`, `§164.316(b)(2)(i)`, `§164.400`, `§164.404`, `§164.406`, `§164.408`, `§164.410`, `§164.414`.

## Citation format used in our docs

- Section: `§164.312`, `§164.308`
- Implementation specification with subsection hierarchy: `§164.312(b)`, `§164.312(a)(2)(iii)`, `§164.308(a)(5)(ii)(C)`
- Written out: "HIPAA Security Rule §164.312(b)"

Stored in D&R rule metadata under `hipaa_safeguard:` and consumed by the HIPAA compliance reviewer agent.

## Scope of reliance

Our docs rely on the source for:
- Section numbering within 45 CFR Part 164
- Subsection hierarchy (Subpart C Technical Safeguards structure)
- Breach Notification Rule citations (§164.400-414 in Subpart D)
- Required / Addressable implementation specification flags (derived from reading the normative text)

Our docs do **not** rely on the source for:
- Interpretation of what "Addressable" means in a particular organizational context
- Application of the 60-day breach-notification timeline to specific fact patterns (counsel / privacy officer)
- Mapping to state privacy laws
- Enforcement discretion by OCR

## Independent re-verification

1. Visit the canonical URL above and inspect 45 CFR Part 164 directly.
2. Run `compliance/testing/tier4_citations.py --framework hipaa` — re-parses the eCFR XML and validates all citations.
3. Subscribe to eCFR amendment notifications; when Part 164 is amended, re-fetch and re-run the verifier.

## Related HHS guidance (not normative but frequently cited)

- HHS *HIPAA Security Rule Crosswalk to NIST Cybersecurity Framework* — https://www.hhs.gov/sites/default/files/nist-csf-to-hipaa-security-rule-crosswalk-02-22-2016-final.pdf
- NIST SP 800-66 Rev 2 — *Implementing the HIPAA Security Rule: A Cybersecurity Resource Guide* — https://csrc.nist.gov/publications/detail/sp/800-66/rev-2/final

These are interpretive aids; the CFR text is authoritative.
