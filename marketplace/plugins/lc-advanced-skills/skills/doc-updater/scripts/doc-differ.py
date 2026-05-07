#!/usr/bin/env python3
"""
LimaCharlie Organization Config Differ

Compares two config.yaml files (previous vs current) and produces a
structured diff showing added, removed, and modified items per category.

Usage:
    python3 doc-differ.py --old previous-config.yaml --new current-config.yaml --output diff.yaml
    python3 doc-differ.py --new current-config.yaml --output diff.yaml   # first run, no previous

Output is a structured YAML file consumed by the AI agent for contextual analysis.

Requires: pip install pyyaml
"""

import argparse
import sys

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Diff helpers
# ---------------------------------------------------------------------------
def diff_lists(old_items: list, new_items: list, key_field: str, compare_fields: list[str] | None = None) -> dict:
    """Compare two lists of dicts by a key field.

    Returns:
        {
            "added": [items in new but not old],
            "removed": [items in old but not new],
            "modified": [{"item": item, "changes": {field: {"old": v, "new": v}}}],
            "unchanged_count": int,
        }
    """
    old_map = {item.get(key_field): item for item in old_items}
    new_map = {item.get(key_field): item for item in new_items}

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    added = [new_map[k] for k in sorted(new_keys - old_keys)]
    removed = [old_map[k] for k in sorted(old_keys - new_keys)]

    modified = []
    unchanged = 0
    for k in sorted(old_keys & new_keys):
        fields_to_check = compare_fields or [f for f in set(list(old_map[k].keys()) + list(new_map[k].keys())) if f != key_field]
        changes = {}
        for field in fields_to_check:
            old_val = old_map[k].get(field)
            new_val = new_map[k].get(field)
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
        if changes:
            modified.append({"item": new_map[k], "key": k, "changes": changes})
        else:
            unchanged += 1

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged_count": unchanged,
    }


def diff_simple_lists(old_items: list, new_items: list) -> dict:
    """Compare two simple lists (strings)."""
    old_set = set(str(x) for x in old_items)
    new_set = set(str(x) for x in new_items)

    return {
        "added": sorted(new_set - old_set),
        "removed": sorted(old_set - new_set),
    }


# ---------------------------------------------------------------------------
# Category diffing
# ---------------------------------------------------------------------------
def diff_sensors(old_config: dict, new_config: dict) -> dict:
    old_sensors = old_config.get("sensors", {})
    new_sensors = new_config.get("sensors", {})

    return {
        "edr": diff_lists(
            old_sensors.get("edr", []),
            new_sensors.get("edr", []),
            key_field="sid",
            compare_fields=["is_online", "is_isolated", "version", "hostname_short"],
        ),
        "cloud": diff_lists(
            old_sensors.get("cloud", []),
            new_sensors.get("cloud", []),
            key_field="sid",
            compare_fields=["is_online", "hostname"],
        ),
        "extensions": diff_lists(
            old_sensors.get("extensions", []),
            new_sensors.get("extensions", []),
            key_field="sid",
            compare_fields=["is_online", "hostname"],
        ),
    }


def diff_rules(old_config: dict, new_config: dict) -> dict:
    old_cats = old_config.get("rules", {}).get("categories", {})
    new_cats = new_config.get("rules", {}).get("categories", {})

    all_cat_keys = sorted(set(list(old_cats.keys()) + list(new_cats.keys())))
    result = {}

    for cat_key in all_cat_keys:
        old_rules = old_cats.get(cat_key, [])
        new_rules = new_cats.get(cat_key, [])
        result[cat_key] = diff_lists(
            old_rules, new_rules,
            key_field="name",
            compare_fields=["enabled", "response", "event"],
        )

    # Also diff FP rules
    old_fp = old_config.get("rules", {}).get("fp_rules", old_config.get("fp_rules", []))
    new_fp = new_config.get("rules", {}).get("fp_rules", new_config.get("fp_rules", []))
    result["fp_rules"] = diff_lists(old_fp, new_fp, key_field="name")

    return result


def diff_agents(old_config: dict, new_config: dict) -> dict:
    old_agents = old_config.get("agents", {})
    new_agents = new_config.get("agents", {})

    # Flatten all agents from teams + standalone for comparison
    def flatten_agents(agents_data):
        flat = []
        for team_key, team in agents_data.get("teams", {}).items():
            for agent in team.get("agents", []):
                flat.append({**agent, "_team": team_key})
        for agent in agents_data.get("standalone", []):
            flat.append({**agent, "_team": "standalone"})
        return flat

    old_flat = flatten_agents(old_agents)
    new_flat = flatten_agents(new_agents)

    return diff_lists(
        old_flat, new_flat,
        key_field="key",
        compare_fields=["model", "budget", "ttl", "schedule", "_team", "trigger_rule"],
    )


def diff_extensions(old_config: dict, new_config: dict) -> dict:
    return diff_lists(
        old_config.get("extensions", []),
        new_config.get("extensions", []),
        key_field="name",
    )


def diff_adapters(old_config: dict, new_config: dict) -> dict:
    old_adapters = old_config.get("adapters", {})
    new_adapters = new_config.get("adapters", {})

    # Combine active + disabled into one list with an "enabled" flag
    def flatten_adapters(adapters_data):
        flat = []
        for a in adapters_data.get("active", []):
            flat.append({**a, "_enabled": True})
        for a in adapters_data.get("disabled", []):
            flat.append({**a, "_enabled": False})
        return flat

    return diff_lists(
        flatten_adapters(old_adapters),
        flatten_adapters(new_adapters),
        key_field="key",
        compare_fields=["_enabled", "type", "platform"],
    )


def diff_outputs(old_config: dict, new_config: dict) -> dict:
    return diff_lists(
        old_config.get("outputs", []),
        new_config.get("outputs", []),
        key_field="name",
    )


def diff_lookups(old_config: dict, new_config: dict) -> dict:
    return diff_lists(
        old_config.get("lookups", []),
        new_config.get("lookups", []),
        key_field="name",
    )


def diff_secrets(old_config: dict, new_config: dict) -> dict:
    return diff_simple_lists(
        old_config.get("secrets", []),
        new_config.get("secrets", []),
    )


def diff_sops(old_config: dict, new_config: dict) -> dict:
    return diff_lists(
        old_config.get("sops", []),
        new_config.get("sops", []),
        key_field="key",
        compare_fields=["enabled", "description", "content"],
    )


def diff_tags(old_config: dict, new_config: dict) -> dict:
    return diff_simple_lists(
        old_config.get("tags", []),
        new_config.get("tags", []),
    )


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------
def count_changes(diff_result: dict) -> int:
    """Count total changes in a diff result (handles nested dicts)."""
    total = 0
    for key, value in diff_result.items():
        if isinstance(value, dict):
            total += len(value.get("added", []))
            total += len(value.get("removed", []))
            total += len(value.get("modified", []))
        elif isinstance(value, list):
            total += len(value)
    return total


def build_summary(diff: dict) -> dict:
    """Build a human-readable summary of the diff."""
    categories_changed = []
    total = 0

    for category, changes in diff.items():
        if category in ("summary", "first_run"):
            continue
        if not isinstance(changes, dict):
            continue
        change_count = count_changes(changes)
        if change_count > 0:
            categories_changed.append(category)
            total += change_count

    return {
        "total_changes": total,
        "categories_changed": categories_changed,
        "has_changes": total > 0,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Diff two LimaCharlie org config snapshots")
    parser.add_argument("--old", default="", help="Previous config.yaml (empty for first run)")
    parser.add_argument("--new", required=True, help="Current config.yaml")
    parser.add_argument("--output", required=True, help="Output diff YAML file")
    args = parser.parse_args()

    # Load new config
    with open(args.new, "r") as f:
        new_config = yaml.safe_load(f) or {}

    # Load old config (empty dict if first run)
    if args.old:
        try:
            with open(args.old, "r") as f:
                old_config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print("  Previous config not found — treating as first run", file=sys.stderr)
            old_config = {}
    else:
        old_config = {}

    is_first_run = not old_config

    print("Computing diff...")

    diff = {
        "first_run": is_first_run,
        "sensors": diff_sensors(old_config, new_config),
        "rules": diff_rules(old_config, new_config),
        "agents": diff_agents(old_config, new_config),
        "extensions": diff_extensions(old_config, new_config),
        "adapters": diff_adapters(old_config, new_config),
        "outputs": diff_outputs(old_config, new_config),
        "lookups": diff_lookups(old_config, new_config),
        "secrets": diff_secrets(old_config, new_config),
        "sops": diff_sops(old_config, new_config),
        "tags": diff_tags(old_config, new_config),
    }

    diff["summary"] = build_summary(diff)

    # Write output
    with open(args.output, "w") as f:
        yaml.dump(diff, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    summary = diff["summary"]
    if is_first_run:
        print(f"\nFirst run — all items treated as new.")
    elif summary["has_changes"]:
        print(f"\n{summary['total_changes']} change(s) detected in: {', '.join(summary['categories_changed'])}")
    else:
        print("\nNo changes detected.")

    print(f"Diff written to: {args.output}")


if __name__ == "__main__":
    main()
