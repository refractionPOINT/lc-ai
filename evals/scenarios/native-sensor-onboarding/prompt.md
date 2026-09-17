Onboard one native Linux endpoint sensor in organization `{{ organization_id }}`
using the evaluator deployment mechanism described in
`/work/endpoint-deployment.json`.

Create or reuse an installation key whose description is
`{{ installation_key_description }}`. Write the requested enrollment document,
wait for its status receipt, and use the returned sensor ID. Add the sensor tag
`{{ required_tag }}` and confirm the sensor is online with the LimaCharlie CLI.

Then use `limacharlie task request --command os_processes` against that sensor.
Write the complete JSON command output to `/work/process-observation.json`. The
response must include the harmless marker process named
`{{ marker_process_name }}`. Do not use a PID supplied by the evaluator and do
not modify other sensors or installation keys.

The deployment document is an evaluator-owned endpoint contract, not a
LimaCharlie API or substitute CLI. Use the LimaCharlie CLI for installation-key,
sensor, tag, and task operations.
