---
name: cloud-security
description: LimaCharlie Cloud Security (CNAPP) — cloud findings triage, security-graph pivoting and queries, attack paths, CIEM identity analysis, inventory, data security, CAASM, compliance, and MSSP fleet views. Use when investigating cloud risk, pivoting between cloud resources and identities, walking attack paths, connecting cloud assets to endpoint sensors, or triaging cloud security findings.
allowed-tools:
  - Bash
  - Read
---

# Cloud Security (CNAPP)

How to investigate and triage cloud risk in LimaCharlie using the `limacharlie cloudsec` CLI. Cloud Security is an agentless CNAPP built into the tenant: it sweeps cloud and identity providers, builds one **security graph** of the estate, and emits risk-ranked findings.

**Prerequisites:** the org must be subscribed to the `ext-cloud-security` extension (every command returns 403 otherwise). Reads need the `cloudsec.get` permission; triage and other writes need `cloudsec.set`. The product is in private beta.

**Providers (5 surfaces, 13 connectors):** cloud infrastructure (`gcp`, `aws`, `azure`), identity (`okta`, `entra`, `google_workspace`, `1password`, `auth0`), SaaS (`cloudflare`, `github`), AI platforms (`openai`, `anthropic`), and LimaCharlie itself (`limacharlie`). Provider configs and policies are Hive records (`cloudsec_provider` / `cloudsec_policy` / `cloudsec_query` hives) managed with the standard `limacharlie hive` commands — remember Hive records are disabled until explicitly enabled.

Every command below takes `--oid <oid>` and supports `--output yaml` and `--ai-help`.

## The Mental Model: One Graph, One Join Key

Everything is a node in one graph, addressed by a URN (`lcrn:...`). **The URN is the universal join key** — any URN you encounter anywhere (a finding, a query row, a neighbors result, a CIEM grant) can be hydrated into its full canonical record:

```bash
limacharlie cloudsec resource get "<urn>" --oid <oid> --output yaml
```

This works for derived nodes too (vulnerabilities, identities, public endpoints) that have no inventory row. Always quote URNs in the shell.

### Node Types

| Label | What it is |
|-------|-----------|
| `ComputeInstance`, `ComputeGroup` | Workloads (VMs, node pools, instance groups) |
| `Network` | VPCs / networks |
| `DataStore` | Buckets, managed databases — the sensitive **sink** attack paths terminate at |
| `Identity` | Humans, service accounts, groups, roles, federations |
| `Vulnerability` | CVEs (with KEV / CVSS / EPSS context) |
| `PublicEndpoint` | The internet boundary |
| `Application` | Identity-provider apps (Okta / Entra) |
| `Account` | Cloud account / project / subscription / workspace |
| `AIService` | Managed AI/ML services (inference endpoints) |
| `Endpoint` | A LimaCharlie runtime sensor (the cloud↔endpoint bridge) |
| `ExternalAsset` | Externally-discovered surface (hostname / IP / cert) |
| `ThirdPartyAsset` | CAASM-ingested third-party inventory (devices, identities) |

Key node properties to filter and reason on: `is_public`, `is_sensitive`, `is_external`, `criticality`, `in_kev`, `cve`, `cvss_score`, identity insight (`mfa_enabled`, `admin_roles`, `can_escalate`, dormancy), and data classes (pii / phi / secrets).

### Edge Types

| Edge | Direction and meaning |
|------|----------------------|
| `can_reach` | workload → workload: network reachability |
| `exposed_to` | workload → `PublicEndpoint`: internet exposure |
| `has_vulnerability` | workload → CVE (carries package + fix version) |
| `has_permission_on` | identity → resource: a grant, carrying the classified **access level** |
| `can_assume` | identity → identity: role assumption / impersonation (the privilege-escalation backbone) |
| `is_member_of` | identity → group / account membership |
| `has_app_access` | identity → IdP application assignment |
| `runs_as` | AI service → its runtime service identity |
| `runs_on` | endpoint sensor ↔ the cloud workload it runs on |

### Risk Semantics That Matter

- **`lc_risk` (0–1000) is THE rank key** for findings — it composes severity, exploitability (EPSS/KEV), and graph context (exposure, reachability, blast radius). Sort worklists by `lc_risk`, not by severity alone; a MEDIUM misconfig on an internet-reachable, KEV-vulnerable path outranks an isolated HIGH.
- **Access is capability, not grant-existence.** `has_permission_on` carries an `access_level`: `data_admin` > `data_write` > `data_read` > `metadata` > `none`. "Reaches sensitive data" means `data_read` or higher. A `metadata`-only grant is a reconnaissance signal, not a data-access risk — do not report it as one.
- **`reachable` is asserted-positive only.** `reachable: true` means a network path was proven. Absence of the flag means *not proven* — never claim a resource is isolated because `reachable` is missing.
- **`in_kev` is the exploitability gate.** A known-exploited CVE on an internet-exposed workload is what promotes mere exposure into a confirmed attack path (`toxic_combination`).

## The Core Workflow

Orient → worklist → pivot → evaluate → triage. Do not skip orientation: facet counts tell you the shape of the estate before you page through anything.

### 1. Orient

```bash
# Composed risk overview: score, top paths, trend
limacharlie cloudsec overview --oid <oid> --output yaml

# Is collection healthy / fresh? (per provider)
limacharlie cloudsec scan-status --provider gcp --oid <oid> --output yaml

# Estate shape: exact counts by class/severity/account, resource types, identity kinds
limacharlie cloudsec finding facets --oid <oid> --output yaml
limacharlie cloudsec inventory facets --oid <oid> --output yaml
limacharlie cloudsec ciem facets --oid <oid> --output yaml
```

If `scan-status` shows no completed sweep, findings and inventory will be empty — report that, don't conclude the estate is clean.

### 2. Worklist

```bash
# The risk-ranked worklist (default sort is lc_risk desc)
limacharlie cloudsec finding list --status open --sort lc_risk --limit 50 --oid <oid> --output yaml

# Filters are repeatable; values OR within a key, AND across keys:
limacharlie cloudsec finding list \
  --class toxic_combination --class public_exposure \
  --severity CRITICAL --severity HIGH \
  --kev --reachable \
  --oid <oid> --output yaml

# Canonical class enum (don't guess class names):
limacharlie cloudsec finding classes --oid <oid> --output yaml
```

**Finding classes:** `toxic_combination`, `public_exposure`, `ciem_risk`, `privilege_escalation`, `vulnerability`, `misconfig`, `coverage_gap`, `device_posture`, and related. Severities: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`. Statuses: `open`, `resolved`.

Pagination is keyset-based: pass the returned `next_cursor` back as `--cursor`. Page size is server-clamped to 1000.

### 3. Pivot

A finding is a pointer into the graph. `finding get` returns the fields to pivot on:

| Field | Pivot |
|-------|-------|
| `resource_urn`, `related_urns` | `resource get "<urn>"` for the full record |
| `path` | The kill-chain of nodes (entry → hops → sink) — hydrate each |
| `pivot_targets`, `target_count` | Blast radius: what an attacker reaches *from* here |
| `ciem_access`, `ciem_escalation` | The structured grant / escalation chain behind identity findings |
| `vulns[]` | CVE, package, fix version, CVSS/EPSS/KEV per vulnerability |
| `evidence.offending_config` | The exact config key, current value, and expected value |
| `remediation.fixes[]` | Ready-made CLI / Terraform fixes |
| `runtime_sids` | Live LimaCharlie sensors on the affected workload — bridge to EDR |

Graph pivots from any URN:

```bash
# 1-hop neighborhood (induced subgraph; sensitive/public neighbors ranked first;
# `truncated` is set when the node has more neighbors than the cap of 500)
limacharlie cloudsec graph neighbors "<urn>" --limit 200 --oid <oid> --output yaml

# Identity 360: everything about one identity — grants, memberships, apps, risk
limacharlie cloudsec ciem identity "<identity-urn>" --oid <oid> --output yaml

# The marquee attack paths (internet → exposed workload → KEV vuln → sensitive sink)
limacharlie cloudsec attack-path list --severity CRITICAL --oid <oid> --output yaml

# The headline CIEM view: public/external access to sensitive resources
limacharlie cloudsec ciem public-access --oid <oid> --output yaml
```

### 4. Bridge to Runtime (Cloud ↔ Endpoint)

Cloud assets and EDR sensors are the same estate. Resolve in either direction, then continue the investigation with the sensor / query skills (LCQL over the sensor's events, live tasking, cases):

```bash
# Which cloud workload is this sensor running on?
limacharlie cloudsec resolve sensors <sid> [<sid>...] --oid <oid> --output yaml

# Which sensors run on this cloud resource?
limacharlie cloudsec resolve assets "<urn>" ["<urn>"...] --oid <oid> --output yaml
```

Both return `resolved` and `unresolved` sets — an unresolved sid/urn is normal (not every workload has an agent).

### 5. Triage

Writes need `cloudsec.set`. Resolution kinds: `mitigated`, `accepted`, `false_positive`; `open` reopens.

```bash
limacharlie cloudsec finding resolve <finding-id> --kind false_positive --reason "..." --oid <oid> --output yaml
limacharlie cloudsec finding resolve <finding-id> --kind accepted --reason "..." --expires-at 2027-01-01T00:00:00Z --oid <oid> --output yaml
limacharlie cloudsec finding bulk-resolve --finding-id <id1> --finding-id <id2> --kind mitigated --reason "..." --oid <oid> --output yaml
limacharlie cloudsec finding set-owner <finding-id> --owner analyst@example.com --oid <oid> --output yaml
limacharlie cloudsec finding set-ticket <finding-id> --ticket JIRA-123 --oid <oid> --output yaml
```

Findings auto-close when the underlying condition disappears from a later sweep — do not mark a finding resolved just because you expect the fix to land; let the sweep confirm it.

## Graph Queries

Three input forms, one endpoint. **Prefer the built-in query pack** — the named queries are the canonical security questions, pre-validated and cheap to run:

```bash
limacharlie cloudsec query list --oid <oid> --output yaml
limacharlie cloudsec query run --named kev_on_internet_exposed --oid <oid> --output yaml
```

The query pack (names are exact; use `query list` for the authoritative set):

| Named query | Question |
|-------------|----------|
| `public_or_external_access_to_sensitive` | Outside principal holds a grant on a sensitive workload |
| `public_or_external_access_to_sensitive_data_store` | Outside principal holds a grant on a sensitive bucket/database |
| `shortest_access_path_external_to_sensitive_data` | Shortest grant/assume chain from an external identity to sensitive data |
| `kev_on_internet_exposed` | KEV vulnerability on an internet-exposed workload |
| `internet_exposed_workloads` | Everything reachable from the internet |
| `can_reach_sensitive_workload` | Network paths into sensitive workloads |
| `public_data_stores` / `sensitive_data_stores` | Public / sensitive buckets and databases |
| `public_ai_services` / `ai_service_identities` | Exposed AI services / the identities they run as |
| `application_access` / `app_access_without_mfa` | IdP app assignments / app access with no MFA |
| `endpoints_on_internet_exposed_workloads` | Sensors running on internet-exposed workloads |
| `hybrid_endpoint_paths_to_sensitive` | Paths crossing endpoint and cloud segments to a sensitive sink |
| `external_entry_points` | Workloads reachable from externally-discovered assets |
| `external_identity_group_membership` | Outside principals inside directory groups |

Results are rows of `alias → URN` bindings. Hydrate any URN with `resource get`. Use `--project a,b` to select which aliases come back.

### Text Queries

For ad-hoc questions, the text form is a compact Cypher-like grammar (NOT natural language — a prose sentence will fail to parse):

```
MATCH (alias:Label {prop: value, ...}) <-[:edge_name {prop: value}]- (alias2:Label) ... RETURN alias, alias2
```

- Node: `(d:DataStore {is_sensitive: true})`. Edge inbound to the previous node: `<-[:edge_name]-`; outbound: `-[:edge_name]->`. Edge names use underscores (`has_permission_on`).
- Inline predicates are AND-ed equalities; values are `true`/`false`, numbers, quoted strings, or barewords.
- **The first node is the anchor** (see the anchor rule below).

```bash
# External identities with an allow-grant on sensitive data stores
limacharlie cloudsec query run --text 'MATCH (d:DataStore {is_sensitive: true})<-[:has_permission_on {effect: allow}]-(i:Identity {is_external: true}) RETURN i, d' --oid <oid> --output yaml

# Known-exploited CVEs on public workloads
limacharlie cloudsec query run --text 'MATCH (v:Vulnerability {in_kev: true})<-[:has_vulnerability]-(w:ComputeInstance {is_public: true}) RETURN w, v' --oid <oid> --output yaml

# Everything one specific identity has a grant on
limacharlie cloudsec query run --text 'MATCH (i:Identity {email: "svc-deploy@example.com"})-[:has_permission_on]->(d:DataStore) RETURN d' --oid <oid> --output yaml
```

### The Selective-Anchor Rule (Queries Get Rejected Otherwise)

Every query must **anchor on a selective node set and traverse inward**. This is validated server-side; a query anchored on the dense fabric is rejected, by design.

- **Inherently selective anchors** (fine as-is): `DataStore`, `Vulnerability`, `PublicEndpoint`, `Application`, `ExternalAsset`, `AIService`, `Account`.
- **Dense types** (`ComputeInstance`, `Identity`, `Endpoint`, `ThirdPartyAsset`, ...) must be narrowed by a selectivity predicate on the anchor: `is_sensitive: true`, `is_public: true`, `is_external: true`, `in_kev: true`, an exact `email`, or an exact `sid`. Note the boolean forms only narrow when `true` — `{is_sensitive: false}` matches nearly everything and is rejected.

If a query is rejected, don't fight the validator — restructure: put the selective end (the sensitive data store, the KEV vuln, the specific identity) first and walk inward toward the dense side. Every question has a selective end.

Queries worth keeping become `cloudsec_query` Hive records (shared, versioned, IaC-manageable).

## Other Areas — Quick Reference

### Inventory (CSPM)

```bash
limacharlie cloudsec inventory list --type <type> --provider gcp --account <acct> --region <region> -q <substr> --oid <oid> --output yaml
```

Inventory listing is account-scoped by default; `--all-accounts` spans the estate. `changes` shows the recent created/closed finding feed; `risk-trend` the score history; `topology` a pre-aggregated estate rollup (counts are exact at any scale).

### Chokepoints

Chokepoints are the few nodes many attack paths funnel through — fixing one collapses many paths. Prioritize them over fixing findings one at a time:

```bash
limacharlie cloudsec chokepoint list --oid <oid> --output yaml
limacharlie cloudsec chokepoint dismiss "<urn>" --reason "..." --oid <oid> --output yaml   # and: restore
```

### Data Security (DSPM)

```bash
limacharlie cloudsec data-security facets --oid <oid> --output yaml
```

### Compliance

```bash
limacharlie cloudsec compliance frameworks --oid <oid> --output yaml
limacharlie cloudsec compliance report --framework cis-gcp --oid <oid> --output yaml
limacharlie cloudsec compliance assignments --oid <oid> --output yaml   # scoped assignments; report --assignment <id>
```

Framework ids include `cis-aws`, `cis-azure`, `cis-gcp`, `soc2`, `pci-dss`, `hipaa`, `iso-27001`, `nist-csf`, `nist-ai-rmf`, `owasp-llm`. Per-control results are PASS / FAIL / NOT_ASSESSED / NOT_APPLICABLE.

### CAASM (Third-Party Asset Inventory)

Merged asset view across ingested third-party sources, plus expected-coverage gap analysis:

```bash
limacharlie cloudsec caasm assets -q <substr> --oid <oid> --output yaml
limacharlie cloudsec caasm coverage --status <status> --oid <oid> --output yaml
limacharlie cloudsec caasm policy get --oid <oid> --output yaml
limacharlie cloudsec caasm ingest --source <source> --records-file records.json --oid <oid> --output yaml
```

Ingest sources are an open registry (e.g. `sentinelone`, `crowdstrike`, `defender`, `okta`, `entraid`, `ms_graph`, `wiz`); payloads are capped at 1 MiB per call.

### Providers, Policy Authoring, Simulation

```bash
# What CAN each provider collect vs. what this org's sweep actually got
limacharlie cloudsec provider manifest --oid <oid> --output yaml

# Preflight a credential before saving the provider record (ephemeral, nothing stored)
limacharlie cloudsec provider test --input-file provider.json --oid <oid> --output yaml

# Policy authoring aids: valid matcher vocabulary + value suggestions from the live estate
limacharlie cloudsec policy vocabulary --oid <oid> --output yaml
limacharlie cloudsec policy suggest --dimension name -q "prod" --oid <oid> --output yaml

# Read-only previews: which resources/findings would a policy rule match?
limacharlie cloudsec simulate resources --input-file rules.json --target data_store --oid <oid> --output yaml
limacharlie cloudsec simulate findings --match-json '{}' --oid <oid> --output yaml
```

Policy matchers use glob patterns: doublestar globs (`*`, `?`, `[...]`, `{a,b}`, `**` crosses `/`) with a list convention — positive patterns OR together, a leading `!` negates and vetoes the whole list. Use `simulate` to verify a matcher before saving the policy; never assume a glob's coverage.

Sensitivity is **user-declared**: nothing is "sensitive" or a crown jewel until a classification policy says so. If attack paths and sensitive-data queries come back empty, check whether a classification policy exists before concluding the estate has no sensitive data.

### MSSP Fleet

```bash
limacharlie cloudsec fleet overview --oid <oid1> --oid <oid2> --oid <oid3> --output yaml
```

The one multi-org command: a posture board across accessible orgs (per-org rollups, `skipped` for orgs without the subscription).

### CSV Export

`export findings` / `export inventory` / `export compliance` / `export query` take the same filters as their list commands plus `-o <file>`. The server walks the full filtered set (100k-row cap; a `#`-prefixed trailer line marks truncation).

## Findings as Events

Findings are platform events: `cloud_finding.created` and `cloud_finding.closed` land in the org's event stream, so D&R rules, Outputs, and Cases work on them like any other telemetry (e.g. auto-open a case on a new `toxic_combination`).

## Gotchas

| Gotcha | Rule |
|--------|------|
| Ranking | Sort and prioritize by `lc_risk`, not raw severity |
| `reachable` | Positive assertions only — absence ≠ isolated |
| `metadata` access | Not data access; don't report it as a data-exposure risk |
| Empty results | Check `scan-status` (has a sweep completed?) and classification policy (is anything declared sensitive?) before concluding "no risk" |
| Query rejected | Anchor wasn't selective — restructure to start from the selective end |
| Text queries | Cypher-like grammar, not natural language; underscore edge names |
| Pack names | Exact, underscore-separated (`public_data_stores`); get them from `query list` |
| Filters | Repeatable flags OR within a key, AND across keys |
| Pagination | Keyset only: pass `next_cursor` back as `--cursor` |
| URNs | Always shell-quote them |
| Auto-close | Sweeps close findings when the condition disappears; don't pre-emptively resolve |
| Hive records | `cloudsec_provider` / `cloudsec_policy` / `cloudsec_query` records are disabled until explicitly enabled |
