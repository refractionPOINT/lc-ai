# Exposure Monitor SOC - Automated External Attack Surface Management

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
      v  [tags: assets-discovered]
      |
      v
Agent 2: Exposure Scanner (Sonnet, ~$0.50)
  - InternetDB (Shodan free) → open ports, CPEs, known vulns
  - CISA KEV cross-reference → actively exploited vulnerabilities
  - urlscan.io → phishing/impersonation detection
  - HTTP security headers audit (HSTS, CSP, X-Frame-Options, etc.)
  - TLS configuration check (protocol version, cipher strength, cert validity)
      |
      v  [tags: exposure-scanned]
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
Case closed (or escalated if critical)
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
| `ai_agent.operate` | All | Run AI agent sessions |
| `lookup.get` | Asset Discovery, Risk Analyst | Read exposure-domains config and exposure-seen ledger |
| `lookup.set` | Risk Analyst | Update exposure-seen ledger |

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
limacharlie sync push --config-file exposure-soc.yaml --hive-ai-agent --hive-dr-general --oid <oid>
```

## Agent Configuration

| Agent | Model | Budget | TTL | Turns |
|-------|-------|--------|-----|-------|
| Asset Discovery | Sonnet | $1.00 | 10 min | 50 |
| Exposure Scanner | Sonnet | $1.50 | 10 min | 60 |
| Risk Analyst | Opus | $2.00 | 15 min | 50 |

## Pipeline Flow

```
asset-discovery ──[assets-discovered]──> exposure-scanner ──[exposure-scanned]──> risk-analyst
```

**Tag progression:**
1. `assets-discovered` → triggers scanner
2. `scanning-exposure` → scanner in progress
3. `exposure-scanned` → triggers risk analyst
4. `analyzing-exposure` → analyst in progress
5. `exposure-report` + `daily-exposure` → final state

## State Management

The SOC maintains an `exposure-seen` lookup that stores the complete state of the
previous scan. This enables change detection:

- **New findings**: Not in previous scan → highlighted in report
- **Resolved findings**: In previous scan but not current → noted as fixed
- **Persistent findings**: In both scans → tracked as ongoing risk

## Files

```
exposure-soc/
├── exposure-soc.yaml                    # Master include file
├── README.md
├── asset-discovery/
│   └── hives/
│       ├── ai_agent.yaml                # Asset discovery prompt
│       ├── dr-general.yaml              # Daily schedule trigger
│       └── secret.yaml                  # All SOC secrets (template)
├── exposure-scanner/
│   └── hives/
│       ├── ai_agent.yaml                # Exposure scanning prompt
│       └── dr-general.yaml              # Triggered by assets-discovered tag
└── risk-analyst/
    └── hives/
        ├── ai_agent.yaml                # Risk analysis prompt
        └── dr-general.yaml              # Triggered by exposure-scanned tag
```
