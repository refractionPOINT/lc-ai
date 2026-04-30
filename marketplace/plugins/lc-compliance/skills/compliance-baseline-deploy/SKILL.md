---
name: compliance-baseline-deploy
description: Deploy the FULL recommended rule baseline for a compliance framework to a LimaCharlie org — every D&R rule, FIM rule, artifact-collection rule, and exfil rule defined in the framework's implementation doc. Defaults to dry-run; --apply is required to actually write. Idempotent; rules already deployed under the same name are skipped. Use when a customer has just installed lc-compliance and wants a framework's rules in their org for the first time, or wants to refresh the baseline after the implementation doc has been updated. Examples - "deploy the full PCI baseline to org XYZ", "install all CMMC rules", "push the HIPAA recommended set", "apply the CIS v8 baseline". Distinct from compliance-deploy, which deploys only the case-reviewer agent (and optionally a small starter rule subset for demos).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
---

# Compliance Baseline Deploy (Full Rule Set)

Deploys the FULL recommended rule baseline for a compliance framework — D&R rules, FIM rules, artifact-collection rules, and exfil rules — to a single LimaCharlie organization. Human-in-the-loop with explicit confirmation; defaults to dry-run.

This is the "I subscribed and want the rules in my org" path. For the case-reviewer agent (separate concern), use `compliance-deploy`. For a gap report, use `compliance-gap`. For a single control lookup, use `compliance-lookup`.

## When to invoke

- Customer has just installed `lc-compliance` and wants the framework's rules deployed for the first time
- Refreshing the deployed baseline after the bundled implementation doc has been updated
- A net-new org being prepared for an audit window

If the user only wants a subset (e.g., for a demo), redirect them to `compliance-deploy --with-rules`, which deploys ~10 representative rules. This skill is for the full set (50–110+ rules per framework).

## Argument parsing

Expected: `<framework> [--oid <oid>] [--apply] [--overwrite] [--kinds <list>]`

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
- `--apply` — required to actually write to the org. Without it, the skill produces a deploy plan and stops.
- `--overwrite` — replace rules that already exist under the same name. Without it, existing rules are SKIPPED (default).
- `--kinds` — comma-separated subset of `dr,fim,artifact,exfil` (default: all four). Useful when an extension is missing (e.g., skip `fim` if `ext-integrity` is not subscribed).

## Locating bundled assets

All framework reference docs ship inside this plugin under `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/`. Throughout this skill, paths written as `compliance/<framework>/...` resolve to `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/...`.

If `${CLAUDE_PLUGIN_ROOT}` is not set, derive the plugin root from this skill's base directory (`<base>/../..`), or fall back to:

```bash
find / -path "*/lc-compliance/.claude-plugin/plugin.json" 2>/dev/null | head -1 | xargs dirname | xargs dirname
```

## Pre-flight checklist

Before assembling the deploy plan, confirm the org has the extensions each rule kind requires:

| Rule kind | Required extension | How to check |
|---|---|---|
| `dr` (D&R rules) | none — built-in | always available |
| `fim` (FIM rules) | `ext-integrity` | `limacharlie --oid <oid> extension list --output yaml \| grep ext-integrity` |
| `artifact` (artifact collection) | `ext-artifact` | same pattern, look for `ext-artifact` |
| `exfil` (exfil routing) | `ext-exfil` | same pattern, look for `ext-exfil` |

If a required extension is not subscribed, do NOT silently skip — surface the gap to the user and ask whether to:
1. Skip that kind for this run (`--kinds` excludes it)
2. Have the user subscribe via the web UI / CLI and re-run

## Workflow

### Step 1 — Resolve framework and load the baseline

```bash
# Read the canonical baseline
cat "${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/recommended-rules.yaml"
```

Extract the four lists from `recommended.`: `dr_rules`, `artifact_rules`, `fim_rules`, `exfil_rules`. Capture the counts from `counts:` for the plan summary.

### Step 2 — Extract each rule's YAML from the implementation doc

The bundled implementation doc has the deployable YAML for every rule, fenced with ` ```yaml ... ``` `. Two block shapes appear:

| Shape | Identifying field | Examples |
|---|---|---|
| **D&R rule** — top-level `name:`, `detect:`, `respond:` | `detect:` and `respond:` keys | `pci-10-failed-logon-windows` |
| **Rule-map entry** — single-key map whose value is a dict with `patterns:` / `events:` / paths | top-level key matches the rule name | `pci-wel-security`, `pci-fim-windows-audit-logs`, `pci-windows-events` |

For each rule name in the baseline:

1. Search the impl doc for a YAML fence that begins with `name: <rule-name>` (D&R) OR `<rule-name>:` at the start of a fenced block (rule-map kinds).
2. Capture the YAML inside the fence verbatim.
3. If a rule name in `recommended-rules.yaml` has no matching block in the impl doc, flag it — never invent or fill in a placeholder.

### Step 3 — Query the org for currently-deployed state

```bash
# D&R rules currently in the general namespace
limacharlie --oid <oid> dr list --namespace general --output yaml

# FIM rules (skip if ext-integrity not subscribed)
limacharlie --oid <oid> integrity list --output yaml 2>/dev/null

# Artifact + exfil — read from extension config hive
limacharlie --oid <oid> hive get --hive-name extension-config --partition-name ext-artifact --output yaml 2>/dev/null
limacharlie --oid <oid> hive get --hive-name extension-config --partition-name ext-exfil --output yaml 2>/dev/null
```

Build a set of currently-deployed rule names per kind. Anything in the deployed set whose name does NOT appear in the recommended baseline is "deployed extra" and stays untouched.

### Step 4 — Compute the deploy plan

For each kind in {dr, fim, artifact, exfil}:

| Bucket | Action |
|---|---|
| In recommended, not deployed | **ADD** — push to org |
| In recommended, deployed under same name | **SKIP** (default) or **UPDATE** if `--overwrite` |
| Deployed extra (not in recommended) | **LEAVE ALONE** — not this skill's concern; reported as informational |
| In recommended, no YAML block found in impl doc | **HALT** — surface to user; do not proceed |

### Step 5 — Show the plan to the user

Print a structured plan, even in `--apply` mode. Required, do not skip:

```
# Compliance Baseline Deploy Plan

**Framework:** PCI DSS v4.0
**Org:** <oid> (<name>)
**Mode:** DRY-RUN (no --apply flag)
**Recommended set version:** <from recommended-rules.yaml `generated:`>

## Pre-flight
- ext-integrity: SUBSCRIBED
- ext-artifact:  SUBSCRIBED
- ext-exfil:     SUBSCRIBED

## Plan summary
| Kind | In baseline | Already deployed | To add | To update | To skip |
|---|---:|---:|---:|---:|---:|
| D&R rules     | 57 | 12 | 45 | 0 | 12 |
| FIM rules     | 23 |  0 | 23 | 0 |  0 |
| Artifact      | 13 |  3 | 10 | 0 |  3 |
| Exfil         |  3 |  0 |  3 | 0 |  0 |
| **Total**     | **96** | **15** | **81** | **0** | **15** |

## Rules to ADD (first 20 of 81)
- D&R: pci-10-failed-logon-windows, pci-10-brute-force-windows, ...
- FIM: pci-fim-windows-audit-logs, ...
- Artifact: pci-wel-security, ...
- Exfil: pci-windows-events, ...

(Use `--apply` to actually deploy.)
```

If this is dry-run, STOP HERE.

### Step 6 — Build sync-push files and apply (only with `--apply`)

For each kind, assemble a sync-push YAML in the proper format. The hive each kind goes into:

| Kind | Hive | `--hive-*` flag |
|---|---|---|
| D&R | `dr-general` | `--hive-dr-general` |
| FIM | `integrity` | `--hive-integrity` |
| Artifact | `extension-config` (partition `ext-artifact`) | `--hive-extension-config` |
| Exfil | `extension-config` (partition `ext-exfil`) | `--hive-extension-config` |

The sync-push file shape (mirrors what the bundled `agent/hives/dr-general.yaml` uses for the reviewer trigger):

```yaml
version: 3
hives:
  dr-general:
    <rule-name>:
      data:
        <rule-yaml-from-impl-doc>
      usr_mtd:
        enabled: true
        expiry: 0
        tags:
          - compliance:<framework>
          - compliance-baseline
```

Write each kind's file to a temp location (e.g., `/tmp/lc-compliance-deploy-<framework>-<kind>-<timestamp>.yaml`) and push:

```bash
limacharlie --oid <oid> sync push \
    --config-file /tmp/lc-compliance-deploy-<framework>-dr.yaml \
    --hive-dr-general
```

Push each kind separately so a failure in one kind doesn't block the others. After each push, print the exact command that ran and the CLI's exit status.

If `--overwrite` is NOT set: before pushing, filter the sync file to remove rule names already present in the org. Idempotency comes from this filter step, not from sync-push semantics — `sync push` will overwrite by default.

### Step 7 — Verify post-deploy

Re-query the org and count actual landed rules per kind. Compare against the deploy plan's "to add" counts:

```bash
limacharlie --oid <oid> dr list --namespace general --output yaml | yq '.[] | .name' | grep -c "^<framework>-"
```

Print a verification table:

```
## Post-deploy verification
| Kind | Planned to add | Found after push | Status |
|---|---:|---:|---|
| D&R rules | 45 | 45 | ✓ |
| FIM rules | 23 | 23 | ✓ |
| Artifact  | 10 | 10 | ✓ |
| Exfil     |  3 |  3 | ✓ |
```

Any mismatch is a hard error — surface it; do NOT report success.

### Step 8 — Remind the user about scope tags

Compliance rules typically condition on a sensor tag (`cde`, `ephi-host`, `cui`, etc.). Without the tag on the right sensors, the rules deploy but never fire. Print the framework's expected tags (table below) and a one-line example.

| Framework | Expected scope tags |
|---|---|
| pci-dss | `cde`, `pci-scope`, `card-data`, `pci-dss` |
| hipaa | `ephi-host`, `hipaa-scope`, `phi-host`, `covered-entity` |
| cmmc | `cui`, `cui-host`, `cmmc-scope`, `dib-host` |
| nist-800-53 | `fisma-scope`, `fedramp-scope`, `federal-system`, `nist-scope` |
| soc2 | `soc2-scope` (or leave unset — SOC 2 defaults to in-scope when rules carry the soc2 tag) |
| iso-27001 | `isms-scope`, `iso-scope`, `iso-27001-scope`, `soa-included` |
| cis-v8 | `cis-scope`, `cis-v8-scope`, plus optional `cis-ig1`/`cis-ig2`/`cis-ig3` for tier |

```bash
limacharlie --oid <oid> tag add --sid <sensor-sid> -t <tag>
```

Do NOT auto-tag sensors. Scope decisions belong to the customer.

## Safety standards

- **Dry-run is the default.** `--apply` is required for any write.
- **Idempotent by default.** Re-running with the same args should be a no-op (every rule SKIPs).
- **Print every write command before and after running it** so the user has an audit trail in chat.
- **One org per invocation.** This skill targets exactly one `--oid`. Never iterate orgs in a loop.
- **Halt on missing rule blocks.** If `recommended-rules.yaml` lists a name with no YAML in the impl doc, stop — do not skip silently and do not invent the rule.
- **Halt on extension gaps unless `--kinds` excludes that kind.** Don't pretend to deploy FIM rules to an org without `ext-integrity`.
- **Never modify "deployed extras."** Rules in the org that aren't in the baseline are out of scope.

## Non-goals

- Do NOT deploy the case-reviewer agent. That's `compliance-deploy`.
- Do NOT run a gap report. That's `compliance-gap`. (Though running `compliance-gap` after a successful baseline deploy is a reasonable suggestion to make at the end.)
- Do NOT subscribe extensions automatically. Surface the gap; let the user decide.
- Do NOT tag sensors automatically.
- Do NOT modify the recommended baseline file. The baseline is the canonical input; this skill consumes it, not edits it.
