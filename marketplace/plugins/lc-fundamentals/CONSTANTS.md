# LimaCharlie Constants Reference

This is the **authoritative source of truth** for LimaCharlie constants. Always reference this file instead of hardcoding values or using values from other documentation.

**Source:** Canonical LimaCharlie platform/architecture identification scheme, kept in sync with the LimaCharlie platform. This file is the authoritative reference — do not copy platform codes from SDK source or other docs, which may lag behind.

## Platform Codes

> **NEVER guess a platform ID, and NEVER infer the platform/OS behind one from memory, the leading hex digit, or pattern matching.** Platform codes are not guessable. Whenever you have a platform ID (or string) and need to know which platform/OS it represents — or you need the code for a given platform — resolve it ONLY against the tables in this file. If the exact code is not listed here, treat it as unknown; do not approximate to the "closest" platform.

Platform codes are returned as `uint32` in sensor info responses.

> **Encoding — read this before interpreting a platform code.** The platform lives in the **high byte** of the `uint32` (the top *two* hex digits, e.g. `0x31000000`). Do **NOT** infer the platform from the top nibble alone. `0x30000000` is macOS but `0x31000000` is Harmony — different platforms that merely share the leading `3`. Always match the *full* code against the tables below; if a code is not in these tables it is unknown, not "the closest family".

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
| Xml | `xml` | 0x02000000 | 33554432 |
| WEL | `wel` | 0x03000000 | 50331648 |
| MS Defender | `msdefender` | 0x04000000 | 67108864 |
| Duo | `duo` | 0x05000000 | 83886080 |
| Okta | `okta` | 0x06000000 | 100663296 |
| SentinelOne | `sentinel_one` | 0x07000000 | 117440512 |
| GitHub | `github` | 0x08000000 | 134217728 |
| Slack | `slack` | 0x09000000 | 150994944 |
| CEF | `cef` | 0x0A000000 | 167772160 |
| LCEvent | `lc_event` | 0x0B000000 | 184549376 |
| Azure AD | `azure_ad` | 0x0C000000 | 201326592 |
| Azure Monitor | `azure_monitor` | 0x0D000000 | 218103808 |
| CanaryToken | `canary_token` | 0x0E000000 | 234881024 |
| GuardDuty | `guard_duty` | 0x0F000000 | 251658240 |
| ITGlue | `itglue` | 0x11000000 | 285212672 |
| K8sPods | `k8s_pods` | 0x12000000 | 301989888 |
| Zeek | `zeek` | 0x13000000 | 318767104 |
| Mac Unified Logging | `mac_unified_logging` | 0x14000000 | 335544320 |
| Azure Event Hub Namespace | `azure_event_hub_namespace` | 0x15000000 | 352321536 |
| Azure Key Vault | `azure_key_vault` | 0x16000000 | 369098752 |
| Azure Kubernetes Service | `azure_kubernetes_service` | 0x17000000 | 385875968 |
| Azure Network Security Group | `azure_network_security_group` | 0x18000000 | 402653184 |
| Azure SQL Audit | `azure_sql_audit` | 0x19000000 | 419430400 |
| Email | `email` | 0x1A000000 | 436207616 |
| Fortigate | `fortigate` | 0x1B000000 | 452984832 |
| Trend Micro Worry-Free | `trend_worryfree` | 0x1C000000 | 469762048 |
| Netscaler | `netscaler` | 0x1D000000 | 486539264 |
| Palo Alto Firewall | `paloalto_fw` | 0x1E000000 | 503316480 |
| IIS Logs | `iis` | 0x1F000000 | 520093696 |
| HubSpot | `hubspot` | 0x21000000 | 553648128 |
| Zendesk | `zendesk` | 0x22000000 | 570425344 |
| PandaDoc | `pandadoc` | 0x23000000 | 587202560 |
| Falcon Cloud | `falconcloud` | 0x24000000 | 603979776 |
| Mimecast | `mimecast` | 0x25000000 | 620756992 |
| Sublime | `sublime` | 0x26000000 | 637534208 |
| Box | `box` | 0x27000000 | 654311424 |
| Cylance | `cylance` | 0x28000000 | 671088640 |
| Proofpoint | `proofpoint` | 0x29000000 | 687865856 |
| Entra ID | `entraid` | 0x2A000000 | 704643072 |
| Wiz | `wiz` | 0x2B000000 | 721420288 |
| Bitwarden | `bitwarden` | 0x2C000000 | 738197504 |
| Trend Micro | `trend_micro` | 0x2D000000 | 754974720 |
| OpenTelemetry | `otel` | 0x2E000000 | 771751936 |
| Cortex XDR | `cortex_xdr` | 0x2F000000 | 788529152 |
| Harmony | `harmony` | 0x31000000 | 822083584 |
| ThreatLocker | `threatlocker` | 0x32000000 | 838860800 |
| HaloPSA | `halopsa` | 0x33000000 | 855638016 |
| Cato | `cato` | 0x34000000 | 872415232 |
| Gmail | `gmail` | 0x35000000 | 889192448 |

> The gaps at `0x20000000` and `0x30000000` are intentional: those high-byte values are the endpoint platforms Linux and macOS (see the table above), so they are not reused for USP adapters.

### Microsoft Source → Adapter + Platform Selection

Microsoft exposes the same products through multiple feeds with different formats, so the `platform` follows the **feed**, not the product. Resolve Microsoft ingestion ONLY against this table — never guess:

| Data wanted | Feed | Adapter type | `platform` |
|---|---|---|---|
| Defender raw endpoint telemetry (Device* events) | Defender XDR Streaming API → Event Hub | `azure_event_hub` | `msdefender` |
| Defender XDR alerts (all Defender products + Entra ID Protection + Purview DLP) | Graph `security/alerts_v2` (polled) | `defender` | `msdefender` |
| M365/O365 unified audit log (Exchange, SharePoint, Teams, Entra audit) | O365 Management Activity API | `office365` | `office365` |
| Entra ID full logs (SignInLogs, AuditLogs — incl. app consent / OAuth2 grant / directory-change operations —, ProvisioningLogs, …) | Entra diagnostic settings → Event Hub | `azure_event_hub` | `azure_ad` |
| Entra ID Protection risk detections only (NOT audit/consent events) | Graph `identityProtection/riskDetections` (polled) | `entraid` | `entraid` |
| Azure activity/resource diagnostic logs | Azure Monitor → Event Hub | `azure_event_hub` | `azure_monitor` (or the resource-specific `azure_key_vault`, `azure_kubernetes_service`, `azure_network_security_group`, `azure_sql_audit`) |
| Event Hub namespace's OWN diagnostic logs | diagnostic settings → Event Hub | `azure_event_hub` | `azure_event_hub_namespace` |
| Live Windows Event Logs (host without EDR) | local WEL subscription | `wel` (Windows binary) | `wel` |
| Offline `.evtx` files | local file | `evtx` | `wel` |
| Custom Graph endpoint | Graph (polled, `url` config) | `ms_graph` | `json` + manual mapping |

Hard rules:
- **NEVER use `platform: json` for a Microsoft feed listed above** — each has a purpose-built parser; `json` breaks event-type/timestamp extraction and (for `msdefender`) per-device sensor splitting.
- **NEVER use `azure_event_hub_namespace` for data merely transiting an Event Hub** — it is only for the namespace's own diagnostic logs.
- **`azure_ad` ≠ `entraid`**: `azure_ad` parses the Event Hub `records` envelope; `entraid` parses Graph riskDetection objects. They are not interchangeable.
- **There is no `evtx` platform** — EVTX files use `platform: wel`.
- Platform strings keep legacy product names (`azure_ad`, `office365`, `msdefender`); modern names like `microsoft365` or `defender_xdr` are not valid platforms.

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

## Cases Extension (`ext-cases`)

See [CASES_CONSTANTS.md](./CASES_CONSTANTS.md) for case status, severity, classification, entity types, verdicts, and note types.

## Sensor Selector Reference

Sensor selectors use [bexpr](https://github.com/hashicorp/go-bexpr) syntax to filter sensors. Use `*` to match all sensors.

### Available Fields

| Field | Type | Description |
|-------|------|-------------|
| `sid` | string | Sensor ID (UUID) |
| `oid` | string | Organization ID (UUID) |
| `iid` | string | Installation Key ID (UUID) |
| `plat` | string | Platform name |
| `ext_plat` | string | Extended platform (for multi-platform adapters) |
| `arch` | string | Architecture |
| `hostname` | string | Sensor hostname |
| `ext_ip` | string | External IP address |
| `int_ip` | string | Internal IP address |
| `mac_addr` | string | MAC address |
| `did` | string | Device ID |
| `enroll` | int | Enrollment timestamp |
| `alive` | int | Last seen timestamp |
| `is_del` | bool | Sensor is deleted |
| `isolated` | bool | Sensor is network isolated |
| `should_isolate` | bool | Sensor should be isolated |
| `kernel` | bool | Kernel mode enabled |
| `sealed` | bool | Sensor is sealed |
| `should_seal` | bool | Sensor should be sealed |
| `tags` | string[] | Sensor tags (use `in` operator) |

### Example Selectors

```
plat == windows                           # All Windows sensors
plat == windows and arch == x64           # 64-bit Windows only
plat == linux and hostname contains "web" # Linux with "web" in hostname
"prod" in tags                            # Sensors tagged "prod"
plat == windows and not isolated          # Non-isolated Windows
ext_plat == windows                       # Carbon Black/Crowdstrike reporting Windows endpoints
```

## UUID Format

Organization ID (OID) and Sensor ID (SID) must be UUID format:

```
Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Length: 36 characters (including dashes)
Example: c7e8f940-1234-5678-abcd-1234567890ab
```

**NEVER use organization names where OID is required.**
