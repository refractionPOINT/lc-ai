# Ticketing Extension Constants (`ext-ticketing`)

**Source:** [ext-ticketing/internal/ticketing/](https://github.com/refractionPOINT/ext-ticketing)

## Ticket Status

| Status | Description |
|--------|-------------|
| `new` | Ticket just created (auto from detection) |
| `acknowledged` | Analyst has seen the ticket |
| `in_progress` | Active investigation underway |
| `escalated` | Escalated to senior analyst or team |
| `resolved` | Investigation complete, findings documented |
| `closed` | Final state, no further action |
| `merged` | Merged into another ticket (terminal) |

## Status Transitions (State Machine)

| From | Allowed To |
|------|------------|
| `new` | `acknowledged`, `in_progress`, `escalated`, `closed`, `merged` |
| `acknowledged` | `in_progress`, `escalated`, `closed`, `merged` |
| `in_progress` | `escalated`, `resolved`, `closed`, `merged` |
| `escalated` | `in_progress`, `resolved`, `closed`, `merged` |
| `resolved` | `closed`, `in_progress` (reopen), `merged` |
| `closed` | (terminal - no transitions) |
| `merged` | (terminal - no transitions) |

## Severity

Derived from detection priority (0-10) using configurable thresholds.

| Severity | Default Priority Range | SLA: MTTA | SLA: MTTR |
|----------|----------------------|-----------|-----------|
| `critical` | 8-10 | 15 min | 4 hours |
| `high` | 5-7 | 15 min | 12 hours |
| `medium` | 3-4 | 60 min | 24 hours |
| `low` | 0-2 | 100 min | ~47 hours |

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

Used for entities, telemetry references, and artifacts.

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
