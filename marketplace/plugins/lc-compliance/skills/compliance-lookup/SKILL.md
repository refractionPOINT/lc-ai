---
name: compliance-lookup
description: Look up how LimaCharlie covers a specific compliance control across any of seven frameworks (CMMC, NIST 800-53, PCI DSS, HIPAA, SOC 2, ISO 27001, CIS v8). Returns the relevant section from the framework's mapping and implementation docs plus the exact D&R rules that carry the control citation in their metadata. Use when the user asks things like "how does LC cover PCI 10.2.1.4?", "show me our NIST AU-2 coverage", "what rules map to CIS Safeguard 8.2?", "HIPAA §164.312(b) coverage".
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Compliance Lookup

Look up how LimaCharlie covers a specific compliance control. Returns the control's conceptual coverage (from the mapping doc) plus the specific deployable rules that cite it (from the implementation doc).

## When to invoke

The user asks a targeted control-coverage question. Examples:
- "how does LC cover PCI 10.2.1.4?"
- "show me NIST AU-2 coverage"
- "what rules map to CIS Safeguard 8.2?"
- "HIPAA §164.312(b)"
- "CMMC AU.L2-3.3.1"

If the user is asking a broader "what am I missing?" question instead of a specific control, use `compliance-gap` instead.

## Argument parsing

Expected input: `<framework> <control-id>`. Examples:

| Input | Framework | Control ID |
|---|---|---|
| `pci 10.2.1.4` or `pci-dss 10.2.1.4` | pci-dss | 10.2.1.4 |
| `nist AU-2` or `800-53 AU-2` | nist-800-53 | AU-2 |
| `cmmc AU.L2-3.3.1` | cmmc | AU.L2-3.3.1 |
| `hipaa §164.312(b)` or `hipaa 164.312(b)` | hipaa | §164.312(b) |
| `soc2 CC6.1` or `cc6.1` | soc2 | CC6.1 |
| `iso A.8.15` or `iso-27001 A.8.15` | iso-27001 | A.8.15 |
| `cis 8.2` or `cis-v8 8.2` | cis-v8 | 8.2 |

If the framework is ambiguous, infer from the control-ID format (e.g., `CC6.1` is SOC 2; `§164.312` is HIPAA; `AU-2` is NIST).

## Locating bundled docs

All framework reference docs ship inside this plugin under `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/`. Throughout this skill, paths written as `compliance/<framework>/...` resolve to `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/...` — read files through that prefix.

If `${CLAUDE_PLUGIN_ROOT}` is not set in your shell, derive the plugin root from this skill's base directory (`<base>/../..`), or fall back to:

```bash
find / -path "*/lc-compliance/.claude-plugin/plugin.json" 2>/dev/null | head -1 | xargs dirname | xargs dirname
```

## Workflow

1. **Resolve the plugin root** (see "Locating bundled docs" above) so the framework directories at `compliance/<framework>/` can be read.

2. **Find the control in the mapping doc.** Grep `compliance/<framework>/<framework>-limacharlie-mapping.md` for the control ID. For HIPAA, match `§164.XXX(…)`; for NIST, match both base controls and enhancements like `AU-2(1)`; for CIS, match `Safeguard N.N`; etc. Extract the surrounding section (heading through next heading).

3. **Find the D&R rules that cite the control.** Grep `compliance/<framework>/<framework>-limacharlie-implementation.md` for the framework's metadata key with the requested control ID as the value:

   | Framework | Metadata key |
   |---|---|
   | cmmc | `cmmc_control:` |
   | nist-800-53 | `nist_control:` |
   | pci-dss | `pci_dss_req:` |
   | hipaa | `hipaa_safeguard:` |
   | soc2 | `soc2_criterion:` |
   | iso-27001 | `iso_27001_control:` |
   | cis-v8 | `cis_safeguard:` |

   For each matching rule, extract: rule name, target event type, and a one-line summary from the rule's description / comment.

4. **Check the attribution doc.** Read `compliance/<framework>/<framework>-attribution.md` once and note the verification status (MACHINE_VERIFIED / ATTESTATION / UNVERIFIED) — include this in the answer so the user knows how much trust to place in the citation.

5. **Respond in markdown.** Structure:

   ```
   # <Framework Canonical Name>: <Control ID>

   **Citation:** <full canonical citation, e.g., "PCI DSS v4.0 Req 10.2.1.4">
   **Verification:** <MACHINE_VERIFIED | ATTESTATION | UNVERIFIED>  (see attribution doc)

   ## Conceptual coverage

   <excerpt from mapping doc — the paragraph describing how LC covers this control>

   ## Deployable rules (N)

   | Rule name | Event | Summary |
   |---|---|---|
   | pci-10-failed-logon-windows | WEL (EventID 4625) | Detect failed Windows logons |
   | ... | | |

   ## Source files

   - `compliance/<framework>/<framework>-limacharlie-mapping.md` (line N)
   - `compliance/<framework>/<framework>-limacharlie-implementation.md` (rule names above)
   - `compliance/<framework>/<framework>-attribution.md` (verification basis)
   ```

6. **If the control ID is not found:**
   - The plugin bundle does not include the testing/attribution-source caches (those stay in the upstream development repo). Without that cache, you cannot distinguish "valid control, not implemented" from "invalid control ID." Report exactly that:
     - "Control ID not found in the bundled mapping or implementation docs. The authoritative-source cache is not bundled with this plugin, so we cannot confirm whether the ID exists in the framework spec — please verify against the publisher's document."
   - Do NOT fabricate coverage. If there are no matches, say so and stop.

## Evidence standards

- Quote mapping-doc text verbatim; don't paraphrase.
- Cite line numbers (`file.md:N`) so the user can jump.
- Never claim a control is "implemented" beyond what the doc and rules actually show. Report what exists, not what you infer.
- If verification status is UNVERIFIED (ISO 27001), include a short disclaimer: "The ISO 27002:2022 authoritative source is paywalled; citation wording is not machine-verified."

## Non-goals

- Do not deploy or modify anything. This is a read-only lookup skill.
- Do not run gap analysis. If the user wants to know what's *missing*, suggest `compliance-gap`.
- Do not query a live LC org. The answer comes from the repo content only.
