# lc-compliance — Claude Code plugin

Three interactive skills for day-to-day compliance engineering against LimaCharlie orgs. Complements the event-driven case-reviewer agent shipped alongside the skills under `compliance/<framework>/agent/` — the agent runs in the LC backend on `case_created` events to produce audit evidence; these skills run in your Claude Code session for on-demand, interactive work.

## Skills

| Skill | What it does | Typical use |
|---|---|---|
| `compliance-lookup` | Look up how LimaCharlie covers a specific compliance control | "how does LC cover PCI 10.2.1.4?", "show me NIST AU-2 coverage" |
| `compliance-gap` | Run an ad-hoc gap analysis against a live org; output to chat | Pre-audit sanity check, exploring coverage, producing a one-off punch list |
| `compliance-deploy` | Guided deployment of a framework's case-reviewer agent (+ optional ~10-rule starter subset for demos) | First-time reviewer-agent setup, demos, refreshing after impl-doc updates |
| `compliance-baseline-deploy` | Deploy the FULL recommended rule baseline (50–110+ rules) for a framework | Customer just installed the plugin and wants the framework's rules in their org |

Invocation follows the Claude Code plugin convention:

```
/lc-compliance:compliance-lookup <framework> <control-id>
/lc-compliance:compliance-gap <framework> [--oid <oid>]
/lc-compliance:compliance-deploy <framework> [--oid <oid>] [--with-rules]
/lc-compliance:compliance-baseline-deploy <framework> [--oid <oid>] [--apply] [--overwrite] [--kinds dr,fim,artifact,exfil]
```

`compliance-baseline-deploy` defaults to a dry-run plan; pass `--apply` to actually push rules.

## Skill vs. reviewer agent — when to use which

| Use case | Shape |
|---|---|
| Continuous per-case compliance classification | **Agent** (`<framework>-compliance-reviewer`) — fires on every `case_created` |
| Ad-hoc "what does LC do for this one control?" | **Skill** (`compliance-lookup`) |
| Ad-hoc "what am I missing?" before an audit | **Skill** (`compliance-gap`) |
| First-time reviewer-agent deployment | **Skill** (`compliance-deploy`) |
| Push the full framework rule baseline into an org | **Skill** (`compliance-baseline-deploy`) |

The two shapes serve different moments. The agent owns continuous, event-driven evidence production (cases, notes, tags persisted in the LC org that auditors rely on). Skills own request-driven interactive work that engineers run during development without wanting backend artifacts.

Gap analysis specifically is skill-only — there is no backend gap-analyzer agent. A gap report is not itself audit evidence; it's an engineering punch list. If you want a persistent record, create a case manually and paste the skill's output into it.

## Framework coverage

Same seven as the repo's agents: CMMC v2, NIST SP 800-53 Rev 5, PCI DSS v4.0, HIPAA Security Rule, SOC 2 TSC, ISO/IEC 27001:2022, CIS Critical Security Controls v8.

## Installation

From a Claude Code session, add the LimaCharlie marketplace and install the plugin:

```
/plugin marketplace add https://github.com/refractionPOINT/lc-ai
/plugin install lc-compliance@lc-marketplace
```

Then invoke any of the three skills as shown above.

## Bundled source material

Reference content for all seven frameworks ships with the plugin under `compliance/<framework>/`:

- `<framework>-limacharlie-mapping.md` — coverage descriptions (quoted verbatim in `compliance-lookup` output)
- `<framework>-limacharlie-implementation.md` — deployable rules whose metadata carries the control citations
- `<framework>-attribution.md` — authoritative source, verification level (MACHINE_VERIFIED / ATTESTATION / UNVERIFIED)
- `recommended-rules.yaml` — canonical rule-name baseline used by the `compliance-gap` diff
- `agent/` — the framework's case-reviewer hive manifest (`ai_agent`, `dr-general`, `secret`)

Skills resolve these paths relative to the plugin's installation directory at runtime. They do not fabricate control wording or invent coverage — if a citation or rule is not present in the bundled docs, the skill reports that rather than making something up.
