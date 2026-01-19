# LimaCharlie Constants Reference

This is the **authoritative source of truth** for LimaCharlie constants. Always reference this file instead of hardcoding values or using values from other documentation.

**Source:** [go-limacharlie/limacharlie/identification.go](https://github.com/refractionPOINT/go-limacharlie)

## Platform Codes

Platform codes are returned as `uint32` in sensor info responses.

| Platform | String | Hex | Decimal |
|----------|--------|-----|---------|
| Windows | `windows` | 0x10000000 | 268435456 |
| Linux | `linux` | 0x20000000 | 536870912 |
| macOS | `macos` | 0x30000000 | 805306368 |
| iOS | `ios` | 0x40000000 | 1073741824 |
| Android | `android` | 0x50000000 | 1342177280 |
| ChromeOS | `chrome` | 0x60000000 | 1610612736 |
| VPN | `vpn` | 0x70000000 | 1879048192 |

### USP Adapter Platforms

| Platform | String | Hex | Decimal |
|----------|--------|-----|---------|
| Text | `text` | 0x80000000 | 2147483648 |
| JSON | `json` | 0x90000000 | 2415919104 |
| GCP | `gcp` | 0xA0000000 | 2684354560 |
| AWS | `aws` | 0xB0000000 | 2952790016 |
| Carbon Black | `carbon_black` | 0xC0000000 | 3221225472 |
| 1Password | `1password` | 0xD0000000 | 3489660928 |
| Office365 | `office365` | 0xE0000000 | 3758096384 |
| Sophos | `sophos` | 0xF0000000 | 4026531840 |
| Crowdstrike | `crowdstrike` | 0x01000000 | 16777216 |
| MS Defender | `msdefender` | 0x04000000 | 67108864 |
| Duo | `duo` | 0x05000000 | 83886080 |
| Okta | `okta` | 0x06000000 | 100663296 |
| SentinelOne | `sentinel_one` | 0x07000000 | 117440512 |
| GitHub | `github` | 0x08000000 | 134217728 |
| Slack | `slack` | 0x09000000 | 150994944 |
| Azure AD | `azure_ad` | 0x0C000000 | 201326592 |
| Azure Monitor | `azure_monitor` | 0x0D000000 | 218103808 |

## Architecture Codes

| Architecture | String | Hex | Decimal |
|--------------|--------|-----|---------|
| x86 | `x86` | 0x00000001 | 1 |
| x64 | `x64` | 0x00000002 | 2 |
| ARM | `arm` | 0x00000003 | 3 |
| ARM64 | `arm64` | 0x00000004 | 4 |
| Alpine64 | `alpine64` | 0x00000005 | 5 |
| Chromium | `chromium` | 0x00000006 | 6 |
| WireGuard | `wireguard` | 0x00000007 | 7 |
| ARM (L) | `arml` | 0x00000008 | 8 |
| USP Adapter | `usp_adapter` | 0x00000009 | 9 |

## IOC Types

Valid IOC types for `search_iocs` and `batch_search_iocs` tools.

**Source:** [lc-mcp-server/internal/tools/historical/historical.go](https://github.com/refractionPOINT/lc-mcp-server)

| Type | Aliases | Description |
|------|---------|-------------|
| `file_hash` | `hash` | File hash (MD5, SHA1, SHA256) |
| `domain` | - | Domain name |
| `ip` | - | IP address |
| `file_path` | - | Full file path |
| `file_name` | - | File name only |
| `user` | `username` | Username |
| `service_name` | - | Service name |
| `package_name` | - | Package name |
| `hostname` | - | Hostname (uses different endpoint) |

### IOC Type Mapping (Extraction to Search)

When extracting IOCs from threat reports (plural field names) and searching via API (singular type values):

| Extraction Field | Search Type |
|------------------|-------------|
| `file_hashes` | `file_hash` |
| `domains` | `domain` |
| `ips` | `ip` |
| `file_names` | `file_name` |
| `file_paths` | `file_path` |
| `urls` | (extract domain/ip first) |

## Timestamps

### Format Rules

| Context | Format | Digits | Example |
|---------|--------|--------|---------|
| Detection/event data | Milliseconds | 13 | 1705420800000 |
| API parameters | Seconds | 10 | 1705420800 |

### Conversion

```bash
# Current time in seconds (for API calls)
date +%s

# Current time in milliseconds (for comparisons with event data)
echo $(($(date +%s) * 1000))

# Convert event timestamp to API format
api_timestamp=$((event_timestamp / 1000))

# Relative times
date -d '1 hour ago' +%s
date -d '24 hours ago' +%s
date -d '7 days ago' +%s
```

**NEVER calculate timestamps manually** - LLMs consistently produce incorrect values.

## Billing Amounts

All billing API responses return amounts in **CENTS**, not dollars.

```
display_amount = api_amount / 100

Example:
  API returns: {"total": 25342}
  Display: $253.42
```

## UUID Format

Organization ID (OID) and Sensor ID (SID) must be UUID format:

```
Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Length: 36 characters (including dashes)
Example: c7e8f940-1234-5678-abcd-1234567890ab
```

**NEVER use organization names where OID is required.**
