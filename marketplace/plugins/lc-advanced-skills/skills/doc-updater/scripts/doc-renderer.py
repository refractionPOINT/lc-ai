#!/usr/bin/env python3
"""
LimaCharlie Organization Documentation Renderer

Renders Jinja2 templates with org configuration data to produce
wiki-ready markdown documentation.

Usage:
    python3 doc-renderer.py --data config.yaml --templates ./templates/ --output ./docs/
    python3 doc-renderer.py --data config.yaml --templates ./templates/ --output ./docs/ --validate-only

Requires: pip install jinja2 pyyaml
"""

import argparse
import os
import re
import sys
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound
except ImportError:
    print("ERROR: jinja2 not installed. Run: pip install jinja2", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Template-to-output mapping
# ---------------------------------------------------------------------------
TEMPLATE_MAP = {
    "readme.md.j2": "README.md",
    "architecture.md.j2": "architecture.md",
    "sensors.md.j2": "sensors.md",
    "detection-rules.md.j2": "detection-rules.md",
    "ai-agents.md.j2": "ai-agents.md",
    "data-pipeline.md.j2": "data-pipeline.md",
    "access-control.md.j2": "access-control.md",
    "runbook-admin.md.j2": "runbooks/common-admin-tasks.md",
    "runbook-ir.md.j2": "runbooks/incident-response.md",
    "runbook-updating.md.j2": "runbooks/updating-docs.md",
}


# ---------------------------------------------------------------------------
# Security redaction
# ---------------------------------------------------------------------------
_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
_WEBHOOK_RE = re.compile(r"https?://[^\s]*hook[^\s]*", re.IGNORECASE)


def redact_ips(text: str) -> str:
    """Replace IPv4 addresses with [REDACTED]."""
    return _IP_RE.sub("[REDACTED-IP]", text)


def redact_webhook_urls(text: str) -> str:
    """Replace webhook URLs with a placeholder."""
    return _WEBHOOK_RE.sub("[REDACTED-WEBHOOK-URL]", text)


def redact(text: str) -> str:
    """Apply all redaction filters."""
    text = redact_ips(text)
    text = redact_webhook_urls(text)
    return text


# ---------------------------------------------------------------------------
# Custom Jinja2 filters
# ---------------------------------------------------------------------------
def filter_badge_encode(value: str) -> str:
    """Encode a string for use in a shields.io badge URL."""
    return (
        str(value)
        .replace("-", "--")
        .replace("_", "__")
        .replace(" ", "_")
    )


def filter_abbreviate_oid(oid: str) -> str:
    """Show first 8 characters of an OID for display."""
    return str(oid)[:8] if oid else ""


def filter_hostname_short(fqdn: str) -> str:
    """Extract the short hostname from an FQDN."""
    return str(fqdn).split(".")[0] if fqdn else ""


def filter_bool_to_yes_no(value) -> str:
    """Convert boolean to Yes/No."""
    if isinstance(value, bool):
        return "**Yes**" if value else "No"
    return str(value)


def filter_redact(text: str) -> str:
    """Jinja2 filter for redaction."""
    return redact(str(text))


# ---------------------------------------------------------------------------
# Data enrichment — compute derived values from raw config
# ---------------------------------------------------------------------------
def enrich_config(config: dict) -> dict:
    """Add computed fields that templates need but the raw data doesn't provide."""

    # --- Sensor counts ---
    sensors = config.get("sensors", {})
    edr = sensors.get("edr", [])
    cloud = sensors.get("cloud", [])
    extensions = sensors.get("extensions", [])

    sensors["edr_count"] = len(edr)
    sensors["cloud_count"] = len(cloud)
    sensors["extension_count"] = len(extensions)
    sensors["edr_online"] = [s for s in edr if s.get("is_online")]
    sensors["edr_offline"] = [s for s in edr if not s.get("is_online")]
    sensors["edr_isolated"] = [s for s in edr if s.get("is_isolated")]
    sensors["cloud_online"] = [s for s in cloud if s.get("is_online")]
    sensors["cloud_offline"] = [s for s in cloud if not s.get("is_online")]

    # --- Normalize rules (ensure all optional fields exist) ---
    rules = config.get("rules", {})
    categories = rules.get("categories", {})

    RULE_DEFAULTS = {
        "name": "", "display_name": "", "event": "", "enabled": False,
        "response": "", "source": "", "mitre": "", "level": "",
        "malware_families": "", "cve": "", "metadata": {},
        "target": "", "trigger_type": "", "schedule": "", "agent": "",
        "team": "", "suppression": "", "trigger_detail": "",
        "lookup_table": "", "dest_output": "",
    }
    for cat_rules in categories.values():
        for rule in cat_rules:
            for key, default in RULE_DEFAULTS.items():
                rule.setdefault(key, default)

    total = 0
    enabled = 0
    disabled = 0
    category_counts = {}
    for cat_name, cat_rules in categories.items():
        count = len(cat_rules)
        total += count
        cat_enabled = sum(1 for r in cat_rules if r.get("enabled"))
        cat_disabled = count - cat_enabled
        enabled += cat_enabled
        disabled += cat_disabled
        category_counts[cat_name] = {
            "total": count,
            "enabled": cat_enabled,
            "disabled": cat_disabled,
        }

    rules["total_count"] = total
    rules["enabled_count"] = enabled
    rules["disabled_count"] = disabled
    rules["category_counts"] = category_counts

    # Build disabled review queue
    review_queue = {}
    for cat_name, cat_rules in categories.items():
        disabled_rules = [r for r in cat_rules if not r.get("enabled")]
        if disabled_rules:
            review_queue[cat_name] = disabled_rules
    rules["review_queue"] = review_queue

    # --- Agent counts ---
    agents = config.get("agents", {})
    teams = agents.get("teams", {})
    standalone = agents.get("standalone", [])

    total_agents = sum(len(t.get("agents", [])) for t in teams.values()) + len(standalone)
    agents["total_count"] = total_agents
    agents["team_count"] = len(teams)

    # Agent scheduling summary
    scheduled = []
    on_demand = []
    for team in teams.values():
        for agent in team.get("agents", []):
            if agent.get("schedule"):
                scheduled.append(agent)
            else:
                on_demand.append(agent)
    for agent in standalone:
        if agent.get("schedule"):
            scheduled.append(agent)
        else:
            on_demand.append(agent)
    agents["scheduled"] = scheduled
    agents["on_demand"] = on_demand

    # --- Extension / adapter / output counts ---
    config.setdefault("extensions", [])
    adapters = config.get("adapters", {})
    adapters["active_count"] = len(adapters.get("active", []))
    adapters["disabled_count"] = len(adapters.get("disabled", []))

    config["lookups"] = config.get("lookups", [])
    config["payloads"] = config.get("payloads", [])
    config["outputs"] = config.get("outputs", [])
    config["secrets"] = config.get("secrets", [])
    config.setdefault("api_keys", {"agent_keys": []})
    config.setdefault("installation_keys", {"user_created": []})
    config["sops"] = config.get("sops", [])
    config["tags"] = config.get("tags", [])
    config["fp_rules"] = config.get("fp_rules", [])
    config.setdefault("services_not_registered", [])
    config.setdefault("known_issues", [])
    config.setdefault("managed_packs", [])
    config.setdefault("recent_changes", [])

    # --- Capabilities table ---
    capabilities = []

    if edr:
        plats = ", ".join(sorted(set(s.get("platform", "?") for s in edr)))
        capabilities.append({
            "name": "EDR Coverage",
            "status": "Active",
            "details": f"{len(edr)} endpoint(s) ({plats})",
        })

    cloud_disabled = [a for a in adapters.get("disabled", []) if a.get("type") != "webhook"]
    if cloud_disabled:
        names = ", ".join(a.get("hostname", "?") for a in cloud_disabled)
        capabilities.append({
            "name": "Cloud Integration",
            "status": "Partial",
            "details": f"{names} adapter(s) disabled",
        })

    if config.get("managed_packs"):
        pack_names = ", ".join(p.get("name", "?") for p in config["managed_packs"])
        capabilities.append({
            "name": "Managed Detection",
            "status": "Active",
            "details": pack_names,
        })

    for team_key, team_data in teams.items():
        agent_count = len(team_data.get("agents", []))
        capabilities.append({
            "name": team_data.get("display_name", team_key),
            "status": "Active",
            "details": f"{agent_count}-agent pipeline",
        })

    config["capabilities"] = capabilities

    return config


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
REQUIRED_TOP_LEVEL = ["org", "sensors", "rules", "agents"]
REQUIRED_ORG_FIELDS = ["name", "oid"]


def validate_config(config: dict) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in config:
            errors.append(f"Missing required top-level field: '{field}'")

    org = config.get("org", {})
    for field in REQUIRED_ORG_FIELDS:
        if field not in org:
            errors.append(f"Missing required org field: 'org.{field}'")

    if not isinstance(config.get("sensors", {}).get("edr"), list):
        errors.append("'sensors.edr' must be a list")

    if not isinstance(config.get("rules", {}).get("categories"), dict):
        errors.append("'rules.categories' must be a dict")

    if not isinstance(config.get("agents", {}).get("teams"), dict):
        errors.append("'agents.teams' must be a dict")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Render LimaCharlie org documentation from config data + Jinja2 templates."
    )
    parser.add_argument(
        "--data", required=True, help="Path to config YAML file"
    )
    parser.add_argument(
        "--templates", required=True, help="Path to Jinja2 template directory"
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for rendered markdown"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate config data without rendering",
    )
    args = parser.parse_args()

    # Load config data
    try:
        with open(args.data, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(config, dict):
        print("ERROR: Config must be a YAML mapping", file=sys.stderr)
        sys.exit(1)

    # Validate
    errors = validate_config(config)
    if errors:
        print("Validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        if args.validate_only:
            sys.exit(1)
        print("WARNING: Proceeding despite validation errors", file=sys.stderr)

    if args.validate_only:
        print("Validation passed.")
        sys.exit(0)

    # Enrich data with computed fields
    config = enrich_config(config)

    # Set up generated_at if not present
    config["org"].setdefault("generated_at", datetime.utcnow().strftime("%Y-%m-%d"))

    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(args.templates),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Register custom filters
    env.filters["badge_encode"] = filter_badge_encode
    env.filters["abbreviate_oid"] = filter_abbreviate_oid
    env.filters["hostname_short"] = filter_hostname_short
    env.filters["yesno"] = filter_bool_to_yes_no
    env.filters["redact"] = filter_redact

    # Render all templates
    rendered_count = 0
    for template_name, output_path in TEMPLATE_MAP.items():
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            print(f"  SKIP: {template_name} (not found)", file=sys.stderr)
            continue

        rendered = template.render(**config)

        # Apply security redaction as final pass
        rendered = redact(rendered)

        full_output = os.path.join(args.output, output_path)
        os.makedirs(os.path.dirname(full_output) or ".", exist_ok=True)

        with open(full_output, "w") as f:
            f.write(rendered)

        rendered_count += 1
        print(f"  Rendered: {output_path}")

    print(f"\nDone: {rendered_count}/{len(TEMPLATE_MAP)} files rendered to {args.output}/")


if __name__ == "__main__":
    main()
