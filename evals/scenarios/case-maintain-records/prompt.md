In organization `{{ organization_id }}`, maintain the case for the supplied
detection below. Reuse the case already linked to this detection if one exists;
otherwise create it with summary `{{ case_summary }}`. Do not create duplicate
cases or duplicate records.

Detection ID: `{{ detection_id }}`

```json
{{ detection_json }}
```

The completed case must have status `{{ target_status }}` and severity
`{{ target_severity }}`. Attach this entity exactly once:

- type: `{{ entity_type }}`
- value: `{{ entity_value }}`
- verdict: `{{ entity_verdict }}`
- entity note: `{{ entity_note }}`

Add exactly one private `{{ note_type }}` case note whose content is:

`{{ note_content }}`

Preserve all existing notes, detections, entities, and unrelated cases. Use the
LimaCharlie CLI for all LimaCharlie operations. When finished, return the case
number and detection ID and briefly describe the changes.
