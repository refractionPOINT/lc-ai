# Cases Extension Constants (`ext-cases`)

**Source:** [ext-cases/internal/cases/](https://github.com/refractionPOINT/ext-cases)

## Case Status

| Status | Description |
|--------|-------------|
| `new` | Case just created (auto from detection) |
| `in_progress` | Active investigation underway |
| `resolved` | Investigation complete, findings documented |
| `closed` | Final state, no further action |

## Status Transitions (State Machine)

| From | Allowed To |
|------|------------|
| `new` | `in_progress`, `closed` |
| `in_progress` | `resolved`, `closed` |
| `resolved` | `closed` |
| `closed` | `in_progress` (reopen) |

## Severity

Initially derived from detection priority (0-10) using configurable thresholds. Severity can also be updated manually via `limacharlie case update --severity <level>`.

| Severity | Default Priority Range | SLA: MTTA | SLA: MTTR |
|----------|----------------------|-----------|-----------|
| `critical` | 8-10 | 15 min | 4 hours |
| `high` | 5-7 | 15 min | 12 hours |
| `medium` | 3-4 | 60 min | 24 hours |
| `low` | 0-2 | 100 min | ~47 hours |
| `info` | *(manual only)* | 480 min | 7 days |

## Classification

| Classification | Description |
|----------------|-------------|
| `pending` | Not yet classified (default) |
| `true_positive` | Confirmed real threat |
| `false_positive` | Confirmed benign |

## Entity Types

| Type | Description |
|------|-------------|
| `ip` | IP address |
| `domain` | Domain name |
| `hash` | File hash (MD5, SHA1, SHA256) |
| `url` | Full URL |
| `user` | Username or user account |
| `email` | Email address |
| `file` | File path or file name |
| `process` | Process name or path |
| `registry` | Registry key or value (Windows) |
| `other` | Any other entity type |

## Verdict

Used for all evidence types: detections, entities, telemetry references, and artifacts.

| Verdict | Description |
|---------|-------------|
| `malicious` | Confirmed malicious |
| `suspicious` | Warrants further investigation |
| `benign` | Confirmed safe |
| `unknown` | Cannot determine |
| `informational` | Context only, not a threat indicator |

## Note Types

| Type | Description |
|------|-------------|
| `general` | General investigation notes |
| `analysis` | Technical analysis findings |
| `remediation` | Remediation steps taken or recommended |
| `escalation` | Escalation rationale and context |
| `handoff` | Shift handoff or analyst transition notes |
| `to_stakeholder` | Notes/communications sent TO external stakeholders (e.g. customers, management) |
| `from_stakeholder` | Notes/communications received FROM external stakeholders |

## Note Visibility

Notes support an `is_public` boolean flag. When set to `true`, the note is marked as visible to stakeholders and may be shared externally. Defaults to `false` (internal only).

## Tags

Cases support arbitrary string tags for custom categorization.

| Constraint | Value |
|-----------|-------|
| Max tag length | 128 characters |
| Max tags per case | 50 |
| Case sensitivity | Case-preserved, case-insensitive dedup |
| Allowed characters | Any printable character (no control chars) |

Tags are managed via the `update` endpoint by replacing the full tag array.
Filtering by tag is supported in the list endpoint with `--tag` flag.

## Markdown Support

The `summary`, `conclusion`, and note `content` fields all support **Markdown** formatting. Use headers, bullet lists, tables, and code blocks for structured, readable reports.
