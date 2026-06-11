# Microsoft Ecosystem Adapters Reference

This is the **authoritative decision guide** for ingesting Microsoft telemetry into LimaCharlie. Read this file BEFORE configuring any adapter for a Microsoft data source (Defender, Office 365 / M365, Entra ID / Azure AD, Azure, Windows Event Logs). The mappings here were derived from the actual LimaCharlie parsers and verified against official Microsoft documentation — do not guess or improvise alternatives.

## The Core Principle

The `client_options.platform` value selects the **server-side parser**, so it must match the **format of the feed**, NOT the product name and NOT the adapter type:

1. **Same product, different feeds → different platforms.** Microsoft exposes the same product through multiple APIs with different payload shapes. Example: Defender raw telemetry (Streaming API) and Defender alerts (Graph API) are different feeds; Entra ID logs via Event Hub and Entra ID risk detections via Graph are different feeds.
2. **The `azure_event_hub` adapter is a transport, not a source.** Its `platform` must describe what is streamed INTO the hub (e.g. `msdefender`, `azure_ad`, `azure_monitor`), never the hub itself.

## Decision Matrix

Find the row matching the data you want, then use EXACTLY that adapter type and `platform`:

| Data you want | Microsoft feed | Adapter type (`sensor_type`) | `platform` |
|---|---|---|---|
| Defender raw endpoint telemetry (process, network, file, registry, logon, image-load events) | Defender XDR **Streaming API** → Event Hub | `azure_event_hub` | `msdefender` |
| Defender XDR **alerts** (Defender for Endpoint/Office 365/Identity/Cloud Apps, Entra ID Protection, Purview DLP) | Microsoft Graph `security/alerts_v2` (polled) | `defender` | `msdefender` |
| M365 / Office 365 **unified audit log** (Exchange, SharePoint, Teams, DLP, Entra directory & sign-in audit records) | Office 365 Management Activity API | `office365` | `office365` |
| Entra ID **full log stream** (SignInLogs, AuditLogs, NonInteractiveUserSignInLogs, ProvisioningLogs, RiskyUsers, …) | Entra ID diagnostic settings → Event Hub | `azure_event_hub` | `azure_ad` |
| Entra ID Protection **risk detections only** | Microsoft Graph `identityProtection/riskDetections` (polled) | `entraid` | `entraid` |
| Azure **activity log / resource diagnostic logs** (generic) | Azure Monitor diagnostic settings → Event Hub | `azure_event_hub` | `azure_monitor` |
| Azure Key Vault audit logs | diagnostic settings → Event Hub | `azure_event_hub` | `azure_key_vault` |
| Azure Kubernetes Service logs | diagnostic settings → Event Hub | `azure_event_hub` | `azure_kubernetes_service` |
| Azure Network Security Group resource logs | diagnostic settings → Event Hub | `azure_event_hub` | `azure_network_security_group` |
| Azure SQL audit logs | diagnostic settings → Event Hub | `azure_event_hub` | `azure_sql_audit` |
| Event Hub **namespace's own** diagnostic logs | diagnostic settings → Event Hub | `azure_event_hub` | `azure_event_hub_namespace` |
| Live Windows Event Logs from a host (no EDR) | Windows Event Log API (local subscription) | `wel` (on-prem, Windows binary only) | `wel` |
| Offline `.evtx` files (DFIR / historical) | local file | `evtx` (on-prem binary) | `wel` |
| Any other Microsoft Graph endpoint (custom) | Microsoft Graph, user-supplied path (polled) | `ms_graph` | `json` + manual `mapping` |
| Defender for Cloud alerts/recommendations | Continuous export → Event Hub | `azure_event_hub` | `json` + manual `mapping` (uses the Security alerts REST schema, NOT the `records` envelope) |

The webhook adapter can substitute for `azure_event_hub` as a transport (e.g. data relayed by Logic Apps); the same `platform` rules apply — the platform follows the payload format.

## Hard Rules (the mistakes to never make)

- **NEVER default to `platform: json` for a feed that has a dedicated platform in the matrix above.** The dedicated parsers extract event type and timestamp automatically, and the `msdefender` parser additionally splits device telemetry into one LimaCharlie sensor per Defender device. With `json` you lose all of that and must hand-build a `mapping` that will be worse.
- **NEVER use `azure_event_hub_namespace` as the platform for "data arriving via an Event Hub".** It exists solely for the Event Hub namespace's own diagnostic logs. This is the most common Microsoft platform mistake.
- **`azure_ad` vs `entraid` are NOT interchangeable**, despite naming both the same product:
  - `azure_ad` parses the Event Hub diagnostic-stream envelope (`records` array, `category`, `time`). Use it for Entra ID logs streamed via Event Hub.
  - `entraid` parses Graph Identity Protection risk-detection objects (`activity`, `detectedDateTime`). Use it ONLY with the `entraid` adapter (riskDetections polling).
  - Crossing them silently breaks event-type and timestamp extraction.
- **`evtx` is an adapter type, not a platform.** There is no `evtx` platform; EVTX file ingestion uses `platform: wel`.
- **Platform strings keep legacy Microsoft product names.** Entra ID was Azure AD (`azure_ad`), Microsoft 365 was Office 365 (`office365`), Defender XDR was M365 Defender (`msdefender`). Do not "fix" these to modern names — `microsoft365`, `m365`, `defender_xdr` etc. are not valid platforms. Resolve all platform strings against CONSTANTS.md.
- **Adapter type ≠ platform**, even when spelled identically. `entraid` and `office365` are each both an adapter type and a platform (they happen to pair); `azure_event_hub` is only an adapter type; `azure_ad` is only a platform. The adapter type for the M365 audit log is `office365`, not `o365` (`o365` is only the source-code directory name in usp-adapters).

## What Each Parser Expects (troubleshooting)

If events arrive with empty/`unknown_event` types or zero timestamps, the platform doesn't match the payload shape. Expected shapes:

| `platform` | Expected payload | Event type from | Timestamp from |
|---|---|---|---|
| `msdefender` | `{"records":[{"category":"AdvancedHunting-<Table>","properties":{...}}]}` (Streaming API) or a bare Graph alert object | `category` (Device* tables map to native LC types: `NEW_PROCESS`, `NETWORK_CONNECTIONS`, `MODULE_LOAD`, `FILE_CREATE`, `REGISTRY_WRITE`, …); falls back to `title` | `properties.Timestamp`, falling back to `time` / `createdDateTime` |
| `office365` | flat unified-audit-log record (Management Activity API common schema) | `Operation` | `CreationTime` |
| `azure_ad`, `azure_monitor`, `azure_key_vault`, `azure_kubernetes_service`, `azure_network_security_group`, `azure_sql_audit`, `azure_event_hub_namespace` | Azure Monitor envelope: `{"records":[{"category":"...","time":"...", ...}]}` | `category` | `time` |
| `entraid` | Graph `riskDetection` object | `activity` (fallback `category`) | `detectedDateTime` |
| `wel` | Windows event XML (wel adapter) or parsed JSON (evtx adapter) | `Event/System/Provider/Name` | `Event/System/TimeCreated/SystemTime` |

Notes:
- `msdefender` device records (`DeviceId`/`DeviceName` present) are re-homed to a per-device LimaCharlie sensor — expect one sensor per Defender device, not one per adapter.
- The Defender XDR Streaming API can stream many Advanced Hunting tables (DeviceProcessEvents, DeviceNetworkEvents, DeviceFileEvents, DeviceRegistryEvents, DeviceLogonEvents, DeviceImageLoadEvents, DeviceEvents, EmailEvents, IdentityLogonEvents, CloudAppEvents, AlertInfo, AlertEvidence, …) — all are handled by `platform: msdefender`.

## Canonical Configurations

### Defender raw telemetry via Event Hub (Streaming API)

Azure side: Defender XDR portal → Settings → Microsoft Defender XDR → Streaming API → add Event Hub destination, select the Advanced Hunting tables.

```yaml
sensor_type: azure_event_hub
azure_event_hub:
  connection_string: "hive://secret/defender-eh-connection"   # MUST include EntityPath=<hub-name>
  client_options:
    identity:
      oid: "<oid>"
      installation_key: "<iid>"
    platform: msdefender
    sensor_seed_key: defender-stream
    hostname: defender-stream
```

### Defender XDR alerts via Graph (polled)

Entra app registration with `SecurityAlert.Read.All` (application) permission.

```yaml
sensor_type: defender
defender:
  tenant_id: "<tenant-id>"
  client_id: "<app-client-id>"
  client_secret: "hive://secret/defender-client-secret"
  client_options:
    identity:
      oid: "<oid>"
      installation_key: "<iid>"
    platform: msdefender
    sensor_seed_key: defender-alerts
    hostname: defender-alerts
```

### M365 unified audit log (Management Activity API)

Requires unified audit logging enabled in the tenant; app needs Office 365 Management API permissions.

```yaml
sensor_type: office365
office365:
  domain: "yourtenant.onmicrosoft.com"
  tenant_id: "<tenant-id>"
  publisher_id: "<tenant-id>"          # usually same as tenant_id
  client_id: "<app-client-id>"
  client_secret: "hive://secret/o365-client-secret"
  endpoint: enterprise                  # or gcc-gov / gcc-high-gov / dod-gov
  content_types: "Audit.AzureActiveDirectory,Audit.Exchange,Audit.SharePoint,Audit.General,DLP.All"
  client_options:
    identity:
      oid: "<oid>"
      installation_key: "<iid>"
    platform: office365
    sensor_seed_key: m365-audit
    hostname: m365-audit
```

Do NOT add a manual `mapping` block — the `office365` parser already handles `Operation`/`CreationTime`.

### Entra ID full logs via Event Hub (diagnostic settings)

Azure side: Entra ID → Diagnostic settings → stream chosen categories (SignInLogs, AuditLogs, …) to an Event Hub.

```yaml
sensor_type: azure_event_hub
azure_event_hub:
  connection_string: "hive://secret/entra-eh-connection"
  client_options:
    identity:
      oid: "<oid>"
      installation_key: "<iid>"
    platform: azure_ad                  # NOT entraid — see Hard Rules
    sensor_seed_key: entra-logs
    hostname: entra-logs
```

### Entra ID Protection risk detections (polled)

Entra app registration with `IdentityRiskEvent.Read.All` (application) permission.

```yaml
sensor_type: entraid
entraid:
  tenant_id: "<tenant-id>"
  client_id: "<app-client-id>"
  client_secret: "hive://secret/entra-client-secret"
  client_options:
    identity:
      oid: "<oid>"
      installation_key: "<iid>"
    platform: entraid
    sensor_seed_key: entra-risk
    hostname: entra-risk
```

### Windows Event Logs — live (on-prem, Windows host)

```bash
./lc_adapter wel \
  client_options.identity.installation_key=<IID> \
  client_options.identity.oid=<OID> \
  client_options.platform=wel \
  client_options.sensor_seed_key=<hostname>-wel \
  "evt_sources=Security:*,System:*,Application:*"
```

### EVTX file — offline (DFIR)

```bash
./lc_adapter evtx \
  client_options.identity.installation_key=<IID> \
  client_options.identity.oid=<OID> \
  client_options.platform=wel \
  client_options.sensor_seed_key=ir-evidence-01 \
  file_path=/cases/host1/Security.evtx
```

## Feed Overlap — avoid double ingestion

When proposing a Microsoft ingestion plan, warn about these overlaps instead of recommending everything:

- **Entra identity events appear in three feeds**: the M365 unified audit log (`Audit.AzureActiveDirectory` content type), the Entra Event Hub stream (SignInLogs/AuditLogs), and — for risk events — Graph riskDetections. Ingesting more than one duplicates identity telemetry. The Event Hub stream is the richest; `Audit.AzureActiveDirectory` is sufficient if the office365 adapter is already deployed.
- **Defender alerts appear in two feeds**: Graph `alerts_v2` (the `defender` adapter) and the Streaming API `AlertInfo`/`AlertEvidence` tables. Pick one.
- **Entra ID Protection alerts** are included in Graph `alerts_v2` (`serviceSource: azureAdIdentityProtection`) — if the `defender` adapter is deployed, the `entraid` adapter adds detail but overlaps.
- **WEL vs EDR sensor**: hosts running the LimaCharlie EDR agent already provide rich endpoint telemetry; the `wel` adapter is for hosts WITHOUT the EDR agent or for specific channels not otherwise collected.

## Official Microsoft References

- Defender XDR Streaming API: https://learn.microsoft.com/en-us/defender-xdr/streaming-api (supported tables: https://learn.microsoft.com/en-us/defender-xdr/supported-event-types)
- Graph security alerts_v2: https://learn.microsoft.com/en-us/graph/api/resources/security-alert
- O365 Management Activity API: https://learn.microsoft.com/en-us/office/office-365-management-api/office-365-management-activity-api-reference
- Entra ID log streaming: https://learn.microsoft.com/en-us/entra/identity/monitoring-health/howto-stream-logs-to-event-hub
- Graph riskDetections: https://learn.microsoft.com/en-us/graph/api/resources/riskdetection
- Azure Monitor → Event Hubs: https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/stream-monitoring-data-event-hubs
