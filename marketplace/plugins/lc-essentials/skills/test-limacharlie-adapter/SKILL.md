---
name: test-limacharlie-adapter
description: Deploy a temporary LimaCharlie Adapter on the local Linux or Mac OS host for testing log ingestion. Downloads the adapter, auto-detects log sources, and streams them to your LimaCharlie organization.
allowed-tools:
  - Task
  - Bash
  - Read
  - AskUserQuestion
  - Skill
---

# Test LimaCharlie Adapter

Deploy a temporary LimaCharlie Adapter on the local Linux or Mac OS host for testing log ingestion. The adapter streams local logs to your LimaCharlie organization in real-time.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### API Access Pattern

All LimaCharlie API calls go through the `limacharlie-api-executor` sub-agent:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: <function-name>
    - Parameters: {<params>}
    - Return: RAW | <extraction instructions>
    - Script path: {skill_base_directory}/../../scripts/analyze-lc-result.sh"
)
```

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **MCP Access** | Call `mcp__*` directly | Use `limacharlie-api-executor` sub-agent |
| **LCQL Queries** | Write query syntax manually | Use `generate_lcql_query()` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `list_user_orgs` if needed) |
| **Parsing** | Write Grok patterns manually | Use `parsing-helper` skill (identifies timezone requirements) |

---

This skill includes a **helper script** (`lc-adapter-helper.sh`) that handles all platform detection, downloading, and process management automatically.

## When to Use

Use this skill when:

- **Testing log ingestion**: Validate that logs flow correctly into LimaCharlie
- **Testing D&R rules on logs**: Write and test detection rules against real log data
- **Exploring adapter behavior**: Understand how adapters forward log data
- **Development and debugging**: Test adapter configurations before production deployment
- **Learning**: Explore LimaCharlie's log ingestion capabilities hands-on

## What This Skill Does

This skill performs a multi-phase deployment:

1. **Phase 1 - Installation Key**: Creates or finds an existing "Test Adapter" installation key in your selected LimaCharlie organization
2. **Phase 2 - Sample Collection & Parsing**: Captures sample logs and invokes the `parsing-helper` skill to generate and validate Grok patterns
3. **Phase 3 - Adapter Deployment**: Downloads the appropriate adapter binary for your platform and runs it with logs piped to stdin, using the parsing configuration from Phase 2
4. **Phase 4 - Verification**: Verifies the adapter is connected and appearing as a sensor
5. **Phase 5 - View Data**: Query and view the parsed ingested data

The adapter:
- Runs in the background (non-blocking)
- Uses a unique temp directory (avoids file conflicts)
- Streams logs in real-time (`journalctl -f` or `tail -f` on Linux, `log stream` on Mac OS)
- Does NOT require root/sudo
- Cleans up automatically when stopped

## Required Information

Before starting, ensure you have:

- **LimaCharlie organization**: Select from your available orgs or create a new one
- **Linux or Mac OS host**: Supports Linux x64, Mac Intel (x64), and Mac Apple Silicon (arm64)
- **Internet access**: Required to download the adapter binary
- **Log access**: On Linux with journalctl, uses system journal (preferred). On Linux without journalctl, needs read access to log files in `/var/log`. On Mac OS, uses the unified logging system via `log stream`

## How to Use

### Pre-requisite: Select an Organization

First, get the list of available organizations:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW"
)
```

This returns your available organizations. Use AskUserQuestion to let the user select one, or if they need a new org, use the `limacharlie-call` skill to create one with `create_org`.

### Phase 1: Get or Create Installation Key

Check for existing "Test Adapter" installation key:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_installation_keys
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\"}
    - Return: Look for key with description 'Test Adapter' and return its iid"
)
```

**If "Test Adapter" key exists**: Extract the `iid` value from the response.

**If not exists**: Create one:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: create_installation_key
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"description\": \"Test Adapter\", \"tags\": [\"test-adapter\", \"temporary\"]}
    - Return: The iid of the created key"
)
```

Save the returned `iid` for later phases.

> **IMPORTANT**: For adapters, the `installation_key` parameter is the **IID (UUID format)**, NOT the full base64-encoded key used by EDR sensors.

### Phase 2: Sample Collection & Parsing Configuration (MANDATORY)

> **DO NOT SKIP THIS PHASE.** You MUST use the `parsing-helper` skill to generate parsing configuration. Never write Grok patterns manually - the parsing-helper will identify timezone requirements and other critical settings.

Before deploying the adapter, capture sample logs and configure parsing rules. This ensures your logs are properly parsed when they arrive in LimaCharlie.

**Step 1**: Copy the helper script to `/tmp`:

```bash
cp plugins/lc-essentials/skills/test-limacharlie-adapter/lc-adapter-helper.sh /tmp/ && chmod +x /tmp/lc-adapter-helper.sh
```

**Step 2**: Capture sample logs to a file:

```bash
/tmp/lc-adapter-helper.sh sample 20 > /tmp/lc-adapter-samples.txt
cat /tmp/lc-adapter-samples.txt
```

**Step 3**: Read the sample file content using the Read tool to have it in context.

**Step 4**: Invoke the parsing-helper skill:

```
Skill("parsing-helper")
```

When parsing-helper asks for sample logs, provide the captured samples from `/tmp/lc-adapter-samples.txt` that are already in context. Inform parsing-helper this is for a **One-off/USP Adapter** (local adapter).

The parsing-helper will:
- Analyze the sample logs
- Generate appropriate Grok pattern
- Test the pattern with `validate_usp_mapping`
- Provide CLI config format for the mapping

**Step 5**: Extract the mapping parameters from parsing-helper output.

The parsing-helper will output mapping parameters like:
- `--grok '<PATTERN>'`
- `--event-type '<PATH>'`
- `--event-time '<PATH>'`
- `--event-time-tz '<TIMEZONE>'` (when timestamp format lacks timezone info)
- `--hostname-path '<PATH>'`

Save these for use in the adapter setup (Phase 3).

### Phase 3: Setup and Start the Adapter (Using Helper Script)

The helper script (already copied in Phase 2) handles platform detection, downloading, and running the adapter.

**Step 1**: Run setup with OID, IID, and mapping config from Phase 2:

```bash
/tmp/lc-adapter-helper.sh setup <OID> <IID> \
  --grok '<GROK_PATTERN_FROM_PARSING_HELPER>' \
  --event-type '<EVENT_TYPE_PATH>' \
  --event-time '<EVENT_TIME_PATH>' \
  --event-time-tz '<TIMEZONE>' \
  --hostname-path '<HOSTNAME_PATH>'
```

> **Note**: Include `--event-time-tz` when the parsing-helper indicates it's needed (e.g., for SYSLOGTIMESTAMP which lacks timezone info).

This command automatically:
- Detects your platform (Linux/Mac, architecture)
- Detects log source (journalctl, log files, or unified logging)
- Creates a temp directory
- Downloads the correct adapter binary
- Creates the launch script with parsing configuration
- Saves configuration for later commands

**Step 2**: Start the adapter:

```bash
/tmp/lc-adapter-helper.sh start
```

### Helper Script Commands Reference

| Command | Description |
|---------|-------------|
| `sample [count]` | Capture sample logs (default 20 lines) |
| `setup <oid> <iid> [--grok ...] [--event-type ...] [--event-time ...] [--event-time-tz ...] [--hostname-path ...]` | Download adapter and create launch script with parsing config |
| `start` | Start the adapter in background |
| `stop` | Stop adapter and cleanup all files |
| `status` | Check if adapter is running |
| `logs` | Show adapter logs (last 50 lines) |
| `info` | Show current configuration |

### Manual Setup (Alternative)

If you prefer not to use the helper script, you can set up manually with separate commands:

1. **Detect platform**: `uname -s` and `uname -m`
2. **Create temp dir**: `mktemp -d /tmp/lc-adapter-test-XXXXXX`
3. **Download adapter**: `curl -sSL "<URL>" -o <TEMP_DIR>/lc_adapter && chmod +x <TEMP_DIR>/lc_adapter`
4. **Create launch script**: Use Write tool to create `<TEMP_DIR>/run_adapter.sh`
5. **Run in background**: `Bash(command="<TEMP_DIR>/run_adapter.sh", run_in_background=true)`

**Important for manual setup**:
- **MUST use `run_in_background: true`** - Shell backgrounding (`&`, `nohup`) does NOT work reliably
- Does NOT require sudo
- The adapter process name is `lc_adapter`

### Phase 4: Verify Adapter Connection

After starting, the adapter should appear in your LimaCharlie organization within a few seconds as a sensor. Verify by listing sensors with a selector that matches the installation key's `iid`:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"selector\": \"iid == `<IID>`\"}
    - Return: RAW"
)
```

You can also check the adapter log for connection status:

```bash
cat "$TEMP_DIR/adapter.log"
```

Look for `usp-client connected` to confirm successful connection.

Also check for any adapter errors:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: get_org_errors
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\"}
    - Return: Look for errors related to the test adapter"
)
```

### Phase 5: Viewing Ingested Data

After the adapter has been running for a few minutes, query the ingested logs.

**Step 1**: Generate the LCQL query from natural language:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: generate_lcql_query
    - Parameters: {\"oid\": \"<OID>\", \"query\": \"all events from sensor <SID> in the last 10 minutes\"}
    - Return: The generated LCQL query string"
)
```

**Step 2**: Execute the generated query:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: run_lcql_query
    - Parameters: {\"oid\": \"<OID>\", \"query\": \"<GENERATED_QUERY_FROM_STEP_1>\", \"limit\": 50}
    - Return: Return sample TEXT values from the events to show the log format"
)
```

Replace `<OID>` with the organization ID and `<SID>` with the sensor ID from the verification step.

### Stopping and Cleanup

**Using helper script** (recommended):

```bash
/tmp/lc-adapter-helper.sh stop
```

This automatically kills all adapter processes and cleans up temp files.

**Check status**:

```bash
/tmp/lc-adapter-helper.sh status
```

**Manual cleanup** (if helper script not available):

```bash
pkill -9 -f lc_adapter; pkill -9 -f "journalctl -f"; pkill -9 -f "tail -f.*log"; pkill -9 -f "log stream"; echo "Cleanup complete"
```

Use `;` instead of `&&` since pkill returns non-zero exit codes even on success.

## Example Usage

### Example 1: Full Deployment Workflow

**User**: "I want to test log ingestion with LimaCharlie"

**Steps**:

1. List organizations:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_user_orgs
    - Parameters: {}
    - Return: RAW"
)
```

Response shows: `[{"name": "My Test Org", "oid": "abc123-def456-..."}]`

2. Ask user to select org (via AskUserQuestion)

3. Check for existing installation key:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_installation_keys
    - Parameters: {\"oid\": \"abc123-def456-...\"}
    - Return: Look for key with description 'Test Adapter' and return its iid"
)
```

4. Create installation key if needed:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: create_installation_key
    - Parameters: {\"oid\": \"abc123-def456-...\", \"description\": \"Test Adapter\", \"tags\": [\"test-adapter\", \"temporary\"]}
    - Return: The iid of the created key"
)
```

Returns: `{"iid": "729b2770-9ae6-4e14-beea-5e42b854adf5", ...}`

5. Copy helper script and capture samples:
```bash
# Copy helper script from skill directory
cp plugins/lc-essentials/skills/test-limacharlie-adapter/lc-adapter-helper.sh /tmp/ && chmod +x /tmp/lc-adapter-helper.sh
```

```bash
# Capture sample logs
/tmp/lc-adapter-helper.sh sample 20 > /tmp/lc-adapter-samples.txt
cat /tmp/lc-adapter-samples.txt
```

Sample output shows logs like:
```
Dec 04 10:30:45 myhost systemd[1]: Started Session 42 of user admin.
Dec 04 10:30:46 myhost sshd[12345]: Accepted publickey for admin from 192.168.1.50 port 54321 ssh2
```

6. Read the sample file and invoke parsing-helper:
```
Skill("parsing-helper")
```

Parsing-helper analyzes the samples and outputs mapping config:
- `--grok '%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{DATA:service}: %{GREEDYDATA:msg}'`
- `--event-type service`
- `--event-time date`
- `--event-time-tz America/New_York` (because SYSLOGTIMESTAMP lacks timezone)
- `--hostname-path host`

7. Setup adapter with mapping config:
```bash
/tmp/lc-adapter-helper.sh setup abc123-def456-... 729b2770-9ae6-4e14-beea-5e42b854adf5 \
  --grok '%{SYSLOGTIMESTAMP:date} %{HOSTNAME:host} %{DATA:service}: %{GREEDYDATA:msg}' \
  --event-type service \
  --event-time date \
  --event-time-tz America/New_York \
  --hostname-path host
```

Output shows platform detection, download progress, and configuration saved.

8. Start the adapter:
```bash
/tmp/lc-adapter-helper.sh start
```

9. Verify adapter connection:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {\"oid\": \"abc123-def456-...\", \"selector\": \"iid == `729b2770-9ae6-4e14-beea-5e42b854adf5`\"}
    - Return: RAW"
)
```

10. Inform user the adapter is running and how to stop it.

### Example 2: Stopping the Test Adapter

**User**: "Stop the test adapter"

**Steps**:

1. Stop adapter using helper script:
```bash
/tmp/lc-adapter-helper.sh stop
```

2. Verify cleanup:
```bash
/tmp/lc-adapter-helper.sh status
```

3. Optionally, delete the sensor from LimaCharlie:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: delete_sensor
    - Parameters: {\"oid\": \"abc123-def456-...\", \"sid\": \"<SENSOR_ID>\"}
    - Return: RAW"
)
```

## Additional Notes

- **Helper script**: The included `lc-adapter-helper.sh` handles all platform detection, downloading, and process management automatically
- **Cross-platform support**: Works on Linux (x64), Mac OS Intel (x64), and Mac OS Apple Silicon (arm64)
- **No root required**: The adapter runs as a regular user
- **Log sources differ by platform**:
  - **Linux with journalctl**: Uses `journalctl -f --no-pager` to stream system logs (preferred)
  - **Linux without journalctl**: Falls back to `tail -f` on log files from `/var/log`
  - **Mac OS**: Uses `log stream` to access macOS unified logging (no file selection needed)
- **Automatic tags**: Sensors enrolled with this key get `test-adapter` and `temporary` tags for easy identification
- **Console visibility**: The adapter appears as a sensor in your LimaCharlie web console at https://app.limacharlie.io
- **Reusable key**: The "Test Adapter" installation key is reused if it already exists, avoiding duplicate keys
- **Debugging**: Use `/tmp/lc-adapter-helper.sh logs` to view adapter logs

## Related Skills

- `parsing-helper`: **Used in Phase 2** to generate and validate Grok parsing patterns for your log data
- `limacharlie-call`: For creating organizations or other API operations
- `detection-engineering`: For creating D&R rules to test with the adapter
- `sensor-health`: To check if your test adapter is reporting properly
- `investigation-creation`: To investigate events from your test adapter
- `test-limacharlie-edr`: For testing the EDR sensor instead of log adapters
