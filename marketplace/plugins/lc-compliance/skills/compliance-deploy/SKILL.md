---
name: compliance-deploy
description: Guided deployment of a compliance framework's case-reviewer agent (and optionally a starter rule subset) to a LimaCharlie org. Walks through LC API-key creation with scoped permissions, Anthropic secret staging, agent hive record sync, and trigger D&R rule installation. Use when the user asks to deploy, install, or set up compliance for PCI, HIPAA, CMMC, NIST 800-53, SOC 2, ISO 27001, or CIS v8 in a given org. Examples - "deploy PCI compliance to org XYZ", "install the HIPAA compliance agent", "set up CMMC compliance on my test org".
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Edit
  - Write
---

# Compliance Deployment (Guided)

Walks the user through deploying a compliance framework's case-reviewer agent to a LimaCharlie organization. Human-in-the-loop at each sensitive step (API key creation, secret staging, rule deployment) — this skill does NOT silently modify an org.

Gap analysis is handled entirely by the `compliance-gap` skill (interactive, output to chat). There is no backend gap-analyzer agent to deploy.

## When to invoke

- User wants to deploy the case-reviewer agent to an org for the first time
- User wants to add a framework's D&R / FIM / artifact / exfil rules to an org that already has a reviewer deployed
- User wants to refresh (re-sync) a framework's deployment after updating the implementation doc

If the user only wants to EXPLORE coverage interactively, redirect to `compliance-gap` or `compliance-lookup` — those don't require deployment.

## Argument parsing

Expected: `<framework> [--oid <oid>] [--with-rules|--no-rules]`

- `--with-rules` — also deploy a starter subset of the framework's D&R / FIM / artifact / exfil rules (5–10 representative rules per kind). Useful for a demo.
- `--no-rules` (default) — deploy only the reviewer agent and leave rule selection to the user

## Locating bundled assets

All framework reference docs and reviewer manifests ship inside this plugin under `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/`. Throughout this skill, paths written as `compliance/<framework>/...` resolve to `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/...` — read and `--config-file` files through that prefix.

If `${CLAUDE_PLUGIN_ROOT}` is not set, derive the plugin root from this skill's base directory (`<base>/../..`), or fall back to:

```bash
find / -path "*/lc-compliance/.claude-plugin/plugin.json" 2>/dev/null | head -1 | xargs dirname | xargs dirname
```

## Pre-flight checklist

Before touching the org, confirm:

1. The plugin's bundled framework directory at `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/` exists — verify `agent/` and the impl doc both exist.
2. The org has `ext-cases` subscribed (required for case_created triggers):
   ```bash
   limacharlie --oid <oid> extension list --output yaml | grep ext-cases
   ```
   If not subscribed, stop and tell the user to subscribe via the web UI or `limacharlie extension subscribe` before continuing.
3. The user has an Anthropic API key on hand. Ask them to paste it OR confirm it's already at `hive://secret/anthropic-key` in the target org.

## Workflow

### Step 1 — Create a scoped LC API key

Required permissions for the case reviewer:

```
org.get,sensor.list,sensor.get,dr.list,insight.det.get,insight.evt.get,
investigation.get,investigation.set,ext.request,ext.list,org_notes.read,
sop.get,sop.get.mtd,ai_agent.operate
```

Create the key and display it ONCE — it cannot be retrieved later:

```bash
limacharlie --oid <oid> api-key create \
    --name <framework>-compliance-reviewer \
    --permissions <comma-separated-list>
```

Capture the `key` field from the JSON output — you'll need it in Step 2.

### Step 2 — Stage both secrets

```bash
# LC API key (the one from Step 1)
limacharlie --oid <oid> hive set --hive-name secret \
    --key <framework>-compliance-reviewer \
    --data '{"secret": "<lc-api-key>"}'

# Anthropic API key
limacharlie --oid <oid> hive set --hive-name secret \
    --key anthropic-key \
    --data '{"secret": "<sk-ant-...>"}'
```

If the Anthropic secret already exists at `anthropic-key`, skip that second command.

### Step 3 — Deploy the reviewer manifest

```bash
limacharlie --oid <oid> sync push \
    --config-file ${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/agent/<framework>-compliance-reviewer.yaml \
    --hive-ai-agent --hive-dr-general
```

### Step 4 — If `--with-rules`, deploy a starter rule subset

Read `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/recommended-rules.yaml` and pick ~5 D&R rules, ~3 FIM rules, ~1 artifact rule, ~1 exfil rule as a starter set. Extract those specific blocks from `${CLAUDE_PLUGIN_ROOT}/compliance/<framework>/<framework>-limacharlie-implementation.md`. Push each kind through its proper API path (mirror `compliance-baseline-deploy` Step 6 — don't use legacy `sync push --integrity` / `--artifact` / `--exfil` flags, they silently no-op on modern orgs):

```bash
# D&R rules — sync push
limacharlie --oid <oid> sync push --config-file /tmp/starter-dr.yaml --hive-dr-general

# FIM, artifact, exfil — extension config-set (include usr_mtd.enabled: true in input file)
limacharlie --oid <oid> extension config-set --name ext-integrity --input-file /tmp/starter-fim.yaml
limacharlie --oid <oid> extension config-set --name ext-artifact  --input-file /tmp/starter-artifact.yaml
limacharlie --oid <oid> extension config-set --name ext-exfil     --input-file /tmp/starter-exfil.yaml
```

For ext-exfil specifically, MERGE the new rules into the existing `data.exfil_rules.list` map (preserve `default-chrome`, `default-linux`, etc.) — read current state with `extension config-get --name ext-exfil` first.

Prompt the user to confirm which rules to include — DON'T assume. Starter-subset intent is partial coverage for demos / smoke tests, not a production rollout.

### Step 5 — Tag in-scope sensors

Remind the user to tag their in-scope sensors with the framework's scope tag so the reviewer's scope check recognizes them:

| Framework | Expected scope tags |
|---|---|
| pci-dss | `cde`, `pci-scope`, `card-data`, `pci-dss` |
| hipaa | `ephi-host`, `hipaa-scope`, `phi-host`, `covered-entity` |
| cmmc | `cui`, `cui-host`, `cmmc-scope`, `dib-host` |
| nist-800-53 | `fisma-scope`, `fedramp-scope`, `federal-system`, `nist-scope` |
| soc2 | `soc2-scope` (or leave unset — SOC 2 defaults to in-scope when rules carry the soc2 tag) |
| iso-27001 | `isms-scope`, `iso-scope`, `iso-27001-scope`, `soa-included` |
| cis-v8 | `cis-scope`, `cis-v8-scope`, plus optional `cis-ig1`/`cis-ig2`/`cis-ig3` for tier |

Example:
```bash
limacharlie --oid <oid> tag add --sid <cde-sensor-sid> -t cde
```

### Step 6 — Post-deploy verification

Run a sanity check to prove the agent record landed:

```bash
limacharlie --oid <oid> hive get \
    --hive-name ai_agent --key <framework>-compliance-reviewer --output yaml

limacharlie --oid <oid> dr list --namespace general --output yaml \
    | grep <framework>
```

The agent hive record should return a populated `data:` block. The `dr list` output should show the trigger rule (`<framework>-compliance-reviewer-trigger`).

### Step 7 — Tell the user what's next

Summarize:

- The case reviewer is deployed. It fires on every `case_created` event and classifies in-scope cases against the framework's controls.
- For gap analysis, invoke the `compliance-gap` skill in your session — no deployment required.
- For control-specific lookups, invoke the `compliance-lookup` skill.

## Evidence standards + safety

- Ask before EVERY write operation. This skill does not deploy anything silently.
- After every sync push, print the exact command that was run so the user can audit.
- If a step fails (e.g., `ext-cases not subscribed`), STOP and surface the error — don't silently skip.
- Never prompt the user to re-paste an API key that was already captured in a prior step.

## Non-goals

- Do NOT create any production deployment plan beyond what's here. The reviewer agent + a starter rule subset is enough to validate the integration; full rule-set rollout is a separate engineering decision.
- Do NOT run `compliance-gap` inside this skill automatically. Recommend it to the user at the end but let them invoke it.
- Do NOT push to multiple orgs at once. Each invocation targets exactly one `--oid`.
