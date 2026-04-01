# LimaCharlie Advanced Skills Plugin

Advanced LimaCharlie workflows for MSSP operations, fleet management, threat intelligence, and infrastructure automation. **Requires the `lc-essentials` plugin** for core platform access, CLI bootstrap, and constants.

All CLI usage rules, timestamp handling, LCQL generation, and D&R rule generation are defined in `lc-essentials`. This plugin adds specialized skills on top.

## Skills

### MSSP & Multi-Tenant
- **reporting** - Multi-tenant security and operational reports with billing, usage, detections, and sensor health
- **graphic-output** - Interactive HTML dashboards with D3.js charts from report data
- **sensor-coverage** - Fleet-wide asset inventory, coverage gap detection, and risk scoring
- **reporting-templates** (command) - Pre-defined report templates

### Threat Intelligence
- **threat-report-evaluation** - Parse threat reports, extract IOCs, hunt across orgs, build detections
- **fp-pattern-finder** - Deterministic FP pattern detection with analyst validation

### Infrastructure & Onboarding
- **adapter-assistant** - Adapter lifecycle (External Adapters, Cloud Sensors, USP)
- **parsing-helper** - Grok parsing rule generation and testing
- **onboard-new-org** - Organization onboarding wizard with cloud discovery and EDR deployment
- **limacharlie-iac** - Infrastructure as Code with ext-git-sync

### Fleet Operations
- **lc-deployer** - Deploy/remove Agentic SOC as Code definitions (ai-team) and individual AI agents (ai-agents)
- **test-limacharlie-edr** - Deploy temporary local EDR agent for testing
- **test-limacharlie-adapter** - Deploy temporary local adapter for testing
