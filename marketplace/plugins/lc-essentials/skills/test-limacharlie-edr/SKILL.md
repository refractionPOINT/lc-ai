---
name: test-limacharlie-edr
description: Deploy a temporary LimaCharlie EDR agent on the local Linux or Mac OS host for testing. Downloads and runs the LC sensor in a temp directory with automatic cleanup. Use for testing detection rules, investigating sensor behavior, or development. Requires selecting or creating a LimaCharlie organization first.
allowed-tools: Task, Bash, Read, AskUserQuestion, Skill
---

# Test LimaCharlie EDR

> **Prerequisites**: Run `/init-lc` to load LimaCharlie guidelines into your CLAUDE.md.
> Always load the `limacharlie-call` skill prior to using LimaCharlie.

Deploy a temporary LimaCharlie EDR sensor on the local Linux or Mac OS host for testing purposes. The sensor runs in the background with automatic cleanup when stopped.

## When to Use

Use this skill when:

- **Testing D&R rules**: Validate detection rules against live sensor data from your own machine
- **Investigating sensor behavior**: Understand what events the sensor generates for specific actions
- **Development and debugging**: Test detections in a controlled environment
- **Quick validation**: Verify your LimaCharlie setup is working correctly
- **Learning**: Explore LimaCharlie capabilities hands-on

## What This Skill Does

This skill performs a two-phase deployment:

1. **Phase 1 - Installation Key**: Creates or finds an existing "Test EDR" installation key in your selected LimaCharlie organization
2. **Phase 2 - Sensor Deployment**: Downloads the appropriate EDR agent for your platform (Linux or Mac OS) to a temporary directory and runs it in the background as root

The sensor:
- Runs in the background (non-blocking)
- Uses a unique temp directory (avoids file conflicts)
- Requires root/sudo for full system monitoring
- Cleans up automatically when stopped

## Required Information

Before starting, ensure you have:

- **LimaCharlie organization**: Select from your available orgs or create a new one
- **Linux or Mac OS host**: Supports Linux x64, Mac Intel (x64), and Mac Apple Silicon (arm64)
- **Internet access**: Required to download the sensor binary
- **Root/sudo access**: The sensor needs elevated privileges for proper monitoring

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

Check for existing "Test EDR" installation key:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_installation_keys
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\"}
    - Return: Look for key with description 'Test EDR' and return its key and iid"
)
```

**If "Test EDR" key exists**: Extract the `key` value from the response.

**If not exists**: Create one:

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: create_installation_key
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"description\": \"Test EDR\", \"tags\": [\"test-edr\", \"temporary\"]}
    - Return: The key and iid of the created installation key"
)
```

Save the returned `key` value for the next phase.

### Phase 2: Download and Run the EDR

**Step 1**: Detect platform and create temp directory:

```bash
OS_TYPE=$(uname -s)
ARCH=$(uname -m)
TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/lc-edr-test-XXXXXX")
echo "Platform: $OS_TYPE ($ARCH), Temp dir: $TEMP_DIR"
```

**Step 2**: Download the appropriate sensor binary:

```bash
if [ "$OS_TYPE" = "Darwin" ]; then
  if [ "$ARCH" = "arm64" ]; then
    DOWNLOAD_URL="https://downloads.limacharlie.io/sensor/mac/arm64"
  else
    DOWNLOAD_URL="https://downloads.limacharlie.io/sensor/mac/64"
  fi
else
  DOWNLOAD_URL="https://downloads.limacharlie.io/sensor/linux/64"
fi
curl -sSL "$DOWNLOAD_URL" -o "$TEMP_DIR/lc_sensor"
chmod +x "$TEMP_DIR/lc_sensor"
echo "Sensor downloaded to: $TEMP_DIR"
```

**Step 3**: Run the sensor in background (as root):

```bash
if [ "$OS_TYPE" = "Darwin" ]; then
  sudo nohup "$TEMP_DIR/lc_sensor" -d <INSTALLATION_KEY> > /dev/null 2>&1 &
else
  sudo setsid "$TEMP_DIR/lc_sensor" -d <INSTALLATION_KEY> > /dev/null 2>&1 &
fi
echo "Sensor started in $TEMP_DIR"
```

**Important**:
- **Linux** uses `setsid` to create a new session and fully detach from the terminal
- **Mac OS** uses `nohup` which achieves similar process detachment
- Both approaches prevent Claude Code from hanging while waiting for the process
- Store the `TEMP_DIR` path for cleanup later
- The sensor process name is `lc_sensor` - use this for stopping

### Verify Sensor Connection

After starting, the sensor should appear in your LimaCharlie organization within a few seconds. Verify by listing sensors with a selector that matches the installation key's `iid` (Installation ID, a UUID):

```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {\"oid\": \"<SELECTED_ORG_ID>\", \"selector\": \"iid == `<INSTALLATION_KEY_IID>`\"}
    - Return: RAW"
)
```

Replace `<INSTALLATION_KEY_IID>` with the `iid` UUID from the installation key used. This selector fetches only the sensor enrolled with that specific installation key, rather than listing all sensors in the organization.

### Stopping and Cleanup

When the user wants to stop the test EDR:

**Single command to stop and clean up** (recommended):

```bash
sudo pkill -9 -f lc_sensor; sudo rm -rf <TEMP_DIR>; echo "Cleanup complete"
```

**Important notes**:
- Use `-9` (SIGKILL) for reliable termination of detached processes
- Use `;` instead of `&&` - pkill returns non-zero exit codes even on success (e.g., 144 when the signal is delivered)
- Do NOT use `KillShell` to stop the sensor - always use `pkill`

**Verify cleanup succeeded**:

```bash
ps aux | grep "[l]c_sensor" || echo "Sensor stopped"
```

The `[l]` bracket trick prevents grep from matching itself in the output.

## Example Usage

### Example 1: Full Deployment Workflow

**User**: "I want to test the LimaCharlie EDR on my machine"

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
    - Return: Look for key with description 'Test EDR' and return its key and iid"
)
```

4. Create installation key if needed:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: create_installation_key
    - Parameters: {\"oid\": \"abc123-def456-...\", \"description\": \"Test EDR\", \"tags\": [\"test-edr\", \"temporary\"]}
    - Return: The key and iid of the created installation key"
)
```

Returns: `{"iid": "test-edr", "key": "abc123:def456:..."}`

5. Download and run sensor:
```bash
OS_TYPE=$(uname -s)
ARCH=$(uname -m)
TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/lc-edr-test-XXXXXX")

if [ "$OS_TYPE" = "Darwin" ]; then
  if [ "$ARCH" = "arm64" ]; then
    DOWNLOAD_URL="https://downloads.limacharlie.io/sensor/mac/arm64"
  else
    DOWNLOAD_URL="https://downloads.limacharlie.io/sensor/mac/64"
  fi
else
  DOWNLOAD_URL="https://downloads.limacharlie.io/sensor/linux/64"
fi
curl -sSL "$DOWNLOAD_URL" -o "$TEMP_DIR/lc_sensor"
chmod +x "$TEMP_DIR/lc_sensor"

if [ "$OS_TYPE" = "Darwin" ]; then
  sudo nohup "$TEMP_DIR/lc_sensor" -d "abc123:def456:..." > /dev/null 2>&1 &
else
  sudo setsid "$TEMP_DIR/lc_sensor" -d "abc123:def456:..." > /dev/null 2>&1 &
fi
echo "Sensor started in $TEMP_DIR"
```

6. Verify sensor connection using a selector with the installation key's `iid`:
```
Task(
  subagent_type="lc-essentials:limacharlie-api-executor",
  model="haiku",
  prompt="Execute LimaCharlie API call:
    - Function: list_sensors
    - Parameters: {\"oid\": \"abc123-def456-...\", \"selector\": \"iid == `<IID_FROM_INSTALLATION_KEY>`\"}
    - Return: RAW"
)
```

7. Inform user the sensor is running and how to stop it (using `sudo pkill -f lc_sensor`).

### Example 2: Stopping the Test EDR

**User**: "Stop the test EDR"

**Steps**:

1. Stop sensor and clean up (single command):
```bash
sudo pkill -9 -f lc_sensor; sudo rm -rf /tmp/lc-edr-test-XXXXXX; echo "Cleanup complete"
```

2. Verify cleanup:
```bash
ps aux | grep "[l]c_sensor" || echo "Sensor stopped"
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

- **Cross-platform support**: Works on Linux (x64), Mac OS Intel (x64), and Mac OS Apple Silicon (arm64)
- **Root privileges required**: The sensor needs sudo/root to properly monitor system calls, processes, files, and network activity
- **Mac OS permissions**: On Mac OS, the sensor may require granting permissions in System Preferences > Privacy & Security (Full Disk Access, Input Monitoring) for full functionality
- **Temp directory**: The sensor creates working files, so we use a dedicated temp directory to keep things clean
- **Automatic tags**: Sensors enrolled with this key get `test-edr` and `temporary` tags for easy identification
- **Console visibility**: The sensor appears in your LimaCharlie web console at https://app.limacharlie.io
- **Background execution**: The sensor runs in background, so you can continue working while it monitors
- **Reusable key**: The "Test EDR" installation key is reused if it already exists, avoiding duplicate keys
- **Cleanup**: Always clean up when done to avoid orphaned processes and files. Use `;` not `&&` when chaining cleanup commands since pkill returns non-zero exit codes even on success

## Related Skills

- `limacharlie-call`: For creating organizations or other API operations
- `detection-engineering`: For creating D&R rules to test with the sensor
- `sensor-health`: To check if your test sensor is reporting properly
- `investigation-creation`: To investigate events from your test sensor
