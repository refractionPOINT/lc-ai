# NIST 800-53 Compliance Reviewer — Automated NIST SP 800-53 Rev 5 Case Classification

An AI agent that acts as a NIST SP 800-53 Rev 5 subject-matter expert. When a security case is
created on a federal-system / FISMA / FedRAMP authorization-boundary endpoint, it classifies the
event against specific NIST controls (including enhancements) and writes audit-grade case
documentation that a 3PAO, FISMA auditor, or agency ISSO can use as assessment evidence.

> **Gap analysis** is handled by the `compliance-gap` skill (in the
> `lc-compliance` Claude Code plugin at `plugin/lc-compliance/`), not by
> a backend agent. This README covers only the case-reviewer agent.

This agent is **complementary** to an L1 SOC bot — it reviews for *compliance impact*, not security
severity. It runs in parallel to the normal case triage flow without interfering with it.

## How It Works

```
Detection fires on a federal-system-tagged endpoint
        |
        v
ext-cases creates a case
        |
        v
Webhook adapter emits case_created event
        |
        v
D&R rule matches (any case_created with case_id)
        |
        v
Suppression check (max 10/min global)
        |
        v
Debounce check (one review per case at a time)
        |
        v
AI agent session starts with case_number + oid
        |
        v
Scope check: is this case NIST-relevant?
        ├── No  → add "not in scope" note, exit
        └── Yes → continue
        |
        v
Baseline inference (Low / Moderate / High / undetermined)
Map event → NIST control identifier(s) + enhancements
Classify compliance impact (control-functioning /
  control-gap / in-scope-ops / security-incident)
Write assessor-ready summary, conclusion, analysis notes
Tag case with compliance classification
        |
        v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- Endpoints inside a NIST 800-53 authorization boundary must carry a scope tag — one of
  `fisma-scope`, `fedramp-scope`, `federal-system`, or `nist-scope`. This is how the agent
  distinguishes in-scope from out-of-scope cases.
- (Optional but recommended) A baseline tag on scoped sensors: `nist-baseline-low`,
  `nist-baseline-moderate`, or `nist-baseline-high`. The agent will otherwise attempt to infer
  the baseline from deployed control enhancements.
- D&R rules from `../nist-800-53-limacharlie-implementation.md` deployed, with the `nist-800-53`
  tag and `metadata.nist_control:` fields preserved (values may be comma-separated like
  `AU-2, AC-7`). These provide the control mapping the agent consumes.
- A LimaCharlie API key with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors to check scope tagging |
| `sensor.get` | Read sensor tags for scope / baseline determination |
| `dr.list` | Read detection rule metadata (nist_control) |
| `insight.det.get` | Read linked detections |
| `insight.evt.get` | Access event telemetry for correlation |
| `investigation.get` | Read cases |
| `investigation.set` | Update case summary/conclusion, add notes/entities/tags |
| `ext.request` | Call ext-cases |
| `sop.get` | Read org-specific NIST SOPs if present |
| `sop.get.mtd` | Read SOP metadata |
| `org_notes.read` | Read org notes (for embedded NIST guidance, if mirrored) |
| `ai_agent.operate` | Run AI agent sessions |

## Installation

```bash
# 1. Replace API-key placeholders in hives/secret.yaml
#    Anthropic key + a LimaCharlie API key with the permissions above

# 2. Deploy via the LC sync command
limacharlie sync --oid <your-oid> --push nist-800-53-compliance-reviewer.yaml

# 3. Tag at least one endpoint as in-scope (otherwise the agent always early-exits)
limacharlie tag add --sid <federal-sensor-sid> -t fisma-scope --oid <your-oid>

# 4. (Optional) Tag the baseline on scoped sensors
limacharlie tag add --sid <sensor-sid> -t nist-baseline-moderate --oid <your-oid>

# 5. Verify the ai_agent hive record exists
limacharlie hive get --hive-name ai_agent --key nist-800-53-compliance-reviewer --oid <your-oid> --output yaml

# 6. Verify the trigger rule exists
limacharlie dr get --name nist-800-53-compliance-reviewer-trigger --namespace general --oid <your-oid> --output yaml
```

## What the Agent Produces

For each NIST-relevant case, the agent adds:

| Field | Content |
|---|---|
| **Summary** | One-paragraph assessor-readable overview: host, event, implicated NIST controls (with enhancements), inferred baseline, compliance classification |
| **Conclusion** | Control mapping with exact identifiers (e.g., "NIST SP 800-53 Rev 5 AU-9, CM-5"), compliance classification with reasoning, and remediation recommendations if a gap was found |
| **Analysis note** | Detailed markdown timeline with baseline determination, event data verbatim, scope-determination explanation, and correlating telemetry |
| **Entities** | IOCs tagged with NIST-relevant context (e.g., privileged accounts, protected-config paths, unsigned binaries on federal systems) |
| **Tags** | One of: `nist-control-functioning`, `nist-control-gap`, `nist-in-scope-ops`, `nist-security-incident` |

## Compliance Classification Categories

| Tag | Meaning | Assessor Value |
|---|---|---|
| `nist-control-functioning` | The detection firing IS the control working. Example: FIM_HIT on a protected path proves SI-7(1) is operational; WEL 4625 proves AU-2/AC-7 logging is live. | Positive evidence of control operation. |
| `nist-control-gap` | The event reveals a compliance gap. Example: WEL 1102 (security log cleared) = AU-9 violation; audit policy changed = AU-9/CM-5 gap; sensor offline on federal system = AU-12 failure. | Assessment finding — requires remediation and documentation. |
| `nist-in-scope-ops` | Expected administrative activity on a federal system. Example: documented privileged maintenance, legitimate patching. | Audit-trail completeness evidence for AU-2 / AU-3. |
| `nist-security-incident` | A potential security incident on in-scope systems. | IR-4 / IR-5 / IR-6 incident-response obligations — IR plan invocation, timeline documentation, US-CERT / agency notification per IR-6 where applicable. |

## Configuration

| Parameter | Value | Notes |
|---|---|---|
| `model` | `sonnet` | Sufficient for structured compliance classification. Escalate to `opus` if classification consistently hits ambiguity on complex control chains. |
| `max_turns` | `20` | Enough for scope check + baseline inference + context gathering + case update |
| `max_budget_usd` | `1.0` | Compliance review is a bounded task |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after review |
| `debounce_key` | `nist-800-53-compliance-reviewer` | One review at a time; subsequent cases queue |
| Suppression | `10/min global` | Matches l1-bot default |

## Baselines

NIST SP 800-53B defines Low, Moderate, and High baselines. The baseline affects which controls and
enhancements apply. The agent:

1. Reads the sensor tag for an explicit baseline marker (`nist-baseline-low`,
   `nist-baseline-moderate`, `nist-baseline-high`) if present
2. Otherwise infers from deployed enhancements (rules citing `SI-4(24)`, `AC-6(9)`, `AU-9(4)`
   imply Moderate or High)
3. Records "baseline: undetermined" in the analysis note if neither signal is available, and
   proceeds using base controls only

## Retention (AU-11)

AU-11 retention is organization-defined per baseline:

| Baseline | Typical retention | LC configuration |
|---|---|---|
| Low | 90 days | Insight default |
| Moderate | 1 year | Insight 90d hot + S3/GCS cold archival |
| High | Multi-year | Cold archival mandatory; consider dedicated analytics output |

The agent flags AU-11 when events touch log-retention integrity (log-clear events, sensor offline
on in-scope systems, archival output failures).

## Coexistence with L1 SOC Bot

The trigger rule fires on the **same** `case_created` event that would trigger an l1-bot. Both can
run in parallel — they don't conflict because:

- L1 bot decides security classification (true/false positive, close, escalate)
- NIST reviewer decides compliance classification (control-functioning/gap/ops/incident)
- Each writes to different case tags and notes
- The NIST reviewer explicitly does NOT modify security status or classification

## Scope Determination — Why It Matters

The agent's first step is an early-exit if the case is not NIST-relevant. This matters because:

- A generic case on a non-federal workstation does NOT need NIST documentation, and generating it
  dilutes the audit evidence
- Assessors look at authorization boundaries carefully — over-claiming scope creates questions
- Most orgs have a distinct federal-system subset within a broader fleet

The agent checks four signals in priority order:
1. Sensor tag (`fisma-scope`, `fedramp-scope`, `federal-system`, `nist-scope`)
2. Detection category prefix (`nist-`)
3. Detection rule tag (`nist-800-53` or `nist`)
4. Detection rule metadata key (`nist_control:`)

Any ONE signal is enough to mark the case in-scope.

## Coverage Gap — What LC Does Not Cover

The agent will NOT claim coverage for these NIST 800-53 families, which are out of LC's scope:

- **PE** (Physical & Environmental) — facility controls
- **PS** (Personnel Security) — screening, access agreements
- **AT** (Awareness & Training) — training programs
- **PL** (Planning) — policy-level
- **CA** (Assessment, Authorization & Monitoring) — process-level
- **PM** (Program Management) — governance
- **SC-7 enforcement** and **SC-18 enforcement** — LC detects only; the enforcement layer lives in
  network devices, WAFs, and OS / application policy

If a case implicates a control in one of these families, the agent will state the coverage gap
explicitly and recommend assessor / ISSO consultation.

## Cross-Framework Notes

NIST SP 800-53 Rev 5 is the parent catalog for several derivative frameworks. This agent's
classifications are directly inheritable by:

- **FedRAMP** (Low, Moderate, High)
- **FISMA**
- **StateRAMP** (with state/local overlay)
- **NIST 800-171** / **CMMC** (as a subset of Moderate)

If you run both this agent and a CMMC reviewer, each writes its own tags and notes — they do not
conflict.

## Related Agents (Future)

This is the **real-time case reviewer** pattern. A weekly audit-reporter agent that produces an
assessor-ready summary of all NIST 800-53 activity over a reporting period is a logical follow-on
(similar in shape to lc-ai's `customer-report` agent with a `168h_per_org` schedule trigger).

## Files

- `nist-800-53-compliance-reviewer.yaml` — top-level manifest (sync entry point)
- `hives/ai_agent.yaml` — agent definition with full NIST SME prompt
- `hives/dr-general.yaml` — D&R trigger rule
- `hives/secret.yaml` — placeholder secrets (replace before deploy)

## Reference Documents

- `../nist-800-53-limacharlie-mapping.md` — the authoritative NIST-to-LC capability map
- `../nist-800-53-limacharlie-implementation.md` — the deployable D&R/FIM rules whose metadata the
  agent consumes
