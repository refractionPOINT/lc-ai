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

What actually stops the agent from doing harm, strongest first:

1. **The hive's promotion gate (a platform change that may not be deployed yet).** The `investigation_plan` hive
   refuses a write whose resulting status is `active` when the token is an API key; only a person signed in to the
   console can promote a template. An organization that manages active templates with infrastructure-as-code can opt
   out with the `allow-api-key-promotion` tag on its `investigation_policy/default` record, and **must not** if it runs
   this agent. Until your platform has this gate, nothing server-side stops this agent's key from writing
   `status: active`: check before relying on it.
2. **The save tool is draft-only.** `investigate_save_plan` always writes `status: draft`, refuses a template that
   validates with errors, never overwrites an active template, never touches a platform-managed one and replaces
   an existing draft only when `overwrite: true` is passed (the agent is told never to pass it). This binds the tool,
   not the key (see below).
3. **The key's permissions.** The agent also holds this API key as its `limacharlie` CLI credential and runs with
   `permission_mode: bypassPermissions`, so anything the key may do, the agent can do without going through the tool.
   Give it the minimal set below and nothing else.
4. **Prompt rules (defense in depth, not a guarantee).** The prompt tells the agent to save only through the tool, to
   never write `status: active`, never start runs or take response actions, and to treat alert content as untrusted.
   The agent reads alert content that an attacker may have written, so a crafted alert may try to talk it out of these
   rules. Do not count on them.

What the key can do beyond the tools, and why it matters:

- `investigation_plan.set` lets the key write any `investigation_plan` record, including through the CLI. Without the
  promotion gate that includes `status: active`, and an active template can be started by a rule or a case trigger,
  with `respond` steps if it has them.
- `investigation.set` lets the key start investigation runs (the same permission the plan tests and operator waves use),
  not only plan tests. A run started this way spends the org's budgets.
- Operator permissions (below) let the agent read the product data those operators read, with the CLI as well.

A draft never runs on its own: it runs only through a plan test or a run started by a person or by a key holding
`investigation.set`, with autonomy capped at suggest. A test runs read-only operators and writes nothing.

## Prerequisites

- The Investigation Engine enabled for the organization
- An Anthropic API key
- A dedicated LimaCharlie API key with only the following permissions. Each one's reach:

| Permission | What it allows | Why the agent needs it |
|-----------|----------------|------------------------|
| `ai_agent.operate` | Using the hosted MCP server | Required by the server for every call |
| `org.get` | Reading basic organization information | Org context for the CLI |
| `insight.det.get` | Reading detections | Reading the alerts to cover |
| `insight.evt.get` | Reading events | Required by every investigation route and by plan tests |
| `investigation.get` | Reading plan templates, the kit, operators and runs | Kit, validation, template list |
| `investigation.set` | Starting runs and tests | Plan tests and operator waves. **It also allows starting real runs from the CLI** |
| `investigation_plan.get` | Reading plan templates | Checking whether a name is free or is a draft |
| `investigation_plan.set` | Writing plan templates | Saving the draft. **It also allows writing any template, including `status: active` where the promotion gate is not deployed** |
| the read permission of every operator product it uses | Reading that product's data | Operators run with the agent's key: for example `mailsec.get` for `mailsec.*` operators and `cloudsec.get` for `entity.*` ones. The kit's operator rows say which products an operator reads. Grant only the products you want drafts for |

No other write permission is needed. In particular do not give it sensor tasking, D&R rule, output or API key
permissions. If you start the agent with a `case_id`, the key also needs whatever read access the cases extension
requires for that key; if you only start it with detection ids or goals, leave that out.

## Installation

Use the `lc-deployer` skill to install and manage this agent. See the [lc-essentials plugin](../../../marketplace/plugins/lc-essentials/) for details.
Nothing in `hives/ai_agent.yaml` needs editing for the organization: the MCP `X-LC-OID` header is `${LC_OID}`,
which the runtime fills with the organization the session runs in, and the MCP `X-LC-API-KEY` header is the same
`hive://secret/ie-plan-author` secret as `lc_api_key_secret`, resolved before the session starts. Only the two
placeholder secrets in `hives/secret.yaml` need real values. If the Investigation Engine tools cannot reach the org,
the agent's first tool call fails and it stops and says so, before spending its budget.

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
