# PCI Compliance Reviewer — Automated PCI DSS Case Classification

An AI agent that acts as a PCI DSS v4.0 subject-matter expert. When a security case is created on a
cardholder-data-environment (CDE) system, it classifies the event against specific PCI requirements
and writes audit-grade case documentation that a Qualified Security Assessor (QSA) can use as
assessment evidence.

> **Gap analysis** is handled by the `compliance-gap` skill (in the
> `lc-compliance` Claude Code plugin at `plugin/lc-compliance/`), not by
> a backend agent. This README covers only the case-reviewer agent.

This agent is **complementary** to an L1 SOC bot — it reviews for *compliance impact*, not security
severity. It runs in parallel to the normal case triage flow without interfering with it.

## How It Works

```
Detection fires on a CDE-tagged endpoint
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
Scope check: is this case PCI-relevant?
        ├── No  → add "not in scope" note, exit
        └── Yes → continue
        |
        v
Map event → PCI requirement number(s)
Classify compliance impact (control-functioning /
  control-gap / in-scope-ops / security-incident-pci)
Write QSA-ready summary, conclusion, analysis notes
Tag case with compliance classification
        |
        v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- Endpoints that should be in PCI scope must carry a CDE tag — one of `cde`, `pci-scope`,
  `card-data`, or `pci-dss`. This is how the agent distinguishes PCI-scoped from out-of-scope cases.
- D&R rules from `../pci-dss-limacharlie-implementation.md` deployed, with the `pci-dss` tag and
  `metadata.pci_dss_req:` fields preserved. These provide the requirement mapping the agent consumes.
- A LimaCharlie API key with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors to check CDE tagging |
| `sensor.get` | Read sensor tags for scope determination |
| `dr.list` | Read detection rule metadata (pci_dss_req) |
| `insight.det.get` | Read linked detections |
| `insight.evt.get` | Access event telemetry for correlation |
| `investigation.get` | Read cases |
| `investigation.set` | Update case summary/conclusion, add notes/entities/tags |
| `ext.request` | Call ext-cases |
| `sop.get` | Read org-specific PCI SOPs if present |
| `sop.get.mtd` | Read SOP metadata |
| `org_notes.read` | Read org notes (for embedded PCI guidance, if mirrored) |
| `ai_agent.operate` | Run AI agent sessions |

## Installation

```bash
# 1. Replace API-key placeholders in hives/secret.yaml
#    Anthropic key + a LimaCharlie API key with the permissions above

# 2. Deploy via the LC sync command
limacharlie sync --oid <your-oid> --push pci-compliance-reviewer.yaml

# 3. Tag at least one endpoint as a CDE system (otherwise the agent always early-exits)
limacharlie tag add --sid <cde-sensor-sid> -t cde --oid <your-oid>

# 4. Verify the ai_agent hive record exists
limacharlie hive get --hive-name ai_agent --key pci-compliance-reviewer --oid <your-oid> --output yaml

# 5. Verify the trigger rule exists
limacharlie dr get --name pci-compliance-reviewer-trigger --namespace general --oid <your-oid> --output yaml
```

## What the Agent Produces

For each PCI-relevant case, the agent adds:

| Field | Content |
|---|---|
| **Summary** | One-paragraph QSA-readable overview: host, event, implicated PCI requirements, compliance classification |
| **Conclusion** | Requirement mapping with exact numbers (e.g., "PCI DSS v4.0 Req 10.2.1.4"), compliance classification with reasoning, and remediation recommendations if a gap was found |
| **Analysis note** | Detailed markdown timeline with event data verbatim, scope-determination explanation, and correlating telemetry |
| **Entities** | IOCs tagged with PCI-relevant context (e.g., shared accounts, CHD-path files, unsigned binaries on CDE hosts) |
| **Tags** | One of: `pci-control-functioning`, `pci-control-gap`, `pci-in-scope-ops`, `pci-security-incident` |

## Compliance Classification Categories

| Tag | Meaning | QSA Value |
|---|---|---|
| `pci-control-functioning` | The detection firing IS the control working. Example: FIM_HIT on a CHD path proves Req 11.5.1 is operational. | Positive evidence of control operation. |
| `pci-control-gap` | The event reveals a compliance gap. Example: Security event log cleared (Req 10.2.1.6 violated); sensor offline on CDE host (Req 10.7.x). | Audit finding — requires remediation and documentation. |
| `pci-in-scope-ops` | Expected CDE administrative activity. Example: legitimate patching, documented privileged access. | Audit-trail completeness evidence for Req 10.2.x. |
| `pci-security-incident` | A potential security incident on in-scope systems. | Req 12.10 incident-response obligations — IR plan invocation, timeline documentation, potential notification. |

## Configuration

| Parameter | Value | Notes |
|---|---|---|
| `model` | `sonnet` | Sufficient for structured compliance classification. Escalate to `opus` if classification consistently hits ambiguity on complex chains. |
| `max_turns` | `20` | Enough for scope check + context gathering + case update |
| `max_budget_usd` | `1.0` | Compliance review is a bounded task |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after review |
| `debounce_key` | `pci-compliance-reviewer` | One review at a time; subsequent cases queue |
| Suppression | `10/min global` | Matches l1-bot default |

## Coexistence with L1 SOC Bot

The trigger rule fires on the **same** `case_created` event that would trigger an l1-bot. Both can run
in parallel — they don't conflict because:

- L1 bot decides security classification (true/false positive, close, escalate)
- PCI reviewer decides compliance classification (control-functioning/gap/ops/incident)
- Each writes to different case tags and notes
- The PCI reviewer explicitly does NOT modify security status or classification

If you want PCI review to **block** downstream SOC flow until completed, run this agent first by
adding a short `debounce_key` sleep at the start of your l1-bot prompt, or use an org-level SOP that
references PCI review output.

## Scope Determination — Why It Matters

The agent's first step is an early-exit if the case is not PCI-relevant. This matters because:

- A generic case on an out-of-scope workstation does NOT need PCI documentation, and generating it
  dilutes the audit evidence
- PCI auditors look at scope boundaries carefully — over-claiming scope creates questions
- Most orgs have a small CDE footprint (dozens of hosts) and a large non-CDE footprint — running the
  agent on every case would waste budget

The agent checks four signals in order:
1. Sensor tag (`cde`, `pci-scope`, `card-data`, `pci-dss`)
2. Detection category prefix (`pci-`)
3. Detection rule tag (`pci-dss`)
4. Detection rule metadata key (`pci_dss_req:`)

Any ONE signal is enough to mark the case in-scope.
