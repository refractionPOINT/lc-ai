---
name: limacharlie-call
description: "**REQUIRED for ALL LimaCharlie operations** - list orgs, sensors, rules, detections, queries, and 186 functions. NEVER call LimaCharlie MCP tools directly. Use cases: 'what orgs do I have', 'list sensors', 'search IOCs', 'run LCQL query', 'create detection rule'. This skill loads function docs and delegates to sub-agent."
allowed-tools:
  - Task
  - Read
  - Bash
---

# LimaCharlie API Operations

Perform any LimaCharlie operation by dynamically loading function references.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **MCP Access** | Call `mcp__*` directly | Use `limacharlie-api-executor` sub-agent |
| **LCQL Queries** | Write query syntax manually | Use `generate_lcql_query()` first |
| **D&R Rules** | Write YAML manually | Use `generate_dr_rule_*()` + `validate_dr_rule_components()` |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `list_user_orgs` if needed) |

---

## How to Use

**Critical**: Always load the relevant function file BEFORE calling it. Never assume you know how just from the name and description.

### Step 1: Check Function Documentation

Before calling any function, **read its documentation** to get correct parameter names:
```
Read ./functions/{function-name}.md
```

**Why this matters:** Parameter names are often prefixed (e.g., `secret_name` not `name`). Using wrong names causes silent failures. Function docs have warnings for commonly confused parameters.

### Step 2: Spawn the Executor

All API operations go through the `limacharlie-api-executor` sub-agent:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="sonnet",
  prompt="Execute LimaCharlie API call:
    - Function: <function-name>
    - Parameters: {<params>}
    - Return: RAW | <what data you need>
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

**Return field is REQUIRED:**
- `RAW` → Complete API response
- `<instructions>` → Extract specific data (e.g., "Count of sensors", "Only hostnames")

**Script path is REQUIRED:** The agent needs this path to handle large API results. Skills have access to `{skill_base_directory}` (shown at the top of this prompt), which resolves to the plugin scripts.

### Parallel Calls

Spawn multiple agents in a single message:
```
Task(subagent_type="lc-essentials:limacharlie-api-executor", prompt="... Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh")
Task(subagent_type="lc-essentials:limacharlie-api-executor", prompt="... Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh")
```

## Functions by Use Case

### Getting Started
- `get_org_oid_by_name` - Convert org name to OID (preferred for single lookups)
- `list_user_orgs` - List all accessible orgs with OIDs (use when listing multiple orgs)

### Sensor Management
- `list_sensors` - **Primary function** for finding sensors. Supports `selector` (bexpr filter) and `online_only` parameters. Use this to find sensors by platform, hostname, tags, etc.
- `get_sensor_info` - Detailed info for a single sensor (when you already have the SID)
- `is_online` - Check if a specific sensor is online
- `get_online_sensors` - Returns only SIDs of online sensors (no filtering). Use `list_sensors` with `online_only: true` instead when you need to filter by platform/hostname/tags
- `add_tag` / `remove_tag` - Sensor tagging
- `isolate_network` / `rejoin_network` - Network isolation

**Finding sensors by platform:** Always use `list_sensors` with a selector:
```
list_sensors(oid, selector="plat == windows", online_only=true)
```
Do NOT use `get_online_sensors` + loop through `get_sensor_info`—that wastes API calls.

### Threat Hunting

**LCQL Workflow (mandatory):**

1. `generate_lcql_query` - Convert natural language to LCQL

2. **Choose execution method based on timeframe:**

   **Default: Use `run_lcql_query_free` (no cost)**
   - When user doesn't specify a timeframe
   - When user requests recent data (last hours/days/weeks within 30 days)
   - When timeframe is unspecified or vague ("recent", "lately", "this month")
   - Automatically uses past 30 days if no timeframe in query

   **Use `run_lcql_query` only for older data (may incur costs)**
   - When user explicitly requests data older than 30 days
   - **Required workflow:**
     1. `generate_lcql_query` - Generate the query
     2. `estimate_lcql_query` - Get cost estimate
     3. **Show cost to user and get confirmation**
     4. `run_lcql_query` - Execute only after user confirms

**Cost awareness:** Queries beyond 30 days may incur charges (~$0.01 per 200K events). Always use `estimate_lcql_query` and confirm with user before running `run_lcql_query`.

**Always offer a free alternative:** When showing cost estimates, also offer to run the query over the free 30-day window instead:
```
Estimated cost: $0.49 for 60-day query

Options:
1. Run full 60-day query ($0.49)
2. Run free 30-day query instead (no cost)
```

**Displaying LCQL queries:**
- **Always show the query before running it** - users must see what will be executed
- Use code blocks (backticks) since LCQL contains `|` which breaks markdown tables
- Format: `Query: \`-1h | * | NEW_PROCESS | / exists\``

Example workflow output:
```
Generated query: `-1h | * | NEW_PROCESS | / exists`
Explanation: Lists all process executions in the last hour

Running query...
[results]
```

**Other search functions:**
- `search_iocs` / `batch_search_iocs` - IOC searches
- `search_hosts` - Host searches
- `get_historic_events` - Historical telemetry
- `get_historic_detections` - Search detections by time
- `get_detection` - Get one detection by ID

### Live Response
- `get_processes` - Running processes
- `get_network_connections` - Active connections
- `get_autoruns` - Persistence mechanisms
- `dir_list` - Browse filesystem
- `yara_scan_*` - YARA scanning

### Detection Engineering
- `generate_dr_rule_detection` - AI-generate detection logic
- `generate_dr_rule_respond` - AI-generate response actions
- `validate_dr_rule_components` - Validate syntax
- `test_dr_rule_events` - Test against sample events
- `replay_dr_rule` - Test against historical data
- `set_dr_general_rule` - Deploy rules

### Configuration
- `list_outputs` / `add_output` / `delete_output` - Data outputs
- `list_secrets` / `set_secret` / `delete_secret` - Secrets
- `list_lookups` / `set_lookup` / `query_lookup` - Lookups
- `list_payloads` / `create_payload` / `get_payload` / `delete_payload` - Payloads

## Available Functions (186)

### Organization Management (9)
- `list_user_orgs` → `./functions/list-user-orgs.md`
- `get_org_oid_by_name` → `./functions/get-org-oid-by-name.md`
- `get_org_info` → `./functions/get-org-info.md`
- `create_org` → `./functions/create-org.md`
- `get_org_errors` → `./functions/get-org-errors.md`
- `dismiss_org_error` → `./functions/dismiss-org-error.md`
- `get_org_invoice_url` → `./functions/get-org-invoice-url.md`
- `get_billing_details` → `./functions/get-billing-details.md`
- `get_usage_stats` → `./functions/get-usage-stats.md`

### API Keys (3)
- `list_api_keys` → `./functions/list-api-keys.md`
- `create_api_key` → `./functions/create-api-key.md`
- `delete_api_key` → `./functions/delete-api-key.md`

### User Management (7)
- `list_org_users` → `./functions/list-org-users.md`
- `add_org_user` → `./functions/add-org-user.md`
- `remove_org_user` → `./functions/remove-org-user.md`
- `get_users_permissions` → `./functions/get-users-permissions.md`
- `add_user_permission` → `./functions/add-user-permission.md`
- `remove_user_permission` → `./functions/remove-user-permission.md`
- `set_user_role` → `./functions/set-user-role.md`

### Group Management (12)
- `list_groups` → `./functions/list-groups.md`
- `list_groups_detailed` → `./functions/list-groups-detailed.md`
- `create_group` → `./functions/create-group.md`
- `get_group_info` → `./functions/get-group-info.md`
- `delete_group` → `./functions/delete-group.md`
- `add_group_member` → `./functions/add-group-member.md`
- `remove_group_member` → `./functions/remove-group-member.md`
- `add_group_owner` → `./functions/add-group-owner.md`
- `remove_group_owner` → `./functions/remove-group-owner.md`
- `set_group_permissions` → `./functions/set-group-permissions.md`
- `add_org_to_group` → `./functions/add-org-to-group.md`
- `remove_org_from_group` → `./functions/remove-org-from-group.md`

### Sensor Operations (13)
- `list_sensors` → `./functions/list-sensors.md`
- `get_sensor_info` → `./functions/get-sensor-info.md`
- `delete_sensor` → `./functions/delete-sensor.md`
- `is_online` → `./functions/is-online.md`
- `get_online_sensors` → `./functions/get-online-sensors.md`
- `add_tag` → `./functions/add-tag.md`
- `remove_tag` → `./functions/remove-tag.md`
- `list_sensor_tags` → `./functions/list-sensor-tags.md`
- `is_isolated` → `./functions/is-isolated.md`
- `isolate_network` → `./functions/isolate-network.md`
- `rejoin_network` → `./functions/rejoin-network.md`
- `get_time_when_sensor_has_data` → `./functions/get-time-when-sensor-has-data.md`
- `upgrade_sensors` → `./functions/upgrade-sensors.md`

### Installation Keys (3)
- `list_installation_keys` → `./functions/list-installation-keys.md`
- `create_installation_key` → `./functions/create-installation-key.md`
- `delete_installation_key` → `./functions/delete-installation-key.md`

### Cloud Sensors (4)
- `list_cloud_sensors` → `./functions/list-cloud-sensors.md`
- `get_cloud_sensor` → `./functions/get-cloud-sensor.md`
- `set_cloud_sensor` → `./functions/set-cloud-sensor.md`
- `delete_cloud_sensor` → `./functions/delete-cloud-sensor.md`

### External Adapters (4)
- `list_external_adapters` → `./functions/list-external-adapters.md`
- `get_external_adapter` → `./functions/get-external-adapter.md`
- `set_external_adapter` → `./functions/set-external-adapter.md`
- `delete_external_adapter` → `./functions/delete-external-adapter.md`

### Live Sensor Commands (21)
- `get_processes` → `./functions/get-processes.md`
- `get_process_modules` → `./functions/get-process-modules.md`
- `get_process_strings` → `./functions/get-process-strings.md`
- `get_network_connections` → `./functions/get-network-connections.md`
- `get_os_version` → `./functions/get-os-version.md`
- `get_users` → `./functions/get-users.md`
- `get_services` → `./functions/get-services.md`
- `get_drivers` → `./functions/get-drivers.md`
- `get_autoruns` → `./functions/get-autoruns.md`
- `get_packages` → `./functions/get-packages.md`
- `get_registry_keys` → `./functions/get-registry-keys.md`
- `dir_list` → `./functions/dir-list.md`
- `dir_find_hash` → `./functions/dir-find-hash.md`
- `find_strings` → `./functions/find-strings.md`
- `yara_scan_process` → `./functions/yara-scan-process.md`
- `yara_scan_file` → `./functions/yara-scan-file.md`
- `yara_scan_directory` → `./functions/yara-scan-directory.md`
- `yara_scan_memory` → `./functions/yara-scan-memory.md`
- `reliable_tasking` → `./functions/reliable-tasking.md`
- `list_reliable_tasks` → `./functions/list-reliable-tasks.md`
- `delete_reliable_task` → `./functions/delete-reliable-task.md`

### Detection & Response Rules (12)
- `get_detection_rules` → `./functions/get-detection-rules.md`
- `list_dr_general_rules` → `./functions/list-dr-general-rules.md`
- `get_dr_general_rule` → `./functions/get-dr-general-rule.md`
- `set_dr_general_rule` → `./functions/set-dr-general-rule.md`
- `delete_dr_general_rule` → `./functions/delete-dr-general-rule.md`
- `list_dr_managed_rules` → `./functions/list-dr-managed-rules.md`
- `get_dr_managed_rule` → `./functions/get-dr-managed-rule.md`
- `set_dr_managed_rule` → `./functions/set-dr-managed-rule.md`
- `delete_dr_managed_rule` → `./functions/delete-dr-managed-rule.md`
- `get_mitre_report` → `./functions/get-mitre-report.md`
- `test_dr_rule_events` → `./functions/test-dr-rule-events.md`
- `replay_dr_rule` → `./functions/replay-dr-rule.md`

### False Positive Rules (4)
- `get_fp_rules` → `./functions/get-fp-rules.md`
- `get_fp_rule` → `./functions/get-fp-rule.md`
- `set_fp_rule` → `./functions/set-fp-rule.md`
- `delete_fp_rule` → `./functions/delete-fp-rule.md`

### Generic Rules (Hive) (4)
- `list_rules` → `./functions/list-rules.md`
- `get_rule` → `./functions/get-rule.md`
- `set_rule` → `./functions/set-rule.md`
- `delete_rule` → `./functions/delete-rule.md`

### Outputs (3)
- `list_outputs` → `./functions/list-outputs.md`
- `add_output` → `./functions/add-output.md`
- `delete_output` → `./functions/delete-output.md`

### Secrets (4)
- `list_secrets` → `./functions/list-secrets.md`
- `get_secret` → `./functions/get-secret.md`
- `set_secret` → `./functions/set-secret.md`
- `delete_secret` → `./functions/delete-secret.md`

### Lookups (5)
- `list_lookups` → `./functions/list-lookups.md`
- `get_lookup` → `./functions/get-lookup.md`
- `set_lookup` → `./functions/set-lookup.md`
- `query_lookup` → `./functions/query-lookup.md`
- `delete_lookup` → `./functions/delete-lookup.md`

### Playbooks (4)
- `list_playbooks` → `./functions/list-playbooks.md`
- `get_playbook` → `./functions/get-playbook.md`
- `set_playbook` → `./functions/set-playbook.md`
- `delete_playbook` → `./functions/delete-playbook.md`

### Extensions (8)
- `list_extension_configs` → `./functions/list-extension-configs.md`
- `get_extension_config` → `./functions/get-extension-config.md`
- `get_extension_schema` → `./functions/get-extension-schema.md`
- `set_extension_config` → `./functions/set-extension-config.md`
- `delete_extension_config` → `./functions/delete-extension-config.md`
- `subscribe_to_extension` → `./functions/subscribe-to-extension.md`
- `unsubscribe_from_extension` → `./functions/unsubscribe-from-extension.md`
- `list_extension_subscriptions` → `./functions/list-extension-subscriptions.md`

### Velociraptor DFIR (3)
- `list_velociraptor_artifacts` → `./functions/list-velociraptor-artifacts.md`
- `show_velociraptor_artifact` → `./functions/show-velociraptor-artifact.md`
- `collect_velociraptor_artifact` → `./functions/collect-velociraptor-artifact.md`

### Binary Library (Binlib) (7)
- `binlib_check_hash` → `./functions/binlib-check-hash.md`
- `binlib_get_hash_metadata` → `./functions/binlib-get-hash-metadata.md`
- `binlib_get_hash_data` → `./functions/binlib-get-hash-data.md`
- `binlib_tag` → `./functions/binlib-tag.md`
- `binlib_untag` → `./functions/binlib-untag.md`
- `binlib_search` → `./functions/binlib-search.md`
- `binlib_yara_scan` → `./functions/binlib-yara-scan.md`

### YARA Rules (4)
- `list_yara_rules` → `./functions/list-yara-rules.md`
- `get_yara_rule` → `./functions/get-yara-rule.md`
- `set_yara_rule` → `./functions/set-yara-rule.md`
- `delete_yara_rule` → `./functions/delete-yara-rule.md`

### Artifacts (2)
- `list_artifacts` → `./functions/list-artifacts.md`
- `get_artifact` → `./functions/get-artifact.md`

### Payloads (4)
- `list_payloads` → `./functions/list-payloads.md`
- `create_payload` → `./functions/create-payload.md`
- `get_payload` → `./functions/get-payload.md`
- `delete_payload` → `./functions/delete-payload.md`

### Event Schemas (5)
- `get_event_schema` → `./functions/get-event-schema.md`
- `get_event_schemas_batch` → `./functions/get-event-schemas-batch.md`
- `get_event_types_with_schemas` → `./functions/get-event-types-with-schemas.md`
- `get_event_types_with_schemas_for_platform` → `./functions/get-event-types-with-schemas-for-platform.md`
- `get_platform_names` → `./functions/get-platform-names.md`

### Queries (10)
- `run_lcql_query` → `./functions/run-lcql-query.md`
- `run_lcql_query_free` → `./functions/run-lcql-query-free.md`
- `validate_lcql_query` → `./functions/validate-lcql-query.md`
- `estimate_lcql_query` → `./functions/estimate-lcql-query.md`
- `analyze_lcql_query` → `./functions/analyze-lcql-query.md`
- `list_saved_queries` → `./functions/list-saved-queries.md`
- `get_saved_query` → `./functions/get-saved-query.md`
- `set_saved_query` → `./functions/set-saved-query.md`
- `delete_saved_query` → `./functions/delete-saved-query.md`
- `run_saved_query` → `./functions/run-saved-query.md`

### Searching & Detection History (8)
- `search_hosts` → `./functions/search-hosts.md`
- `search_iocs` → `./functions/search-iocs.md`
- `batch_search_iocs` → `./functions/batch-search-iocs.md`
- `get_historic_events` → `./functions/get-historic-events.md`
- `get_historic_detections` - Search by time: `(oid, start, end)` → `./functions/get-historic-detections.md`
- `get_detection` - Get one by ID: `(oid, detection_id)` → `./functions/get-detection.md`
- `get_event_by_atom` → `./functions/get-event-by-atom.md`
- `get_atom_children` → `./functions/get-atom-children.md`

### Investigations (5)
- `list_investigations` → `./functions/list-investigations.md`
- `get_investigation` → `./functions/get-investigation.md`
- `set_investigation` → `./functions/set-investigation.md`
- `delete_investigation` → `./functions/delete-investigation.md`
- `expand_investigation` → `./functions/expand-investigation.md`

### AI-Powered Generation (6)
- `generate_lcql_query` → `./functions/generate-lcql-query.md`
- `generate_dr_rule_detection` → `./functions/generate-dr-rule-detection.md`
- `generate_dr_rule_respond` → `./functions/generate-dr-rule-respond.md`
- `generate_sensor_selector` → `./functions/generate-sensor-selector.md`
- `generate_python_playbook` → `./functions/generate-python-playbook.md`
- `generate_detection_summary` → `./functions/generate-detection-summary.md`

### Validation Tools (2)
- `validate_dr_rule_components` → `./functions/validate-dr-rule-components.md`
- `validate_yara_rule` → `./functions/validate-yara-rule.md`

---

## Additional Resources

- **Detailed API usage**: [CALLING_API.md](../../CALLING_API.md)
- **Plugin architecture**: [ARCHITECTURE.md](../../ARCHITECTURE.md)

The `limacharlie-api-executor` agent handles large results (>100KB) automatically by downloading resource links and processing data according to your Return specification.
