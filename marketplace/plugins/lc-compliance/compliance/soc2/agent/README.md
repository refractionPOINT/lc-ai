# SOC 2 Compliance Reviewer — Automated SOC 2 Case Classification

An AI agent that acts as a SOC 2 Trust Services Criteria (TSC) subject-matter expert. When a
security case is created on an in-scope production system, it classifies the event against
specific SOC 2 criteria and writes audit-grade case documentation that a SOC 2 auditor can use
as Type I (design) or Type II (operating effectiveness) evidence.

> **Gap analysis** is handled by the `compliance-gap` skill (in the
> `lc-compliance` Claude Code plugin at `plugin/lc-compliance/`), not by
> a backend agent. This README covers only the case-reviewer agent.

This agent is **complementary** to an L1 SOC bot — it reviews for *compliance impact*, not
security severity. It runs in parallel to the normal case triage flow without interfering with it.

## SOC 2 Framing — Why This Agent Matters

Unlike PCI DSS or HIPAA, SOC 2 is not about protecting a specific data class — it is about the
**operating effectiveness of controls over the audit observation period** (typically 12 months
for a Type II report). The primary deliverable of this agent is therefore different:

- A detection firing is not just a security alert — it is **audit evidence** that CC4.1 (Ongoing
  Monitoring) and CC7.2/CC7.3 (System Component Monitoring, Evaluation of Security Events) are
  operating.
- The detection-to-case lifecycle (detect → triage → document → classify → resolve) is exactly
  the evidence a Type II auditor samples from.
- A detection rule that exists on paper but produces no evidence is a Type II finding. The
  agent's job is to convert every in-scope case into a durable, citable piece of operating
  evidence.

## How It Works

```
Detection fires on an in-scope endpoint
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
Scope check: is this case SOC-2-relevant?
        ├── No  → add "not in scope" note, exit
        └── Yes → continue
        |
        v
Map event → SOC 2 TSC criterion number(s)
Classify compliance impact (criterion-operating /
  criterion-gap / in-scope-ops / security-incident)
Write auditor-ready summary, conclusion, analysis notes
Tag case with compliance classification
        |
        v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- D&R rules from `../soc2-limacharlie-implementation.md` deployed, with the `soc2` tag and
  `metadata.soc2_criterion:` fields preserved. These provide the criterion mapping the agent
  consumes.
- Scope tagging strategy:
  - SOC 2 scope is typically broad (most of production). By default, the agent treats a case as
    in-scope when the detection rule carries the `soc2` tag, regardless of sensor tags.
  - To EXCLUDE a sensor from SOC 2 review (e.g., a dev/sandbox endpoint), do NOT tag it with
    `soc2-scope`, `in-scope-system`, or `audit-scope`, and deploy only non-`soc2`-tagged rules
    to that sensor.
  - To narrow scope to a specific subset of sensors, tag those sensors with one of
    `soc2-scope`, `in-scope-system`, or `audit-scope`, and the agent will only classify cases
    from those sensors.
- A LimaCharlie API key with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors to check scope tagging |
| `sensor.get` | Read sensor tags for scope determination |
| `dr.list` | Read detection rule metadata (soc2_criterion) |
| `insight.det.get` | Read linked detections |
| `insight.evt.get` | Access event telemetry for correlation |
| `investigation.get` | Read cases |
| `investigation.set` | Update case summary/conclusion, add notes/entities/tags |
| `ext.request` | Call ext-cases |
| `sop.get` | Read org-specific SOC 2 SOPs if present |
| `sop.get.mtd` | Read SOP metadata |
| `org_notes.read` | Read org notes (for embedded SOC 2 guidance, if mirrored) |
| `ai_agent.operate` | Run AI agent sessions |

## Installation

```bash
# 1. Replace API-key placeholders in hives/secret.yaml
#    Anthropic key + a LimaCharlie API key with the permissions above

# 2. Deploy via the LC sync command
limacharlie sync --oid <your-oid> --push soc2-compliance-reviewer.yaml

# 3. (Optional) Narrow scope — tag only production in-scope endpoints
limacharlie tag add --sid <prod-sensor-sid> -t soc2-scope --oid <your-oid>

# 4. Verify the ai_agent hive record exists
limacharlie hive get --hive-name ai_agent --key soc2-compliance-reviewer --oid <your-oid> --output yaml

# 5. Verify the trigger rule exists
limacharlie dr get --name soc2-compliance-reviewer-trigger --namespace general --oid <your-oid> --output yaml
```

## What the Agent Produces

For each in-scope case, the agent adds:

| Field | Content |
|---|---|
| **Summary** | One-paragraph auditor-readable overview: host, event, implicated SOC 2 criteria, compliance classification |
| **Conclusion** | Criterion mapping with exact citations (e.g., "SOC 2 TSC CC6.1"), compliance classification with reasoning, remediation if a gap, and Type II observation-period framing |
| **Analysis note** | Detailed markdown timeline with event data verbatim, scope-determination explanation, correlating telemetry, and explicit Type II operating-evidence framing |
| **Entities** | IOCs tagged with SOC 2-relevant context (e.g., privileged users, config-file paths, unsigned binaries) |
| **Tags** | One of: `soc2-criterion-operating`, `soc2-criterion-gap`, `soc2-in-scope-ops`, `soc2-security-incident` |

## Compliance Classification Categories

| Tag | Meaning | Auditor Value |
|---|---|---|
| `soc2-criterion-operating` | The detection firing IS the control operating. Example: FIM_HIT on /etc/sudoers demonstrates CC7.1 and CC8.1 are operating. | **Primary Type II evidence** — recurring operating effectiveness. |
| `soc2-criterion-gap` | The event reveals a compliance gap. Example: audit log cleared (CC8.1 bypass); sensor offline on in-scope host (CC4.1 gap). | **Type II finding** — requires remediation, documented observation, and response. |
| `soc2-in-scope-ops` | Expected administrative activity on an in-scope system. Example: legitimate patching, documented privileged access. | Audit-trail completeness evidence for CC2.x / CC7.3. |
| `soc2-security-incident` | A potential security incident on in-scope systems. | CC7.4 incident-response obligations — IR plan invocation, timeline, containment, CC2.3 communication. |

## Configuration

| Parameter | Value | Notes |
|---|---|---|
| `model` | `sonnet` | Sufficient for structured compliance classification |
| `max_turns` | `20` | Enough for scope check + context gathering + case update |
| `max_budget_usd` | `1.0` | Compliance review is a bounded task |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after review |
| `debounce_key` | `soc2-compliance-reviewer` | One review at a time; subsequent cases queue |
| Suppression | `10/min global` | Matches l1-bot default |

## Retention — Type II Observation Period

SOC 2 Type II reports cover an observation period, typically **12 months** for annual reports,
6 months for initial reports. Auditors expect evidence retained across that window. LC Insight
retains 90 days hot; the full observation window requires a cold-archive output:

- Configure S3 or GCS output streaming `event`, `detect`, and `audit` streams for 12-month+
  archival
- Cases themselves persist indefinitely in ext-cases — no additional config required
- Document the retention architecture in your SOC 2 system description

See `../soc2-limacharlie-mapping.md#retention-guidance` for the full pattern.

## Coexistence with L1 SOC Bot

The trigger rule fires on the **same** `case_created` event that would trigger an l1-bot. Both
can run in parallel — they don't conflict because:

- L1 bot decides security classification (true/false positive, close, escalate)
- SOC 2 reviewer decides compliance classification (criterion-operating/gap/ops/incident)
- Each writes to different case tags and notes
- The SOC 2 reviewer explicitly does NOT modify security status or classification

## Scope Determination — Why the Default Is Different from PCI/HIPAA

PCI DSS and HIPAA have narrowly-scoped data classes (CHD, ePHI). SOC 2 scope is usually broad —
most of a SaaS organization's production surface is in scope for Security (CC) by default. The
agent therefore uses an "in-scope by default if the rule is SOC-2-tagged" model:

1. Sensor tag (`soc2-scope`, `in-scope-system`, `audit-scope`) — explicit inclusion
2. Detection category prefix (`soc2-`)
3. Detection rule tag (`soc2`) — primary default trigger
4. Detection rule metadata key (`soc2_criterion:`)

Any ONE signal is enough to mark the case in-scope. To exclude a sensor, ensure it has no scope
tag AND that rules applied to it do not carry the `soc2` tag.

## Out-of-LC-Scope Criteria

The agent will explicitly decline to claim coverage for:

- **CC1** (Control Environment) — governance/board-level
- **A1.1** (capacity planning), **A1.3** (recovery testing) — APM/backup tools own these
- **PI1** (Processing Integrity) — application-layer input/transaction validation
- **P1–P8** (Privacy) — policy/process controls
- **CC9.2 vendor due-diligence workflow** — LC surfaces vendor telemetry, not the assessment

If a case implicates any of these, the agent will note the gap and state that LC is not the
authoritative control.
