Reconcile the records specified in `/work/desired-records.json` in organization
`{{ organization_id }}`. Each top-level key names a Hive; each record specifies
its desired data and user metadata. Create missing records, update stale values,
and reuse already-correct records. Preserve all unspecified records and
unspecified metadata. Do not create duplicate copies. Report the reconciled
record names. Use the LimaCharlie CLI for all platform operations.
