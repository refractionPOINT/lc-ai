---
name: render-cards
description: Emit interactive UI cards into the LimaCharlie AI Terminal chat for see/browse intents — orgs, slash commands, and every major LC resource (sensors, cases, detections, vulnerabilities, secrets, D&R rules, FP rules, YARA rules, lookups, cloud sensors, SOPs, AI agents/skills/memory, playbooks, installation keys, API keys, outputs, adapters, artifacts, payloads, users, roles, extensions). The frontend renders a clickable card inline rather than a text list or wall of fields. Use when the user says "show me my orgs", "list my orgs", "show secrets in org X", "open case 42", "show sensor abc-123", "list detections", "what can you do", "help", or any phrasing that suggests interacting with the data rather than hearing a count or summary. Cards are emitted by running `lc-card <card> [args]` via Bash — its stdout is the descriptor JSON the frontend parses.
allowed-tools:
  - Bash
---

# Interactive UI Cards

The LimaCharlie AI Terminal frontend can render interactive cards inline in
the chat when a tool_result's content matches a known descriptor shape. Use
this skill whenever the user wants to *see/browse* their data rather than
just hear a summary — the card is far more useful than a text list or a
verbose dump of fields.

## When to use

**Trigger intents**

- Org browsing — "show me my orgs", "list my orgs", "what orgs do I have access to"
- Slash-command help — "help", "what can you do", "what commands are there"
- Resource browsing — "show secrets in org X", "list D&R rules", "show me sensors", "list cases"
- Single-resource inspection — "open case 42", "show sensor abc-123", "what's in secret API_KEY"

**Do not use when**

- The user asked a counting / summarizing question ("how many sensors are offline?") — answer in text.
- The user is performing a mutating action ("create secret", "delete sensor X") — use the LC CLI as normal.
- The user explicitly asks for raw YAML/JSON — they want pipe-able data, not a card.

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
2. After emitting the card, **do not also describe the data in text**. The card *is* the answer. A short framing sentence is fine ("Showing case #42."); a verbose list of every field duplicates what the card already shows.
3. The card's `summary` field is your scratch note for follow-up turns ("Showed 3 secrets matching `prod`"). Keep it brief and accurate so future turns can reason about what was shown.
4. Resource cards require `--oid <oid>` — every card except `org-list` and `help` is scoped to a single organization. The user must have already specified which org they're working in (see `AUTOINIT.md`).
5. List vs single: pick the *list* card when the user wants to browse / find / filter; pick the *single* card when the user names a specific resource ("show case 42", "open secret API_KEY"). When in doubt, list — the user can drill in from the card UI.

## Card catalog

The cards are grouped by resource family. Every resource family follows the
same two-card pattern unless noted:

- **`<resource>`** — single-record view, requires `--oid` plus the resource's
  unique identifier (usually `--name`, sometimes `--sid`, `--iid`,
  `--payload-id`, `--case-number`, `--cve`, `--detect-id`, `--uid`,
  `--sensor-type`).
- **`<resource>-list`** — paginated list view, requires `--oid`, optional
  `--filter STR` (case-insensitive substring) and `--limit N` (1-50,
  default 5).

The list-card schema is identical across families:

```json
{
  "type": "object",
  "required": ["oid"],
  "properties": {
    "oid":    { "type": "string", "minLength": 1 },
    "filter": { "type": "string" },
    "limit":  { "type": "integer", "minimum": 1, "maximum": 50, "default": 5 }
  },
  "additionalProperties": false
}
```

The single-record schema is `{oid, <id_field>}`, both required, both
non-empty strings (or integer for `case_number`) — see the per-card sections
for the exact id field name.

### Generic UI

#### `org-list`

User wants to see / browse their accessible orgs.

```bash
lc-card org-list [--search QUERY]
```

```json
{
  "type": "object",
  "properties": {
    "search": { "type": "string", "minLength": 1, "maxLength": 200 },
    "limit":  { "type": "integer", "minimum": 1, "maximum": 100 }
  },
  "additionalProperties": false
}
```

Examples:

- *"show me all my orgs"* → `lc-card org-list`
- *"find orgs matching acme"* → `lc-card org-list --search acme`

#### `help`

User wants a list of local slash commands / shortcuts in the AI Terminal.

```bash
lc-card help
```

```json
{ "type": "object", "properties": {}, "additionalProperties": false }
```

Examples: *"what can you do"*, *"help"*, *"what commands are there"*.

### Hive resources (single + list, keyed by `--name`)

These all follow the standard `(oid, name)` / `(oid, [filter, limit])` shape.

| Card subcommand     | Single component         | List component               | `--name` is                                 |
| ------------------- | ------------------------ | ---------------------------- | ------------------------------------------- |
| `secret`            | `SecretCard`             | `SecretListCard`             | secret name (hive record name)              |
| `dnr-rule`          | `DnrRuleCard`            | `DnrRuleListCard`            | D&R rule name                               |
| `fp-rule`           | `FpRuleCard`             | `FpRuleListCard`             | FP rule name                                |
| `yara-rule`         | `YaraRuleCard`           | `YaraRuleListCard`           | YARA rule name                              |
| `lookup`            | `LookupCard`             | `LookupListCard`             | lookup name                                 |
| `cloud-sensor`      | `CloudSensorCard`        | `CloudSensorListCard`        | cloud sensor name                           |
| `sop`               | `SopCard`                | `SopListCard`                | SOP name                                    |
| `ai-agent`          | `AiAgentCard`            | `AiAgentListCard`            | AI agent name                               |
| `ai-skill`          | `AiSkillCard`            | `AiSkillListCard`            | AI skill slug                               |
| `ai-memory`         | `AiMemoryCard`           | `AiMemoryListCard`           | owning agent ID                             |
| `playbook`          | `PlaybookCard`           | `PlaybookListCard`           | playbook name                               |
| `api-key`           | `ApiKeyCard`             | `ApiKeyListCard`             | key friendly name (raw key is NEVER passed) |
| `output`            | `OutputCard`             | `OutputListCard`             | output name                                 |
| `payload`           | `PayloadCard`            | `PayloadListCard`            | payload name                                |
| `role`              | `RoleCard`               | `RoleListCard`               | GroupID or display name                     |
| `extension`         | `ExtensionCard`          | `ExtensionListCard`          | machine name (e.g. `cases`, `artifact`)     |

Examples:

- *"show me the API_TOKEN secret in acme"* → `lc-card secret --oid OID --name API_TOKEN`
- *"list secrets in acme matching prod"* → `lc-card secret-list --oid OID --filter prod`
- *"show D&R rules"* → `lc-card dnr-rule-list --oid OID`
- *"open playbook nightly-scan"* → `lc-card playbook --oid OID --name nightly-scan`

### Endpoints & credentials

#### `sensor` / `sensor-list`

Single sensor is keyed by `--sid` (the sensor UUID).

```bash
lc-card sensor --oid <oid> --sid <sid>
lc-card sensor-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema: `{oid: string, sid: string}` (both required).
List filter matches hostname / sid / tags.

#### `installation-key` / `installation-key-list`

Keyed by `--iid`. The frontend deliberately never accepts the raw key
material — that's stripped by Ajv.

```bash
lc-card installation-key --oid <oid> --iid <iid>
lc-card installation-key-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema: `{oid: string, iid: string}`.

#### `api-key` / `api-key-list`

Already covered in the hive-resources table above (keyed by `--name`). Raw
key material is never accepted — the card fetches metadata only.

### Data flow

#### `output` / `output-list`

Standard `--name` shape (see hive-resources table). List filter spans name /
module / stream.

#### `adapter` / `adapter-list`

Single adapter is keyed by `--sensor-type` (the ingestion identifier:
`s3`, `syslog`, `wel`, ...).

```bash
lc-card adapter --oid <oid> --sensor-type <type>
lc-card adapter-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema: `{oid: string, sensor_type: string}`.

#### `artifact` / `artifact-list`

Keyed by `--payload-id`.

```bash
lc-card artifact --oid <oid> --payload-id <pid>
lc-card artifact-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema: `{oid: string, payload_id: string}`.

#### `payload` / `payload-list`

Standard `--name` shape (in the hive-resources table). Note: distinct from
`artifact` — payloads are reusable named blobs, artifacts are
per-collection.

### Workflow

#### `case` / `case-list`

Single case is keyed by `--case-number` (a positive **integer**, not a
string).

```bash
lc-card case --oid <oid> --case-number 42
lc-card case-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema: `{oid: string, case_number: integer (minimum 1)}`.
List filter spans summary / assignees / tags.

#### `vulnerability` / `vulnerability-list`

The single-card schema is **polymorphic**: scope it to a CVE *or* to a
sensor, never both. Pass either `--cve` or `--sid`, never both, never
neither.

```bash
lc-card vulnerability --oid <oid> --cve CVE-2024-1234
lc-card vulnerability --oid <oid> --sid <sid>
lc-card vulnerability-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema (`oneOf`):

```json
{
  "type": "object",
  "oneOf": [
    {
      "required": ["oid", "cve"],
      "properties": {
        "oid": { "type": "string", "minLength": 1 },
        "cve": { "type": "string", "minLength": 1 }
      },
      "additionalProperties": false
    },
    {
      "required": ["oid", "sid"],
      "properties": {
        "oid": { "type": "string", "minLength": 1 },
        "sid": { "type": "string", "minLength": 1 }
      },
      "additionalProperties": false
    }
  ]
}
```

List filter matches CVE id only (the API doesn't expose richer fields).

#### `detection` / `detection-list`

Single detection is keyed by `--detect-id` (opaque atom ID from the
detections pipeline).

```bash
lc-card detection --oid <oid> --detect-id <id>
lc-card detection-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema: `{oid: string, detect_id: string}`. List filter is
applied client-side to a pre-fetched page (the detections API has no
free-text search) across category / source / rule / hostname / sid.

### Access

#### `user` / `user-list`

Single user is keyed by `--uid` (accepts a uid *or* an email; the frontend
resolves against both).

```bash
lc-card user --oid <oid> --uid alice@example.com
lc-card user-list --oid <oid> [--filter STR] [--limit N]
```

Single-card schema: `{oid: string, uid: string}`.

#### `role` / `role-list`

Already covered in the hive-resources table (keyed by `--name`, accepts
either GroupID or display name).

### Extensions

#### `extension` / `extension-list`

In the hive-resources table. `--name` is the machine name (e.g. `cases`,
`artifact`), not the human label shown in the web UI.

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
