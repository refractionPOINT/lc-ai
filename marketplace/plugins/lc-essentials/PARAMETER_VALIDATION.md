# Parameter Validation Guide

This document defines validation rules for common LimaCharlie API parameters. **Always validate parameters before making API calls** to prevent errors and reduce hallucinations.

## Common Parameter Types

### Organization ID (OID)

```
Format: UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
Length: 36 characters (including dashes)
Example: c7e8f940-1234-5678-abcd-1234567890ab
```

**Validation:**
- Must be exactly 36 characters
- Must match UUID pattern with dashes
- **NEVER** use organization names directly
- If you receive an org name, call `get_org_oid_by_name` first

**Common errors:**
- Using org name: `"Production Fleet"` - WRONG
- Missing dashes: `"c7e8f94012345678abcd1234567890ab"` - WRONG
- Wrong length: `"c7e8f940-1234"` - WRONG

### Sensor ID (SID)

```
Format: UUID (same as OID)
Length: 36 characters
Example: abc12345-def6-7890-abcd-ef1234567890
```

**Validation:** Same rules as OID.

### Timestamps

```
API parameters: Unix epoch SECONDS (10 digits)
Event data: Unix epoch MILLISECONDS (13 digits)
```

**Validation:**
1. Calculate using bash, never manually
2. Must be positive integer
3. Historical timestamps must be < current time
4. Time ranges: `start_time < end_time`
5. Convert event timestamps: `api_timestamp = event_timestamp / 1000`

**Common errors:**
- Wrong year (2024 vs 2025)
- Milliseconds in API parameter (off by 1000x)
- Future timestamps for historical queries

### IOC Types

Valid values for `ioc_type` parameter:

| Type | Aliases | Description |
|------|---------|-------------|
| `file_hash` | `hash` | MD5, SHA1, SHA256 |
| `domain` | - | Domain name |
| `ip` | - | IP address |
| `file_path` | - | Full file path |
| `file_name` | - | File name only |
| `user` | `username` | Username |
| `service_name` | - | Service name |
| `package_name` | - | Package name |
| `hostname` | - | Hostname |

**Validation:**
- Must be one of the above values (case-sensitive)
- Plural forms (`file_hashes`, `domains`) are NOT valid for API calls
- Use singular form always

### IOC Values

**Validation by type:**

| IOC Type | Format | Example |
|----------|--------|---------|
| `file_hash` | Hex string (32/40/64 chars) | `d41d8cd98f00b204e9800998ecf8427e` |
| `domain` | Valid domain | `example.com` |
| `ip` | IPv4 or IPv6 | `192.168.1.1` |
| `file_path` | Absolute path | `/usr/bin/bash` or `C:\Windows\System32\cmd.exe` |
| `file_name` | File name only | `svchost.exe` |

**Wildcards:** Use `%` for prefix/suffix matching (e.g., `%svchost.exe`)

### JSON Arrays (for batch operations)

**Validation:**
- Must be valid JSON array syntax
- Each object must have required fields
- Check max batch size (typically 1000 items)

**Example (batch_search_iocs):**
```json
[
  {"type": "file_hash", "value": "abc123..."},
  {"type": "domain", "value": "malware.com"}
]
```

**Common errors:**
- Missing quotes around strings
- Trailing commas
- Using plural type names (`file_hashes` instead of `file_hash`)

### Sensor Selectors

Sensor selectors use [bexpr](https://github.com/hashicorp/go-bexpr) syntax.

**Validation:**
- `*` matches all sensors
- Field names must be valid (see AUTOINIT.md for list)
- String values must be quoted in comparisons
- Platform values: `windows`, `linux`, `macos` (lowercase)

**Examples:**
```
*                                    # All sensors
plat == windows                      # Windows only
plat == linux and hostname contains "web"
"prod" in tags                       # Tag membership
```

## Validation Checklist

Before making any API call, verify:

- [ ] OID is valid UUID format (36 chars with dashes)
- [ ] Timestamps calculated via bash, not manually
- [ ] Time ranges have start < end
- [ ] IOC types use singular form
- [ ] JSON arrays are valid syntax
- [ ] Required parameters are present
- [ ] Parameter names match function documentation exactly

## Error Recovery

When validation fails, **try to self-correct before asking the user**:

### 1. Auto-Recovery Actions (Try These First)

| Error | Auto-Recovery Action |
|-------|---------------------|
| Received org name instead of OID | Call `get_org_oid_by_name` to look up the UUID |
| Received sensor hostname instead of SID | Call `search_hosts` to find the sensor ID |
| Timestamp looks wrong (future date, wrong year) | Re-run bash `date` command to get correct value |
| IOC type is plural (`file_hashes`) | Convert to singular (`file_hash`) automatically |
| JSON parse error | Check for common issues: missing quotes, trailing commas |
| Unknown platform code | Look up in CONSTANTS.md |

### 2. Retry Logic

- **Max 2 retries** for recoverable errors
- After each retry, log what was attempted and why it failed
- If the same error occurs twice, stop retrying

### 3. Only Ask User When

- Multiple valid options exist and user preference matters
- Required information is genuinely missing (no lookup available)
- After 2 failed auto-recovery attempts
- Security-sensitive operations need confirmation

### 4. Error Reporting (Last Resort)

When you must report an error:
- State what you tried to auto-recover
- Explain specifically what's needed
- Provide an example of the correct format

## Adding Validation to Function Docs

Each function .md file should include a validation section:

```markdown
## Parameter Validation

| Parameter | Format | Validation |
|-----------|--------|------------|
| oid | UUID | 36 chars, dashes required |
| start_time | Unix seconds | Must be < current time |
| ioc_type | string | One of: file_hash, domain, ip, ... |

**Pre-call checklist:**
- [ ] OID is UUID (not org name)
- [ ] Timestamps from bash
- [ ] IOC type is singular form
```
