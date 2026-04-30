---
name: compliance-gap
description: Run an ad-hoc compliance gap analysis against a live LimaCharlie org — compares what the org is currently collecting and detecting against the framework's recommended rule set, and returns a markdown punch list directly in chat (no case is created, no deployment needed). This is the primary way to run a gap analysis — there is no backend agent counterpart. Use for day-to-day engineering sanity checks and pre-audit reviews against CMMC, NIST 800-53, PCI DSS, HIPAA, SOC 2, ISO 27001, or CIS v8. Examples - "show me my PCI gaps", "run a HIPAA gap analysis on org XYZ", "what CIS safeguards am I missing?"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Compliance Gap Analysis (Interactive)

Compares an LC org's currently-deployed telemetry and detections against a framework's recommended rule set (from this repo's implementation doc), and produces a gap report in the user's chat. This is the primary way to run a gap analysis in this repo — there is no backend agent counterpart.

## When to invoke

- User wants a gap check at any time ("am I missing anything important for PCI?")
- Pre-audit sanity check before a QSA / ISSO / auditor reviews
- Exploring coverage without wanting backend artifacts in the LC org
- Producing a one-off gap report for an engineer, security lead, or auditor

If the user wants the full punch list to persist in the LC org as a case (for auditors to reference later), suggest they create a case themselves and paste the report in — this skill intentionally does not write to the org.

## Argument parsing

Expected: `<framework> [--oid <oid>] [--baseline <low|moderate|high>] [--ig <1|2|3>]`

| Framework shorthand | Resolved |
|---|---|
| `pci`, `pci-dss` | pci-dss |
| `nist`, `800-53`, `nist-800-53` | nist-800-53 |
| `cmmc` | cmmc |
| `hipaa` | hipaa |
| `soc2` | soc2 |
| `iso`, `iso-27001` | iso-27001 |
| `cis`, `cis-v8` | cis-v8 |

- `--oid` defaults to the CLI's current org. If no org is set, ask the user.
- `--baseline` applies to NIST 800-53 only (Low / Moderate / High).
- `--ig` applies to CIS v8 only (Implementation Group 1/2/3).

## Locating bundled docs

All framework reference docs ship inside this plugin under `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/`. Throughout this skill, paths written as `compliance/<framework>/...` resolve to `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/...` — read files through that prefix.

If `${CLAUDE_PLUGIN_ROOT}` is not set, derive the plugin root from this skill's base directory (`<base>/../..`), or fall back to:

```bash
find / -path "*/lc-compliance/.claude-plugin/plugin.json" 2>/dev/null | head -1 | xargs dirname | xargs dirname
```

## Required reading before running

Read these once per invocation (they cache within the session):

1. `compliance/<framework>/<framework>-limacharlie-mapping.md` — for contextual coverage descriptions
2. `compliance/<framework>/<framework>-limacharlie-implementation.md` — for the recommended rule set
3. `compliance/<framework>/<framework>-attribution.md` — to note verification status in the report
4. `compliance/<framework>/recommended-rules.yaml` — a pre-extracted list of rule names by kind (already generated; use this as the canonical list)

## Workflow

1. **Resolve framework + oid.** Parse args; confirm framework exists at `compliance/<framework>/`.

2. **Load the recommended rule set.** Read `compliance/<framework>/recommended-rules.yaml`. Extract four lists from `recommended.`: `dr_rules`, `artifact_rules`, `fim_rules`, `exfil_rules`.

3. **Query the org's current state** via the LC CLI. Use `--output yaml` on every command.

   ```bash
   limacharlie --oid <oid> dr list --namespace general --output yaml
   limacharlie --oid <oid> dr list --namespace managed --output yaml
   limacharlie --oid <oid> extension config-list --output yaml  # artifact + exfil
   limacharlie --oid <oid> integrity list --output yaml 2>/dev/null || echo "ext-integrity not subscribed"
   limacharlie --oid <oid> sensor list --output yaml
   ```

   Skip the ones that fail (e.g., `ext-integrity` returns an error if not subscribed — capture as a gap, don't abort).

4. **Compute the gap for each category.**

   **Telemetry (Exfil) gap** — For each platform in {windows, linux, macos}, compare the org's current `ext-exfil.data.exfil_rules.list.<name>.events` against the recommended exfil rule's events. Missing events → telemetry gap.

   **Artifact collection gap** — Diff recommended `artifact_rules` names against `ext-artifact` keys in the org.

   **FIM gap** — Diff recommended `fim_rules` against the `integrity list` output.

   **D&R rule gap** — Diff recommended `dr_rules` against the union of general + managed namespace dr rule names.

   **Name drift** — A recommended rule may be deployed under a different name. If a canonical name is missing, note "canonical name not found — verify manually" rather than claiming a hard gap.

   **Sensor-scope gap** — Filter `sensor list` output to sensors with any of the framework's scope tags (e.g., `cde` for PCI, `ephi-host` for HIPAA, `cui` for CMMC). If any in-scope sensor has been offline > 7 days, flag that as a control-failure gap (e.g., PCI Req 10.7, HIPAA §164.312(b)).

5. **Apply framework-specific adaptations** (mirror the gap-analyzer agent's prompt):

   - **NIST** — filter by baseline if provided (`--baseline moderate` includes AU-7, AU-9(4), AC-6, AC-6(9), SI-4(2/4/5/24), SI-7(1/7), AC-6(10); Low is base; High adds more).
   - **CMMC** — cross-walk each gap to its 800-171 Rev 2 control (part after the dash, e.g., `AU.L2-3.3.1` → 800-171 `3.3.1`). Flag DFARS 252.204-7012 relevance.
   - **HIPAA** — for Addressable specs, include the verbatim "Addressable does NOT mean optional" line.
   - **SOC 2** — group gaps by Common Criteria (CC1–CC9); note that each detection firing is evidence of operating effectiveness over the Type II observation window.
   - **ISO 27001** — use "nonconformity" language (never "gap"/"violation"). Check for an `soa` note in the org; if present, skip SoA-excluded controls. Include the UNVERIFIED caveat.
   - **CIS v8** — respect `--ig` flag OR `cis-ig1/2/3` sensor tags; below-tier gaps are "true gaps"; above-tier are "stretch goals."

6. **Emit the report as a markdown message** in the user's chat.

   Structure (all sections required, even if empty — empty sections confirm what WAS verified):

   ```
   # <Framework Canonical Name> Gap Analysis (Interactive)

   **Org:** <oid> (<name if available>)
   **Generated:** <ISO timestamp>
   **Recommended set version:** <from note.data.generated>
   **Verification level:** <from attribution doc>
   **Scope:** <detected sensor-tag scope, or "not detected — ran org-wide">

   ## Summary
   - Telemetry gaps: <N>
   - Artifact collection gaps: <N>
   - FIM gaps: <N> (or "ext-integrity not subscribed — see Section C")
   - D&R rule gaps: <N>
   - Sensor-coverage issues: <N>
   - Name-drift candidates: <N> (manual review)
   - Deployed extras: <N> (not in recommended set; informational)

   ## A. Telemetry Gaps
   ...

   ## B. Artifact Collection Gaps
   ...

   ## C. FIM Gaps
   ...

   ## D. D&R Rule Gaps
   ...

   ## E. Name Drift
   ...

   ## F. Sensor Coverage
   ...

   ## G. Deployed Extras (informational)
   ...

   ## Prioritized Remediation
   1. Below-tier / required gaps first
   2. Enhancements and addressable specs
   3. Stretch-goal / above-tier items
   ```

## Evidence standards

- NEVER fabricate. If a recommended rule's control mapping isn't available in the note, write "mapping not available — verify against implementation doc."
- NEVER claim "compliant" / "non-compliant." Use "gap exists" / "not currently deployed" / "would satisfy Req X.Y.Z if deployed."
- Cite specific control IDs in the framework's canonical format (e.g., "PCI DSS v4.0 Req 10.2.1.4", "NIST SP 800-53 Rev 5 AU-2(1)", "HIPAA Security Rule §164.312(b)").
- Report the complete punch list — not a summary. Auditors and engineers need to see each line.
- If verification status is UNVERIFIED (ISO 27001), prepend the report with a 3-line caveat banner.

## Non-goals

- Do NOT write anything to the LC org. No case created, no note written, no sensor tagged. Output goes to chat only.
- Do NOT deploy rules to fix gaps. If the user wants guided deployment, suggest `compliance-deploy`.

## Performance hints

- Read all the CLI outputs ONCE at the start. Don't re-invoke per-rule.
- For frameworks with many recommended rules (CIS v8: 110+, ISO: 95+), prefer showing counts in summary + 10-15 missing rules per category in the body; offer to expand with `--verbose` if the user wants the full list inline.
