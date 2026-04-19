# Case Investigator - Incremental Per-Case Investigator

An AI agent that investigates detections as ext-cases links them to a case, picking up
from its last checkpoint so it never re-investigates work it has already done.

## How It Works

```
ext-cases links a detection to a case (auto-grouping or manual)
      |
      v
Webhook adapter emits "case_detection_added" event
      |
      v
D&R rule matches (event=case_detection_added)
      |
      v
Suppression check (max 20/min across the org)
      |
      v
Debounce check (key = case-investigator-<case_number>)
      |   -- only one run per case at a time
      |   -- new detections mid-run queue and re-fire when the session ends
      v
Agent loads the case + its note timeline
      |
      v
Finds the last "case-investigator-checkpoint" note (if any)
      |
      v
Investigates every detection linked AFTER that checkpoint
      |
      v
Writes analysis notes, entities, telemetry; refreshes summary/conclusion
      |
      v
Writes a new checkpoint note: last_detect_id=<id>
      |
      v
Session terminates (one_shot)
```

## Checkpointing

Each run ends by adding a case note whose first line is an exact marker:

```
case-investigator-checkpoint: last_detect_id=<DET_ID>
```

On the next run, the agent reads the case timeline, finds the most recent checkpoint,
and only investigates detections linked after it. This means the agent can be
triggered repeatedly as new detections arrive without duplicating work or colliding
with itself (the `debounce_key` serializes runs per case).

## Recommendations

If the agent hits an error, confusing LimaCharlie behavior, or anything that prevents
it from doing its job well, it adds a note of `type: recommendation` describing:

- What went wrong (with exact errors/commands)
- Any workaround it found (or "None — blocked")
- A specific, actionable recommendation for owners — e.g. update this agent's
  prompt, change a skill, add an SOP, add an `org_note`, or file a CLI bug.

This is the primary feedback loop for improving the agent over time.

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) subscribed and configured
- An Anthropic API key
- A LimaCharlie API key with the following permissions:

| Permission | Why |
|-----------|-----|
| `org.get` | Basic org context |
| `sensor.list` | List sensors in the organization |
| `sensor.get` | Get detailed sensor information |
| `sensor.task` | Sensor tasking for timeline, process trees, network data |
| `dr.list` | Read D&R rules for detection context |
| `insight.det.get` | List and read detections |
| `insight.evt.get` | Read events for IOC searches and timeline queries |
| `investigation.get` | List and read cases and their timelines |
| `investigation.set` | Update cases, add notes, entities, telemetry |
| `ext.request` | Make requests to extensions (e.g. ext-cases) |
| `org_notes.*` | Read and write org notes |
| `sop.get` | Read SOPs for operational guidance |
| `sop.get.mtd` | Read SOP metadata |
| `ai_agent.operate` | Allow the agent to run AI agent sessions |

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the
[lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Claude model used for investigation |
| `max_turns` | `50` | Maximum CLI tool calls per run |
| `max_budget_usd` | `3.0` | Cost cap per run |
| `ttl_seconds` | `1800` | Hard timeout (30 minutes) |
| `one_shot` | `true` | Session terminates after completing |
| `debounce_key` | `case-investigator-{{ .event.case_number }}` | One run per case at a time; pending detections re-fire on completion |
| Suppression | `20/min` | Maximum AI agent invocations per minute across the org (global) |

## What the agent does NOT do

- It does not close, resolve, or reclassify cases — humans own the final verdict.
- It does not create new cases — that is the triage agent's job.
- It does not remove or re-link detections; it only investigates what is already
  attached to the case.

## Files

- `hives/ai_agent.yaml` - AI agent definition with incremental investigation prompt
- `hives/dr-general.yaml` - D&R rule triggering on `case_detection_added`
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
