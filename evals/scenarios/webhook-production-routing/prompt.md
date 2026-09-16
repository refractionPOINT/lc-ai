In organization `{{ organization_id }}`, configure the hosted JSON webhook
source named `{{ adapter_name }}` and an enabled automation rule named
`{{ rule_name }}`. The rule must report only events for which:

- the event type is `LC_EVAL_ROUTE`;
- `event/eval_trial_id` equals `{{ trial_selector }}`; and
- `event/environment` equals `production`.

Use report category `{{ report_category }}`. Configure the webhook output
`{{ output_name }}` to send detections in that category to
`{{ destination_url }}` with the supplied output secret. Preserve the existing
unrelated output exactly.

A controller feed sends documented sample events while you work; the adapter
may initially be absent. You may inspect ingestion and detections with the
LimaCharlie CLI. Use that CLI for every LimaCharlie operation. Final grading
stops the feed and sends fresh private positive and negative probes.

Return the adapter, rule, and output names with a concise completion statement.
