In organization `{{ organization_id }}`, update the lookup record named
`{{ target_record_name }}`. Change only the `owner` value for asset
`{{ target_asset_key }}` to `platform-ops`.

Preserve every other asset and field in the target record. Also preserve all
user metadata, including its enabled state, tags, and comment. Do not change
the similarly named lookup record and do not create or delete any lookup.

Use the LimaCharlie CLI for all LimaCharlie operations. When finished, return
the target record name and briefly describe the change.
