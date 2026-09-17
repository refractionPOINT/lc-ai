"""Build and describe isolated, commit-pinned native harness contexts."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any

from .config import sha256
from .models import AgentConfig, RunConfig

PLUGIN_PATHS = (
    "marketplace/plugins/lc-essentials/skills",
    "marketplace/plugins/lc-advanced-skills/skills",
    "marketplace/plugins/lc-fundamentals/skills",
    "marketplace/plugins/lc-compliance/skills",
)
SUPPORT_ALLOWLIST = {
    "lc-fundamentals": ("CONSTANTS.md",),
    "lc-compliance": ("compliance",),
}
SUPPORT_MOUNT_ROOT = "/opt/lc-eval-skill-support"


def _archive_paths() -> tuple[str, ...]:
    support = tuple(
        f"marketplace/plugins/{plugin}/{relative}"
        for plugin, relative_paths in SUPPORT_ALLOWLIST.items()
        for relative in relative_paths
    )
    return (*PLUGIN_PATHS, *support)


def prepare_context_corpus(config: RunConfig) -> dict[str, Any] | None:
    """Archive the configured Git object and normalize its native skill tree."""
    explicit = [a for a in config.agents if a.context_mode == "lc_ai"]
    if not explicit:
        return None
    pin = config.context.lc_ai
    if pin is None:
        raise ValueError("context.lc_ai source pin is required for context_mode='lc_ai'")
    commit = pin.commit
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("the lc_ai context commit must be a full lowercase Git object id")
    root = config.run_data_dir / "build" / "contexts" / commit[:12]
    archive, extracted, skills, support = (
        root / "lc-ai-skills.tar", root / "archive", root / "skills", root / "support"
    )
    root.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_suffix(".tmp")
    with temporary.open("wb") as output:
        result = subprocess.run(
            ["git", "-C", str(pin.path), "archive", "--format=tar", commit, *_archive_paths()],
            stdout=output, stderr=subprocess.PIPE, timeout=120,
        )
    if result.returncode:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("failed to archive the pinned lc-ai skill corpus")
    os.replace(temporary, archive)
    if extracted.exists():
        shutil.rmtree(extracted)
    extracted.mkdir()
    with tarfile.open(archive) as stream:
        _extract_regular(stream, extracted)
    if skills.exists():
        shutil.rmtree(skills)
    skills.mkdir()
    if support.exists():
        shutil.rmtree(support)
    support.mkdir()
    for plugin, relative_paths in SUPPORT_ALLOWLIST.items():
        plugin_support = support / plugin
        plugin_support.mkdir()
        for relative in relative_paths:
            source = extracted / "marketplace/plugins" / plugin / relative
            if not source.exists():
                raise ValueError(f"pinned plugin support asset is missing: {plugin}/{relative}")
            destination = plugin_support / relative
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
    inventory: dict[str, str] = {}
    rewrites: dict[str, Any] = {}
    for plugin_path in PLUGIN_PATHS:
        plugin = Path(plugin_path).parts[2]
        source = extracted / plugin_path
        for skill_file in sorted(source.glob("*/SKILL.md")):
            source_name = skill_file.parent.name
            name = f"{plugin}--{source_name}"
            destination = skills / name
            shutil.copytree(skill_file.parent, destination)
            skill_text = (destination / "SKILL.md").read_text()
            normalized, count = re.subn(
                r"(?m)^name:\s*[^\n]+$", f"name: {name}", skill_text, count=1,
            )
            if count != 1:
                raise ValueError(f"skill {plugin}/{source_name} has no unique frontmatter name")
            (destination / "SKILL.md").write_text(normalized)
            transformed = _rewrite_standalone_references(destination, plugin, source_name, name)
            if transformed:
                rewrites[name] = {"count": len(transformed), "files": transformed}
            inventory[name] = plugin
    if not inventory:
        raise ValueError("pinned lc-ai archive contains no native skills")
    corpus_digest = _tree_digest(skills)
    canary_name = sorted(inventory)[0]
    canary_plugin, canary_source_name = canary_name.split("--", 1)
    source_canary = extracted / f"marketplace/plugins/{canary_plugin}/skills/{canary_source_name}/SKILL.md"
    manifest = {
        "profile": "lc_ai",
        "source_commit": commit,
        "source_worktree_dirty_at_pin": pin.dirty,
        "source_archive_sha256": sha256(archive),
        "source_skill_corpus_sha256": _paths_digest(
            extracted, tuple(Path(path) for path in PLUGIN_PATHS)
        ),
        "corpus_sha256": corpus_digest,
        "support_sha256": _tree_digest(support),
        "support_root": str(support),
        "support_mount_root": SUPPORT_MOUNT_ROOT,
        "support_allowlist": {key: list(value) for key, value in SUPPORT_ALLOWLIST.items()},
        "reference_rewrites": rewrites,
        "skill_count": len(inventory),
        "skills": inventory,
        "canary": {
            "skill": canary_name,
            "source_skill": canary_source_name,
            "plugin": canary_plugin,
            "skill_md_sha256": sha256(skills / canary_name / "SKILL.md"),
            "source_skill_md_sha256": sha256(source_canary),
        },
        "skill_root": str(skills),
    }
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def context_identity(config: RunConfig, agent: AgentConfig, corpus: dict[str, Any] | None) -> dict[str, Any]:
    mode = agent.context_mode
    if mode == "lc_ai" and corpus is None:
        raise ValueError("lc_ai context corpus has not been prepared")
    lc_ai_identity = None
    if mode == "lc_ai" and corpus:
        common_keys = ("source_commit", "source_archive_sha256", "source_skill_corpus_sha256", "skill_count", "canary")
        keys = common_keys if agent.adapter == "ai_sessions" else (
            *common_keys, "corpus_sha256", "support_sha256",
        )
        lc_ai_identity = {key: corpus[key] for key in keys}
    return {
        "mode": mode,
        "delivery": (
            "ai_sessions_plugin_autoinit"
            if agent.adapter == "ai_sessions" and mode == "lc_ai"
            else "native_user_skills"
            if mode == "lc_ai"
            else "isolated_empty_user_context"
            if mode == "bare"
            else "legacy_unspecified"
        ),
        "docs_commit": config.sources.docs.commit,
        "lc_ai": lc_ai_identity,
        "provider_builtin_skills": "possible",
    }


def audit_host_context_boundary(agent: AgentConfig, corpus: dict[str, Any] | None) -> dict[str, Any]:
    """Describe the only context inputs exposed to the fresh container home."""
    exposed = ["selected_auth_file", "minimal_onboarding_state", "pinned_docs_archive"]
    if agent.context_mode == "lc_ai" and agent.adapter != "ai_sessions":
        if corpus is None or not Path(str(corpus["skill_root"])).is_dir():
            raise ValueError("prepared lc_ai skill root is missing")
        exposed.append("pinned_lc_ai_skill_archive")
        exposed.append("pinned_lc_ai_support_allowlist")
    return {
        "fresh_home": "/auth",
        "docs_mount": "/docs",
        "exposed_inputs": exposed,
        "host_user_config": False,
        "host_memory": False,
        "host_mcp": False,
        "host_skills": False,
        "image_lc_paths_masked": agent.adapter == "ai_sessions" and agent.context_mode == "bare",
    }


def fingerprint_plugin_skills(root: Path) -> dict[str, Any]:
    """Fingerprint the exact skill content in an extracted lc-ai archive."""
    inventory: dict[str, str] = {}
    digest = hashlib.sha256()
    for plugin_path in PLUGIN_PATHS:
        plugin = Path(plugin_path).parts[2]
        for skill_file in sorted((root / plugin_path).glob("*/SKILL.md")):
            source_name = skill_file.parent.name
            name = f"{plugin}--{source_name}"
            inventory[name] = plugin
            for path in sorted(p for p in skill_file.parent.rglob("*") if p.is_file()):
                digest.update(path.relative_to(root).as_posix().encode())
                digest.update(b"\0")
                digest.update(path.read_bytes())
                digest.update(b"\0")
    if not inventory:
        raise ValueError("pinned lc-ai archive contains no native skills")
    canary_name = sorted(inventory)[0]
    canary_plugin, canary_source_name = canary_name.split("--", 1)
    canary_path = root / f"marketplace/plugins/{canary_plugin}/skills/{canary_source_name}/SKILL.md"
    return {
        "corpus_sha256": digest.hexdigest(), "skill_count": len(inventory), "skills": inventory,
        "canary": {
            "skill": canary_name, "source_skill": canary_source_name, "plugin": canary_plugin,
            "source_skill_md_sha256": sha256(canary_path),
        },
    }


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _paths_digest(root: Path, paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative_root in paths:
        for path in sorted(p for p in (root / relative_root).rglob("*") if p.is_file()):
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _rewrite_standalone_references(
    root: Path, plugin: str, source_name: str, normalized_name: str,
) -> dict[str, dict[str, str]]:
    replacements = (
        (f"${{CLAUDE_PLUGIN_ROOT}}/skills/{source_name}", f"/auth/skills/{normalized_name}"),
        (f"/opt/{plugin}/skills/{source_name}", f"/auth/skills/{normalized_name}"),
        ("${CLAUDE_PLUGIN_ROOT}", f"{SUPPORT_MOUNT_ROOT}/{plugin}"),
    )
    changed: dict[str, dict[str, str]] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        transformed = text
        for before, after in replacements:
            transformed = transformed.replace(before, after)
        if transformed != text:
            source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
            path.write_text(transformed)
            changed[path.relative_to(root).as_posix()] = {
                "source_sha256": source_sha256,
                "transformed_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
    return changed


def _extract_regular(stream: tarfile.TarFile, destination: Path) -> None:
    resolved = destination.resolve()
    for member in stream.getmembers():
        target = (destination / member.name).resolve()
        if target != resolved and resolved not in target.parents:
            raise ValueError("lc-ai archive path escapes its context root")
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
        elif member.isfile():
            target.parent.mkdir(parents=True, exist_ok=True)
            source = stream.extractfile(member)
            if source is None:
                raise ValueError("lc-ai archive contains an unreadable regular file")
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(member.mode & 0o777)
        else:
            raise ValueError("lc-ai archive contains links or device entries")
