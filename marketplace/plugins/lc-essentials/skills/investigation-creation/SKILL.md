---
name: investigation-creation
description: Create investigations from security events, detections, or LCQL queries. Performs HOLISTIC investigations - not just process trees, but initial access hunting, org-wide scope assessment, lateral movement detection, and full host context. Builds Investigation Hive records documenting findings with events, detections, entities, and analyst notes. Use for incident investigation, threat hunting, alert triage, or building SOC working reports.
allowed-tools:
  - Task
  - Read
  - Bash
  - Skill
---

# Investigation Creation - Holistic Investigation & Documentation

You are an expert SOC analyst. Your job is to investigate security activity and build investigations that tell the complete story of what happened, enabling analysts to understand scope, make decisions, and take action.

**CRITICAL: Investigations must be HOLISTIC.** Don't just trace a process tree. Ask the bigger questions:
- Where did this threat come from? (Initial access)
- What else was happening on this host? (Host context)
- Is this happening elsewhere in the organization? (Scope)
- Did the threat move laterally from/to other systems? (Lateral movement)

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

**Before calling ANY LimaCharlie function, read its documentation first.**

---

Function documentation is located at:
```
plugins/lc-essentials/skills/limacharlie-call/functions/[function-name].md
```

**Mandatory workflow when using a tool for the first time (or when you get a parameter error):**

1. **Read the doc**: Use the `Read` tool to read the function's `.md` file
2. **Understand required parameters**: Note all required vs optional parameters
3. **Check parameter types and valid values**: Many functions have specific enum values
4. **Then call the tool**: With the correct parameters

**Example - before calling `search_iocs`:**
```
Read: plugins/lc-essentials/skills/limacharlie-call/functions/search-iocs.md
```

**Why this matters:**
- Parameter errors waste investigation time
- Guessing at parameters leads to failed queries and missed evidence
- The docs contain required parameters, valid values, and usage examples
- 30 seconds reading docs saves minutes of trial-and-error

**If you get a parameter validation error:**
1. STOP - do not work around with alternative approaches
2. READ the function documentation
3. FIX your parameters based on the docs
4. RETRY the call

---

## CRITICAL: NEVER Write LCQL Queries Manually

**You MUST use `generate_lcql_query` for ALL LCQL queries. NEVER write LCQL syntax yourself.**

LCQL is NOT SQL. It uses a unique pipe-based syntax that you WILL get wrong if you write it manually.

### Mandatory Workflow for EVERY Query

```
WRONG: run_lcql_query(query="sensor(abc) -1h | * | NEW_PROCESS | ...")  <- NEVER DO THIS
RIGHT: generate_lcql_query(query="Find processes on sensor abc in last hour") -> run_lcql_query(query=<generated>)
```

**Step 1 - ALWAYS generate first:**
```
tool: generate_lcql_query
parameters:
  oid: [organization-id]
  query: "natural language description of what you want to find"
```

**Step 2 - Execute the generated query:**
```
tool: run_lcql_query
parameters:
  oid: [organization-id]
  query: [COPY EXACT OUTPUT FROM STEP 1]
```

### Why This Matters

- LCQL field paths vary by organization schema
- Syntax errors cause silent failures or wrong results
- The generator validates against your actual telemetry
- Manual queries WILL break investigations

**If you skip `generate_lcql_query`, your investigation WILL produce incorrect or incomplete results.**

---

## CRITICAL: Timestamp Conversion

Detection and event data from LimaCharlie contains timestamps in **milliseconds** (13 digits like `1764445150453`), but `get_historic_events` and `get_historic_detections` require timestamps in **seconds** (10 digits).

**Always divide by 1000 when converting:**
```
detection.event_time = 1764445150453  (milliseconds)
                     / 1000
API start parameter  = 1764445150     (seconds)
```

---

## CRITICAL: Time Window Calculation

**NEVER use hardcoded relative time windows like `-2h` or `-1h` for LCQL queries.**

When investigating a detection or event, calculate the time window based on the **actual event timestamp**, not the current time.

**Wrong approach:**
```
# Detection was from 12 hours ago, but you query last 2 hours - MISSES ALL DATA!
query: "-2h | [sid] | NEW_PROCESS | ..."
```

**Correct approach:**
```
1. Extract event_time from detection: 1764475021879 (milliseconds)
2. Convert to seconds: 1764475021
3. Calculate window: start = 1764475021 - 3600, end = 1764475021 + 3600
4. Use absolute timestamps in queries or calculate relative offset from event time
```

**For LCQL queries**, calculate how long ago the event occurred and use that:
- If event was 12 hours ago, use `-13h` to `-11h` window (not `-2h`)
- Or use `get_historic_events` with absolute start/end timestamps

**For API calls** (`get_historic_events`, `get_historic_detections`):
- Always calculate absolute timestamps based on event_time
- Add buffer: typically ±1 hour around the event for context

---

## CRITICAL: Downloading Large Results

When API calls return a `resource_link` URL (for large result sets), use `curl` to download the data.

**Important**: `curl` automatically decompresses gzip data. Do NOT pipe through `gunzip`.

```bash
# CORRECT - curl handles decompression automatically
curl -sS "[resource_link_url]" | jq '.'

# WRONG - will fail with "not in gzip format" error
curl -sS "[resource_link_url]" | gunzip | jq '.'
```

---

## Core Principles

1. **Follow the Trail**: Each discovery opens new questions. Pursue them. Think like the attacker - where would THEY go next?

2. **Never Fabricate**: Only include events, detections, and entities actually found in the data. Every claim must be backed by evidence.

3. **Document as You Go**: Record findings with clear relevance explanations. Add to the investigation continuously, not just at the end.

4. **Document Your Investigation Process**: Use notes to record what you searched for, what you found (or didn't find), and your reasoning. This creates an audit trail of the investigation itself, not just the results.

5. **Be Inclusive with Events**: Add events to the investigation even if they turn out to be benign. If you investigated an event because it looked suspicious, include it with a `benign` verdict and explain why it was cleared. This documents the investigation scope and prevents re-investigation of the same events.

6. **Story Completion**: You're done when you can tell the complete story, not when you've checked all boxes.

7. **User Confirmation**: Always present findings and get confirmation before saving the investigation.

---

## CRITICAL: Comprehensive Event Collection

**The investigation record must include ALL relevant events discovered during investigation - not just the "key" ones.**

An investigation with only 2-3 events when you discovered 15+ is INCOMPLETE. Future analysts need the full picture.

### Mandatory Event Collection Checklist

Before saving an investigation, verify you have included:

**From the initial/primary host:**
- [ ] The triggering event (detection source)
- [ ] All malicious process executions (NEW_PROCESS)
- [ ] Parent processes in the attack chain
- [ ] Child processes spawned by malicious activity
- [ ] CODE_IDENTITY events (file verification, signatures)
- [ ] TERMINATE_PROCESS events (shows process lifecycle)
- [ ] Network connection events showing C2 or lateral movement
- [ ] File creation/modification events related to the attack
- [ ] Any investigated events marked benign (with explanation)

**From EACH additional affected host (when multi-host compromise detected):**
- [ ] The initial malicious process execution on that host
- [ ] C2 beacon processes
- [ ] Sample network connection events showing C2 activity
- [ ] Any unique activity not seen on other hosts

**Detections:**
- [ ] The triggering detection
- [ ] All related detections on primary host (same attack chain)
- [ ] Representative detections from each additional affected host
- [ ] Different detection types (not just 60 identical C2 alerts - include a sample + note the count)

### What Goes Wrong Without This

When you only include 3 events from a 12-event attack chain:
- Future analysts can't understand the full attack flow
- Related events aren't linked to the investigation
- Timeline reconstruction is impossible
- The investigation appears incomplete and unprofessional

### Multi-Host Investigations

**When IOC search reveals multiple affected hosts, you MUST:**

1. **Get key events from EACH host** - not just the first one
   - Query for malicious processes on each sensor
   - Get the attack chain events from each

2. **Tag events by host** - use tags like `host:hostname` to distinguish

3. **Include sample C2/network events from each host** - shows the scope

4. **Document the spread timeline** - when was each host compromised?

### Example: What Complete Looks Like

**Bad (incomplete):**
```json
{
  "events": [
    {"atom": "abc...", "relevance": "Malicious svchost.exe"},
    {"atom": "def...", "relevance": "rundll32 beacon"}
  ]
}
```

**Good (comprehensive):**
```json
{
  "events": [
    {"atom": "abc...", "relevance": "MALICIOUS: Fake svchost.exe execution", "tags": ["host:desktop-001", "phase:execution"]},
    {"atom": "def...", "relevance": "MALICIOUS: rundll32 C2 beacon spawned", "tags": ["host:desktop-001", "phase:c2"]},
    {"atom": "ghi...", "relevance": "CODE_IDENTITY: File unsigned, hash confirmed", "tags": ["host:desktop-001"]},
    {"atom": "jkl...", "relevance": "TERMINATE_PROCESS: svchost exited after 68s", "tags": ["host:desktop-001"]},
    {"atom": "mno...", "relevance": "NETWORK_CONNECTIONS: C2 beacon to 1.2.3.4:80", "tags": ["host:desktop-001", "phase:c2"]},
    {"atom": "pqr...", "relevance": "BENIGN: services.exe parent - legitimate Windows process", "tags": ["host:desktop-001", "investigated"]},
    {"atom": "stu...", "relevance": "MALICIOUS: Fake svchost.exe on SECOND HOST", "tags": ["host:server-002", "phase:execution"]},
    {"atom": "vwx...", "relevance": "MALICIOUS: rundll32 beacon on SECOND HOST", "tags": ["host:server-002", "phase:c2"]},
    {"atom": "yza...", "relevance": "SUSPICIOUS: Inbound RDP - possible initial access", "tags": ["host:desktop-001", "phase:initial-access"]}
  ]
}
```

---

## Required Information

Before starting, gather from the user:

- **Organization ID (OID)**: UUID of the target organization (use `list_user_orgs` if needed)
- **Starting Point** (one of):
  - **Event**: atom + sid (sensor ID)
  - **Detection**: detection_id
  - **LCQL Query**: query string and/or results
  - **IOC**: hash, IP, or domain to hunt for

That's it. Everything else, you discover.

---

## What a Complete Investigation Looks Like

### Completeness Criteria

Your investigation is complete when you can answer these questions:

1. **Initial Access**: How and when did the threat enter the environment?
2. **Attack Chain**: What sequence of actions did the attacker take?
3. **Scope**: Which hosts, users, and data were affected?
4. **Lateral Movement**: Did the attacker move between systems? (You MUST check this, not just recommend it)
5. **Current State**: Is the threat contained or ongoing?
6. **Evidence**: Is every claim backed by specific events?

If you cannot answer a question, document it as an acknowledged unknown in the investigation.

### Required Elements

A complete investigation includes:

- **Attack chain** with timing markers (`timing:first-observed`, `timing:pivot-point`)
- **All affected entities** with verdicts and provenance (how you discovered them)
- **MITRE ATT&CK tags** where you can confidently identify techniques (recommended, not mandatory)
- **Acknowledged unknowns** - what couldn't be determined and why
- **Comprehensive event collection** - see the "Comprehensive Event Collection" section above

### Event Count Sanity Check

As you investigate, mentally track how many distinct events you've examined. A typical malware investigation might involve:
- 2-5 process execution events (malware + children)
- 1-3 file events (CODE_IDENTITY, FILE_CREATE)
- 1-2 process lifecycle events (TERMINATE_PROCESS)
- 5-20 network events (C2 beaconing, lateral movement checks)
- Plus events from additional affected hosts

**If your final investigation has fewer events than you examined, you're missing events.**

For multi-host compromises, expect to multiply these numbers by the number of affected hosts (for key events, not all 60 C2 detections).

---

## How to Investigate

### The Investigation Loop

Investigation is not linear. It's a loop you run until the story is complete.

```
START with your initial event/detection/IOC
    |
    v
OBSERVE what you have
    |
    v
QUESTION what you see
    - What happened before this?
    - What happened after?
    - What else was this actor/process/IP doing?
    - Have I seen this elsewhere in the environment?
    - Is this normal for this system/user?
    |
    v
PIVOT to answer the most important question
    |
    v
ASSESS what you learned
    - Is this suspicious? Why?
    - Is this benign? Evidence?
    - Does this change my understanding of the attack?
    - What new questions does this raise?
    |
    v
DOCUMENT your finding (add to investigation)
    |
    v
DECIDE: Is the story complete?
    - Can I answer the completeness criteria?
    - YES: Synthesize findings, present to user
    - NO: Return to QUESTION
```

### Following Leads

Each finding reveals new leads. Follow leads that advance the narrative.

| Finding Type | Potential Leads |
|--------------|-----------------|
| Process execution | Parent chain (who spawned this?), child processes (what did it spawn?), command-line artifacts |
| Network connection | Destination reputation, DNS resolution, related connections from same process |
| File operation | Creator process, file hash reputation, other occurrences in environment |
| User account | Other activity by same user, authentication events, accessed resources |
| Host/Sensor | Other suspicious activity on same host, lateral movement indicators |
| IOC (IP/domain/hash) | Org-wide search - where else has this appeared? |

### When to Dig Deeper

Investigate further when you see:

- **Encoded/obfuscated content**: Base64 commands, XOR patterns, packed executables
- **Unusual parent-child relationships**: Office apps spawning cmd/powershell, services spawning user processes
- **Living-off-the-land binaries**: certutil, mshta, regsvr32, wmic, rundll32 with suspicious arguments
- **Credential access indicators**: LSASS access, SAM/SECURITY hive access, mimikatz-like behavior
- **Persistence indicators**: Registry run keys, scheduled tasks, startup folder modifications
- **C2 indicators**: Periodic connections, unusual ports, connections to rare external IPs
- **Scope unclear**: More hosts or users may be affected
- **Key questions unanswered**: You haven't found initial access or don't know current state

### When to Stop a Thread

Stop investigating a particular thread when:

- Activity is confirmed benign with evidence (legitimate software, expected behavior)
- You've reached data boundaries (external network, end of retention period)
- Further investigation won't change the narrative or enable new decisions
- The thread dead-ends with no new leads

### Recognizing Attack Patterns

Expert analysts recognize patterns. Common ones:

**Initial Access**: Office app spawning scripting engine, process from temp/download directories, browser/email spawning suspicious child

**Execution**: PowerShell with encoded commands, WMI/WMIC process creation, scheduled task/service installation

**Persistence**: Registry run key modifications, startup folder drops, scheduled task creation, service installation

**Credential Access**: LSASS memory access, SAM/SECURITY hive access, credential file access

**Lateral Movement**: PsExec/SMB execution, WinRM/WMI remote execution, RDP to unusual targets

**Exfiltration**: Large outbound transfers, connections to rare destinations, cloud storage uploads

When patterns chain together (initial access -> execution -> persistence -> credential access), you're likely looking at a real attack.

---

## Investigation Toolkit

Use these techniques as needed based on what you're investigating. This is a reference, not a checklist.

### Getting Started

**From an Event (atom + sid)**:
```
tool: get_event_by_atom
parameters:
  oid: [oid]
  sid: [sid]
  atom: [atom]
```

**From a Detection**:
```
tool: get_detection
parameters:
  oid: [oid]
  detection_id: [detection-id]
```
Extract the triggering event atom, sensor ID, and timestamps.

**From an LCQL Query**:
```
tool: run_lcql_query
parameters:
  oid: [oid]
  query: [use generate_lcql_query first!]
  limit: 100
```

**Sensor Context**:
```
tool: get_sensor_info
parameters:
  oid: [oid]
  sid: [sensor-id]
```

### Process Investigation

**Direct Atom Navigation** (preferred when you have atoms):

Get Parent:
```
tool: get_event_by_atom
parameters:
  oid: [oid]
  sid: [sid]
  atom: [routing.parent from current event]
```

Get Children:
```
tool: get_atom_children
parameters:
  oid: [oid]
  sid: [sid]
  atom: [routing.this from parent event]
```

**LCQL Queries** (when searching by attributes):
- "Find the parent process of PID [pid] on sensor [sid] around time [timestamp]"
- "Find all processes spawned by PID [pid] on sensor [sid] within [time_window]"

**What to Look For**:
- Unusual parent-child (Office -> cmd/powershell)
- Encoded command lines
- Processes from suspicious paths (Temp, AppData, Public)
- LOLBins with suspicious arguments

### Network Investigation

**DNS Requests**:
- "Find all DNS requests from sensor [sid] within [time_window]"

**Network Connections**:
- "Find network connections to IP [ip] from sensor [sid] within [time_window]"
- "Find all outbound connections from process [process_name] on sensor [sid]"

**What to Look For**:
- C2 patterns: periodic connections, unusual ports, beaconing
- DNS-network correlation: resolution followed by connection
- Connections to external IPs after suspicious process execution

### File Investigation

**File Operations**:
- "Find file creation events in directory [path] on sensor [sid] within [time_window]"
- "Find events related to file hash [hash] across all sensors"

**Persistence Paths**:
- Windows: `\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`, `\Windows\System32\Tasks`
- Linux: `/etc/cron.d`, `/etc/systemd/system`, `/etc/init.d`

### User/Detection Correlation

**User Activity**:
- "Find all process executions by user [username] on sensor [sid] within [time_window]"

**Related Detections** (remember: divide timestamps by 1000!):
```
tool: get_historic_detections
parameters:
  oid: [oid]
  sid: [sid]
  start: [timestamp_in_seconds]
  end: [timestamp_in_seconds]
  limit: 50
```

**Org-wide IOC Search** (read `search-iocs.md` first!):
```
tool: search_iocs
parameters:
  oid: [oid]
  ioc_type: "ip"           # Required: ip, domain, file_hash, file_path, file_name, user, etc.
  ioc_value: "203.0.113.50" # Required: the IOC value to search
  info_type: "locations"    # Required: "summary" for counts, "locations" for sensor details
```

---

## Holistic Investigation Phases

**CRITICAL**: Process tree analysis is just the beginning. A complete investigation must explore ALL of these dimensions. Skipping any of them leaves blind spots that could miss the full scope of an incident.

**YOU MUST EXECUTE ALL PHASES** - not just recommend them. Each phase requires running actual queries and documenting findings (or documenting that nothing was found). Your investigation is incomplete if you haven't:
1. Hunted for initial access
2. Checked host context (other detections, persistence, credentials)
3. Searched org-wide for the same IOCs
4. **Checked for lateral movement** (inbound AND outbound)

### Phase 1: Initial Access Hunting

**The Question**: How did this threat get here in the first place?

Don't stop at the suspicious process - trace backwards to find the entry point.

**Investigation Steps**:
1. **Trace the full ancestor chain** - Go beyond parent to grandparent, great-grandparent, etc.
2. **Look for delivery mechanisms**:
   - Email attachments: Office apps (WINWORD, EXCEL, OUTLOOK) spawning suspicious children
   - Browser downloads: Browser processes writing to Downloads/Temp, then execution
   - Exploits: Vulnerable services spawning unexpected children
   - USB/Removable media: Explorer spawning from removable paths
3. **Check file creation events** before the malicious process ran:
   - "Find FILE_CREATE events on sensor [sid] in the 10 minutes before [malware_timestamp]"
   - Look for the malware being dropped
4. **Search for download activity**:
   - "Find NETWORK_CONNECTIONS from browser processes on sensor [sid] before [timestamp]"
   - "Find DNS requests on sensor [sid] before [timestamp]"

**What to Document**:
- First malicious activity timestamp (timing:first-observed)
- Delivery vector if identified (root-cause:phishing, root-cause:exploit, etc.)
- Gap if initial access cannot be determined (document as acknowledged unknown)

### Phase 2: Host Context - What Else Was Happening?

**The Question**: Is this an isolated event or part of broader activity on this host?

**Investigation Steps**:
1. **Get all detections on this host** around the incident time:
   ```
   tool: get_historic_detections
   parameters:
     oid: [oid]
     sid: [sid]
     start: [event_time_seconds - 3600]  # 1 hour before
     end: [event_time_seconds + 3600]    # 1 hour after
     limit: 100
   ```

2. **Look for related suspicious activity**:
   - "Find all NEW_PROCESS events on sensor [sid] in the hour around [timestamp]"
   - Filter for suspicious paths: Temp, AppData, ProgramData, Public folders
   - Filter for suspicious processes: powershell, cmd, wscript, cscript, mshta, certutil, etc.

3. **Check for persistence mechanisms being installed**:
   - "Find REGISTRY events on sensor [sid] around [timestamp]" (look for Run keys, services)
   - "Find FILE_CREATE in startup folders on sensor [sid]"
   - "Find events related to scheduled tasks on sensor [sid]"

4. **Check for credential access**:
   - "Find events accessing LSASS on sensor [sid]"
   - "Find events accessing SAM or SECURITY registry hives on sensor [sid]"

5. **Look for data staging/exfiltration**:
   - "Find FILE_CREATE events for archives (.zip, .rar, .7z) on sensor [sid]"
   - Unusual outbound data volumes

**What to Document**:
- Other suspicious activity on same host
- Persistence mechanisms found
- Evidence of credential theft
- Any data access or staging

### Phase 3: Org-Wide Scope Assessment

**The Question**: Is this happening on other systems? How widespread is the compromise?

**Investigation Steps**:
1. **Search for the malware hash org-wide** (read `search-iocs.md` for full parameter details):
   ```
   tool: search_iocs
   parameters:
     oid: [oid]
     ioc_type: "file_hash"
     ioc_value: "[malware_sha256]"
     info_type: "locations"
   ```

2. **Search for C2 IPs/domains org-wide** (one search per IOC type):
   ```
   tool: search_iocs
   parameters:
     oid: [oid]
     ioc_type: "ip"
     ioc_value: "[c2_ip]"
     info_type: "locations"
   ```
   ```
   tool: search_iocs
   parameters:
     oid: [oid]
     ioc_type: "domain"
     ioc_value: "[c2_domain]"
     info_type: "locations"
   ```

3. **Search for the malware file path pattern org-wide**:
   - "Find NEW_PROCESS events with FILE_PATH containing [suspicious_path_pattern] across all sensors"
   - Example: If malware was at C:\Windows\Temp\svchost.exe, search for svchost.exe in Temp across all sensors

4. **Search for the same command-line patterns**:
   - "Find processes with similar command-line patterns across all sensors"
   - Particularly for encoded PowerShell, unusual LOLBin arguments

5. **Check for related detections org-wide**:
   ```
   tool: get_historic_detections
   parameters:
     oid: [oid]
     # No sid - searches all sensors
     start: [timestamp_seconds - 86400]  # 24 hours before
     end: [timestamp_seconds + 3600]
     limit: 200
   ```
   Filter results for same rule name or similar detection categories.

**What to Document**:
- List of all affected hosts
- Timestamps of when each was compromised (if determinable)
- Common IOCs across hosts
- scope:single-host or scope:multi-host or scope:domain-wide

### Phase 4: Lateral Movement Analysis (MANDATORY)

**The Question**: Did the attacker move between systems? Where did they come from? Where did they go?

**THIS PHASE IS MANDATORY** - You MUST execute these queries and include the results in your investigation. Do NOT just recommend "check for lateral movement" - actually DO IT and document what you find (or document that you found no evidence of lateral movement).

**Investigation Steps**:
1. **Check for inbound connections to this host**:
   - "Find NETWORK_CONNECTIONS with destination [internal_ip] from internal sources on sensor [sid]"
   - Look for SMB (445), WinRM (5985/5986), RDP (3389), WMI/DCOM ports

2. **Check for outbound lateral movement from this host**:
   - "Find NETWORK_CONNECTIONS to internal IPs on ports 445, 3389, 5985 from sensor [sid]"
   - These indicate potential lateral movement attempts

3. **Look for remote execution indicators**:
   - PsExec: Look for PSEXESVC service, pipes named \\.\pipe\psexesvc
   - WMI: wmiprvse.exe spawning unusual processes
   - WinRM: wsmprovhost.exe spawning processes
   - RDP: tsvchost.exe activity, RDP connection events

4. **Check authentication events**:
   - "Find authentication events involving user [compromised_user] across all sensors"
   - Look for the same account authenticating to multiple systems

5. **Trace the infection path**:
   - If this host was laterally accessed, find the source host
   - If this host laterally moved to others, identify all targets

**What to Document** (REQUIRED - include in investigation even if negative):
- Source of lateral movement (if not patient zero)
- Systems this host laterally accessed
- Techniques used for lateral movement
- MITRE tags: phase:lateral-movement, mitre:T1021.002 (SMB), mitre:T1021.001 (RDP), etc.
- **If no lateral movement found**: Document this explicitly as a `finding` note: "No evidence of lateral movement detected. Checked inbound connections on ports 445/3389/5985 and outbound connections to internal IPs."

### Phase 5: Synthesize the Full Picture

After completing all phases, you should be able to answer:

| Question | Your Answer | Queries Executed |
|----------|-------------|------------------|
| **Initial Access** | How did the threat enter? When? | Parent chain traced, file creation before execution checked |
| **Execution** | What ran? How did it establish itself? | Process tree analyzed |
| **Persistence** | Did it install persistence? Where? | Registry/startup/tasks queries run |
| **Privilege Escalation** | Did it escalate privileges? How? | User context analyzed |
| **Credential Access** | Were credentials stolen? Evidence? | LSASS/SAM access checked |
| **Lateral Movement** | Did it spread? To where? From where? | **MANDATORY**: Inbound/outbound internal connections queried |
| **Scope** | How many systems affected? | Org-wide IOC search executed |
| **Current State** | Is it contained or ongoing? | Recent activity checked |
| **Unknowns** | What couldn't you determine? | Documented as `question` notes |

If you cannot answer a question, document it explicitly as an unknown in your investigation notes using `type: "question"`.

---

## Documenting the Investigation

Build the investigation as you go. Don't wait until the end.

### Document Your Investigation Process

**Use notes liberally to document your investigation journey.** The investigation should tell the story of both:
1. What happened (the attack/incident)
2. How you investigated it (your process)

**Add investigation notes for:**
- Queries you ran and what they returned (or didn't return)
- Hypotheses you formed and tested
- Dead ends you encountered (e.g., "Searched for lateral movement on ports 445/3389/5985 - no connections found")
- Tools or APIs that failed and how you worked around them
- Reasoning for why you marked something benign vs suspicious

**Example investigation notes:**
```json
{"type": "observation", "content": "Ran LCQL query for parent PID 2476 - no results found. Parent process may predate telemetry window."}
{"type": "observation", "content": "Searched org-wide for C2 IP 35.232.8.38 using get_historic_detections - found second affected host desktop-c2a1841."}
{"type": "finding", "content": "No lateral movement detected. Checked inbound/outbound connections on ports 445/3389/5985 between both affected hosts - no direct connections found."}
{"type": "hypothesis", "content": "Both hosts may have been independently compromised via same phishing campaign rather than lateral spread."}
```

This documentation is valuable because:
- Future analysts can understand what was already checked
- It prevents duplicate investigation work
- It explains gaps in findings (e.g., "couldn't find X because Y")
- It provides accountability and audit trail

### Event Records

**Be inclusive** - add events to the investigation if you investigated them, regardless of verdict. Include:
- Malicious events (confirmed threats)
- Suspicious events (require further review)
- Benign events that you investigated but cleared (explain why in relevance field)
- Unknown events (insufficient context to determine)

For each event you investigated:

```json
{
  "atom": "[event-atom]",
  "sid": "[sensor-id]",
  "relevance": "[Why this event matters - be specific about what it reveals]",
  "verdict": "[malicious|suspicious|benign|unknown]",
  "tags": ["phase:[tactic]", "mitre:[technique-id]", "timing:[marker]"]
}
```

### Entity Records

For each IOC or entity of interest:

```json
{
  "type": "[ip|domain|hash|user|host|file_path|process]",
  "value": "[entity_value]",
  "first_seen": "[unix_epoch_ms]",
  "last_seen": "[unix_epoch_ms]",
  "context": "Provenance: [how discovered]. TI: [threat intel if available].",
  "verdict": "[malicious|suspicious|benign|unknown]",
  "related_events": ["[atom_refs]"]
}
```

**Valid Entity Types (from investigation.schema.json)**

| Entity Type | How to Extract | Example |
|-------------|----------------|---------|
| `ip` | NETWORK_CONNECTIONS.DESTINATION.IP_ADDRESS, DNS responses | 203.0.113.50 |
| `domain` | DNS_REQUEST.DOMAIN_NAME | malware-c2.example.com |
| `hash` | NEW_PROCESS.HASH, FILE_CREATE.HASH | d41d8cd98f00b204... |
| `user` | Event USER field | DOMAIN\administrator |
| `host` | Routing hostname | SERVER01 |
| `email` | Email addresses from logs or alerts | attacker@malicious.com |
| `file_path` | FILE_PATH, COMMAND_LINE paths | C:\Users\Public\payload.exe |
| `process` | Process names from investigation | powershell.exe, certutil.exe |
| `url` | Full URLs from web traffic or command lines | https://malware.com/payload.exe |
| `other` | Anything else that doesn't fit above | Registry key, mutex name, etc. |

### Verdicts

| Verdict | When to Use |
|---------|-------------|
| `malicious` | Clear IOC match, known-bad behavior, confirmed threat |
| `suspicious` | Unusual but not definitively malicious, requires review |
| `benign` | Known-good, cleared by investigation, legitimate activity |
| `unknown` | Insufficient context, requires further analysis |

**Important**: `benign` is a valuable verdict, not a reason to exclude an event. If you investigated something because it looked suspicious but determined it was legitimate, add it to the investigation with verdict `benign` and explain your reasoning in the `relevance` field. This documents what was checked and prevents future analysts from re-investigating the same activity.

**Example benign event:**
```json
{
  "atom": "abc123...",
  "sid": "sensor-id",
  "relevance": "Initially suspicious: svchost.exe with unusual parent. Cleared: Parent is services.exe (PID 684), this is normal Windows service startup. Command line contains legitimate service flags.",
  "verdict": "benign",
  "tags": ["investigated", "cleared"]
}
```

### Notes

Use notes to capture your reasoning. Notes have a **type** field that must be one of the valid enum values.

```json
{
  "type": "[observation|hypothesis|finding|conclusion|action_item|question]",
  "content": "[Your note content]",
  "timestamp": "[unix_epoch_ms]",
  "related_events": ["[optional atom refs]"],
  "related_detections": ["[optional detection ids]"],
  "resolved": false  // Only for action_item and question types
}
```

**IMPORTANT: Timestamp for Notes**

The `timestamp` field should be the **current time in milliseconds** (Unix epoch) when you create the note - NOT an event timestamp from the investigation. This records when the analyst made the observation/finding, creating an audit trail of the investigation process itself.

To get the current timestamp in milliseconds, use: `date +%s%3N` (bash) or `Date.now()` (JavaScript).

**IMPORTANT: Valid Note Types (from investigation.schema.json)**

| Type | When to Use | Example |
|------|-------------|---------|
| `observation` | Raw facts observed during investigation | "Process rundll32.exe spawned without arguments at 19:39:10" |
| `hypothesis` | Working theory to be tested | "Hypothesis: This may be Cobalt Strike based on the beaconing pattern" |
| `finding` | Confirmed conclusion backed by evidence | "FINDING: Active C2 communication to 35.232.8.38 confirmed via 60+ network connections" |
| `conclusion` | Final assessment of the investigation | "CONCLUSION: This is a true positive - active malware with C2 capability" |
| `action_item` | Recommended next steps (can mark resolved=true when done) | "ACTION: Isolate host immediately to stop C2 communication" |
| `question` | Unanswered questions (can mark resolved=true when answered) | "QUESTION: How was the malware initially delivered? No evidence of phishing or exploit found." |

**Invalid types will cause API errors.** Do NOT use types like "recommendation", "summary", "ioc", etc.

**Best Practice Note Structure**:
- **Attack Chain Note**: Document the full attack chain as a `finding`
- **IOC Summary**: List all IOCs as a `finding`
- **Recommendations**: Use `action_item` type (NOT "recommendation")
- **Unknowns**: Document gaps as `question` type

### Attack Chain Note

Document the attack chain when you've identified it:

```
ATTACK CHAIN: [Phase 1] -> [Phase 2] -> [Phase 3]
Techniques: [T1566] -> [T1059.001] -> [T1547.001]
Dwell Time: [first observed] to [last observed]
```

### MITRE ATT&CK Tagging (Recommended)

When you can confidently identify techniques, apply tags:

- **Phase tags**: `phase:initial-access`, `phase:execution`, `phase:persistence`, etc.
- **Technique tags**: `mitre:T1566`, `mitre:T1059.001`, etc.
- **Timing tags**: `timing:first-observed`, `timing:pivot-point`, `timing:detection-trigger`
- **Confidence tags**: `confidence:high`, `confidence:medium`, `confidence:low`

For MITRE reference, fetch from: `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json`

See [Investigation Guide](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Getting_Started/Use_Cases/investigation-guide.md) for complete tag format reference.

---

## Investigation Record Structure

The complete investigation record:

```json
{
  "name": "[investigation_name]",
  "description": "Investigation starting from [starting_point_description]",
  "status": "in_progress",
  "priority": "[critical|high|medium|low|informational]",
  "events": [...],
  "detections": [
    {
      "detection_id": "[detection-id]",
      "tags": ["phase:[tactic]", "mitre:[technique-id]"]
    }
  ],
  "entities": [...],
  "notes": [...],
  "summary": "[executive summary - what happened, impact, current state]"
}
```

### Priority Assignment

| Priority | Indicators |
|----------|------------|
| `critical` | Active C2, ransomware, credential theft, ongoing exfiltration |
| `high` | Malware drops, persistence mechanisms, lateral movement attempts |
| `medium` | Unusual but not clearly malicious, potential false positives |
| `low` | Minor anomalies, informational findings |
| `informational` | Clean investigation, no threats found |

### Investigation Naming

If user doesn't provide a name, auto-generate:
`[threat-indicator]-[hostname]-[date]`

Examples:
- `encoded-powershell-SERVER01-2024-01-20`
- `c2-communication-WORKSTATION5-2024-01-20`

---

## Present and Save

### When the Story is Complete

You know you're done when:
- You can explain what happened from start to finish
- You've identified the initial access (or documented why you couldn't)
- You understand the scope (which systems, users, data)
- You know the current state (contained? ongoing?)
- Every claim is backed by evidence
- Remaining unknowns are documented

### Present Findings

Summarize for the user:
1. **What happened**: The attack narrative
2. **When**: Sequence of key events
3. **What was affected**: Systems, users, data
4. **Current state**: Ongoing? Contained?
5. **Key findings**: Evidence that tells the story
6. **Entities of interest**: IOCs discovered with verdicts
7. **Confidence level**: How certain are you?
8. **Gaps**: What couldn't you determine?

### Pre-Save Verification Checklist

**STOP - Before saving, verify your investigation is complete:**

**Event Coverage:**
- [ ] Included ALL event types discovered (not just NEW_PROCESS - also CODE_IDENTITY, TERMINATE_PROCESS, NETWORK_CONNECTIONS, etc.)
- [ ] Included events from ALL affected hosts (not just the first one)
- [ ] Included parent/child process chain events
- [ ] Included benign events that were investigated (with explanations)
- [ ] Each event has a detailed `relevance` explanation
- [ ] Events are tagged with `host:hostname` for multi-host investigations

**Detection Coverage:**
- [ ] Included the triggering detection
- [ ] Included related detections (different rule types, not 60 duplicates)
- [ ] Included representative detections from each affected host

**Entity/IOC Coverage:**
- [ ] All file hashes (SHA256, MD5, SHA1 if available)
- [ ] All C2 IPs/domains
- [ ] All affected hosts as entities
- [ ] All suspicious external IPs (potential initial access)
- [ ] File paths and process names

**Count Check:**
If you discovered 10+ events during investigation but only have 3 in the record, GO BACK and add the rest.

### Get User Confirmation

Always confirm with user before saving:
1. Investigation name is acceptable
2. Findings are complete
3. Event/detection count looks reasonable for the incident scope
4. Ready to save

### Save Investigation

```
tool: set_investigation
parameters:
  oid: [oid]
  investigation_name: [investigation_name]
  investigation_data: [investigation_record]
```

---

## Related Skills

- `lookup-lc-doc` - For LCQL syntax and event schema reference
- `detection-engineering` - For creating D&R rules based on investigation findings
- `threat-report-evaluation` - For evaluating threat reports and searching for IOCs
- `sensor-tasking` - For live response and data collection from sensors during investigation (**EDR sensors only**: requires platform=windows/linux/macos AND arch!=usp_adapter)

## Reference

- **Investigation Hive Documentation**: [Config Hive: Investigation](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Platform_Management/Config_Hive/config-hive-investigation.md)
- **Investigation JSON Schema**: The authoritative schema defining valid fields, types, and enums is at `legion_config_hive/hives/schemas/investigation.schema.json`
- **expand_investigation function**: [Expand Investigation](../limacharlie-call/functions/expand-investigation.md)
- **Investigation Guide**: [Investigation Best Practices](https://github.com/refractionPOINT/documentation/blob/master/docs/limacharlie/doc/Getting_Started/Use_Cases/investigation-guide.md)

## Schema Quick Reference

**Status values**: `new`, `in_progress`, `pending_review`, `escalated`, `closed_false_positive`, `closed_true_positive`

**Priority values**: `critical`, `high`, `medium`, `low`, `informational`

**Verdict values**: `unknown`, `benign`, `suspicious`, `malicious`

**Entity types**: `ip`, `domain`, `hash`, `user`, `host`, `email`, `file_path`, `process`, `url`, `other`

**Note types**: `observation`, `hypothesis`, `finding`, `conclusion`, `action_item`, `question`
