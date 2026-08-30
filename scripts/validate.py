#!/usr/bin/env python3
"""Offline validation for the lc-ai marketplace + plugins.

Runs without network access or LC credentials. Checks:
  1. marketplace.json + each plugin.json shape (jsonschema)
  2. SKILL.md frontmatter required keys, name matches directory
  3. YAML parse for every .yaml under marketplace/
  4. Path references inside SKILL.md (compliance/<x>/..., ${CLAUDE_PLUGIN_ROOT}/...) resolve
  5. bash -n on fenced ```bash blocks in SKILL.md
  6. baseline regression: skills present on master that disappear in this branch
     (without an accompanying BREAKING.md entry) cause a failure
  7. safety invariants for the disabled-by-default mailsec-triage bundle
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = ROOT / "marketplace" / "plugins"
BASELINE_REF = "master"
IGNORE_FILE = ROOT / ".validate-ignore"


def _load_ignores() -> list[str]:
    if not IGNORE_FILE.exists():
        return []
    return [
        line.strip()
        for line in IGNORE_FILE.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


IGNORES = _load_ignores()
errors: list[str] = []
warnings: list[str] = []
suppressed: list[str] = []


def err(msg: str) -> None:
    for pat in IGNORES:
        if pat in msg:
            suppressed.append(msg)
            return
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


# ---------- 1. marketplace.json + plugin.json ----------

MARKETPLACE_SCHEMA = {
    "type": "object",
    "required": ["name", "owner", "plugins"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "owner": {"type": "object", "required": ["name"]},
        "plugins": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "source", "version"],
                "properties": {
                    "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
                    "source": {"type": "string"},
                    "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+"},
                    "description": {"type": "string"},
                },
            },
        },
    },
}

PLUGIN_SCHEMA = {
    "type": "object",
    "required": ["name", "version"],
    "properties": {
        "name": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+"},
    },
}


def validate_manifests() -> list[Path]:
    """Returns list of plugin directories declared by marketplace.json."""
    plugin_dirs: list[Path] = []

    if not MARKETPLACE.exists():
        err(f"missing {MARKETPLACE.relative_to(ROOT)}")
        return plugin_dirs

    try:
        market = json.loads(MARKETPLACE.read_text())
    except json.JSONDecodeError as e:
        err(f"marketplace.json: invalid JSON — {e}")
        return plugin_dirs

    for v in Draft202012Validator(MARKETPLACE_SCHEMA).iter_errors(market):
        err(f"marketplace.json: {'/'.join(str(p) for p in v.absolute_path)}: {v.message}")

    seen_names = set()
    for entry in market.get("plugins", []):
        name = entry.get("name", "?")
        if name in seen_names:
            err(f"marketplace.json: duplicate plugin name '{name}'")
        seen_names.add(name)

        src = entry.get("source", "")
        plugin_dir = (ROOT / src).resolve() if src.startswith("./") else None
        if plugin_dir is None or not plugin_dir.exists():
            err(f"marketplace.json: plugin '{name}' source path does not exist: {src}")
            continue
        plugin_dirs.append(plugin_dir)

        plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"
        if not plugin_json.exists():
            err(f"plugin '{name}': missing .claude-plugin/plugin.json")
            continue
        try:
            pj = json.loads(plugin_json.read_text())
        except json.JSONDecodeError as e:
            err(f"plugin '{name}': plugin.json invalid JSON — {e}")
            continue
        for v in Draft202012Validator(PLUGIN_SCHEMA).iter_errors(pj):
            err(f"plugin '{name}': plugin.json: {v.message}")
        if pj.get("name") != name:
            err(f"plugin '{name}': plugin.json name '{pj.get('name')}' does not match marketplace entry")
        if pj.get("version") != entry.get("version"):
            warn(
                f"plugin '{name}': version mismatch — marketplace.json says "
                f"{entry.get('version')}, plugin.json says {pj.get('version')}"
            )

    return plugin_dirs


# ---------- 2. SKILL.md frontmatter ----------

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)", re.DOTALL)
SKILL_REQUIRED_KEYS = {"name", "description"}


def validate_skills(plugin_dirs: list[Path]) -> list[Path]:
    skill_files: list[Path] = []
    for pdir in plugin_dirs:
        for skill_md in (pdir / "skills").glob("*/SKILL.md"):
            skill_files.append(skill_md)
            label = skill_md.relative_to(ROOT)
            text = skill_md.read_text()
            m = FRONTMATTER_RE.match(text)
            if not m:
                err(f"{label}: missing YAML frontmatter")
                continue
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError as e:
                err(f"{label}: frontmatter YAML invalid — {e}")
                continue

            missing = SKILL_REQUIRED_KEYS - set(fm)
            if missing:
                err(f"{label}: frontmatter missing keys: {sorted(missing)}")

            expected = skill_md.parent.name
            if fm.get("name") and fm["name"] != expected:
                err(f"{label}: name '{fm['name']}' does not match directory '{expected}'")
    return skill_files


# ---------- 3. YAML parse for every .yaml ----------

def validate_yaml(plugin_dirs: list[Path]) -> None:
    for pdir in plugin_dirs:
        for y in pdir.rglob("*.yaml"):
            try:
                yaml.safe_load(y.read_text())
            except yaml.YAMLError as e:
                err(f"{y.relative_to(ROOT)}: invalid YAML — {e}")


# ---------- 4. SKILL.md path references ----------

# capture compliance/<framework>/<rest> and ${CLAUDE_PLUGIN_ROOT}/<rest>
PATH_REFS = [
    re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)"),
    re.compile(r"(?<![A-Za-z0-9_./-])compliance/([a-z0-9-]+/[A-Za-z0-9_./-]+)"),
]


def validate_path_refs(skill_files: list[Path]) -> None:
    for skill_md in skill_files:
        plugin_root = skill_md.parents[2]  # plugins/<plugin>/skills/<skill>/SKILL.md → plugins/<plugin>
        text = skill_md.read_text()
        # strip fenced code blocks first so example paths don't false-positive
        # but we still want to check real references — leave them in
        seen = set()
        for rx in PATH_REFS:
            for m in rx.finditer(text):
                ref = m.group(1).rstrip("/.,)`'\"")
                if ref in seen:
                    continue
                seen.add(ref)
                # for the second regex, rebuild full relative
                full_ref = ref if rx is PATH_REFS[0] else f"compliance/{ref}"
                # ignore wildcards / placeholders
                if any(t in full_ref for t in ("<", ">", "*", "...")):
                    continue
                # only check refs that look like concrete files (have an extension or known dir)
                target = plugin_root / full_ref
                if not target.exists():
                    # try with parent only — many references are to dirs
                    if not target.parent.exists():
                        err(f"{skill_md.relative_to(ROOT)}: dangling path ref → {full_ref}")


# ---------- 5. bash -n on fenced bash blocks ----------

BASH_BLOCK_RE = re.compile(r"```bash\n(.*?)```", re.DOTALL)


PLACEHOLDER_RE = re.compile(r"<[A-Za-z_][A-Za-z0-9_ -]*>")


def validate_bash(skill_files: list[Path]) -> None:
    for skill_md in skill_files:
        for i, m in enumerate(BASH_BLOCK_RE.finditer(skill_md.read_text())):
            snippet = m.group(1)
            # CLI examples use <placeholder> tokens that aren't valid bash —
            # substitute them with a literal so bash -n only flags real syntax issues.
            sanitized = PLACEHOLDER_RE.sub("PLACEHOLDER", snippet)
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
                f.write(sanitized)
                tmp = f.name
            r = subprocess.run(["bash", "-n", tmp], capture_output=True, text=True)
            if r.returncode != 0:
                err(f"{skill_md.relative_to(ROOT)}: bash block #{i+1} parse error — {r.stderr.strip()}")


# ---------- 6. baseline regression: deleted skills vs master ----------

def _resolve_baseline_ref() -> str | None:
    """Try BASELINE_REF, fall back to origin/<ref>. Returns None if neither exists."""
    for candidate in (BASELINE_REF, f"origin/{BASELINE_REF}"):
        r = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", candidate],
            capture_output=True, text=True, cwd=ROOT,
        )
        if r.returncode == 0:
            return candidate
    return None


def list_skills_at(ref: str) -> set[str]:
    """Returns 'plugin/skill' set from ref:marketplace/plugins/*/skills/*/SKILL.md."""
    r = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref],
        capture_output=True, text=True, cwd=ROOT,
    )
    if r.returncode != 0:
        warn(f"baseline: could not read git ref {ref}")
        return set()
    out = set()
    for line in r.stdout.splitlines():
        m = re.match(r"marketplace/plugins/([^/]+)/skills/([^/]+)/SKILL\.md$", line)
        if m:
            out.add(f"{m.group(1)}/{m.group(2)}")
    return out


def validate_baseline() -> None:
    ref = _resolve_baseline_ref()
    if ref is None:
        warn(f"baseline: ref '{BASELINE_REF}' not found locally — skipping regression check")
        return
    base = list_skills_at(ref)
    head = list_skills_at("HEAD")
    if not base:
        return
    deleted = base - head
    # a skill that moved from plugin-A to plugin-B (same skill name) is fine
    head_names = {s.split("/", 1)[1] for s in head}
    truly_gone = {s for s in deleted if s.split("/", 1)[1] not in head_names}
    moved = deleted - truly_gone

    breaking_md = ROOT / "BREAKING.md"
    breaking_text = breaking_md.read_text() if breaking_md.exists() else ""

    for s in sorted(truly_gone):
        if s in breaking_text:
            continue
        err(f"baseline regression: skill '{s}' present on {BASELINE_REF} but missing from HEAD "
            f"and not documented in BREAKING.md")
    for s in sorted(moved):
        warn(f"baseline: skill '{s}' moved between plugins — verify intentional")


# ---------- 7. mailsec-triage bundle safety ----------

def validate_mailsec_triage() -> None:
    """Load the real bundle and pin the controls that make it safe to install.

    This intentionally inspects the checked-in YAML instead of reconstructing the
    records in a test. A prior extension implementation tested copies of its install
    logic and therefore could stay green while the production records drifted.
    """
    root = ROOT / "ai-agents" / "triage" / "mailsec-triage"
    manifest_path = root / "mailsec-triage.yaml"
    agent_path = root / "hives" / "ai_agent.yaml"
    rules_path = root / "hives" / "dr-general.yaml"

    try:
        manifest = yaml.safe_load(manifest_path.read_text())
        agent_doc = yaml.safe_load(agent_path.read_text())
        rules_doc = yaml.safe_load(rules_path.read_text())
    except (OSError, yaml.YAMLError) as e:
        err(f"mailsec-triage: cannot load bundle: {e}")
        return

    includes = set(manifest.get("include", []))
    expected_includes = {"hives/ai_agent.yaml", "hives/dr-general.yaml"}
    if includes != expected_includes:
        err("mailsec-triage: bundle must include exactly the agent and both trigger rules")

    try:
        agent = agent_doc["hives"]["ai_agent"]["mailsec-triage"]
        data = agent["data"]
    except (KeyError, TypeError) as e:
        err(f"mailsec-triage: missing agent record field: {e}")
        return

    if agent.get("usr_mtd", {}).get("enabled") is not False:
        err("mailsec-triage: agent must ship explicitly disabled")
    for field in ("anthropic_secret", "provider", "credentials", "bedrock", "vertex"):
        if field in data:
            err(f"mailsec-triage: checked-in agent must not select or embed AI credential field {field!r}")
    for field, expected in (("max_turns", 20), ("max_budget_usd", 0.5), ("ttl_seconds", 180)):
        if data.get(field) != expected:
            err(f"mailsec-triage: {field} must be {expected!r}, got {data.get(field)!r}")

    prompt = data.get("prompt", "")
    for required in ("--oid <oid>", "--output yaml", "mailsec report resolve"):
        if required not in prompt:
            err(f"mailsec-triage: prompt is missing required CLI contract {required!r}")
    if "mailsec message eml" in prompt:
        err("mailsec-triage: default playbook must not download raw EML")

    try:
        rules = rules_doc["hives"]["dr-general"]
    except (KeyError, TypeError) as e:
        err(f"mailsec-triage: missing trigger rules: {e}")
        return
    expected_rules = {"mailsec-triage-suspicious", "mailsec-triage-user-report"}
    if set(rules) != expected_rules:
        err(f"mailsec-triage: trigger set must be {sorted(expected_rules)!r}")
        return

    events = set()
    suppressions = []
    for name, rule in rules.items():
        if rule.get("usr_mtd", {}).get("enabled") is not False:
            err(f"mailsec-triage: trigger {name!r} must ship explicitly disabled")
        try:
            event = rule["data"]["detect"]["event"]
            response = rule["data"]["respond"][0]
            suppression = response["suppression"]
        except (KeyError, IndexError, TypeError) as e:
            err(f"mailsec-triage: trigger {name!r} is incomplete: {e}")
            continue
        events.add(event)
        if response.get("definition") != "hive://ai_agent/mailsec-triage":
            err(f"mailsec-triage: trigger {name!r} does not name the bundled agent")
        suppressions.append(suppression)

    if events != {"EMAIL_MESSAGE", "EMAIL_USER_REPORT"}:
        err("mailsec-triage: triggers must cover suspicious messages and every user report")
    if len(suppressions) == 2:
        if suppressions[0] != suppressions[1]:
            err("mailsec-triage: both triggers must share one suppression descriptor")
        expected = {
            "is_global": True,
            "keys": ["mailsec-triage-volume"],
            "max_count": 60,
            "period": "1m",
        }
        if suppressions[0] != expected:
            err(f"mailsec-triage: suppression must be the bounded org-global contract {expected!r}")


# ---------- main ----------

def main() -> int:
    plugin_dirs = validate_manifests()
    skill_files = validate_skills(plugin_dirs)
    validate_yaml(plugin_dirs)
    validate_path_refs(skill_files)
    validate_bash(skill_files)
    validate_baseline()
    validate_mailsec_triage()

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print()
    print(f"{len(plugin_dirs)} plugins, {len(skill_files)} skills checked — "
          f"{len(errors)} errors, {len(warnings)} warnings, "
          f"{len(suppressed)} suppressed via .validate-ignore")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
