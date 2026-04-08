#!/usr/bin/env python3
"""
LimaCharlie Organization Config Exporter

Collects all org configuration via the limacharlie CLI and produces
a config.yaml file in the schema expected by doc-renderer.py.

Usage:
    python3 doc-exporter.py --oid <uuid> --output config.yaml
    python3 doc-exporter.py --oid <uuid> --output config.yaml --repo-url https://github.com/org/repo

Requires: pip install pyyaml
          limacharlie CLI installed and authenticated
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def run_lc(args: list[str], oid: str) -> dict | list | None:
    """Run a limacharlie CLI command and return parsed YAML output."""
    cmd = ["limacharlie"] + args + ["--oid", oid, "--output", "yaml"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"  WARN: {' '.join(cmd[:4])}... failed: {result.stderr.strip()}", file=sys.stderr)
            return None
        return yaml.safe_load(result.stdout) if result.stdout.strip() else None
    except subprocess.TimeoutExpired:
        print(f"  WARN: {' '.join(cmd[:4])}... timed out", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  WARN: {' '.join(cmd[:4])}... error: {e}", file=sys.stderr)
        return None


def run_lc_raw(args: list[str], oid: str) -> str:
    """Run a limacharlie CLI command and return raw stdout."""
    cmd = ["limacharlie"] + args + ["--oid", oid, "--output", "yaml"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Platform constants
# ---------------------------------------------------------------------------
PLAT_NAMES = {
    268435456: "Windows",
    536870912: "Linux",
    805306368: "macOS",
    67108864: "Cloud Sensor",
    2415919104: "Extension",
}

ARCH_NAMES = {
    1: "x86",
    2: "x86_64",
    3: "ARM",
    4: "ARM64",
}


# ---------------------------------------------------------------------------
# Sensor collection
# ---------------------------------------------------------------------------
def collect_sensors(oid: str) -> dict:
    """Collect and categorize sensors."""
    print("  Collecting sensors...")
    raw = run_lc(["sensor", "list"], oid)
    if not raw:
        return {"edr": [], "cloud": [], "extensions": []}

    sensors = raw if isinstance(raw, list) else []
    edr, cloud, extensions = [], [], []

    for s in sensors:
        plat_code = s.get("plat", 0)
        hostname = s.get("hostname", "")
        hostname_short = hostname.split(".")[0] if hostname else ""

        if plat_code == 2415919104:  # Extension sensor
            extensions.append({
                "hostname": hostname_short,
                "sid": s.get("sid", ""),
                "is_online": s.get("is_online", False),
            })
        elif plat_code == 67108864:  # Cloud sensor
            cloud.append({
                "hostname": hostname_short,
                "sid": s.get("sid", ""),
                "type": _infer_cloud_type(s),
                "platform": _infer_cloud_platform(s),
                "is_online": s.get("is_online", False),
                "enrolled": _format_date(s.get("enroll", "")),
                "tags": s.get("tags", []),
            })
        else:  # EDR sensor
            plat_name = PLAT_NAMES.get(plat_code, f"Unknown ({plat_code})")
            arch_name = ARCH_NAMES.get(s.get("arch", 0), "")
            version = s.get("version", "")
            if version.startswith("lc_sensor_"):
                version = version[len("lc_sensor_"):]

            edr.append({
                "hostname_short": hostname_short,
                "sid": s.get("sid", ""),
                "platform": f"{plat_name} ({arch_name})" if arch_name else plat_name,
                "version": version,
                "is_online": s.get("is_online", False),
                "is_isolated": s.get("is_isolated", s.get("should_isolate", False)),
                "enrolled": _format_date(s.get("enroll", "")),
            })

    return {"edr": edr, "cloud": cloud, "extensions": extensions}


def _infer_cloud_type(sensor: dict) -> str:
    tags = sensor.get("tags", [])
    hostname = sensor.get("hostname", "").lower()
    if "defender" in hostname:
        return "Azure Event Hub"
    if "office365" in hostname or "o365" in hostname:
        return "Office 365"
    return "Cloud Sensor"


def _infer_cloud_platform(sensor: dict) -> str:
    hostname = sensor.get("hostname", "").lower()
    if "defender" in hostname:
        return "MS Defender"
    if "office365" in hostname or "o365" in hostname:
        return "Office 365"
    return "Cloud"


def _format_date(ts: str) -> str:
    if not ts:
        return ""
    return ts.split(" ")[0] if " " in str(ts) else str(ts)[:10]


# ---------------------------------------------------------------------------
# Rule collection and categorization
# ---------------------------------------------------------------------------
def collect_rules(oid: str) -> dict:
    """Collect D&R rules and categorize them."""
    print("  Collecting D&R rules...")
    raw = run_lc(["dr", "list"], oid)
    if not raw:
        return {"categories": {}, "managed_packs": [], "fp_rules": []}

    # dr list returns a dict keyed by rule name with full definitions
    if isinstance(raw, dict):
        rules_items = list(raw.items())
    elif isinstance(raw, list):
        rules_items = [(r.get("name", ""), r) for r in raw if isinstance(r, dict)]
    else:
        rules_items = []

    categories: dict[str, list] = {}
    for name, rule_data in rules_items:
        if not name:
            continue

        rule_data = rule_data if isinstance(rule_data, dict) else {}
        data = rule_data.get("data", rule_data)
        usr_mtd = rule_data.get("usr_mtd", {})
        detect = data.get("detect", {})
        respond = data.get("respond", [])
        tags = usr_mtd.get("tags", [])
        enabled = usr_mtd.get("enabled", True)

        cat = _categorize_rule(name, detect, respond, tags)

        if cat not in categories:
            categories[cat] = []

        rule_info = _build_rule_info(name, cat, detect, respond, tags, enabled, data)
        categories[cat].append(rule_info)

    # Collect FP rules
    print("  Collecting FP rules...")
    fp_raw = run_lc(["fp", "list"], oid)
    fp_rules = []
    if fp_raw and isinstance(fp_raw, dict):
        for fp_name, fp_data in fp_raw.items():
            fp_rules.append({"name": fp_name, "description": ""})

    # Collect managed packs
    managed_packs = _detect_managed_packs(oid)

    return {"categories": categories, "managed_packs": managed_packs, "fp_rules": fp_rules}


def _categorize_rule(name: str, detect: dict, respond: list, tags: list) -> str:
    """Determine which category a rule belongs to."""
    target = detect.get("target", "")

    # Schedule-based rules are always AI triggers
    if target == "schedule":
        return "ai_triggers"

    # AI trigger rules — only if they actually start an AI agent
    has_ai_action = False
    for action in (respond if isinstance(respond, list) else []):
        if isinstance(action, dict) and action.get("action") == "start ai agent":
            has_ai_action = True
            break
        action_str = str(action)
        if "hive://ai_agent/" in action_str:
            has_ai_action = True
            break

    if has_ai_action:
        return "ai_triggers"

    for tag in tags:
        if tag.startswith("ai-team:") or tag.startswith("ai-agent:"):
            return "ai_triggers"

    # Name-based
    if name.startswith("intel-"):
        return "intel_pipeline"
    if name.startswith("mdr-"):
        return "mdr_hunting"
    if name.startswith("bas-"):
        return "bas_generated"

    # System/deployment
    if target == "deployment":
        return "system"

    # Data pipeline (output routing)
    for action in (respond if isinstance(respond, list) else []):
        action_str = str(action)
        if "output" in action_str.lower() and "report" not in action_str.lower():
            return "data_pipeline"

    # Check for -to-output pattern
    if "-to-" in name and ("output" in name or "bigquery" in name):
        return "data_pipeline"

    return "threat_detection"


def _build_rule_info(name: str, cat: str, detect: dict, respond: list, tags: list, enabled: bool, data: dict) -> dict:
    """Build a rule info dict matching the config schema."""
    display_names = {
        "threat_detection": "Threat Detection",
        "system": "System",
        "ai_triggers": "AI Triggers",
        "intel_pipeline": "Intel Pipeline",
        "mdr_hunting": "MDR Hunting",
        "bas_generated": "BAS Generated",
        "data_pipeline": "Data Pipeline",
    }

    info = {
        "name": name,
        "display_name": display_names.get(cat, cat),
        "enabled": enabled,
    }

    if cat == "ai_triggers":
        event = detect.get("event", "")
        target = detect.get("target", "")
        is_schedule = target == "schedule" or "_per_org" in str(event)

        # Find agent from respond
        agent = ""
        for action in (respond if isinstance(respond, list) else []):
            if isinstance(action, dict):
                defn = action.get("definition", "")
                if "hive://ai_agent/" in defn:
                    agent = defn.split("hive://ai_agent/")[-1].strip()
                    break
            action_str = str(action)
            if "hive://ai_agent/" in action_str:
                match = re.search(r"hive://ai_agent/([\w-]+)", action_str)
                if match:
                    agent = match.group(1)

        # Infer schedule from event
        schedule = ""
        if "1h_per_org" in str(event):
            schedule = "Every 1h"
        elif "24h_per_org" in str(event):
            schedule = "Every 24h"
        elif "168h_per_org" in str(event):
            schedule = "Every 168h"

        # Determine trigger type
        if is_schedule:
            trigger_type = "schedule"
            trigger_detail = ""
        elif "case_tags_updated" in str(event):
            trigger_type = "tag"
            trigger_detail = _extract_tag_trigger(detect)
        elif "case_escalated" in str(event):
            trigger_type = "escalation"
            trigger_detail = "case escalated"
        elif "case_note_added" in str(event):
            trigger_type = "mention"
            trigger_detail = _extract_mention_trigger(detect, name)
        else:
            trigger_type = "event"
            trigger_detail = str(event)

        # Infer team from tags
        team = ""
        for tag in tags:
            if tag.startswith("ai-team:"):
                parts = tag.split(":")
                if len(parts) >= 2:
                    team = parts[1].replace("-", " ").title()
                    break
            elif tag.startswith("ai-agent:"):
                team = "Standalone"

        info.update({
            "trigger_type": trigger_type,
            "schedule": schedule,
            "agent": agent,
            "team": team,
            "trigger_detail": trigger_detail,
            "suppression": _extract_suppression(respond),
        })

    elif cat in ("intel_pipeline", "mdr_hunting"):
        metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
        info.update({
            "event": detect.get("event", ""),
            "source": metadata.get("intel_source", ""),
            "mitre": ", ".join(metadata.get("mitre", [])) if isinstance(metadata.get("mitre"), list) else str(metadata.get("mitre", "")),
            "level": metadata.get("level", ""),
            "cve": metadata.get("cve", ""),
            "response": _summarize_respond(respond),
        })

    elif cat == "data_pipeline":
        info.update({
            "event": detect.get("event", ""),
            "response": _summarize_respond(respond),
            "dest_output": _extract_output_dest(respond),
        })

    elif cat == "system":
        info.update({
            "event": detect.get("event", ""),
            "target": detect.get("target", ""),
            "response": _summarize_respond(respond),
        })

    else:  # threat_detection, bas_generated
        event = detect.get("event", "")
        if isinstance(event, list):
            event = ", ".join(str(e) for e in event)
        info.update({
            "event": str(event),
            "response": _summarize_respond(respond),
        })

    return info


def _extract_tag_trigger(detect: dict) -> str:
    """Extract the tag name from a tag-based trigger."""
    rules = detect.get("rules", [])
    for rule in rules:
        path = rule.get("path", "")
        value = rule.get("value", "")
        if "new_tags" in path:
            return str(value)
    return ""


def _extract_mention_trigger(detect: dict, name: str) -> str:
    """Extract the mention keyword from a mention-based trigger."""
    rules = detect.get("rules", [])
    for rule in rules:
        value = rule.get("value", "")
        if value and isinstance(value, str) and "@" not in value:
            if "content" in rule.get("path", ""):
                return str(value)
    # Fallback: extract from rule name
    if "-on-mention" in name:
        return name.replace("-on-mention", "")
    return ""


def _extract_suppression(respond: list) -> str:
    """Extract suppression info from respond actions."""
    for action in (respond if isinstance(respond, list) else []):
        if isinstance(action, dict) and "suppression" in action:
            supp = action["suppression"]
            period = supp.get("period", "")
            max_count = supp.get("max_count", "")
            if period and max_count:
                return f"{max_count} per key per {period}"
    return ""


def _summarize_respond(respond: list) -> str:
    """Create a brief summary of response actions."""
    parts = []
    for action in (respond if isinstance(respond, list) else []):
        if isinstance(action, dict):
            parts.append(action.get("action", ""))
        elif isinstance(action, str):
            parts.append(action.split(":")[0].strip() if ":" in action else action)
    return " + ".join(p for p in parts[:3] if p)


def _extract_output_dest(respond: list) -> str:
    """Extract output destination from respond actions."""
    for action in (respond if isinstance(respond, list) else []):
        action_str = str(action)
        if "output" in action_str.lower():
            match = re.search(r"name:\s*(\S+)", action_str)
            if match:
                return match.group(1)
    return ""


def _detect_managed_packs(oid: str) -> list:
    """Detect managed rule packs from extension list."""
    exts = run_lc(["extension", "list"], oid)
    if not exts:
        return []

    KNOWN_PACKS = {
        "soteria-rules-edr": {"name": "Soteria EDR", "docs_url": "https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/edr/"},
        "soteria-rules-aws": {"name": "Soteria AWS", "docs_url": "https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/aws/"},
        "soteria-rules-o365": {"name": "Soteria O365", "docs_url": "https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/m365/"},
    }

    packs = []
    ext_list = exts if isinstance(exts, list) else list(exts.keys()) if isinstance(exts, dict) else []
    for ext in ext_list:
        ext_name = ext.get("name", ext) if isinstance(ext, dict) else str(ext)
        if ext_name in KNOWN_PACKS:
            packs.append({"extension": ext_name, **KNOWN_PACKS[ext_name]})

    return packs


# ---------------------------------------------------------------------------
# Agent collection
# ---------------------------------------------------------------------------
def collect_agents(oid: str) -> dict:
    """Collect AI agents and organize into teams."""
    print("  Collecting AI agents...")
    raw = run_lc(["hive", "list", "--hive-name", "ai_agent"], oid)
    if not raw:
        return {"teams": {}, "standalone": []}

    agents_data = raw if isinstance(raw, dict) else {}
    teams: dict[str, dict] = {}
    standalone = []

    for key, agent_data in agents_data.items():
        data = agent_data.get("data", {})
        usr_mtd = agent_data.get("usr_mtd", {})
        tags = usr_mtd.get("tags", [])

        # Extract a one-line purpose from the prompt (first non-empty paragraph)
        prompt = data.get("prompt", "")
        purpose = ""
        if prompt:
            for line in prompt.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("You will receive"):
                    # Take first sentence up to ~120 chars
                    purpose = line[:200].rstrip(".")
                    if len(purpose) > 120:
                        purpose = purpose[:120].rsplit(" ", 1)[0] + "..."
                    break

        agent_info = {
            "name": data.get("name", key).split(" - ")[0].split(" Case ")[0].strip(),
            "key": key,
            "model": data.get("model", ""),
            "budget": data.get("max_budget_usd", 0),
            "ttl": data.get("ttl_seconds", 0),
            "trigger_rule": "",
            "schedule": "",
            "trigger_type": "",
            "trigger_detail": "",
            "purpose": purpose,
        }

        # Determine team from tags: match lc-soc:<team>:<role> or ai-team:<team>
        team_key = None
        for tag in tags:
            if tag.startswith("lc-soc:"):
                parts = tag.split(":")
                if len(parts) >= 3:
                    team_key = parts[1]  # e.g., "baselining-soc"
                    break
            elif tag.startswith("ai-team:"):
                parts = tag.split(":")
                if len(parts) >= 2:
                    team_key = parts[1]
                    break

        # Extract sends-to relationships from tags
        sends_to = []
        for tag in tags:
            if ":sends-to:" in tag:
                target = tag.split(":sends-to:")[-1]
                sends_to.append(target)
        agent_info["sends_to"] = sends_to

        if team_key:
            if team_key not in teams:
                teams[team_key] = {
                    "display_name": team_key.replace("-", " ").title(),
                    "description": "",
                    "agents": [],
                    "inter_agent_tags": [],
                    "mentions": [],
                }
            teams[team_key]["agents"].append(agent_info)
        else:
            standalone.append(agent_info)

    # Build inter-agent communication data for each team
    for team_data in teams.values():
        mentions = []
        for agent in team_data["agents"]:
            for target in agent.get("sends_to", []):
                mentions.append({
                    "mention": f"@{target}",
                    "agent": target,
                    "set_by": agent["key"],
                })
        team_data["mentions"] = mentions

    return {"teams": teams, "standalone": standalone}


# ---------------------------------------------------------------------------
# Cross-reference D&R trigger rules to agents
# ---------------------------------------------------------------------------
def _link_trigger_rules_to_agents(config: dict) -> None:
    """Cross-reference D&R trigger rules to populate agent trigger/schedule fields."""
    # Build map: agent_key → trigger rule info
    trigger_map: dict[str, dict] = {}
    for cat, rules in config.get("rules", {}).get("categories", {}).items():
        if cat != "ai_triggers":
            continue
        for rule in rules:
            agent_key = rule.get("agent", "")
            if agent_key:
                trigger_map[agent_key] = {
                    "trigger_rule": rule.get("name", ""),
                    "schedule": rule.get("schedule", ""),
                    "trigger_type": rule.get("trigger_type", ""),
                    "trigger_detail": rule.get("trigger_detail", ""),
                }

    # Apply to agents in teams
    for team_data in config.get("agents", {}).get("teams", {}).values():
        for agent in team_data.get("agents", []):
            info = trigger_map.get(agent["key"], {})
            if info:
                agent["trigger_rule"] = info["trigger_rule"]
                agent["schedule"] = info["schedule"]
                agent["trigger_type"] = info["trigger_type"]
                agent["trigger_detail"] = info["trigger_detail"]

    # Apply to standalone agents
    for agent in config.get("agents", {}).get("standalone", []):
        info = trigger_map.get(agent["key"], {})
        if info:
            agent["trigger_rule"] = info["trigger_rule"]
            agent["schedule"] = info["schedule"]
            agent["trigger_type"] = info["trigger_type"]
            agent["trigger_detail"] = info["trigger_detail"]

    # Generate team descriptions
    SOC_DESCRIPTIONS = {
        "baselining-soc": "Baselining SOC — aggressively creates FP rules to reduce noise on newly onboarded orgs while triaging real threats",
        "tiered-soc": "Tiered SOC — full defense-in-depth pipeline with L1, L2, containment, and threat hunting",
        "lean-soc": "Lean SOC — minimal viable SOC with bulk triage and escalation",
        "bas-team": "Breach & Attack Simulation — automated adversary simulation using Atomic Red Team, with detection validation and gap analysis",
        "intel-team": "Threat Intelligence Pipeline — automated ingestion, curation, and operationalization of threat intelligence into detection rules and lookups",
        "mdr-team": "Managed Detection & Response — proactive threat hunting and investigation across the fleet",
        "exposure-soc": "Exposure SOC — external attack surface monitoring and vulnerability-driven detection",
    }
    for team_key, team_data in config.get("agents", {}).get("teams", {}).items():
        if not team_data.get("description"):
            team_data["description"] = SOC_DESCRIPTIONS.get(team_key, "")


# ---------------------------------------------------------------------------
# Simple collections
# ---------------------------------------------------------------------------
def collect_extensions(oid: str) -> list:
    """Collect subscribed extensions."""
    print("  Collecting extensions...")
    raw = run_lc(["extension", "list"], oid)
    if not raw:
        return []

    EXTENSION_CATEGORIES = {
        "ext-velociraptor": "Security Analysis & DFIR",
        "ext-hayabusa": "Security Analysis & DFIR",
        "ext-plaso": "Security Analysis & DFIR",
        "ext-yara": "Security Analysis & DFIR",
        "ext-yara-manager": "Security Analysis & DFIR",
        "ext-dumper": "Security Analysis & DFIR",
        "ext-zeek": "Security Analysis & DFIR",
        "ext-artifact": "Security Analysis & DFIR",
        "ext-cases": "Security Operations",
        "ext-atomic-red-team": "Security Operations",
        "ext-reliable-tasking": "Security Operations",
        "ext-exfil": "Security Operations",
        "ext-integrity": "Security Operations",
        "ext-sensor-cull": "Security Operations",
        "soteria-rules-edr": "Threat Intelligence & Detection",
        "soteria-rules-aws": "Threat Intelligence & Detection",
        "soteria-rules-o365": "Threat Intelligence & Detection",
        "loldrivers": "Threat Intelligence & Detection",
        "binlib": "Threat Intelligence & Detection",
        "ext-lookup-manager": "Infrastructure & Management",
        "payload-manager": "Infrastructure & Management",
        "ext-infrastructure": "Infrastructure & Management",
        "ext-pagerduty": "Notifications & Integrations",
        "ext-twilio": "Notifications & Integrations",
        "ext-govee": "Notifications & Integrations",
    }

    EXTENSION_DOCS = {
        "ext-velociraptor": "https://docs.limacharlie.io/5-integrations/extensions/third-party/velociraptor/",
        "ext-hayabusa": "https://docs.limacharlie.io/5-integrations/extensions/third-party/hayabusa/",
        "ext-plaso": "https://docs.limacharlie.io/5-integrations/extensions/third-party/plaso/",
        "ext-yara": "https://docs.limacharlie.io/5-integrations/extensions/third-party/yara/",
        "ext-yara-manager": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/yara-manager/",
        "ext-dumper": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/dumper/",
        "ext-zeek": "https://docs.limacharlie.io/5-integrations/extensions/third-party/zeek/",
        "ext-artifact": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/artifact/",
        "ext-cases": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/cases/",
        "ext-atomic-red-team": "https://docs.limacharlie.io/5-integrations/extensions/third-party/atomic-red-team/",
        "ext-reliable-tasking": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/reliable-tasking/",
        "ext-exfil": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/exfil/",
        "ext-integrity": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/integrity/",
        "ext-sensor-cull": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/sensor-cull/",
        "binlib": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/binlib/",
        "ext-lookup-manager": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/lookup-manager/",
        "payload-manager": "https://docs.limacharlie.io/5-integrations/extensions/limacharlie/payload-manager/",
        "ext-pagerduty": "https://docs.limacharlie.io/5-integrations/extensions/third-party/pagerduty/",
        "ext-twilio": "https://docs.limacharlie.io/5-integrations/extensions/third-party/twilio/",
        "ext-govee": "https://docs.limacharlie.io/5-integrations/extensions/third-party/govee/",
        "soteria-rules-edr": "https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/edr/",
        "soteria-rules-aws": "https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/aws/",
        "soteria-rules-o365": "https://docs.limacharlie.io/3-detection-response/managed-rulesets/soteria/m365/",
    }

    extensions = []
    ext_list = raw if isinstance(raw, list) else [{"name": k} for k in raw] if isinstance(raw, dict) else []
    for ext in ext_list:
        name = ext.get("name", "") if isinstance(ext, dict) else str(ext)
        extensions.append({
            "name": name,
            "category": EXTENSION_CATEGORIES.get(name, "Other"),
            "description": ext.get("label", "") if isinstance(ext, dict) else "",
            "docs_url": EXTENSION_DOCS.get(name, ""),
        })

    return extensions


def collect_adapters(oid: str) -> dict:
    print("  Collecting cloud adapters...")
    raw = run_lc(["cloud-adapter", "list"], oid)
    if not raw:
        return {"active": [], "disabled": []}

    active, disabled = [], []
    adapter_list = raw if isinstance(raw, list) else list(raw.values()) if isinstance(raw, dict) else []

    for a in adapter_list:
        info = {
            "key": a.get("name", a.get("key", "")),
            "type": a.get("sensor_type", a.get("type", "")),
            "platform": a.get("platform", ""),
            "hostname": a.get("hostname", ""),
            "installation_key": a.get("installation_key", ""),
            "tags": a.get("tags", []),
        }
        if a.get("enabled", True) is False:
            disabled.append(info)
        else:
            active.append(info)

    return {"active": active, "disabled": disabled}


def collect_simple_list(oid: str, noun: str, verb: str = "list") -> list | dict | None:
    return run_lc([noun, verb], oid)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Export LimaCharlie org config to YAML")
    parser.add_argument("--oid", required=True, help="Organization UUID")
    parser.add_argument("--output", required=True, help="Output YAML file path")
    parser.add_argument("--org-name", default="", help="Organization display name (auto-detected if omitted)")
    parser.add_argument("--repo-url", default="", help="GitHub repo URL for the docs")
    args = parser.parse_args()

    oid = args.oid
    print(f"Exporting config for org {oid}...")

    # Resolve org name
    org_name = args.org_name
    if not org_name:
        orgs = run_lc(["org", "list"], oid)
        if orgs and isinstance(orgs, list):
            for o in orgs:
                if o.get("oid") == oid:
                    org_name = o.get("name", oid[:8])
                    break
        if not org_name:
            org_name = oid[:8]

    config = {
        "org": {
            "name": org_name,
            "oid": oid,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
    }

    # Collect all config
    config["sensors"] = collect_sensors(oid)
    rules_data = collect_rules(oid)
    config["rules"] = {"categories": rules_data["categories"], "managed_packs": rules_data["managed_packs"], "fp_rules": rules_data["fp_rules"]}
    config["agents"] = collect_agents(oid)

    # Cross-reference D&R trigger rules to agents
    _link_trigger_rules_to_agents(config)

    config["extensions"] = collect_extensions(oid)
    config["adapters"] = collect_adapters(oid)

    # Simple collections
    print("  Collecting outputs...")
    outputs_raw = collect_simple_list(oid, "output")
    config["outputs"] = []
    if outputs_raw and isinstance(outputs_raw, list):
        for o in outputs_raw:
            config["outputs"].append({
                "name": o.get("name", ""),
                "module": o.get("module", ""),
                "stream": o.get("for", ""),
                "created_by": o.get("by", ""),
            })

    print("  Collecting lookups...")
    lookups_raw = collect_simple_list(oid, "lookup")
    config["lookups"] = []
    if lookups_raw:
        names = lookups_raw if isinstance(lookups_raw, list) else list(lookups_raw.keys()) if isinstance(lookups_raw, dict) else []
        for name in names:
            n = name if isinstance(name, str) else name.get("name", str(name))
            config["lookups"].append({"name": n, "purpose": "", "managed_by": ""})

    print("  Collecting payloads...")
    payloads_raw = collect_simple_list(oid, "payload")
    config["payloads"] = []
    if payloads_raw and isinstance(payloads_raw, list):
        for p in payloads_raw:
            config["payloads"].append({
                "name": p.get("name", ""),
                "size": str(p.get("size", "")),
                "created_by": p.get("created_by", ""),
                "category": "",
            })

    print("  Collecting secrets...")
    secrets_raw = collect_simple_list(oid, "secret")
    config["secrets"] = []
    if secrets_raw:
        if isinstance(secrets_raw, dict):
            config["secrets"] = sorted(secrets_raw.keys())
        elif isinstance(secrets_raw, list):
            config["secrets"] = sorted(str(s) for s in secrets_raw)

    print("  Collecting SOPs...")
    sops_raw = collect_simple_list(oid, "sop")
    config["sops"] = []
    if sops_raw and isinstance(sops_raw, dict):
        for key, sop_data in sops_raw.items():
            data = sop_data.get("data", {})
            config["sops"].append({
                "key": key,
                "enabled": sop_data.get("usr_mtd", {}).get("enabled", True),
                "description": data.get("description", ""),
                "content": data.get("text", ""),
            })

    print("  Collecting tags...")
    tags_raw = collect_simple_list(oid, "tag")
    config["tags"] = sorted(tags_raw) if isinstance(tags_raw, list) else []

    print("  Collecting installation keys...")
    ikeys_raw = collect_simple_list(oid, "installation-key")
    config["installation_keys"] = {"user_created": []}
    # installation-key list returns a dict keyed by IID, not a list
    if ikeys_raw:
        if isinstance(ikeys_raw, dict):
            ikeys_items = list(ikeys_raw.values())
        elif isinstance(ikeys_raw, list):
            ikeys_items = ikeys_raw
        else:
            ikeys_items = []
        for k in ikeys_items:
            if not isinstance(k, dict):
                continue
            tags = k.get("tags", "")
            # tags may be a comma-separated string or a list
            if isinstance(tags, str):
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            else:
                tag_list = tags if isinstance(tags, list) else []
            if "lc:system" not in tag_list:
                config["installation_keys"]["user_created"].append({
                    "iid": k.get("iid", ""),
                    "description": k.get("desc", ""),
                    "tags": tag_list,
                })

    print("  Collecting API keys...")
    apikeys_raw = collect_simple_list(oid, "api-key")
    config["api_keys"] = {"agent_keys": []}
    if apikeys_raw and isinstance(apikeys_raw, list):
        for k in apikeys_raw:
            name = k.get("name", "")
            if not name.startswith("_"):
                config["api_keys"]["agent_keys"].append({
                    "name": name,
                    "permissions": ", ".join(sorted(k.get("priv", []))),
                })

    # Managed packs (top-level alias for renderer capabilities)
    config["managed_packs"] = rules_data["managed_packs"]
    config["fp_rules"] = rules_data["fp_rules"]

    # Services not registered
    config["services_not_registered"] = []

    # Known issues (auto-detected)
    config["known_issues"] = _detect_known_issues(config)

    # Repo URL
    if args.repo_url:
        config["repo_url"] = args.repo_url

    # Write output
    with open(args.output, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"\nExport complete: {args.output}")
    print(f"  Sensors: {len(config['sensors']['edr'])} EDR, {len(config['sensors']['cloud'])} cloud, {len(config['sensors']['extensions'])} extensions")
    total_rules = sum(len(v) for v in config['rules']['categories'].values())
    print(f"  Rules: {total_rules} across {len(config['rules']['categories'])} categories")
    print(f"  Agents: {sum(len(t['agents']) for t in config['agents']['teams'].values()) + len(config['agents']['standalone'])}")
    print(f"  Extensions: {len(config['extensions'])}")


def _detect_known_issues(config: dict) -> list:
    """Auto-detect known issues from the config."""
    issues = []

    for s in config.get("sensors", {}).get("edr", []):
        if s.get("is_isolated"):
            issues.append(f"EDR sensor {s['hostname_short']} is network-isolated — verify if isolation is still needed")
        if not s.get("is_online"):
            issues.append(f"EDR sensor {s['hostname_short']} is offline")

    for a in config.get("adapters", {}).get("disabled", []):
        issues.append(f"{a['key']} adapter ({a['type']}) is disabled")

    total_rules = sum(len(v) for v in config.get("rules", {}).get("categories", {}).values())
    disabled = sum(1 for cats in config.get("rules", {}).get("categories", {}).values() for r in cats if not r.get("enabled"))
    if disabled > 0:
        issues.append(f"{disabled} D&R rules are deployed disabled, awaiting human review")

    if not config.get("fp_rules"):
        issues.append("No FP rules deployed yet (org may be in baselining mode)")

    return issues


if __name__ == "__main__":
    main()
