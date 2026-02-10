---
name: graphic-output
description: |
  Generate interactive HTML dashboards and visualizations from LimaCharlie data using Jinja2 templates and D3.js charts. Creates professional, self-contained HTML reports with pie charts, bar charts, line graphs, gauges, sortable tables, and responsive layouts. Supports MSSP multi-tenant dashboards, single-org details, sensor health reports, detection analytics, and billing summaries. Integrates with reporting, sensor-health, and detection-engineering skills. Built with strict data accuracy guardrails - NEVER fabricates, estimates, or infers data. Use for "visual report", "dashboard", "HTML output", "interactive charts", "export HTML", "generate visualization", "graphical report".
allowed-tools:
  - Task
  - Read
  - Write
  - Bash
---

# Graphic Output Skill

Generate interactive HTML dashboards and visualizations from structured LimaCharlie data. This skill transforms JSON report data into professional, self-contained HTML documents with D3.js charts and interactive elements.

**Core Philosophy**: Visualize ONLY what exists. This skill has strict guardrails that make data fabrication impossible. Every chart, number, and label must come directly from the input data.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **Data Fabrication** | Generate, estimate, or infer missing data | Show "N/A" or "Data unavailable" |
| **Data Modification** | Round, truncate, or rename values | Display values exactly as provided |
| **Missing Fields** | Show zero for missing values | Show empty state with clear messaging |

---

## Data Accuracy Guardrails

### CRITICAL: These Rules Are Absolute

#### Principle 1: NEVER Fabricate Data

**Absolute Rules:**
- NEVER generate, estimate, infer, or extrapolate data not in the input
- NEVER fill in missing values with assumptions
- NEVER create "example" or "placeholder" data
- NEVER calculate derived metrics not explicitly provided
- NEVER guess at trends, patterns, or projections

**Always:**
- Show "N/A" or "Data unavailable" for missing fields
- Display empty chart states with clear messaging
- Document what data is missing in the output
- Pass through data exactly as received

#### Principle 2: Represent Data As-Is

**Absolute Rules:**
- Display values EXACTLY as provided in input
- Do NOT round, truncate, or modify numeric values (except for display formatting)
- Do NOT reorder, filter, or exclude data without explicit instruction
- Do NOT combine or aggregate data that wasn't pre-aggregated
- Do NOT rename categories or labels

**Display Formatting Allowed:**
- Adding thousand separators (1234567 → 1,234,567)
- Converting bytes to human-readable (1073741824 → 1 GB) with original shown
- Date formatting (Unix timestamp → readable date)
- Percentage formatting (0.945 → 94.5%)

**NOT Allowed:**
- Changing "unknown" to a guessed value
- Interpolating missing data points in time series
- Creating trend lines from insufficient data
- Smoothing or averaging values

#### Principle 3: Explicit Data Provenance

Every visualization MUST indicate:
- Source of the data (which skill/API provided it)
- Timestamp when data was collected
- Time window the data covers
- Any known limitations or caveats

**Example:**
```
Data Source: reporting skill (org-reporter agents)
Collected: 2025-11-27 14:32:45 UTC
Time Window: Nov 1-30, 2025 (30 days)
Note: 4 organizations hit detection limit - actual counts higher
```

#### Principle 4: Handle Missing Data Explicitly

When data is missing or unavailable:

**For Charts:**
- Show empty chart with message: "No data available"
- Do NOT show chart with zero values (unless zero is the actual value)
- Do NOT substitute placeholder data

**For Metrics/Cards:**
- Display "N/A" or "—" for missing values
- Include note explaining why data is unavailable
- Do NOT show "0" unless zero is the actual value

**For Tables:**
- Show empty rows with "N/A" in cells
- Include row even if partial data available
- Mark incomplete rows visually

#### Principle 5: Warning Propagation

All warnings from source data MUST be displayed:
- Detection limit warnings
- Partial data warnings
- Permission errors
- Failed organization notices

Warnings must be:
- Prominently displayed (not hidden in footnotes)
- Associated with affected visualizations
- Actionable (explain what user can do)

#### Principle 6: No Calculations

**Do NOT perform:**
- Cost calculations from usage metrics
- Growth rate calculations
- Percentage changes between periods
- Statistical analysis (mean, median, std dev)
- Trend predictions

**Exception:** The following display-only calculations are permitted:
- Percentage of total (for pie charts) when total is provided
- Health percentage when online/total counts provided
- These must use ONLY values from input data

### Validation Checklist

Before rendering any visualization, verify:

```
[ ] Every value traces to input data
[ ] No fields contain fabricated content
[ ] Missing data shows as "N/A" not zero
[ ] All warnings from input are displayed
[ ] Data source and timestamp shown
[ ] Time window clearly indicated
[ ] Detection limits flagged if present
[ ] Failed organizations documented
```

### Error Messages for Violations

If the skill detects a guardrail violation:

```
ERROR: Data Accuracy Violation

Attempted to render chart with fabricated data.
Field 'detection_trend' was not provided in input.

Resolution: Either provide the required data from a source skill,
or use a template that doesn't require this field.

This skill will NOT generate placeholder, example, or estimated data.
```

## When to Use This Skill

Use this skill when the user needs to:

### Visual Reports
- **"Generate a visual report for all my organizations"** - Multi-tenant dashboard
- **"Create an HTML dashboard from the report"** - Convert text report to visual
- **"Make an interactive chart of detections"** - Detection analytics visualization
- **"Export as HTML with graphs"** - Visual export format

### Dashboard Generation
- **"Show me a dashboard of sensor health"** - Fleet health gauges and charts
- **"Create a visual overview of my MSSP clients"** - Multi-org summary
- **"Generate billing dashboard"** - Usage metrics visualization

### Integration with Other Skills
- After running the `reporting` skill - visualize the collected data
- After running `sensor-health` skill - create health dashboard
- After `detection-engineering` testing - visualize test results

## What This Skill Does

This skill:
1. Accepts structured JSON data from source skills (reporting, sensor-health, etc.)
2. **Validates data completeness** - checks all required fields exist
3. Selects the appropriate visualization template
4. Spawns the `html-renderer` subagent to generate HTML
5. **Enforces data accuracy guardrails** throughout rendering
6. Returns the path to the self-contained HTML file

**Output Characteristics:**
- Self-contained HTML (no external dependencies)
- Embedded D3.js visualizations
- Interactive charts (hover, click, tooltips)
- Responsive layout (works on any screen size)
- Print-friendly styles
- Sortable data tables
- **Data provenance clearly shown**
- **All warnings prominently displayed**

## Available Templates

| Template | Description | Best For |
|----------|-------------|----------|
| `mssp-dashboard` | Multi-tenant overview with aggregate metrics, org table, charts | MSSP/multi-org reports |
| `security-overview` | Single-org comprehensive security report with platform breakdown, MITRE coverage, detection timeline, rules inventory | Individual org deep-dive |
| `billing-summary` | Multi-tenant billing roll-up with per-tenant breakdown, SKU details, cost distribution charts | Billing/cost analysis |
| `custom-report` | **Component-based flexible reports** - build any report by specifying which components to include | Ad-hoc/custom reports |

**Note:** Use `custom-report` when none of the predefined templates fit your needs. It supports composable components that can be arranged in any order.

### Custom Report Components

The `custom-report` template supports these component types:

| Component | Description |
|-----------|-------------|
| `summary_cards` | Grid of metric cards with icons, values, labels |
| `chart` | Pie, doughnut, bar, or line charts |
| `two_column` | Side-by-side charts layout |
| `table` | Data tables with optional sorting |
| `metric_grid` | Compact grid of small metrics |
| `platform_table` | Platform breakdown with sensors/detections |
| `alert_banner` | Info/warning/danger/success banners |
| `text_section` | Free-form HTML content |
| `divider` | Visual separator |

**Example custom report request:**
> "Create a report with 3 summary cards showing sensors, detections, and rules, then a pie chart of platform distribution, and a table of my top 5 detection categories"

## Required Information

Before using this skill, you need:

### From Source Skill (e.g., reporting)
- **Structured JSON data** matching the template's expected schema
- **Metadata** including generation timestamp, time window, org counts
- **All warnings and errors** from data collection

### Data Requirements by Template

Each template has required and optional fields. The skill will:
- Render visualizations for fields that are present
- Show "Data unavailable" for missing optional fields
- **Refuse to render** if required fields are missing (no fabrication)

## How to Use

### Step 1: Ensure Data is Available

The graphic-output skill requires structured JSON data. This typically comes from:

1. **Reporting skill output** - Multi-tenant report data
2. **Sensor-health skill output** - Fleet health data
3. **Manually structured data** - Following the schema

**IMPORTANT:** The skill will ONLY visualize data that exists. It will NOT:
- Create sample data
- Fill in missing values
- Generate placeholder content

If integrating with the reporting skill, the data structure should include:
```json
{
  "metadata": {
    "generated_at": "2025-11-27T14:32:45Z",
    "time_window": {
      "start": 1730419200,
      "end": 1733011199,
      "start_display": "2025-11-01 00:00:00 UTC",
      "end_display": "2025-11-30 23:59:59 UTC",
      "days": 30
    },
    "organizations": {
      "total": 14,
      "successful": 12,
      "failed": 2,
      "success_rate": 85.7
    }
  },
  "data": {
    "aggregate": { ... },
    "organizations": [ ... ]
  },
  "warnings": [ "4 organizations hit detection limit" ],
  "errors": [ { "org": "...", "error": "..." } ]
}
```

### Step 2: Select Template

Choose the appropriate template based on data type:

- **Multi-org data** → `mssp-dashboard`
- **Single org data** → `org-detail`
- **Health-focused** → `sensor-health`
- **Detection-focused** → `detection-summary`
- **Billing/usage** → `billing-summary`

### Step 3: Spawn HTML Renderer

Use the Task tool to spawn the html-renderer subagent:

```
Task(
  subagent_type="lc-essentials:html-renderer",
  model="sonnet",
  prompt="Render HTML dashboard with the following parameters:

    Template: mssp-dashboard

    Output Path: /tmp/lc-mssp-report-2025-11-27.html

    Data:
    {
      \"metadata\": { ... },
      \"data\": { ... },
      \"warnings\": [ ... ],
      \"errors\": [ ... ]
    }

    IMPORTANT: Apply strict data accuracy guardrails.
    - Visualize ONLY data provided in the input
    - Show 'N/A' for any missing fields
    - Display all warnings prominently
    - Do NOT fabricate any data

    Return the file path and rendering summary when complete."
)
```

### Step 4: Launch in Browser (Default Completion)

**IMPORTANT:** When generating any HTML report, always open it in the user's browser as the default completion action.

```bash
# On ChromeOS/Linux with garcon:
garcon-url-handler "http://localhost:8080/report.html"

# Alternative for other systems:
xdg-open "/tmp/report.html"
# or
open "/tmp/report.html"  # macOS
```

Before opening, ensure an HTTP server is running to serve the file:
```bash
# Start server if not already running
cd /tmp && python3 -m http.server 8080 --bind 0.0.0.0 &
```

This ensures the user immediately sees their report without manual steps.

### Step 5: Return Results to User

After the renderer completes and browser is opened, inform the user:

```
Interactive HTML dashboard generated successfully!

File: /tmp/lc-mssp-report-2025-11-27.html
Size: 245 KB

Data Provenance:
- Source: reporting skill
- Collected: 2025-11-27 14:32:45 UTC
- Time Window: Nov 1-30, 2025 (30 days)
- Organizations: 12 of 14 successful

Contents:
- Executive summary with 4 metric cards
- Platform distribution pie chart
- Organization health bar chart
- Detection category breakdown
- Daily detection trend line chart
- Sortable organization details table
- 2 warnings displayed (detection limits)
- 2 failed organizations documented

Data Accuracy:
- All visualizations show actual data from source
- No values were estimated or fabricated
- Missing data marked as "N/A"

Open this file in any web browser to view the interactive dashboard.
```

## Template Details

### MSSP Dashboard (`mssp-dashboard`)

**Purpose:** Multi-tenant overview for MSSPs managing multiple organizations

**Visualizations:**
- Summary cards (sensors, detections, rules, orgs)
- Platform distribution donut chart
- Organization health horizontal bar chart
- Top detection categories bar chart
- Detection volume trend line chart (if daily_trend provided)
- Per-organization sortable table
- Warnings and errors section

**Required Data Fields:**
```
metadata.generated_at                    # When data was collected
metadata.time_window.start_display       # Time range start
metadata.time_window.end_display         # Time range end
metadata.organizations.total             # Total org count
metadata.organizations.successful        # Successful org count

data.aggregate.sensors.total             # Total sensor count
data.aggregate.sensors.online            # Online sensor count
data.aggregate.sensors.platforms         # Platform breakdown object
data.aggregate.detections.retrieved      # Detection count
data.aggregate.detections.top_categories # Array of {label, value}
data.aggregate.rules.total               # Total rules
data.aggregate.rules.enabled             # Enabled rules

data.organizations                       # Array of org objects
```

**Optional Data Fields (shown if present, "N/A" if missing):**
```
data.aggregate.detections.daily_trend    # For trend chart
data.aggregate.detections.limit_reached  # Limit warning flag
data.aggregate.detections.orgs_at_limit  # Count of orgs at limit
data.aggregate.usage.*                   # Usage metrics

warnings                                 # Array of warning strings
errors                                   # Array of error objects
```

**Guardrail Behavior:**
- If `daily_trend` missing: Shows "Trend data not available" instead of chart
- If `platforms` empty: Shows "Platform data not available"
- If org has missing fields: Shows "N/A" in table cell
- All `warnings` displayed in dedicated section
- All `errors` displayed with remediation steps

### Security Overview (`security-overview`)

**Purpose:** Comprehensive single-organization security report with platform breakdown, MITRE coverage, detection timeline, and rules inventory.

**Visualizations:**
- Active threat alert banners (if threats present)
- Summary cards (sensors, detections, rules, MITRE coverage)
- Platform breakdown table with sensor and detection counts
- Detection timeline chart (24h or custom window)
- MITRE ATT&CK technique tags
- D&R rule inventory breakdown
- Attack pattern analysis (if data available)
- Top detections table

**Required Data Fields:**
```
metadata.generated_at                    # When data was collected
metadata.time_window.start_display       # Time range start
metadata.time_window.end_display         # Time range end
metadata.org_name                        # Organization name
metadata.oid                             # Organization ID

data.summary.sensors_total               # Total sensor count
data.summary.detections_total            # Detection count
data.summary.rules_total                 # Total rules
```

**Optional Data Fields (shown if present, "N/A" if missing):**
```
data.summary.sensors_online              # Online sensor count
data.summary.detections_24h              # 24h detection count
data.summary.rules_enabled               # Enabled rules
data.summary.mitre_coverage              # MITRE coverage percentage

data.active_threats[]                    # Active threat alerts
data.platforms[]                         # Platform breakdown
data.hourly_detections[]                 # Detection timeline
data.top_detections[]                    # Top detection categories
data.mitre_techniques[]                  # MITRE technique coverage
data.rules.*                             # Rule inventory breakdown
data.attack_analysis.*                   # Attack pattern analysis

warnings                                 # Array of warning strings
errors                                   # Array of error objects
```

**Guardrail Behavior:**
- If `hourly_detections` missing: Shows "Timeline data not available"
- If `platforms` empty: Shows "Platform data not available"
- If `mitre_techniques` missing: MITRE section hidden
- All `warnings` displayed prominently
- No data fabrication under any circumstances

## Chart Behavior with Missing Data

### Pie Chart
- **All data present**: Normal pie chart with legend
- **Empty data array**: "No data available for this chart"
- **Some categories zero**: Shows non-zero slices only with note

### Bar Chart
- **All data present**: Normal bar chart
- **Empty data array**: "No data available for this chart"
- **Missing values**: Bar not shown, "N/A" in axis label

### Line Chart
- **Complete time series**: Normal line with points
- **Gaps in data**: Line breaks at gaps (no interpolation)
- **No data**: "Time series data not available"
- **Single point**: Shows point with note "Insufficient data for trend"

### Gauge
- **Value provided**: Normal gauge display
- **Value missing**: Gauge at 0 with "N/A" label
- **Value out of range**: Clamped with warning

### Data Table
- **Complete rows**: Normal display
- **Missing cells**: "N/A" in cell
- **Empty table**: "No data available"

## Warning Display Requirements

All warnings MUST be displayed. The skill will:

1. **Aggregate warnings** in a dedicated section
2. **Associate warnings** with affected charts
3. **Style warnings prominently** (amber background, icon)

**Warning Types:**
- Detection limit warnings → Shown above detection charts
- Permission errors → Shown in errors section
- Partial data warnings → Shown inline with affected metrics
- Failed organizations → Listed with details

**Example Warning Display:**
```
⚠️ Data Limitations

• 4 organizations hit the 5,000 detection limit
  Actual detection counts are higher than shown.
  Affected: Acme Corp, GlobalTech, Nexus, Pinnacle

• 2 organizations failed completely
  See Errors section for details.

• Billing data unavailable for 3 organizations
  Required permission: billing:read
```

## Error Handling

### Missing Required Fields
The skill will NOT render if required fields are missing:

```
Error: Cannot render mssp-dashboard

Missing required fields:
- data.aggregate.sensors.total
- data.aggregate.detections.top_categories

Resolution:
1. Ensure the source skill collected this data
2. Check for API errors in the source skill output
3. Use a different template that doesn't require these fields
```

### Invalid Data Types
```
Error: Invalid data type

Field: data.aggregate.sensors.total
Expected: number
Received: string ("unknown")

Resolution:
The source data contains invalid types. Check the source skill output.
```

### Partial Data
When some data is available but not all:

```
Warning: Partial data available

Rendering with available data. The following are unavailable:
- Detection trend chart (daily_trend not provided)
- Billing status (billing data missing for 5 orgs)

These sections will show "Data unavailable" messages.
```

## Output File Details

Generated HTML files are:

1. **Self-contained** - All CSS, JavaScript, and data embedded
2. **No external dependencies** - Works offline
3. **Responsive** - Adapts to screen size
4. **Print-ready** - Optimized print stylesheet
5. **Interactive** - Hover tooltips, clickable elements
6. **Accessible** - ARIA labels, keyboard navigation

**Data Provenance Section (Always Included):**
```html
<footer class="data-provenance">
  <h3>Data Provenance</h3>
  <dl>
    <dt>Generated</dt>
    <dd>2025-11-27 14:32:45 UTC</dd>
    <dt>Time Window</dt>
    <dd>Nov 1-30, 2025 (30 days)</dd>
    <dt>Organizations</dt>
    <dd>12 of 14 (85.7% success rate)</dd>
    <dt>Data Source</dt>
    <dd>LimaCharlie API via reporting skill</dd>
  </dl>
  <p class="accuracy-note">
    All values shown are from actual API responses.
    No data has been estimated, interpolated, or fabricated.
  </p>
</footer>
```

## Related Skills

- **reporting** - Source of MSSP report data
- **sensor-health** - Source of health monitoring data
- **detection-engineering** - Source of rule test results
- **limacharlie-call** - Direct API access for custom data

## Files in This Skill

```
skills/graphic-output/
├── SKILL.md                           # This file
├── IMPLEMENTATION_PLAN.md             # Detailed implementation plan
├── templates/
│   ├── base.html.j2                   # Base template with CSS, Chart.js utilities
│   └── reports/
│       ├── mssp-dashboard.html.j2     # Multi-tenant MSSP dashboard
│       ├── security-overview.html.j2  # Single-org security report
│       ├── billing-summary.html.j2    # Multi-tenant billing report
│       └── custom-report.html.j2      # Component-based flexible reports
├── static/
│   └── js/
│       └── lc-charts.js               # Chart.js utility functions
└── schemas/
    ├── mssp-report.json               # Schema for mssp-dashboard data
    ├── security-overview.json         # Schema for security-overview data
    ├── billing-summary.json           # Schema for billing-summary data
    └── custom-report.json             # Schema for custom-report components
```
