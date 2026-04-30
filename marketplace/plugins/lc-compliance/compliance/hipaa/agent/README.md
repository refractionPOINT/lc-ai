# HIPAA Compliance Reviewer — Automated HIPAA Security Rule Case Classification

An AI agent that acts as a HIPAA Security Rule (45 CFR Part 164) subject-matter expert. When a
security case is created on an endpoint handling electronic Protected Health Information (ePHI),
it classifies the event against specific HIPAA safeguards and writes audit-grade case
documentation suitable for an internal HIPAA Security Officer, an external auditor, or an HHS OCR
investigation record.

> **Gap analysis** is handled by the `compliance-gap` skill (in the
> `lc-compliance` Claude Code plugin at `plugin/lc-compliance/`), not by
> a backend agent. This README covers only the case-reviewer agent.

This agent is **complementary** to an L1 SOC bot — it reviews for *compliance impact*, not
security severity. It runs in parallel to the normal case triage flow without interfering with it.

## How It Works

```
Detection fires on an ePHI-tagged endpoint
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
Scope check: is this case HIPAA-relevant?
        ├── No  → add "not in scope" note, exit
        └── Yes → continue
        |
        v
Map event → HIPAA safeguard citation(s)
Classify compliance impact (safeguard-functioning /
  safeguard-gap / in-scope-ops / security-incident)
If security-incident → surface §164.400-414
  Breach Notification obligation in the conclusion
Write audit-ready summary, conclusion, analysis notes
Tag case with compliance classification
        |
        v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- Endpoints that should be in HIPAA scope must carry an ePHI tag — one of `ephi-host`,
  `hipaa-scope`, `phi-host`, or `covered-entity`. This is how the agent distinguishes ePHI-scoped
  from out-of-scope cases.
- D&R rules from `../hipaa-limacharlie-implementation.md` deployed, with the `hipaa` tag and
  `metadata.hipaa_safeguard:` fields preserved. These provide the safeguard citations the agent
  consumes.
- A LimaCharlie API key with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors to check ePHI tagging |
| `sensor.get` | Read sensor tags for scope determination |
| `dr.list` | Read detection rule metadata (hipaa_safeguard) |
| `insight.det.get` | Read linked detections |
| `insight.evt.get` | Access event telemetry for correlation |
| `investigation.get` | Read cases |
| `investigation.set` | Update case summary/conclusion, add notes/entities/tags |
| `ext.request` | Call ext-cases |
| `sop.get` | Read org-specific HIPAA SOPs if present |
| `sop.get.mtd` | Read SOP metadata |
| `org_notes.read` | Read org notes (for embedded HIPAA guidance, if mirrored) |
| `ai_agent.operate` | Run AI agent sessions |

## Installation

```bash
# 1. Replace API-key placeholders in hives/secret.yaml
#    Anthropic key + a LimaCharlie API key with the permissions above

# 2. Deploy via the LC sync command
limacharlie sync --oid <your-oid> --push hipaa-compliance-reviewer.yaml

# 3. Tag at least one endpoint as an ePHI-bearing system (otherwise the agent always early-exits)
limacharlie tag add --sid <ephi-sensor-sid> -t ephi-host --oid <your-oid>

# 4. Verify the ai_agent hive record exists
limacharlie hive get --hive-name ai_agent --key hipaa-compliance-reviewer --oid <your-oid> --output yaml

# 5. Verify the trigger rule exists
limacharlie dr get --name hipaa-compliance-reviewer-trigger --namespace general --oid <your-oid> --output yaml
```

## What the Agent Produces

For each HIPAA-relevant case, the agent adds:

| Field | Content |
|---|---|
| **Summary** | One-paragraph auditor-readable overview: host, event, implicated HIPAA safeguards, compliance classification |
| **Conclusion** | Safeguard mapping with exact citations (e.g., "HIPAA Security Rule §164.312(b)"), compliance classification with reasoning, remediation recommendations for gaps, and — for security incidents — explicit §164.400-414 Breach Notification language for the privacy/security officer |
| **Analysis note** | Detailed markdown timeline with event data verbatim, scope-determination explanation, correlating telemetry, and (for incidents) a Breach Notification Assessment subsection |
| **Entities** | IOCs tagged with HIPAA-relevant context (e.g., shared / terminated / emergency accounts, ePHI-path files, unsigned binaries on ePHI hosts) |
| **Tags** | One of: `hipaa-safeguard-functioning`, `hipaa-safeguard-gap`, `hipaa-in-scope-ops`, `hipaa-security-incident` |

## Compliance Classification Categories

| Tag | Meaning | Audit Value |
|---|---|---|
| `hipaa-safeguard-functioning` | The detection firing IS the safeguard working. Example: FIM_HIT on an ePHI path proves §164.312(c)(1)/(c)(2) integrity monitoring is operational; logged failed logon proves §164.312(b) + §164.308(a)(5)(ii)(C). | Positive evidence of safeguard operation. |
| `hipaa-safeguard-gap` | The event reveals a compliance gap. Example: Security event log cleared → §164.312(b) violated; sensor offline on an ePHI host → §164.312(b) gap; shared account used → §164.312(a)(2)(i) gap; BitLocker disabled → §164.312(a)(2)(iv) Addressable-spec failure. | Audit finding — requires remediation and documentation. |
| `hipaa-in-scope-ops` | Expected ePHI-host administrative activity. Example: documented privileged maintenance, approved patching. | Audit-trail completeness evidence for §164.312(b) / §164.308(a)(1)(ii)(D). |
| `hipaa-security-incident` | A potential security incident on in-scope systems. Triggers §164.308(a)(6)(ii) response-and-reporting. | Invokes IR plan. MUST also surface §164.400-414 Breach Notification question to the privacy/security officer within the 60-day window. |

## Breach Notification (§164.400-414) — Why the Agent Flags It

HIPAA's Breach Notification Rule is a **distinct obligation** on top of security response. When
unsecured ePHI is accessed, acquired, used, or disclosed in a manner not permitted by the
Privacy Rule, the Covered Entity must notify:

- Affected individuals (§164.404) — within 60 days of discovery
- HHS (§164.408) — within 60 days for breaches of 500+ records; annually for smaller breaches
- Media (§164.406) — for breaches affecting 500+ residents of a state or jurisdiction

The agent is NOT the breach-determination authority — that is the privacy / security officer's
job. But because the 60-day clock starts at **discovery**, and discovery is typically the moment
of case creation or first analyst triage, the agent's role is to surface the question
unambiguously at the earliest possible point.

For every `hipaa-security-incident` classification, the Conclusion includes this exact sentence:

> Potential Breach Notification obligations under §164.400-414 apply if unsecured ePHI was
> accessed, acquired, used, or disclosed. The privacy/security officer should make the final
> determination within the 60-day notification window.

## Required vs Addressable Safeguards

HIPAA implementation specifications are flagged **Required (R)** or **Addressable (A)**.
"Addressable" does NOT mean optional — the Covered Entity must assess whether the specific
safeguard is reasonable and appropriate, and either implement it, implement an equivalent, or
document why neither applies (45 CFR §164.306(d)).

The agent treats both categories with equal rigor when classifying. A gap against an Addressable
safeguard is still a documented audit finding unless the org has on record an equivalent control
or a documented justification for non-implementation.

## Configuration

| Parameter | Value | Notes |
|---|---|---|
| `model` | `sonnet` | Sufficient for structured compliance classification. Escalate to `opus` if classification consistently hits ambiguity on complex chains. |
| `max_turns` | `20` | Enough for scope check + context gathering + case update |
| `max_budget_usd` | `1.0` | Compliance review is a bounded task |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after review |
| `debounce_key` | `hipaa-compliance-reviewer` | One review at a time; subsequent cases queue |
| Suppression | `10/min global` | Matches l1-bot default |

## Coexistence with L1 SOC Bot

The trigger rule fires on the **same** `case_created` event that would trigger an l1-bot. Both
can run in parallel — they don't conflict because:

- L1 bot decides security classification (true/false positive, close, escalate)
- HIPAA reviewer decides compliance classification (safeguard-functioning/gap/ops/incident)
- Each writes to different case tags and notes
- The HIPAA reviewer explicitly does NOT modify security status or classification

If you want HIPAA review to **block** downstream SOC flow until completed, run this agent first
by adding a short `debounce_key` sleep at the start of your l1-bot prompt, or use an org-level
SOP that references HIPAA review output.

## Scope Determination — Why It Matters

The agent's first step is an early-exit if the case is not HIPAA-relevant. This matters because:

- A generic case on an out-of-scope workstation does NOT need HIPAA documentation, and generating
  it dilutes the audit evidence
- HIPAA auditors look at scope boundaries carefully — over-claiming ePHI scope creates questions
- Most orgs have a defined ePHI footprint (EMR servers, database hosts, claims-processing
  workstations) and a larger non-ePHI footprint — running the agent on every case would waste
  budget

The agent checks four signals in order:
1. Sensor tag (`ephi-host`, `hipaa-scope`, `phi-host`, `covered-entity`)
2. Detection category prefix (`hipaa-`)
3. Detection rule tag (`hipaa` / `hipaa-security-rule`)
4. Detection rule metadata key (`hipaa_safeguard:`)

Any ONE signal is enough to mark the case in-scope.

## Audit Log Retention — A Known HIPAA Ambiguity

HIPAA does **NOT** prescribe a specific audit-log retention period in §164.312(b). However,
§164.316(b)(2)(i) requires **6-year** retention of security documentation, and industry practice
extends that period to audit logs which support the documented safeguards.

The agent does not opine on retention durations — retention is a platform-configuration concern
(Insight hot window + S3/GCS cold archival lifecycle). If you receive an audit question on
retention, see `../hipaa-limacharlie-mapping.md` §164.316.

## Files

- `hipaa-compliance-reviewer.yaml` — top-level manifest (sync entry point)
- `hives/ai_agent.yaml` — agent definition with full HIPAA SME prompt
- `hives/dr-general.yaml` — D&R trigger rule
- `hives/secret.yaml` — placeholder secrets (replace before deploy)

## Reference Documents

- `../hipaa-limacharlie-mapping.md` — the authoritative HIPAA-to-LC capability map
- `../hipaa-limacharlie-implementation.md` — the deployable D&R / FIM / artifact / exfil rules
  whose `hipaa_safeguard:` metadata the agent consumes
- `../hipaa-attribution.md` — authoritative HIPAA Security Rule source citation and verification
  status (MACHINE_VERIFIED against eCFR)
