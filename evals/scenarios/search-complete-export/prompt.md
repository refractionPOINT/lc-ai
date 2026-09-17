Export every telemetry event in organization `{{ organization_id }}` between
epoch seconds `{{ window_start }}` and `{{ window_end }}` that has all of these
properties:

- `event_type` is `LC_EVAL_EXPORT`
- `eval_trial_id` is `{{ trial_selector }}`
- `environment` is `production`

The supplied `event-schema.json` describes the event fields. Write
`/work/export.jsonl` with one JSON object per unique `eval_event_id`. Each line
must contain exactly `eval_event_id`, `environment`, and `message`. Include the
complete result set, even when the search response is paginated, and exclude
all other events. Use the LimaCharlie CLI for all LimaCharlie operations.

When finished, report the number of exported objects.
