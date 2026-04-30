# CMMC Compliance Reviewer — Automated CMMC v2 Case Classification

An AI agent that acts as a CMMC v2 (Cybersecurity Maturity Model Certification) Level 2 and Level 3
subject-matter expert. When a security case is created on a CUI-handling endpoint in a Defense
Industrial Base (DIB) environment, it classifies the event against specific CMMC practices and
writes audit-grade case documentation that a C3PAO (Certified Third-Party Assessor Organization)
can use as assessment evidence.

> **Gap analysis** is handled by the `compliance-gap` skill (in the
> `lc-compliance` Claude Code plugin at `plugin/lc-compliance/`), not by
> a backend agent. This README covers only the case-reviewer agent.

This agent is **complementary** to an L1 SOC bot — it reviews for *compliance impact*, not security
severity. It runs in parallel to the normal case triage flow without interfering with it.

## How It Works

```
Detection fires on a CUI-tagged endpoint
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
Scope check: is this case CMMC-relevant?
        |-- No  --> add "not in scope" note, exit
        `-- Yes --> continue
        |
        v
Map event --> CMMC Practice ID(s)
Classify compliance impact (control-functioning /
  control-gap / in-scope-ops / security-incident)
Write C3PAO-ready summary, conclusion, analysis notes
Tag case with compliance classification
        |
        v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- Endpoints that should be in CMMC scope must carry a CUI/DIB tag — one of `cui`, `cui-host`,
  `cmmc-scope`, or `dib-host`. This is how the agent distinguishes CMMC-scoped from out-of-scope
  cases.
- D&R rules from `../cmmc-limacharlie-implementation.md` deployed, with the `cmmc` tag and
  `metadata.cmmc_control:` fields preserved. These provide the practice mapping the agent consumes.
- A LimaCharlie API key with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors to check CUI/DIB tagging |
| `sensor.get` | Read sensor tags for scope determination |
| `dr.list` | Read detection rule metadata (cmmc_control) |
| `insight.det.get` | Read linked detections |
| `insight.evt.get` | Access event telemetry for correlation |
| `investigation.get` | Read cases |
| `investigation.set` | Update case summary/conclusion, add notes/entities/tags |
| `ext.request` | Call ext-cases |
| `sop.get` | Read org-specific CMMC SOPs if present |
| `sop.get.mtd` | Read SOP metadata |
| `org_notes.read` | Read org notes (for embedded CMMC guidance, if mirrored) |
| `ai_agent.operate` | Run AI agent sessions |

## Installation

```bash
# 1. Replace API-key placeholders in hives/secret.yaml
#    Anthropic key + a LimaCharlie API key with the permissions above

# 2. Deploy via the LC sync command
limacharlie sync --oid <your-oid> --push cmmc-compliance-reviewer.yaml

# 3. Tag at least one endpoint as a CUI/DIB system (otherwise the agent always early-exits)
limacharlie tag add --sid <cui-sensor-sid> -t cui --oid <your-oid>

# 4. Verify the ai_agent hive record exists
limacharlie hive get --hive-name ai_agent --key cmmc-compliance-reviewer --oid <your-oid> --output yaml

# 5. Verify the trigger rule exists
limacharlie dr get --name cmmc-compliance-reviewer-trigger --namespace general --oid <your-oid> --output yaml
```

## What the Agent Produces

For each CMMC-relevant case, the agent adds:

| Field | Content |
|---|---|
| **Summary** | One-paragraph C3PAO-readable overview: host, event, implicated CMMC practices, compliance classification |
| **Conclusion** | Practice mapping with exact IDs (e.g., "CMMC v2 Practice AU.L2-3.3.1"), compliance classification with reasoning, and remediation recommendations if a gap was found |
| **Analysis note** | Detailed markdown timeline with event data verbatim, scope-determination explanation, and correlating telemetry |
| **Entities** | IOCs tagged with CMMC-relevant context (e.g., privileged accounts, CUI-path files, unsigned binaries on DIB hosts, potential exfil destinations) |
| **Tags** | One of: `cmmc-control-functioning`, `cmmc-control-gap`, `cmmc-in-scope-ops`, `cmmc-security-incident` |

## Compliance Classification Categories

| Tag | Meaning | C3PAO Value |
|---|---|---|
| `cmmc-control-functioning` | The detection firing IS the control working. Example: `YARA_DETECTION` proves SI.L2-3.14.2 is operational; FIM_HIT on a baseline file proves CM.L2-3.4.1 is operational. | Positive evidence of control operation. |
| `cmmc-control-gap` | The event reveals a compliance gap. Example: Security event log cleared (AU.L2-3.3.4 violated); Defender real-time protection disabled (SI.L2-3.14.2 violated); sensor offline on CUI host (AU.L2-3.3.1 gap). | Assessment finding — requires remediation and documentation. |
| `cmmc-in-scope-ops` | Expected CUI/DIB administrative activity. Example: legitimate patching, documented privileged access. | Audit-trail completeness evidence for AU.L2-3.3.1, AU.L2-3.3.2. |
| `cmmc-security-incident` | A potential security incident on in-scope systems. | IR.L2-3.6.1 / IR.L2-3.6.2 incident-response obligations — IR plan invocation, timeline documentation, potential DFARS 252.204-7012 72-hour DoD reporting if CUI exposure is suspected. |

## Configuration

| Parameter | Value | Notes |
|---|---|---|
| `model` | `sonnet` | Sufficient for structured compliance classification. Escalate to `opus` if classification consistently hits ambiguity on complex chains. |
| `max_turns` | `20` | Enough for scope check + context gathering + case update |
| `max_budget_usd` | `1.0` | Compliance review is a bounded task |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after review |
| `debounce_key` | `cmmc-compliance-reviewer` | One review at a time; subsequent cases queue |
| Suppression | `10/min global` | Matches l1-bot default |

## Data Retention Notes

CMMC Level 2 requires **90 days active audit-log retention**; organization-defined archival is
required. Level 3 (800-172) expects longer archival windows aligned to the contracting
instrument.

- LimaCharlie Insight provides 90 days of hot retention (meets L2 active-retention requirement)
- Add an S3 or GCS output for long-term archival (meets L2/L3 archival requirement)
- If the agent observes retention-relevant events (output delivery failure, sensor offline on a
  CUI host, log tampering), it will flag them against AU.L2-3.3.1 / AU.L2-3.3.8

## Coexistence with L1 SOC Bot

The trigger rule fires on the **same** `case_created` event that would trigger an l1-bot. Both can
run in parallel — they don't conflict because:

- L1 bot decides security classification (true/false positive, close, escalate)
- CMMC reviewer decides compliance classification (control-functioning/gap/ops/incident)
- Each writes to different case tags and notes
- The CMMC reviewer explicitly does NOT modify security status or classification

If you want CMMC review to **block** downstream SOC flow until completed, run this agent first by
adding a short `debounce_key` sleep at the start of your l1-bot prompt, or use an org-level SOP
that references CMMC review output.

## Scope Determination — Why It Matters

The agent's first step is an early-exit if the case is not CMMC-relevant. This matters because:

- A generic case on an out-of-scope workstation does NOT need CMMC documentation, and generating
  it dilutes the assessment evidence
- C3PAOs look at scope boundaries carefully — over-claiming scope creates questions
- Most DIB orgs have a small CUI footprint (the "enclave" approach) and a large non-CUI
  footprint — running the agent on every case would waste budget

The agent checks four signals in order:
1. Sensor tag (`cui`, `cui-host`, `cmmc-scope`, `dib-host`)
2. Detection category prefix (`cmmc-`)
3. Detection rule tag (`cmmc`)
4. Detection rule metadata key (`cmmc_control:`)

Any ONE signal is enough to mark the case in-scope.

## Out-of-Scope CMMC Families (Not Covered by LC)

LimaCharlie provides endpoint-and-telemetry evidence. The following CMMC practice families are
**not** covered by this agent and require separate evidence streams:

- Physical Protection (PE) — facility/badge controls, visitor logs
- Personnel Security (PS) — screening, termination procedures
- Awareness & Training (AT) — training records, curriculum
- Written policies themselves (documentation authorship)
- Non-endpoint Media Protection (MP) — physical media handling
- Perimeter boundary (SC-7) at the network gateway, as opposed to endpoint

The agent will never claim coverage for these — if a case happens to touch one of them, the
agent defers to the organization's SSP (System Security Plan) and non-LC controls.

## Related Agents (Future)

This is the **real-time case reviewer** pattern. A weekly audit-reporter agent that produces a
C3PAO-ready summary of all CMMC activity over a reporting period is a logical follow-on (similar
in shape to lc-ai's `customer-report` agent with a `168h_per_org` schedule trigger).

## Files

- `cmmc-compliance-reviewer.yaml` — top-level manifest (sync entry point)
- `hives/ai_agent.yaml` — agent definition with full CMMC SME prompt
- `hives/dr-general.yaml` — D&R trigger rule
- `hives/secret.yaml` — placeholder secrets (replace before deploy)

## Reference Documents

- `../cmmc-limacharlie-mapping.md` — the authoritative CMMC-to-LC capability map
- `../cmmc-limacharlie-implementation.md` — the deployable D&R/FIM/artifact-collection rules whose
  metadata the agent consumes
