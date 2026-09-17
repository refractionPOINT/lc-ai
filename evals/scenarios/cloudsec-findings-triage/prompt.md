In organization `{{ organization_id }}`, export the complete Cloud Security
findings set for repository `{{ repository }}`, source `ingest`, and status
`open` to `/work/cloudsec-findings.csv`. Use the Cloud Security full-set CSV
export command so the file retains its native header and one row per finding.

Then assign exactly these finding IDs to `{{ target_owner }}` and accept their
risk:

{{ target_finding_ids }}

Suggested acceptance reason: `{{ acceptance_reason }}`. This text is advisory;
reason persistence is outside the task requirements because the backend does
not return it.

Do not change any other finding, owner, ticket, disposition, or Cloud Security
policy. These are supplied operational criteria; do not reassess which
findings should be accepted. Use the LimaCharlie CLI for all LimaCharlie
operations. When finished, report the exported row count and changed IDs.
