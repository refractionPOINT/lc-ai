# Exposure Monitor Team - Automated External Attack Surface Management

An AI-powered SOC that runs daily to discover, scan, and report on your organization's
external attack surface using free OSINT sources. No API keys required beyond LimaCharlie
and Anthropic.

## How It Works

```
24h_per_org schedule fires (daily)
      |
      v
Agent 1: Asset Discovery (Sonnet, ~$0.30)
  - Reads org domains from exposure-domains lookup
  - crt.sh certificate transparency → subdomain enumeration
  - DNS resolution (A, AAAA, CNAME, MX, TXT via DNS-over-HTTPS)
  - Certificate expiry detection (< 30 days)
  - Dangling DNS / subdomain takeover detection
  - DNS security check (SPF, DMARC)
      |
      v  [@exposure-scanner note]
      |
      v
Agent 2: Exposure Scanner (Sonnet, ~$0.50)
  - InternetDB (Shodan free) → open ports, CPEs, known vulns
  - CISA KEV cross-reference → actively exploited vulnerabilities
  - urlscan.io → phishing/impersonation detection
  - HTTP security headers audit (HSTS, CSP, X-Frame-Options, etc.)
  - TLS configuration check (protocol version, cipher strength, cert validity)
      |
      v  [@exposure-risk-analyst note]
      |
      v
Agent 3: Risk Analyst (Opus, ~$2.00)
  - Diffs against previous scan (exposure-seen lookup ledger)
  - Classifies findings by severity (CRITICAL/HIGH/MEDIUM/LOW)
  - Generates prioritized risk report with remediation recommendations
  - Updates exposure ledger for next day's comparison
  - Escalates case if critical findings exist
      |
      v  [tags: exposure-report, daily-exposure]
      v
Case closed (or tagged needs-escalation if critical)
```

**Total cost: ~$2.80/day** using all free OSINT sources.

## Data Sources

All sources are free with no API keys required:

| Source | What It Provides | Rate Limit |
|--------|-----------------|------------|
| [crt.sh](https://crt.sh) | Certificate transparency — subdomain discovery | No hard limit |
| [InternetDB](https://internetdb.shodan.io) | Open ports, CPEs, known vulns per IP | No auth, no limit |
| [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | Actively exploited vulnerability catalog | Free JSON feed |
| [urlscan.io](https://urlscan.io) | Website scanning — phishing/impersonation | 100 searches/day |
| [DNS-over-HTTPS](https://dns.google) | DNS resolution (A, AAAA, CNAME, TXT) | No hard limit |

## What It Detects

### Critical
- CISA KEV vulnerabilities on exposed services (actively exploited in the wild)
- Dangling DNS with confirmed subdomain takeover potential
- Expired TLS certificates on production endpoints
- Database ports exposed to internet (MySQL, PostgreSQL, MongoDB, Redis)
- RDP or Telnet exposed to internet

### High
- SSH exposed to internet
- Known CVEs on exposed services
- Missing HSTS on authentication endpoints
- Deprecated TLS (1.0/1.1)
- New subdomains with exposed services
- Missing SPF or DMARC on root domains

### Medium
- Certificates expiring within 30 days
- Missing security headers (CSP, X-Frame-Options)
- Server version disclosure
- New open ports on existing infrastructure
- Self-signed certificates

## Prerequisites

- [ext-cases](https://doc.limacharlie.io/docs/extensions/ext-cases) extension subscribed and configured
- An Anthropic API key
- Three LimaCharlie API keys (one per agent) with the following permissions:

| Permission | Agent | Why |
|-----------|-------|-----|
| `org.get` | All | Basic org context |
| `investigation.get` | All | Read cases |
| `investigation.set` | All | Create/update cases, add notes, entities |
| `ext.request` | All | Make requests to extensions |
| `org_notes.*` | All | Read and write org notes |
| `sop.get` | Read SOPs for operational guidance |
| `sop.get.mtd` | Read SOP metadata |
| `ai_agent.operate` | All | Run AI agent sessions |
| `ai_agent.exec` | Asset Discovery, Exposure Scanner | Trigger downstream agents via @mention notes |
| `lookup.get` | Asset Discovery, Risk Analyst | Read exposure-domains config and exposure-seen ledger |
| `lookup.set` | Risk Analyst | Update exposure-seen ledger |
| `ai_memory.get` | All | Read persistent memory (asset inventory, baselines, accepted risks) |
| `ai_memory.set` | All | Write persistent memory at end of run |
| `ai_memory.del` | All | Drop memories that no longer apply (e.g. fixed dangling DNS) |

## Configuration

### Step 1: Add Your Domains

Create the `exposure-domains` lookup with the domains you want to monitor:

```bash
cat > /tmp/exposure-domains.yaml << 'EOF'
data:
  lookup_data:
    "example.com": {"primary": true}
    "example.io": {"primary": false}
    "example.dev": {"primary": false}
usr_mtd:
  enabled: true
EOF
limacharlie lookup set --key exposure-domains --input-file /tmp/exposure-domains.yaml --oid <oid>
```

Add all root domains your organization owns. The SOC will discover subdomains
automatically via certificate transparency.

### Step 2: Install the SOC

Use the `lc-deployer` skill to install, or manually:

1. Create API keys for each agent
2. Store secrets in the secret hive
3. Push the configuration:
```bash
limacharlie sync push --config-file exposure-team.yaml --hive-ai-agent --hive-dr-general --oid <oid>
```

## Agent Configuration

| Agent | Model | Budget | TTL | Turns |
|-------|-------|--------|-----|-------|
| Asset Discovery | Sonnet | $1.00 | 10 min | 50 |
| Exposure Scanner | Sonnet | $1.50 | 10 min | 60 |
| Risk Analyst | Opus | $2.00 | 15 min | 50 |

## Inter-Agent Communication

Agents signal each other by writing case notes with @mentions. D&R rules match on `note_added` events containing the @mention and require `ai_agent.exec` permission.

| Signal | Meaning | Written By | Triggers |
|--------|---------|------------|----------|
| `@exposure-scanner` note | Assets discovered, ready for scanning | Asset Discovery | Exposure Scanner |
| `@exposure-risk-analyst` note | Scan complete, ready for analysis | Exposure Scanner | Risk Analyst |

**Lock/status tags** (still tag-based, for concurrency control):

| Tag | Meaning | Added By |
|-----|---------|----------|
| `scanning-exposure` | Scan in progress (lock) | Exposure Scanner |
| `analyzing-exposure` | Analysis in progress (lock) | Risk Analyst |
| `exposure-report` | Report complete (completion signal) | Risk Analyst |
| `exposure-pipeline` | Marks case as part of exposure pipeline | Asset Discovery |
| `daily-exposure` | Marks daily exposure report | Risk Analyst |

## State Management

The SOC maintains an `exposure-seen` lookup that stores the complete state of the
previous scan. This enables change detection:

- **New findings**: Not in previous scan → highlighted in report
- **Resolved findings**: In previous scan but not current → noted as fixed
- **Persistent findings**: In both scans → tracked as ongoing risk

In addition to the lookup ledger, each agent maintains its own `ai_memory`
record for prose-level context that's awkward to fit in a flat key/value
lookup:

| Agent | Memory key | Purpose |
|-------|-----------|---------|
| Asset Discovery | `inventory/subdomains.md`, `inventory/ips.md`, `inventory/dangling.md`, `inventory/cert-expiry.md`, `inventory/dns-security.md` | Stable view of the org's external surface |
| Asset Discovery | `state/last-run.md` | When discovery last ran, what it covered |
| Exposure Scanner | `baselines/known-ports.md` | Stable port/CPE map per IP, used to surface true changes |
| Exposure Scanner | `state/last-scan.md` | When the scan ran, IPs covered, urlscan budget used |
| Risk Analyst | `feedback/accepted-risks.md` | Operator-accepted exposures (explicit only) — downgrade severity, never re-escalate |
| Risk Analyst | `feedback/reporting-style.md` | Operator-stated style preferences |
| Risk Analyst | `state/last-report.md` | Yesterday's report counts, used for trend lines |

See [`../../MEMORY.md`](../../MEMORY.md) for the design contract that all of
these follow (read–diff–update workflow, what not to put in memory, partial
merge semantics).

## Files

```
exposure-team/
├── exposure-team.yaml                    # Master include file
├── README.md
├── asset-discovery/
│   └── hives/
│       ├── ai_agent.yaml                # Asset discovery prompt
│       ├── dr-general.yaml              # Daily schedule trigger
│       └── secret.yaml                  # API key placeholder
├── exposure-scanner/
│   └── hives/
│       ├── ai_agent.yaml                # Exposure scanning prompt
│       ├── dr-general.yaml              # @exposure-scanner mention trigger
│       └── secret.yaml                  # API key placeholder
└── risk-analyst/
    └── hives/
        ├── ai_agent.yaml                # Risk analysis prompt
        ├── dr-general.yaml              # @exposure-risk-analyst mention trigger
        └── secret.yaml                  # API key placeholder
```
