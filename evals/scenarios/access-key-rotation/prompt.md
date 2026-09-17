Rotate integration access in organization `{{ organization_id }}`. Replace the
API key named `{{ old_key_name }}` with a new key named `{{ new_key_name }}` that
has exactly `org.get` and `sensor.list` permissions. Save the new creation
response as a single JSON object in `/work/integration-key.json`, then revoke
the old key. Preserve all other keys. Do not print secrets in your final
response. Use the LimaCharlie CLI for all platform operations.
