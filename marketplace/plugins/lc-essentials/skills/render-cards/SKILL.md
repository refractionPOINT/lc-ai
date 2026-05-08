---
name: render-cards
description: Emit interactive UI cards into the LimaCharlie AI Terminal chat for see/browse intents — orgs, available commands. The frontend renders a clickable card inline rather than a text list. Use when the user says "show me my orgs", "list my orgs", "list orgs", "what orgs do I have", "what orgs do I have access to", "browse my orgs", "show orgs", "what can you do", "help", "what commands are available", "what slash commands are there", or any phrasing that suggests interacting with the data rather than hearing a count or summary. Cards are emitted by running `lc-card <card> [args]` via Bash — its stdout is the descriptor JSON the frontend parses.
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
- "Help", "what can you do", "what commands are there", "what slash commands are available"

**Do not use when**

- The user asked a counting / summarizing question ("how many orgs do I have?") — answer in text.
- The user is performing a mutating action ("create org", "delete sensor X") — use the LC CLI as normal.
- The user wants details about a *specific* named org — answer with `limacharlie org get` instead of emitting a list card.

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
lc-card org-list [--search QUERY]
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
