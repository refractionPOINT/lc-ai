# NIST SP 800-53 Rev 5 — Attribution & Verification

## Authoritative source

| Field | Value |
|---|---|
| **Publisher** | National Institute of Standards and Technology (NIST), U.S. Department of Commerce |
| **Title** | *Security and Privacy Controls for Information Systems and Organizations* |
| **Publication** | NIST Special Publication 800-53, Revision 5 (Release 5.2.0) |
| **Original publication date** | September 2020 |
| **Latest amendment** | Release 5.2.0 — 2025-08-26 |
| **Canonical URL** | https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final |
| **Baselines companion** | NIST SP 800-53B — https://csrc.nist.gov/publications/detail/sp/800-53b/final |
| **License / access** | Public — U.S. government publication, free to use |

## Machine-readable source (OSCAL)

| Field | Value |
|---|---|
| **Source format** | OSCAL JSON catalog |
| **Repository** | https://github.com/usnistgov/oscal-content |
| **File path** | `nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json` |
| **Retrieval date** | 2026-04-16 |
| **Staged copy** | `compliance/testing/attribution_sources/nist-800-53-rev5-extracted.json` |
| **Controls extracted** | 1,196 (including enhancements) |

## Verification status

**MACHINE_VERIFIED** — Every control ID cited in our docs is validated by Tier 4 against the OSCAL catalog. A control ID that does not exist in the catalog fails the build.

## Citation format used in our docs

- Base controls: `AU-2`, `AC-7`, `SI-4`
- Enhancements: `AU-2(1)`, `SI-4(24)`
- Written out: "NIST SP 800-53 Rev 5 AU-2"

Stored in the D&R rule metadata under `nist_control:` — agents consume this to drive their compliance classification. Comma-separated values (e.g., `"AU-2, AC-7"`) are split and each ID validated independently.

## Scope of reliance

Our docs rely on the source for:
- Control identifier format and naming (family-number + enhancement notation)
- Control family definitions (AU, AC, SI, IR, CM, SC, RA, IA families cited)
- Baseline selection semantics (Low / Moderate / High as defined in SP 800-53B)

Our docs do **not** rely on the source for:
- Interpretation of control implementation requirements (auditor / ISSO judgment)
- Control tailoring for specific system contexts
- Mapping to derivative frameworks (FedRAMP, FISMA — our cross-reference is illustrative)

## Independent re-verification

1. Download the current OSCAL catalog from the URL above.
2. Run `compliance/testing/tier4_citations.py --framework nist-800-53` — the tool re-extracts control IDs and validates every citation in our docs.
3. For control wording or control statement semantics, consult the NIST SP 800-53 Rev 5 PDF directly. The OSCAL representation preserves control IDs but the normative text resides in the PDF.

## Derivative frameworks noted

- NIST SP 800-171 (CMMC foundation) — a subset of 800-53 tailored to non-federal systems handling CUI
- FedRAMP Low/Moderate/High — selects and tailors 800-53 controls per baseline
- FISMA — governed by 800-53 control selection

These derivative relationships are noted in the mapping doc but are not themselves authoritative unless independently cited.
