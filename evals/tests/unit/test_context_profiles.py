from __future__ import annotations

import subprocess
from pathlib import Path


from lc_eval.adapters import ClaudeCodeAdapter, ClaudeCodeConfig
from lc_eval.context_profiles import audit_host_context_boundary, context_identity, prepare_context_corpus
from lc_eval.models import AgentConfig, ContextConfig, LCConfig, RunConfig, SourcePin, Sources


def _config(tmp_path: Path, mode: str, adapter: str = "codex") -> RunConfig:
    repo = tmp_path / "lc-ai"
    skill = repo / "marketplace/plugins/lc-essentials/skills/canary"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: canary\ndescription: pinned canary\n---\nCANARY-CONTENT\n")
    (skill / "REFERENCE.md").write_text("PINNED-SKILL-REFERENCE\n")
    for plugin, marker in (("lc-essentials", "advanced"), ("lc-fundamentals", "fundamental")):
        duplicate = repo / f"marketplace/plugins/{plugin}/skills/sensor-tasking"
        duplicate.mkdir(parents=True)
        (duplicate / "SKILL.md").write_text(
            f"---\nname: sensor-tasking\ndescription: {marker}\n---\n{marker} sensor prose line is distinct.\n"
        )
    fundamentals = repo / "marketplace/plugins/lc-fundamentals"
    (fundamentals / "CONSTANTS.md").write_text("PINNED-CONSTANTS\n")
    compliance = repo / "marketplace/plugins/lc-compliance/compliance/cis"
    compliance.mkdir(parents=True)
    (compliance / "reference.md").write_text("PINNED-COMPLIANCE\n")
    adapter_skill = repo / "marketplace/plugins/lc-fundamentals/skills/adapters"
    adapter_skill.mkdir()
    (adapter_skill / "SKILL.md").write_text(
        "---\nname: adapters\ndescription: adapter docs\n---\n"
        "Read ${CLAUDE_PLUGIN_ROOT}/CONSTANTS.md for the pinned table.\n"
    )
    for plugin in ("lc-advanced-skills", "lc-fundamentals", "lc-compliance"):
        empty = repo / f"marketplace/plugins/{plugin}/skills"
        empty.mkdir(parents=True, exist_ok=True)
        (empty / ".keep").write_text("")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=eval", "-c", "user.email=eval@example.invalid",
         "commit", "-qm", "fixture"], check=True,
    )
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    pin = SourcePin(path=repo, commit=commit)
    return RunConfig(
        run_data_dir=(tmp_path / "run").resolve(),
        sources=Sources(cli=pin, docs=pin),
        lc=LCConfig(executable=Path("/bin/true"), executable_sha256="x", version="x"),
        agents=[AgentConfig(adapter=adapter, context_mode=mode)],
        context=ContextConfig(lc_ai=pin),
    )


def test_pinned_context_archive_contains_actual_skill_content(tmp_path):
    config = _config(tmp_path, "lc_ai")
    manifest = prepare_context_corpus(config)
    assert manifest is not None
    assert manifest["skills"] == {
        "lc-essentials--canary": "lc-essentials",
        "lc-essentials--sensor-tasking": "lc-essentials",
        "lc-fundamentals--sensor-tasking": "lc-fundamentals",
        "lc-fundamentals--adapters": "lc-fundamentals",
    }
    normalized = (Path(manifest["skill_root"]) / "lc-essentials--canary/SKILL.md").read_text()
    assert "name: lc-essentials--canary" in normalized
    assert normalized.endswith("CANARY-CONTENT\n")
    assert (
        Path(manifest["skill_root"]) / "lc-essentials--canary/REFERENCE.md"
    ).read_text() == "PINNED-SKILL-REFERENCE\n"
    adapters = (Path(manifest["skill_root"]) / "lc-fundamentals--adapters/SKILL.md").read_text()
    assert "/opt/lc-eval-skill-support/lc-fundamentals/CONSTANTS.md" in adapters
    assert "CLAUDE_PLUGIN_ROOT" not in adapters
    assert (Path(manifest["support_root"]) / "lc-fundamentals/CONSTANTS.md").read_text() == "PINNED-CONSTANTS\n"
    assert (Path(manifest["support_root"]) / "lc-compliance/compliance/cis/reference.md").is_file()
    assert manifest["support_sha256"]
    assert manifest["source_skill_corpus_sha256"] != manifest["corpus_sha256"]
    assert "name: lc-essentials--sensor-tasking" in (
        Path(manifest["skill_root"]) / "lc-essentials--sensor-tasking/SKILL.md"
    ).read_text()
    assert "name: lc-fundamentals--sensor-tasking" in (
        Path(manifest["skill_root"]) / "lc-fundamentals--sensor-tasking/SKILL.md"
    ).read_text()
    identity = context_identity(config, config.agents[0], manifest)
    assert identity["lc_ai"]["corpus_sha256"] == manifest["corpus_sha256"]
    assert identity["lc_ai"]["canary"] == {
        "skill": "lc-essentials--canary",
        "source_skill": "canary",
        "plugin": "lc-essentials",
        "skill_md_sha256": manifest["canary"]["skill_md_sha256"],
        "source_skill_md_sha256": manifest["canary"]["source_skill_md_sha256"],
    }
    assert audit_host_context_boundary(config.agents[0], manifest)["host_skills"] is False


def test_pinned_archive_ignores_dirty_worktree_content(tmp_path):
    config = _config(tmp_path, "lc_ai")
    config.context.lc_ai.dirty = True
    untracked = config.context.lc_ai.path / "marketplace/plugins/lc-essentials/skills/untracked"
    untracked.mkdir()
    (untracked / "SKILL.md").write_text("UNTRACKED")
    manifest = prepare_context_corpus(config)
    assert manifest["source_worktree_dirty_at_pin"] is True
    assert "untracked" not in manifest["skills"]


def test_bare_context_builds_no_lc_ai_archive_and_discloses_codex_builtins(tmp_path):
    config = _config(tmp_path, "bare")
    assert prepare_context_corpus(config) is None
    identity = context_identity(config, config.agents[0], None)
    assert identity["lc_ai"] is None
    assert identity["provider_builtin_skills"] == "possible"


def test_provider_builtin_skills_are_disclosed_for_every_profile(tmp_path):
    config = _config(tmp_path, "lc_ai", "claude_code")
    corpus = prepare_context_corpus(config)
    assert context_identity(config, config.agents[0], corpus)["provider_builtin_skills"] == "possible"


def test_ai_sessions_bare_discloses_possible_provider_builtins(tmp_path):
    config = _config(tmp_path, "bare", "ai_sessions")
    identity = context_identity(config, config.agents[0], None)
    assert identity["lc_ai"] is None
    assert identity["provider_builtin_skills"] == "possible"


def test_claude_lc_ai_enables_native_skill_tool(tmp_path):
    adapter = ClaudeCodeAdapter(ClaudeCodeConfig(
        trial_id="t", model="m", workdir=tmp_path, executable="claude", context_mode="lc_ai",
    ))
    argv = adapter.build_argv()
    assert "Skill" in argv[argv.index("--tools") + 1].split(",")
    assert "--safe-mode" not in argv
    assert "--disable-slash-commands" not in argv
