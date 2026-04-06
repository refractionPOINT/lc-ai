# LimaCharlie Maintainer — Daily Org Self-Improvement

An autonomous agent that runs daily to make your LimaCharlie organization better. It reviews AI session transcripts, analyzes cases, engineers FP rules for noisy detections, identifies detection gaps, and audits org hygiene — all guided by a SOUL.md SOP that defines your security philosophy.

## How It Works

```
Schedule: every 24 hours
      |
      v
Load SOUL.md SOP (guiding principles)
      |
      v
PART 1: Review AI Sessions
  - List recent sessions (success/fail/timeout/over-budget)
  - Fetch transcripts for failures to diagnose root causes
  - Identify broken agents, inefficient prompts, missing permissions
      |
      v
PART 2: Review Cases
  - Dashboard + 24h summary
  - Identify FP patterns (same detection closed as FP 3+ times)
  - Clean stale lock tags on stuck cases
  - Flag SLA violations and unresolved TPs
      |
      v
PART 3: FP Rule Engineering
  - For noisy FP patterns: query sample detections
  - Identify benign commonality (path, cmdline, parent, user)
  - Create targeted FP rules tagged 'maintainer-generated'
      |
      v
PART 4: Detection Gap Analysis
  - Inventory D&R rules, FP rules, sensors
  - Compare against SOUL.md priorities
  - Create rules for straightforward gaps
  - Document complex gaps for human review
      |
      v
PART 5: Org Hygiene
  - Verify outputs are configured
  - Check extension subscriptions
  - Review audit log for unusual admin activity
  - Check integrity/exfil rules
      |
      v
PART 6: Daily Maintenance Report
  - Create case with comprehensive findings
  - Tag: maintainer-report, daily-report
  - Close case
  - Session terminates (one_shot)
```

## The SOUL.md SOP

The SOUL (Security Operations & Unified Logic) is a document you store in the `sop` hive under the key `SOUL`. It tells the maintainer what your organization cares about — security philosophy, priorities, risk tolerance, and operational preferences.

On first run, if SOUL.md doesn't exist, the agent creates a starter template and exits. Customize it before the next run.

**Example SOUL priorities:**
- "Aggressively tune FPs — analyst fatigue is our biggest risk"
- "Focus detection coverage on lateral movement and credential theft"
- "Never auto-create containment rules — always flag for human review"
- "Our critical assets are tagged `critical` — prioritize their coverage"

## Finding Reports

```bash
limacharlie case list --tag maintainer-report --oid <oid> --output yaml
```

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed
- An Anthropic API key
- A LimaCharlie API key with the permissions below
- A `SOUL` SOP in the sop hive (created automatically on first run)

## API Key Permissions

Create an API key named `limacharlie-maintainer` with:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `sensor.list` | Sensor coverage inventory |
| `sensor.get` | Sensor detail for gap analysis |
| `dr.list` | List D&R rules for coverage analysis |
| `dr.set` | Create D&R rules for detection gaps |
| `fp.list` | List FP rules |
| `fp.set` | Create FP rules for noisy detections |
| `insight.det.get` | Query historical detections |
| `insight.evt.get` | Query events for FP pattern analysis |
| `investigation.get` | List/read cases, dashboard, report summary |
| `investigation.set` | Create report cases, clean stale tags |
| `ext.request` | Invoke extensions |
| `output.list` | Audit output configurations |
| `audit.get` | Review audit logs for hygiene |
| `integrity.list` | Check integrity monitoring rules |
| `exfil.list` | Check exfil prevention rules |
| `org_notes.*` | Read and write org notes |
| `sop.get` | Read SOUL.md and other SOPs |
| `sop.get.mtd` | Read SOP metadata |
| `sop.set` | Create starter SOUL.md on first run |
| `ai_agent.get` | List AI sessions and transcripts |
| `ai_agent.operate` | Allow the agent to run |

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Deep reasoning for analysis and rule engineering |
| `max_turns` | `50` | Many tool calls needed across all review phases |
| `max_budget_usd` | `5.0` | Cost cap per daily run |
| `ttl_seconds` | `900` | Hard timeout (15 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| Schedule | `24h_per_org` | Runs once per day |

## Files

- `hives/ai_agent.yaml` - Agent definition with full maintenance prompt
- `hives/dr-general.yaml` - D&R rule: triggers on `24h_per_org` schedule event
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
