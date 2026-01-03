---
description: Pre-defined report templates combining data collection and visualization. Usage: /lc-essentials:reporting-templates
---

# Reporting Templates

Present the user with a menu of pre-defined report templates. Each template uses the `reporting` skill for data collection. **By default, output is displayed in the console as formatted markdown/tables.** HTML visualization is available as an optional output format.

## Instructions

Use the `AskUserQuestion` tool to present the template menu:

```
AskUserQuestion(
  questions=[{
    "question": "Which report template would you like to generate?",
    "header": "Template",
    "options": [
      {"label": "MSSP Executive Summary", "description": "High-level metrics across all customers: sensor counts, detection volumes, SLA status"},
      {"label": "Customer Health Dashboard", "description": "Per-org health scores, offline sensors, detection trends with drill-down"},
      {"label": "Monthly Billing Report", "description": "Usage statistics and billing data for customer invoicing"},
      {"label": "Detection Analytics", "description": "Security activity breakdown: top categories, trends, alert volumes by org"}
    ],
    "multiSelect": false
  }]
)
```

## Data Processing Guidelines

### Currency Conversion (CRITICAL)

**The Stripe API returns all monetary amounts in CENTS, not dollars.**

When processing billing data from `get_billing_details`:
- `amount`, `amount_due`, `balance`, `unit_amount` → **divide by 100** for USD display
- Example: `amount_due: 10684` = **$106.84** (NOT $10,684)
- Example: `balance: -2048` = **-$20.48** credit (NOT -$2,048)

**Validation**: Always verify that line item amounts sum to the total. If they don't match expectations, you likely have a unit conversion error.

```
# Correct conversion
amount_cents = 10684
amount_usd = amount_cents / 100  # $106.84

# Display format
f"${amount_usd:,.2f}"  # "$106.84"
```

### Bytes Conversion

When displaying data volumes:
- Raw bytes → divide by `1024^3` for GB
- Always specify units explicitly (GB, TB, MB)

---

## Template Definitions

### Template 1: MSSP Executive Summary

**Purpose**: High-level overview for MSSP leadership - quick health check across all customers.

**Data Collection** (reporting skill):
- List all organizations
- Per-org: sensor count (online/offline), detection count (7 days), SLA status
- Aggregate totals across fleet

**Console Output** (default):
- Summary section: Total orgs, Total sensors, Total detections, Fleet coverage %
- Platform breakdown table
- Top 10 orgs by detection volume table
- All orgs health status table with indicators (green/yellow/red shown as text badges)

**Time Range**: Default last 7 days, prompt user to confirm.

---

### Template 2: Customer Health Dashboard

**Purpose**: Operational dashboard for SOC teams - identify customers needing attention.

**Data Collection** (reporting skill):
- List all organizations
- Per-org: sensor inventory with online/offline status, detection counts by category
- Identify: offline sensors >24h, orgs below SLA, detection spikes

**Console Output** (default):
- Fleet coverage percentage with status indicator
- Org health matrix table (orgs x metrics with status badges)
- Offline sensors by org table
- Alert list: Orgs requiring immediate attention (highlighted)

**Time Range**: Default last 7 days, prompt user to confirm.

---

### Template 3: Monthly Billing Report

**Purpose**: Usage data for customer invoicing and capacity planning.

**Data Collection** (reporting skill):
- List all organizations
- Per-org: billing details, usage stats (events, outputs, storage)
- Aggregate: total usage, month-over-month comparison if available

**CRITICAL: Currency Handling**
- All Stripe API amounts are in **CENTS** - divide by 100 for USD
- `amount_due: 10684` → `$106.84`
- `balance: -2048` → `-$20.48` (credit)
- Always validate: sum of line items should equal total

**Console Output** (default):
- Summary section: Total events, Total output bytes (GB), Active sensors
- Top consumers table (sorted by usage)
- Full org breakdown table with usage columns
- Usage distribution by tier
- All monetary values displayed in USD with proper conversion

**Time Range**: Prompt user for billing period (default: previous calendar month).

---

### Template 4: Detection Analytics

**Purpose**: Security activity analysis for threat intelligence and tuning.

**Data Collection** (reporting skill):
- List all organizations
- Per-org: detections by category, top detection rules triggered
- Aggregate: fleet-wide detection categories, rule effectiveness

**Console Output** (default):
- Summary section: Total detections, Unique categories, Orgs with alerts
- Detection categories table (top 10)
- Detections by organization table
- Top triggered rules table with counts
- Warning section: Detection limits reached (if applicable)

**Time Range**: Default last 30 days, prompt user to confirm.

---

## Execution Flow

Once the user selects a template:

1. **Confirm Time Range**: Use `AskUserQuestion` to confirm or customize the time period
2. **Confirm Scope**: Ask if they want all orgs or a specific subset
3. **Collect Data**: Use the `lc-essentials:limacharlie-call` skill to list organizations, then spawn `org-reporter` agents in parallel to collect data from each organization
4. **Display Results**: Output the report as formatted markdown tables directly in the console

### Optional: HTML Output

If the user explicitly requests HTML output (e.g., "generate as HTML", "create dashboard file"), then:
1. Spawn `html-renderer` agent to create the visualization dashboard
2. Save to `/tmp/{report-name}-{date}.html`
3. Open in browser using `xdg-open` or serve via HTTP server

## Example Conversation Flow

```
User: /lc-essentials:reporting-templates

Assistant: [Presents template menu]

User: MSSP Executive Summary

Assistant: [Confirms time range, collects data via limacharlie-call skill, displays formatted report in console]

Assistant: Here is your MSSP Executive Summary:

```

═══════════════════════════════════════════════════════════════════════════════
                        MSSP EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════════════════
Generated: 2025-12-30 14:00:00 UTC
Time Range: 2025-12-23 00:00:00 UTC to 2025-12-30 23:59:59 UTC (7 days)
Organizations Processed: 26 of 26 (100% success rate)
═══════════════════════════════════════════════════════════════════════════════

## Fleet Overview

┌─────────────────────────┬────────────────┐
│ Metric                  │ Value          │
├─────────────────────────┼────────────────┤
│ Total Organizations     │ 26             │
│ Total Sensors           │ 145            │
│ Sensors Online          │ 138 (95.2%)    │
│ Sensors Offline         │ 7 (4.8%)       │
│ Fleet Coverage          │ 95.2%          │
│ Total Detections (7d)   │ 1,247          │
│ Orgs with Detections    │ 18             │
│ Orgs Passing SLA (>90%) │ 24 of 26       │
└─────────────────────────┴────────────────┘

## Platform Distribution

┌──────────────┬───────┬────────────┐
│ Platform     │ Count │ Percentage │
├──────────────┼───────┼────────────┤
│ Linux        │ 82    │ 56.6%      │
│ Windows      │ 48    │ 33.1%      │
│ macOS        │ 12    │ 8.3%       │
│ Chrome OS    │ 3     │ 2.0%       │
└──────────────┴───────┴────────────┘

## Top 10 Organizations by Detection Volume

┌────┬──────────────────────────────┬────────────┬─────────────────┐
│ #  │ Organization                 │ Detections │ Top Category    │
├────┼──────────────────────────────┼────────────┼─────────────────┤
│ 1  │ refractionPOINT              │ 342        │ network_threat  │
│ 2  │ lc-infrastructure            │ 287        │ suspicious_proc │
│ 3  │ Acme Inc. Test               │ 156        │ malware         │
│ 4  │ lc_demo                      │ 124        │ credential_acc  │
│ 5  │ PC Load Letter Enterprises   │ 89         │ persistence     │
│ 6  │ TPS Reporting Solutions      │ 76         │ lateral_move    │
│ 7  │ agentic-secops-example       │ 54         │ network_threat  │
│ 8  │ SOP Tester                   │ 43         │ discovery       │
│ 9  │ lc-probe-usa                 │ 31         │ exfiltration    │
│ 10 │ lc-probe-europe              │ 28         │ suspicious_proc │
└────┴──────────────────────────────┴────────────┴─────────────────┘

## Organization Health Status

┌──────────────────────────────┬─────────┬────────┬─────────┬────────────┬────────┬─────────┐
│ Organization                 │ Sensors │ Online │ Offline │ Coverage % │ Det(7d)│ Status  │
├──────────────────────────────┼─────────┼────────┼─────────┼────────────┼────────┼─────────┤
│ Acme Inc. Test               │ 12      │ 12     │ 0       │ 100%       │ 156    │ [GREEN] │
│ Acme Office Supplies Inc.    │ 8       │ 8      │ 0       │ 100%       │ 12     │ [GREEN] │
│ agentic-secops-example       │ 5       │ 5      │ 0       │ 100%       │ 54     │ [GREEN] │
│ lc-ctf                       │ 6       │ 5      │ 1       │ 83%        │ 15     │ [YELLOW]│
│ lc-infrastructure            │ 25      │ 23     │ 2       │ 92%        │ 287    │ [GREEN] │
│ lc_demo                      │ 18      │ 16     │ 2       │ 89%        │ 124    │ [YELLOW]│
│ refractionPOINT              │ 15      │ 14     │ 1       │ 93%        │ 342    │ [GREEN] │
│ TPS Reporting Solutions      │ 5       │ 4      │ 1       │ 80%        │ 76     │ [YELLOW]│
│ ... (18 more organizations)  │         │        │         │            │        │         │
└──────────────────────────────┴─────────┴────────┴─────────┴────────────┴────────┴─────────┘

Status Legend: [GREEN] = >95% | [YELLOW] = 80-95% | [RED] = <80%

## Attention Required

⚠️  3 organizations below 95% SLA threshold:
    • lc-ctf: 83% coverage (1 sensor offline)
    • lc_demo: 89% coverage (2 sensors offline)
    • TPS Reporting Solutions: 80% coverage (1 sensor offline)

## Detection Category Summary (Fleet-Wide)

┌─────────────────────────┬───────┬────────────┐
│ Category                │ Count │ Percentage │
├─────────────────────────┼───────┼────────────┤
│ network_threat          │ 398   │ 31.9%      │
│ suspicious_process      │ 287   │ 23.0%      │
│ malware                 │ 189   │ 15.2%      │
│ credential_access       │ 156   │ 12.5%      │
│ persistence             │ 98    │ 7.9%       │
│ other                   │ 119   │ 9.5%       │
└─────────────────────────┴───────┴────────────┘

═══════════════════════════════════════════════════════════════════════════════
Report completed: 2025-12-30 14:02:15 UTC | Execution time: 2m 15s
═══════════════════════════════════════════════════════════════════════════════
```

### Example: Customer Health Dashboard

```
═══════════════════════════════════════════════════════════════════════════════
                      CUSTOMER HEALTH DASHBOARD
═══════════════════════════════════════════════════════════════════════════════
Generated: 2025-12-30 14:00:00 UTC
Time Range: Last 7 Days | Organizations: 26
═══════════════════════════════════════════════════════════════════════════════

## Fleet Health Score: 95.2% [GREEN]

┌─────────────────────┬────────┐
│ Health Metric       │ Status │
├─────────────────────┼────────┤
│ Online Coverage     │ 95.2%  │
│ SLA Compliance      │ 92.3%  │
│ Detection Response  │ 98.1%  │
│ Data Freshness      │ 99.5%  │
└─────────────────────┴────────┘

## Organizations Requiring Attention

┌──────────────────────────────┬─────────────┬──────────────────────────────────────┐
│ Organization                 │ Issue       │ Details                              │
├──────────────────────────────┼─────────────┼──────────────────────────────────────┤
│ TPS Reporting Solutions      │ [CRITICAL]  │ 1 sensor offline >48h (SERVER-DB01)  │
│ lc_demo                      │ [WARNING]   │ 2 sensors offline >24h               │
│ lc-ctf                       │ [WARNING]   │ Detection spike: +450% vs avg        │
│ lc-infrastructure            │ [INFO]      │ 2 sensors offline <24h (maintenance) │
└──────────────────────────────┴─────────────┴──────────────────────────────────────┘

## Offline Sensors by Organization

┌──────────────────────────────┬─────────┬────────────────┬─────────────────────┐
│ Organization                 │ Offline │ Duration       │ Hostnames           │
├──────────────────────────────┼─────────┼────────────────┼─────────────────────┤
│ TPS Reporting Solutions      │ 1       │ 52 hours       │ SERVER-DB01         │
│ lc_demo                      │ 2       │ 28-36 hours    │ DESKTOP-A1, LAP-42  │
│ lc-ctf                       │ 1       │ 18 hours       │ CTF-NODE-03         │
│ lc-infrastructure            │ 2       │ 4-6 hours      │ BUILD-01, BUILD-02  │
│ refractionPOINT              │ 1       │ 2 hours        │ DEV-TEST-VM         │
└──────────────────────────────┴─────────┴────────────────┴─────────────────────┘

## Detection Trends (7-Day)

┌─────────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│ Org         │ Day 1  │ Day 2  │ Day 3  │ Day 4  │ Day 5  │ Day 6  │ Day 7  │
├─────────────┼────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ lc-ctf      │ 2      │ 3      │ 5      │ 45     │ 120    │ 89     │ 78     │ ⚠️ SPIKE
│ refraction  │ 48     │ 52     │ 47     │ 51     │ 49     │ 48     │ 47     │ STABLE
│ lc-infra    │ 38     │ 41     │ 42     │ 39     │ 44     │ 42     │ 41     │ STABLE
│ Acme Test   │ 22     │ 24     │ 21     │ 23     │ 22     │ 22     │ 22     │ STABLE
└─────────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘

## Org Health Matrix

┌──────────────────────────────┬──────────┬──────────┬──────────┬──────────┐
│ Organization                 │ Coverage │ SLA      │ Alerts   │ Overall  │
├──────────────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Acme Inc. Test               │ [GREEN]  │ [GREEN]  │ [GREEN]  │ [GREEN]  │
│ refractionPOINT              │ [GREEN]  │ [GREEN]  │ [YELLOW] │ [GREEN]  │
│ lc-infrastructure            │ [GREEN]  │ [GREEN]  │ [YELLOW] │ [GREEN]  │
│ lc_demo                      │ [YELLOW] │ [YELLOW] │ [GREEN]  │ [YELLOW] │
│ lc-ctf                       │ [YELLOW] │ [GREEN]  │ [RED]    │ [YELLOW] │
│ TPS Reporting Solutions      │ [YELLOW] │ [RED]    │ [GREEN]  │ [RED]    │
│ ... (20 more)                │          │          │          │          │
└──────────────────────────────┴──────────┴──────────┴──────────┴──────────┘

═══════════════════════════════════════════════════════════════════════════════
```

### Example: Monthly Billing Report

```
═══════════════════════════════════════════════════════════════════════════════
                       MONTHLY BILLING REPORT
═══════════════════════════════════════════════════════════════════════════════
Generated: 2025-12-30 14:00:00 UTC
Billing Period: December 2025 (2025-12-01 to 2025-12-31)
Organizations: 26
═══════════════════════════════════════════════════════════════════════════════

## Fleet Usage Summary

┌────────────────────────────┬──────────────────────┐
│ Metric                     │ Total                │
├────────────────────────────┼──────────────────────┤
│ Total Sensor Events        │ 1,247,832,456        │
│ Total Data Output          │ 3,847 GB             │
│ D&R Rule Evaluations       │ 45,230,890           │
│ Peak Concurrent Sensors    │ 142                  │
│ Active Organizations       │ 26                   │
└────────────────────────────┴──────────────────────┘

## Subscription & Billing Summary

**IMPORTANT: All amounts converted from Stripe API (cents ÷ 100 = USD)**

┌──────────────────────────────┬─────────┬────────────────┬──────────────┐
│ Service                      │ Qty     │ Unit (USD)     │ Total (USD)  │
├──────────────────────────────┼─────────┼────────────────┼──────────────┤
│ LC-INSIGHT (Licensed)        │ 42      │ $0.50/unit     │ $21.00       │
│ LCIO-EXP1-GENERAL-V1         │ 42      │ $2.00/unit     │ $84.00       │
│ SOTERIA-RULES                │ 5       │ $0.50/unit     │ $2.50        │
├──────────────────────────────┼─────────┼────────────────┼──────────────┤
│ SUBTOTAL (Licensed)          │         │                │ $107.50      │
└──────────────────────────────┴─────────┴────────────────┴──────────────┘

Raw API values for verification:
- amount_due: 10750 cents → $107.50
- balance: -2048 cents → -$20.48 (credit)

## Top 10 Consumers by Event Volume

┌────┬──────────────────────────────┬─────────────────┬────────────┬─────────────┐
│ #  │ Organization                 │ Events          │ Output GB  │ Peak Sensors│
├────┼──────────────────────────────┼─────────────────┼────────────┼─────────────┤
│ 1  │ lc-infrastructure            │ 425,000,000     │ 1,245 GB   │ 25          │
│ 2  │ refractionPOINT              │ 312,000,000     │ 892 GB     │ 15          │
│ 3  │ lc_demo                      │ 187,000,000     │ 534 GB     │ 18          │
│ 4  │ Acme Inc. Test               │ 98,000,000      │ 287 GB     │ 12          │
│ 5  │ PC Load Letter Enterprises   │ 67,000,000      │ 198 GB     │ 10          │
│ 6  │ TPS Reporting Solutions      │ 45,000,000      │ 134 GB     │ 5           │
│ 7  │ agentic-secops-example       │ 34,000,000      │ 98 GB      │ 5           │
│ 8  │ SOP Tester                   │ 28,000,000      │ 82 GB      │ 4           │
│ 9  │ lc-probe-usa                 │ 12,000,000      │ 35 GB      │ 5           │
│ 10 │ lc-probe-europe              │ 9,800,000       │ 29 GB      │ 4           │
└────┴──────────────────────────────┴─────────────────┴────────────┴─────────────┘

## Full Organization Breakdown

┌──────────────────────────────┬─────────────────┬────────────┬─────────────┬────────────┐
│ Organization                 │ Events          │ Output GB  │ Evaluations │ Peak Sens. │
├──────────────────────────────┼─────────────────┼────────────┼─────────────┼────────────┤
│ Acme Inc. Test               │ 98,000,000      │ 287 GB     │ 4,520,000   │ 12         │
│ Acme Office Supplies Inc.    │ 5,200,000       │ 15 GB      │ 890,000     │ 8          │
│ agentic-secops-example       │ 34,000,000      │ 98 GB      │ 2,100,000   │ 5          │
│ agentic-secops-tester        │ 2,100,000       │ 6 GB       │ 450,000     │ 3          │
│ github-integration-test      │ 890,000         │ 2 GB       │ 120,000     │ 2          │
│ iac-test2                    │ 0               │ 0 GB       │ 0           │ 0          │
│ lc-cicd-go-sdk               │ 450,000         │ 1 GB       │ 78,000      │ 1          │
│ lc-cicd-live-service         │ 1,200,000       │ 3 GB       │ 156,000     │ 1          │
│ lc-infrastructure            │ 425,000,000     │ 1,245 GB   │ 12,450,000  │ 25         │
│ lc_demo                      │ 187,000,000     │ 534 GB     │ 8,900,000   │ 18         │
│ refractionPOINT              │ 312,000,000     │ 892 GB     │ 9,800,000   │ 15         │
│ ... (15 more organizations)  │                 │            │             │            │
└──────────────────────────────┴─────────────────┴────────────┴─────────────┴────────────┘

## Usage by Tier

┌─────────────────────┬───────┬─────────────────┬────────────────┐
│ Tier                │ Orgs  │ Total Events    │ % of Fleet     │
├─────────────────────┼───────┼─────────────────┼────────────────┤
│ Enterprise (>100M)  │ 3     │ 924,000,000     │ 74.1%          │
│ Growth (10M-100M)   │ 5     │ 272,000,000     │ 21.8%          │
│ Starter (<10M)      │ 18    │ 51,832,456      │ 4.1%           │
└─────────────────────┴───────┴─────────────────┴────────────────┘

## Billing Status

┌──────────────────────────────┬───────────┬────────────┬─────────────────┐
│ Organization                 │ Plan      │ Status     │ Next Billing    │
├──────────────────────────────┼───────────┼────────────┼─────────────────┤
│ lc-infrastructure            │ Licensed  │ Active     │ 2026-01-01      │
│ refractionPOINT              │ Licensed  │ Active     │ 2026-01-01      │
│ lc_demo                      │ Licensed  │ Active     │ 2026-01-15      │
│ Acme Inc. Test               │ Licensed  │ Active     │ 2026-01-01      │
│ ... (22 more)                │           │            │                 │
└──────────────────────────────┴───────────┴────────────┴─────────────────┘

Note: For detailed billing amounts, see individual organization invoices in LimaCharlie console.

═══════════════════════════════════════════════════════════════════════════════
```

### Example: Detection Analytics

```
═══════════════════════════════════════════════════════════════════════════════
                        DETECTION ANALYTICS REPORT
═══════════════════════════════════════════════════════════════════════════════
Generated: 2025-12-30 14:00:00 UTC
Time Range: Last 30 Days (2025-12-01 to 2025-12-30)
Organizations: 26
═══════════════════════════════════════════════════════════════════════════════

## Detection Summary

┌─────────────────────────────┬────────────────┐
│ Metric                      │ Value          │
├─────────────────────────────┼────────────────┤
│ Total Detections            │ 4,892          │
│ Unique Categories           │ 18             │
│ Unique Rules Triggered      │ 47             │
│ Organizations with Alerts   │ 22 of 26       │
│ Avg Detections per Org      │ 188            │
│ Peak Detection Day          │ 2025-12-15     │
└─────────────────────────────┴────────────────┘

## Detection Categories (Top 10)

┌────┬─────────────────────────┬───────┬────────────┬───────────────────────┐
│ #  │ Category                │ Count │ Percentage │ Trend (vs prev month) │
├────┼─────────────────────────┼───────┼────────────┼───────────────────────┤
│ 1  │ network_threat          │ 1,245 │ 25.4%      │ ↑ +12%                │
│ 2  │ suspicious_process      │ 987   │ 20.2%      │ ↓ -5%                 │
│ 3  │ malware                 │ 654   │ 13.4%      │ ↑ +8%                 │
│ 4  │ credential_access       │ 512   │ 10.5%      │ → stable              │
│ 5  │ persistence             │ 398   │ 8.1%       │ ↑ +15%                │
│ 6  │ lateral_movement        │ 287   │ 5.9%       │ ↓ -3%                 │
│ 7  │ discovery               │ 234   │ 4.8%       │ → stable              │
│ 8  │ exfiltration            │ 189   │ 3.9%       │ ↑ +22%                │
│ 9  │ defense_evasion         │ 156   │ 3.2%       │ → stable              │
│ 10 │ initial_access          │ 123   │ 2.5%       │ ↓ -8%                 │
└────┴─────────────────────────┴───────┴────────────┴───────────────────────┘

## Detections by Organization

┌──────────────────────────────┬────────────┬─────────────────┬─────────────────┐
│ Organization                 │ Detections │ Top Category    │ Limit Status    │
├──────────────────────────────┼────────────┼─────────────────┼─────────────────┤
│ refractionPOINT              │ 1,245      │ network_threat  │ OK              │
│ lc-infrastructure            │ 987        │ suspicious_proc │ OK              │
│ Acme Inc. Test               │ 654        │ malware         │ OK              │
│ lc_demo                      │ 512        │ credential_acc  │ OK              │
│ PC Load Letter Enterprises   │ 398        │ persistence     │ OK              │
│ TPS Reporting Solutions      │ 287        │ lateral_move    │ OK              │
│ agentic-secops-example       │ 234        │ network_threat  │ OK              │
│ SOP Tester                   │ 189        │ discovery       │ OK              │
│ lc-probe-usa                 │ 123        │ exfiltration    │ OK              │
│ lc-probe-europe              │ 98         │ suspicious_proc │ OK              │
│ ... (16 more with <100)      │ 165        │ various         │ OK              │
└──────────────────────────────┴────────────┴─────────────────┴─────────────────┘

## Top Triggered Rules

┌────┬────────────────────────────────────────────┬───────┬─────────────────────┐
│ #  │ Rule Name                                  │ Count │ Category            │
├────┼────────────────────────────────────────────┼───────┼─────────────────────┤
│ 1  │ general.encoded-powershell                 │ 456   │ suspicious_process  │
│ 2  │ general.suspicious-network-connection      │ 389   │ network_threat      │
│ 3  │ general.known-malware-hash                 │ 287   │ malware             │
│ 4  │ general.credential-dump-attempt            │ 234   │ credential_access   │
│ 5  │ general.registry-persistence               │ 198   │ persistence         │
│ 6  │ general.lateral-movement-psexec            │ 167   │ lateral_movement    │
│ 7  │ general.dns-tunneling                      │ 145   │ exfiltration        │
│ 8  │ general.scheduled-task-creation            │ 134   │ persistence         │
│ 9  │ general.mimikatz-behavior                  │ 123   │ credential_access   │
│ 10 │ general.unusual-parent-child               │ 112   │ suspicious_process  │
└────┴────────────────────────────────────────────┴───────┴─────────────────────┘

## Detection Limit Warnings

⚠️  No organizations reached the 5,000 detection limit for this time period.
    All detection counts shown are complete.

## MITRE ATT&CK Coverage

┌────────────────────────┬───────────────────┬───────┐
│ Tactic                 │ Techniques Seen   │ Count │
├────────────────────────┼───────────────────┼───────┤
│ Initial Access         │ T1566, T1190      │ 123   │
│ Execution              │ T1059, T1204      │ 456   │
│ Persistence            │ T1053, T1547      │ 398   │
│ Privilege Escalation   │ T1055, T1068      │ 234   │
│ Defense Evasion        │ T1027, T1070      │ 156   │
│ Credential Access      │ T1003, T1110      │ 512   │
│ Discovery              │ T1082, T1083      │ 234   │
│ Lateral Movement       │ T1021, T1570      │ 287   │
│ Collection             │ T1005, T1039      │ 89    │
│ Exfiltration           │ T1041, T1567      │ 189   │
│ Command & Control      │ T1071, T1095      │ 1,245 │
└────────────────────────┴───────────────────┴───────┘

═══════════════════════════════════════════════════════════════════════════════
Report completed: 2025-12-30 14:05:30 UTC
Detection data subject to 5,000/org limit. All organizations within limit.
═══════════════════════════════════════════════════════════════════════════════
```
