# CIS v8 Compliance Reviewer — Automated CIS Controls v8 Case Classification

An AI agent that acts as a CIS Critical Security Controls v8 subject-matter expert. When a
security case is created, it classifies the event against specific CIS v8 Safeguards — with
Implementation Group (IG1/IG2/IG3) awareness — and writes audit-grade case documentation
that an assessor can use as evidence.

> **Gap analysis** is handled by the `compliance-gap` skill (in the
> `lc-compliance` Claude Code plugin at `plugin/lc-compliance/`), not by
> a backend agent. This README covers only the case-reviewer agent.

This agent is **complementary** to an L1 SOC bot — it reviews for *compliance impact*, not
security severity. It runs in parallel to the normal case triage flow without interfering
with it.

## How It Works

```
Detection fires on a sensor
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
Scope check: is this case CIS v8-relevant?
        (Default: yes, when detection carries cis-v8 tag;
         opt-out via absence of CIS rules + no cis-scope tags)
        ├── No  → add "not in scope" note, exit
        └── Yes → continue
        |
        v
Map event → CIS v8 Safeguard number(s)
Identify each safeguard's IG tier (IG1/IG2/IG3)
Compare against org's committed IG (if cis-ig1/cis-ig2/cis-ig3 tagged)
Classify compliance impact (safeguard-operating /
  safeguard-gap / in-scope-ops / security-incident)
Write assessor-ready summary, conclusion, analysis notes
Tag case with compliance classification
        |
        v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- D&R rules from `../cis-v8-limacharlie-implementation.md` deployed, with the `cis-v8` tag and
  `metadata.cis_safeguard:` fields preserved. These provide the safeguard mapping the agent
  consumes.
- (Optional) Sensor or org tags for Implementation Group tier — `cis-ig1`, `cis-ig2`, or
  `cis-ig3` — so the agent can flag when an event represents coverage exceeding the org's
  committed IG tier.
- (Optional) Explicit scope tags — `cis-scope` or `cis-v8-scope` — if the org scopes CIS v8
  coverage to a subset of the fleet. CIS is most commonly applied org-wide, so these tags
  are usually unnecessary.
- A LimaCharlie API key with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors to check CIS tagging |
| `sensor.get` | Read sensor tags for scope and IG determination |
| `dr.list` | Read detection rule metadata (cis_safeguard) |
| `insight.det.get` | Read linked detections |
| `insight.evt.get` | Access event telemetry for correlation |
| `investigation.get` | Read cases |
| `investigation.set` | Update case summary/conclusion, add notes/entities/tags |
| `ext.request` | Call ext-cases |
| `sop.get` | Read org-specific CIS SOPs if present |
| `sop.get.mtd` | Read SOP metadata |
| `org_notes.read` | Read org notes (for embedded CIS guidance, if mirrored) |
| `ai_agent.operate` | Run AI agent sessions |

## Installation

```bash
# 1. Replace API-key placeholders in hives/secret.yaml
#    Anthropic key + a LimaCharlie API key with the permissions above

# 2. Deploy via the LC sync command
limacharlie sync --oid <your-oid> --push cis-v8-compliance-reviewer.yaml

# 3. (Optional) Tag sensors / org with the committed IG tier
limacharlie tag add --sid <sid> -t cis-ig1 --oid <your-oid>    # small org baseline
limacharlie tag add --sid <sid> -t cis-ig2 --oid <your-oid>    # medium org essentials
limacharlie tag add --sid <sid> -t cis-ig3 --oid <your-oid>    # large/regulated org

# 4. Verify the ai_agent hive record exists
limacharlie hive get --hive-name ai_agent --key cis-v8-compliance-reviewer --oid <your-oid> --output yaml

# 5. Verify the trigger rule exists
limacharlie dr get --name cis-v8-compliance-reviewer-trigger --namespace general --oid <your-oid> --output yaml
```

## What the Agent Produces

For each CIS v8-relevant case, the agent adds:

| Field | Content |
|---|---|
| **Summary** | One-paragraph assessor-readable overview: host, event, implicated CIS v8 Safeguards with IG tiers, compliance classification |
| **Conclusion** | Safeguard mapping in the form "CIS v8 Safeguard N.N" with IG tier, org IG context and cross-tier flag if applicable, compliance classification with reasoning, and remediation recommendations if a gap was found |
| **Analysis note** | Detailed markdown timeline with event data verbatim, scope-determination explanation, correlating telemetry, and IG cross-tier notes |
| **Entities** | IOCs tagged with CIS-relevant context |
| **Tags** | One of: `cis-safeguard-operating`, `cis-safeguard-gap`, `cis-in-scope-ops`, `cis-security-incident` |

## Compliance Classification Categories

| Tag | Meaning | Assessor Value |
|---|---|---|
| `cis-safeguard-operating` | The detection firing IS the safeguard working. Example: a DNS_REQUEST matching the malicious-domain lookup proves CIS v8 Safeguard 9.2 is operational. | Positive evidence of safeguard operation. |
| `cis-safeguard-gap` | The event reveals a gap. Example: Security event log cleared (8.2 violated); firewall disabled (4.4/4.5); Defender disabled (10.1). | Assessment finding — requires remediation and documentation. |
| `cis-in-scope-ops` | Expected administrative activity. Example: legitimate patching, documented privileged access. | Audit-trail completeness evidence for 8.2 / 8.5 / 8.8. |
| `cis-security-incident` | A potential security incident on in-scope systems. | CIS v8 Safeguards 17.3–17.9 obligations — IR reporting, communication, post-incident review. |

## Implementation Group (IG) Awareness

Each CIS v8 Safeguard has an assigned IG tier:

- **IG1** (foundational) — minimum any organisation should implement
- **IG2** (essential) — medium-sized organisations
- **IG3** (advanced) — large or regulated organisations

The agent reads sensor/org tags `cis-ig1`, `cis-ig2`, `cis-ig3` to determine the org's
committed tier. When a detected event corresponds to a **higher-tier safeguard than the
org's committed tier**, the agent flags this as "exceeds baseline — evidence of maturity
above committed IG tier." This is a compliance-relevant positive finding and worth
documenting for assessors.

## Configuration

| Parameter | Value | Notes |
|---|---|---|
| `model` | `sonnet` | Sufficient for structured compliance classification. |
| `max_turns` | `20` | Enough for scope check + context gathering + case update |
| `max_budget_usd` | `1.0` | Compliance review is a bounded task |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after review |
| `debounce_key` | `cis-v8-compliance-reviewer` | One review at a time; subsequent cases queue |
| Suppression | `10/min global` | Matches l1-bot default |

## Coexistence with L1 SOC Bot

The trigger rule fires on the **same** `case_created` event that would trigger an l1-bot.
Both can run in parallel — they don't conflict because:

- L1 bot decides security classification (true/false positive, close, escalate)
- CIS v8 reviewer decides compliance classification (safeguard-operating / gap / ops / incident)
- Each writes to different case tags and notes
- The CIS v8 reviewer explicitly does NOT modify security status or classification

## Scope Determination — Why It Matters

CIS v8 is commonly applied as an **org-wide baseline**, so the default disposition for any
case is in-scope. The agent still runs an explicit scope check so the reasoning is recorded
in the case.

The agent checks four signals in priority order:
1. Sensor tag (`cis-scope`, `cis-v8-scope`) — explicit scope marker
2. Detection rule tag (`cis-v8`) — authored as a CIS rule
3. Detection rule metadata key (`cis_safeguard:`) — authored with explicit safeguard mapping
4. Detection category prefix (`cis-`)

If none of those signals are present and no `cis-scope` / `cis-v8-scope` tag exists in the
org at all, the agent defaults to in-scope whenever the detection carries a `cis-v8` tag
(org-wide baseline assumption).

## Retention Guidance for CIS 8.10

CIS v8 Safeguard 8.10 mandates **at least 90 days** of audit-log retention. LC Insight
default retention meets this minimum. Strongly recommend extending via an S3/GCS output for:

- IG3 organisations
- Any organisation with regulatory overlay (HIPAA 6 yr, PCI 1 yr, SOX 7 yr, FedRAMP High multi-year)
- Organisations that need historical search beyond 90 days — pair with a SIEM output
  (Splunk, Chronicle, Elastic, Sentinel) for long-window analytics

## What CIS v8 Does NOT Cover via LC

The agent is instructed to NEVER claim coverage for these areas:

- **Control 12** — Network Infrastructure Management (LC is an endpoint tool, not a network device manager)
- **Control 14** — Security Awareness and Skills Training (no LC role)
- **Control 15** — Service Provider Management (no LC role)
- **Control 11** — Data Recovery itself (LC detects shadow-copy destruction but does not perform backups)
- **Safeguard 1.1** — active network discovery (LC is agent-based)
- **Safeguards 16.1–16.3, 16.6, 16.8–16.14** — SDLC / code-time controls
- **Safeguards 3.3, 3.6, 3.10, 3.11** — data encryption enforcement (OS/MDM capability)
- **Safeguards 6.3, 6.4, 6.5** — MFA enforcement (IdP capability)

## Files

- `cis-v8-compliance-reviewer.yaml` — top-level manifest (sync entry point)
- `hives/ai_agent.yaml` — agent definition with full CIS v8 SME prompt
- `hives/dr-general.yaml` — D&R trigger rule (validated with `limacharlie dr validate`)
- `hives/secret.yaml` — placeholder secrets (replace before deploy)

## Reference Documents

- `../cis-v8-limacharlie-mapping.md` — the authoritative CIS v8-to-LC capability map
- `../cis-v8-limacharlie-implementation.md` — the deployable D&R/FIM rules whose metadata
  the agent consumes
- `../cis-v8-attribution.md` — authoritative CIS Controls v8 source citation and
  verification status (ATTESTATION level)
