# ISO 27001 Compliance Reviewer — Automated ISO/IEC 27001:2022 Case Classification

An AI agent that acts as an ISO/IEC 27001:2022 Information Security Management System (ISMS)
subject-matter expert. When a security case is created on an ISMS-scoped asset (included in
the organization's Statement of Applicability, or "SoA"), it classifies the event against
specific Annex A controls and writes audit-grade case documentation that an accredited
certification-body auditor can use as evidence of control operating effectiveness during
surveillance or recertification audits.

> **Gap analysis** is handled by the `compliance-gap` skill (in the
> `lc-compliance` Claude Code plugin at `plugin/lc-compliance/`), not by
> a backend agent. This README covers only the case-reviewer agent.

This agent is **complementary** to an L1 SOC bot — it reviews for *compliance impact*, not
security severity. It runs in parallel to the normal case triage flow without interfering with it.

## How It Works

```
Detection fires on an ISMS-scope-tagged endpoint
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
Debounce check (one review per agent at a time)
        |
        v
AI agent session starts with case_number + oid
        |
        v
Scope check: is this case within the declared ISMS / SoA?
        ├── No  → add "not in scope" note, exit
        └── Yes → continue
        |
        v
Map event → Annex A control ID(s)
Classify compliance impact (iso-control-effective /
  iso-nonconformity / iso-in-scope-ops / iso-security-incident)
Write auditor-ready summary, conclusion, analysis notes
Tag case with compliance classification
        |
        v
Session terminates (one_shot)
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- Endpoints that should be in ISMS scope must carry a scope tag — one of (priority order):
  `isms-scope`, `iso-scope`, `iso-27001-scope`, `soa-included`. This is how the agent
  distinguishes ISMS-scoped from out-of-scope cases. Tag assets that the SoA includes as
  applicable.
- D&R rules from `../iso-27001-limacharlie-implementation.md` deployed, with the `iso-27001`
  tag and `metadata.iso_27001_control:` fields preserved. These provide the control mapping
  the agent consumes.
- A LimaCharlie API key with these permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context for CLI commands |
| `sensor.list` | List sensors to check ISMS-scope tagging |
| `sensor.get` | Read sensor tags for scope determination |
| `dr.list` | Read detection rule metadata (`iso_27001_control`) |
| `insight.det.get` | Read linked detections |
| `insight.evt.get` | Access event telemetry for correlation |
| `investigation.get` | Read cases |
| `investigation.set` | Update case summary/conclusion, add notes/entities/tags |
| `ext.request` | Call ext-cases |
| `sop.get` | Read org-specific ISO SOPs if present |
| `sop.get.mtd` | Read SOP metadata |
| `org_notes.read` | Read org notes (for embedded ISO guidance, if mirrored) |
| `ai_agent.operate` | Run AI agent sessions |

## Installation

```bash
# 1. Replace API-key placeholders in hives/secret.yaml
#    Anthropic key + a LimaCharlie API key with the permissions above

# 2. Deploy via the LC sync command
limacharlie sync --oid <your-oid> --push iso-27001-compliance-reviewer.yaml

# 3. Tag at least one endpoint as ISMS-scoped (otherwise the agent always early-exits)
limacharlie tag add --sid <scoped-sensor-sid> -t isms-scope --oid <your-oid>

# 4. Verify the ai_agent hive record exists
limacharlie hive get --hive-name ai_agent --key iso-27001-compliance-reviewer --oid <your-oid> --output yaml

# 5. Verify the trigger rule exists
limacharlie dr get --name iso-27001-compliance-reviewer-trigger --namespace general --oid <your-oid> --output yaml
```

## What the Agent Produces

For each ISMS-relevant case, the agent adds:

| Field | Content |
|---|---|
| **Summary** | One-paragraph auditor-readable overview: host, event, implicated Annex A control(s), compliance classification |
| **Conclusion** | Control mapping with exact IDs (e.g., "ISO/IEC 27001:2022 Annex A.8.15"), compliance classification with reasoning, and corrective-action recommendations if a nonconformity was found |
| **Analysis note** | Detailed markdown timeline with event data verbatim, scope-determination rationale, 2022↔2013 cross-reference where relevant, and correlating telemetry |
| **Entities** | IOCs tagged with ISO-relevant context (e.g., shared accounts → A.8.5, ISMS-scoped data paths → A.8.3, unsigned binaries → A.8.19) |
| **Tags** | One of: `iso-control-effective`, `iso-nonconformity`, `iso-in-scope-ops`, `iso-security-incident` |

## Compliance Classification Categories

| Tag | Meaning | Auditor Value |
|---|---|---|
| `iso-control-effective` | The detection firing IS the control operating effectively. Example: FIM_HIT on a monitored config file proves A.8.9 configuration-change detection is working; YARA_DETECTION proves A.8.7 is operating. | Positive evidence of control operating effectiveness for the audit window. |
| `iso-nonconformity` | The event reveals a failure to fulfill a control requirement. Example: Windows Security log cleared (A.8.15 nonconformity); sensor offline on SoA-included host (A.8.16 nonconformity); shared/generic account used (A.8.5 nonconformity). | Audit finding — requires corrective action under ISO 27001 clause 10.1. Distinct from a security incident. |
| `iso-in-scope-ops` | Expected administrative activity on an ISMS-scoped asset. Example: legitimate patching, documented privileged access. | Audit-trail completeness evidence for A.8.15 logging. |
| `iso-security-incident` | A potential information security incident on an ISMS-scoped asset. | Triggers A.5.24–A.5.27 incident-management process obligations. |

### Nonconformity vs. Security Incident

ISO 27001 explicitly distinguishes these two concepts, and their downstream workflows differ:

- A **nonconformity** is a control-design or control-operation failure — an audit finding
  requiring a corrective action (clause 10.1). Example: the configured FIM rule does not
  monitor an ISMS-scoped data directory.
- A **security incident** is an information-security event adverse enough to invoke the
  incident-management process (A.5.24–A.5.27). Example: confirmed malware detection on an
  SoA-included production server.

The agent uses `iso-nonconformity` for the former and `iso-security-incident` for the latter.

## Scope Determination — Why the SoA Matters

The agent's first step is an early-exit if the case is not within the declared ISMS scope.
This matters because:

- A generic case on an SoA-excluded asset does NOT need ISO 27001 documentation, and
  generating it dilutes the audit evidence
- ISO auditors examine scope declarations carefully — over-claiming scope creates questions
  about whether the SoA is being managed
- The SoA is the authoritative statement of which controls are applicable; tagging reflects
  that SoA decision per asset

The agent checks four signals in priority order:
1. Sensor tag — `isms-scope`, `iso-scope`, `iso-27001-scope`, or `soa-included`
2. Detection category prefix (`iso-`)
3. Detection rule tag (`iso-27001`)
4. Detection rule metadata key (`iso_27001_control:`, values like `'A.8.15'`)

Any ONE signal is enough to mark the case in-scope.

## Configuration

| Parameter | Value | Notes |
|---|---|---|
| `model` | `sonnet` | Sufficient for structured compliance classification. Escalate to `opus` if classification consistently hits ambiguity on multi-control events. |
| `max_turns` | `20` | Enough for scope check + context gathering + case update |
| `max_budget_usd` | `1.0` | Compliance review is a bounded task |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after review |
| `debounce_key` | `iso-27001-compliance-reviewer` | One review at a time; subsequent cases queue |
| Suppression | `10/min global` | Matches l1-bot default |

## ISO-Specific Coverage Notes

Coverage gaps the agent will acknowledge rather than claim (matches the mapping document):

- **A.6 People** (awareness, training, disciplinary, agreements) — policy/process, not endpoint
- **A.7 Physical** (A.7.1–A.7.14, facilities and equipment) — not endpoint
- **A.8.10 Certified erasure** — LC detects deletion but does not perform certified
  cryptographic erasure for end-of-life media
- **A.8.22 Network segregation enforcement** — LC detects violations; segregation is a
  network-device responsibility
- **A.8.23 Inline web filtering** — Detection-only; HTTP blocking requires a web proxy / SWG
- **A.8.26 / A.8.28 SDLC / secure coding at code time** — runtime monitoring only
- **A.8.8 Authoritative vulnerability scanning / pen testing** — LC is not a scanner
- **A.8.5 MFA enforcement** — IdP-level control; LC detects authentication events only

### Retention Note

ISO/IEC 27001:2022 does not prescribe a specific log-retention period. A.8.15 defers to the
organization's risk assessment. Three years is common industry practice driven by overlapping
regulatory regimes. LimaCharlie's default is 90 days Insight hot retention plus S3/GCS output
for longer archival — document your chosen retention period in the SoA. The agent will not
claim a specific retention figure.

### 2022 ↔ 2013 Transitioning Orgs

Many organizations are still mid-transition from ISO/IEC 27001:2013 to the 2022 edition.
The agent includes a short 2022↔2013 mapping note in its analysis output for common
controls (e.g., A.8.15 Logging ← 2013 A.12.4.1 / A.12.4.2 / A.12.4.3) so auditors working
off either edition can cross-reference.

## Coexistence with L1 SOC Bot

The trigger rule fires on the **same** `case_created` event that would trigger an l1-bot.
Both can run in parallel — they don't conflict because:

- L1 bot decides security classification (true/false positive, close, escalate)
- ISO reviewer decides compliance classification (control-effective / nonconformity /
  in-scope-ops / security-incident)
- Each writes to different case tags and notes
- The ISO reviewer explicitly does NOT modify security status or classification

If you want ISO review to **block** downstream SOC flow until completed, run this agent
first by adding a short `debounce_key` sleep at the start of your l1-bot prompt, or use an
org-level SOP that references ISO review output.

## Related Agents (Future)

This is the **real-time case reviewer** pattern. A periodic audit-reporter agent that
produces an auditor-ready summary of all ISMS-scoped activity across the surveillance-audit
window is a logical follow-on (similar to lc-ai's `customer-report` with a `168h_per_org`
schedule trigger), including control-sampling support for recertification-audit preparation.

## Files

- `iso-27001-compliance-reviewer.yaml` — top-level manifest (sync entry point)
- `hives/ai_agent.yaml` — agent definition with full ISO 27001 SME prompt
- `hives/dr-general.yaml` — D&R trigger rule
- `hives/secret.yaml` — placeholder secrets (replace before deploy)

## Reference Documents

- `../iso-27001-limacharlie-mapping.md` — the authoritative ISO 27001 Annex A → LC
  capability map
- `../iso-27001-limacharlie-implementation.md` — the deployable D&R, FIM, and Artifact
  Collection rules whose metadata the agent consumes
