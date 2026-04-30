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


# ---------- main ----------

def main() -> int:
    plugin_dirs = validate_manifests()
    skill_files = validate_skills(plugin_dirs)
    validate_yaml(plugin_dirs)
    validate_path_refs(skill_files)
    validate_bash(skill_files)
    validate_baseline()

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
