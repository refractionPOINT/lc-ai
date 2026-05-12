---
name: render-cards
description: Emit interactive UI cards into the LimaCharlie AI Terminal chat for see/browse intents. The frontend renders a clickable card inline rather than a text list. Trigger this skill whenever the user wants to *see/browse* a resource ("show me my <X>", "list <X>", "what <X> do I have", "browse <X>", "open <name>") for any of these resource types — orgs, secrets, D&R rules, FP rules, YARA rules, lookups, cloud sensors, SOPs, AI agents, AI skills, AI memories, playbooks, sensors, installation keys, API keys, outputs, adapters, artifacts, payloads, cases, vulnerabilities, detections, users, roles, extensions — or for the slash-command palette ("help", "what can you do", "what commands are available"). Cards are emitted by running `lc-card <card> [args]` via Bash — its stdout is the descriptor JSON the frontend parses.
allowed-tools:
  - Bash
---

# Interactive UI Cards

The LimaCharlie AI Terminal frontend can render interactive cards inline in
the chat when a tool_result's content matches a known descriptor shape. Use
this skill whenever the user wants to *see/browse* their data rather than
just hear a summary — the card is far more useful than a text list.

## When to use

**Trigger intents**

- "Show me my orgs", "list my orgs", "what orgs do I have access to", "browse orgs"
- "Show me my secrets / sensors / cases / detections / …", "list <resource>", "browse <resource>", "open <resource> <name>"
- "Help", "what can you do", "what commands are there", "what slash commands are available"

**Do not use when**

- The user asked a counting / summarizing question ("how many sensors do I have?") — answer in text.
- The user is performing a mutating action ("create secret", "delete sensor X") — use the LC CLI as normal.
- The user wants the *contents* of a record that the card doesn't surface (e.g. the raw secret value, the rule body). Cards intentionally omit sensitive payloads — fall back to the CLI for those.

## How to emit a card

Run `lc-card <card> [args]` via Bash. The script outputs the descriptor JSON
to stdout; the frontend extracts it from the tool_result content and renders
the matching component.

```bash
lc-card <card> [args...]
```

`lc-card` lives at `/opt/lc-essentials/bin/lc-card`, which is already on
`PATH` in the runner image. Run `lc-card --help` (or `lc-card <card> --help`)
for the up-to-date list of cards and their flags — the script is the source
of truth for the descriptor schema.

**Rules**

1. Don't try to construct the descriptor JSON yourself with `printf`/`echo` — let `lc-card` do it. The script is the only place that knows the current schema and version numbers.
2. After emitting the card, **do not also describe the data in text**. The card *is* the answer. A short framing sentence is fine ("Showing your accessible orgs."); a verbose list of every item duplicates what the card already shows.
3. The card's `summary` field is your scratch note for follow-up turns ("Showed 3 orgs matching `acme`"). Keep it brief and accurate so future turns can reason about what was shown.
4. **`oid` scoping.** Every resource card (everything except `org-list` and `help`) targets one org. Pass `--oid <OID>` whenever an active org is known from prompt context. If you omit it, the frontend silently swaps in an org picker before mounting the card — fine when the user has not yet picked an org, wasteful otherwise.

## Available cards

Each card section below documents its props as a JSON Schema fragment — the
exact shape the frontend validates after `lc-card` translates your CLI args
into the descriptor. Stay within the schema's bounds (e.g. `maxLength`,
`maximum`) to avoid validation failures that drop you back to a raw JSON
view.

### org-list

The user wants to see / browse their accessible orgs as an interactive list.
The card has its own pagination, inline detail view, and search. Don't worry
about pre-filtering or pre-paginating — emit it once and the user drives the
rest.

**Usage**

```bash
lc-card org-list [--search QUERY] [--limit N]
```

**Props schema**

```json
{
  "type": "object",
  "properties": {
    "search": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "description": "Substring matched against org name, code, OID, or description."
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "description": "Page size for the list view. Defaults to 5 when omitted."
    }
  },
  "additionalProperties": false
}
```

**Examples**

User: *"show me all my orgs"*

```bash
lc-card org-list
```

User: *"find orgs with 'acme' in the name"*

```bash
lc-card org-list --search acme
```

### help

The user wants a list of available local slash commands / shortcuts in the
AI Terminal.

**Usage**

```bash
lc-card help
```

**Props schema**

```json
{ "type": "object", "properties": {}, "additionalProperties": false }
```

**Example**

User: *"what can you do"*, *"help"*, *"what commands are there"*

```bash
lc-card help
```

### Resource cards (shared shape)

Every resource type below has a **detail** card (`lc-card <resource>`) and a
**list** card (`lc-card <resource>-list`). They share the same schema shape
across all resources — only the identifier flag changes per resource.

**Detail card schema**

```json
{
  "type": "object",
  "required": ["<id_field>"],
  "additionalProperties": false,
  "properties": {
    "oid": { "type": "string" },
    "<id_field>": { "type": "string", "minLength": 1 }
  }
}
```

(`case_number` is an `integer >= 1` instead of a string — the lone exception.)

**List card schema**

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "oid": { "type": "string" },
    "filter": { "type": "string" },
    "limit": { "type": "integer", "minimum": 1, "maximum": 50, "default": 5 }
  }
}
```

`filter` is a client-side, case-insensitive substring match — emit it once
and the user refines from there. Don't pre-filter by post-processing CLI
output and emitting a smaller filter; pass the user's term verbatim.

#### Catalog

| Subcommand          | Detail flag         | What it shows                                                  |
|---------------------|---------------------|----------------------------------------------------------------|
| `secret`            | `--name`            | Hive secret (vault entry — value not exposed by the card).     |
| `dnr-rule`          | `--name`            | Detection & Response rule.                                     |
| `fp-rule`           | `--name`            | False Positive rule.                                           |
| `yara-rule`         | `--name`            | YARA rule.                                                     |
| `lookup`            | `--name`            | Lookup table.                                                  |
| `cloud-sensor`      | `--name`            | Cloud Sensor configuration.                                    |
| `sop`               | `--name`            | Standard Operating Procedure.                                  |
| `ai-agent`          | `--name`            | AI agent (hive record).                                        |
| `ai-skill`          | `--name`            | AI skill / slug.                                               |
| `ai-memory`         | `--name`            | AI memory record (`--name` is the owning agent id).            |
| `playbook`          | `--name`            | Playbook hive record.                                          |
| `sensor`            | `--sid`             | Endpoint sensor (UUID).                                        |
| `installation-key`  | `--iid`             | Installation key (secret value is never surfaced).             |
| `api-key`           | `--name`            | API key metadata (raw key never surfaced).                     |
| `output`            | `--name`            | Data output route.                                             |
| `adapter`           | `--sensor-type`     | Ingestion adapter (e.g. `s3`, `syslog`, `wel`).                |
| `artifact`          | `--payload-id`      | Stored artifact.                                               |
| `payload`           | `--name`            | Payload definition.                                            |
| `case`              | `--case-number`     | Case (integer, sequential within the org).                     |
| `detection`         | `--detect-id`       | Detection atom from the detections pipeline.                   |
| `user`              | `--uid`             | User (accepts uid OR email — wrapper resolves both).           |
| `role`              | `--name`            | Access role (accepts display name OR GroupID).                 |
| `extension`         | `--name`            | Installed extension (`--name` is the machine name, not label). |
| `vulnerability`     | `--cve` OR `--sid`  | Polymorphic — see dedicated section below.                     |

**Examples**

User: *"show me my secrets"* (active org `abc-123`)

```bash
lc-card secret-list --oid abc-123
```

User: *"open the prod-aws secret"*

```bash
lc-card secret --oid abc-123 --name prod-aws
```

User: *"list my sensors with 'web' in the hostname"*

```bash
lc-card sensor-list --oid abc-123 --filter web
```

User: *"open case 42"*

```bash
lc-card case --oid abc-123 --case-number 42
```

User: *"show me user kirill@example.com"*

```bash
lc-card user --oid abc-123 --uid kirill@example.com
```

User: *"list cases"* but **no active org has been selected** — omit `--oid`; the
frontend will surface the org picker before mounting the card:

```bash
lc-card case-list
```

### vulnerability (polymorphic detail card)

The Vulnerability detail card is the only resource card with two distinct
shapes, picked via `oneOf` in the schema: a **CVE-scoped** view (one CVE
across the org) or an **endpoint-scoped** view (one sensor's vuln record).

**Usage**

```bash
lc-card vulnerability --oid OID --cve CVE-YYYY-NNNN    # CVE-scoped
lc-card vulnerability --oid OID --sid SENSOR-UUID      # endpoint-scoped
```

Pass exactly one of `--cve` / `--sid`. Passing both, or neither, is an
error — the script exits non-zero with a message rather than emitting an
invalid descriptor.

**Props schema**

```json
{
  "type": "object",
  "oneOf": [
    {
      "type": "object",
      "required": ["cve"],
      "additionalProperties": false,
      "properties": {
        "oid": { "type": "string" },
        "cve": { "type": "string", "minLength": 1 }
      }
    },
    {
      "type": "object",
      "required": ["sid"],
      "additionalProperties": false,
      "properties": {
        "oid": { "type": "string" },
        "sid": { "type": "string", "minLength": 1 }
      }
    }
  ]
}
```

The list card `vulnerability-list` follows the standard resource list shape
above — its `filter` matches against the CVE id.

## Versioning

The script always emits the latest known version of each card. If the
frontend doesn't recognize a `(component, version)` pair (older client,
new card you don't know about), it silently falls back to rendering the raw
JSON in a code block — older clients degrade gracefully.

## Relationship to the LC CLI

The general rule from `AUTOINIT.md` ("always use the limacharlie CLI via Bash")
still applies for everything else. This skill is the narrow exception for
"see/browse" intents where an interactive card UX is strictly better than a
text dump. When unsure, default to the CLI — a card you didn't need is wasted
UI; a CLI call you didn't need is a wasted turn.
