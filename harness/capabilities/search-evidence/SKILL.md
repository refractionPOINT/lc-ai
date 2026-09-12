---
name: search-evidence
description: "Query telemetry and detections, inspect event schemas, run bounded LCQL searches and retrieve IOC evidence."
---

# Search and telemetry evidence

Establish organization, absolute UTC time window, event source and requested output before searching. Compute timestamps with a date library or shell; confirm each API's units. Event timestamps commonly use milliseconds while query parameters commonly use seconds. Treat retention gaps and partial coverage explicitly.

Inspect `event types`, `event schema` or `schema` and a small representative event. Use the documented LCQL syntax; `ai generate-query` can draft it. Run `search validate` and inspect the result before execution, including after every edit. Use server-side time, sensor and field filters and aggregation when the question needs counts. Inspect `search estimate` when available for a broad query; narrow before repeated expensive scans.

Paginate using the returned cursor until absent or the stated budget is reached; a short page is not necessarily final. Record query, window, source IDs, truncation and coverage. Keep bulky events in artifacts and return concise evidence with stable identifiers. Use event ancestry/timeline commands for relationships rather than inventing a parent from similar process names. Bound streaming duration. IOC enrichments are source assertions with timestamps, not proof of compromise.

## References

Read the relevant bundled documentation before using unfamiliar schemas or operations. Paths are relative to the documentation docs root.

- `4-data-queries/query-cli.md`
- `4-data-queries/query-limits-and-performance.md`
- `4-data-queries/lcql-examples.md`
- `8-reference/event-schemas.md`
- `8-reference/authentication-resource-locator.md`
