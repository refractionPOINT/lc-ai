# Investigation Plan Author - Drafts Investigation Engine Plans

An AI agent that writes Investigation Engine plan templates. A plan template is a YAML document that says which facts to
gather for a kind of alert, which combinations of facts prove a true or false positive, and what to respond with.
They are long to write by hand, so a person describes what they want (a detection, a case, a category or a goal) and
this agent drafts, validates and tests the template on the organization's real past alerts, then saves it as a
**draft**. A person reviews the draft and promotes it to active in the console. The agent never does.

## How It Works

```
A person starts the agent with a detection id, a case id, a detection category or a goal
      |
      v
investigate_authoring_kit (in pieces): template schema, authoring guide, managed examples, policy; investigate_operators: the org's operator catalog
      |
      v
Reads the real alerts (limacharlie CLI) and tries operators on real values (investigate_wave)
      |
      v
Drafts the template
      |
      v
investigate_validate_plan  <---- fix every error, read every warning
      |
      v
investigate_test_plan on real past alerts (closed cases give the expected answer)
      |   -- reads disagreements, unknowns and cost, refines (at most 5 cycles)
      v
investigate_save_plan (always status: draft) with a summary of what was tested
      |
      v
Reports: template name, test result, doubts, how to promote
```

## Running It

From the console, the Investigations templates page starts it with the detection or a goal. From the CLI:

```bash
limacharlie ai start-session --definition ie-plan-author \
  --data '{"detection_id": "<DETECTION_ID>"}'

limacharlie ai start-session --definition ie-plan-author \
  --data '{"goal": "Triage of encoded PowerShell detections", "detect_cat": "encoded-powershell", "template_name": "encoded-powershell-triage"}'
```

The context may carry `detection_id`, `case_id`, `detect_cat`, `goal` and `template_name`.

## Safety

- The agent saves only through `investigate_save_plan`, which always writes `status: draft`, refuses a template that
  validates with errors, never overwrites an active template and never touches a platform-managed one.
- A draft never runs on its own: it runs only through a plan test or a run a person starts, with autonomy capped at
  suggest. Promotion to active is a person's change in the console.
- The agent does not start runs and takes no response action. A test runs read-only operators with the agent's own API
  key and writes nothing.
- Alert content is treated as untrusted data.
- The API key is what bounds the agent. Give it the permissions below and no more.

## Prerequisites

- The Investigation Engine enabled for the organization
- An Anthropic API key
- A LimaCharlie API key with the following permissions:

| Permission | Why |
|-----------|-----|
| `ai_agent.operate` | Required by the hosted MCP server for every call |
| `org.get` | Basic org context |
| `insight.det.get` | Read detections |
| `insight.evt.get` | Read events; required by the investigation routes and by plan tests |
| `investigation.get` | Read cases, templates and runs |
| `investigation.set` | Run plan tests and operator waves |
| `investigation_plan.get` | Check whether a template name is free or is a draft |
| `investigation_plan.set` | Save the draft |
| the permission of every operator product it reads | Operators run with the agent's key: for example `mailsec.get` for `mailsec.*` operators and `cloudsec.get` for `entity.*` ones. The kit's operator rows say which products an operator reads |

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.
Before deploying, set `X-LC-OID` in `hives/ai_agent.yaml` to the organization id: the Investigation Engine tools come
from the hosted MCP server's `investigation_engine` profile, which takes the organization id in a header.

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `model` | `opus` | Claude model for drafting and reading test results |
| `max_turns` | `100` | Maximum tool calls per session |
| `max_budget_usd` | `4.0` | Cost cap per session (plan tests spend search and LLM steps on top, billed to the org) |
| `ttl_seconds` | `2700` | Hard timeout (45 minutes) |
| `one_shot` | `true` | Session terminates after the report |

## Files

- `hives/ai_agent.yaml` - AI agent definition with the authoring workflow
- `hives/secret.yaml` - Placeholder secrets (Anthropic key, LC API key)
