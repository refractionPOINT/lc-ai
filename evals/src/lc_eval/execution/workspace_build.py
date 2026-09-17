"""Build the reduced, reproducible AI Sessions image used by workspace evals.

This is deliberately separate from the production session-runner image.  It
contains the real native coordinator and Python bridge, but inherits the
already-pinned eval candidate image instead of downloading the production
image's unrelated cloud and analysis CLIs.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

from ..config import PROJECT, atomic_json, sha256
from .docker import _build_key, build_image, extract_archive, image_id, run
from .workspace_policy import apply_policy_overlay
from ..context_profiles import fingerprint_plugin_skills

SDK_PINS = {
    "claude-agent-sdk": "0.1.63",
    "openai": "2.36.0",
    "google-genai": "2.2.0",
    "mcp": "1.28.1",
    "aiohttp": "3.13.3",
}
LC_AI_PATHS = (
    "marketplace/plugins/lc-essentials",
    "marketplace/plugins/lc-advanced-skills",
    "marketplace/plugins/lc-fundamentals",
    "marketplace/plugins/lc-compliance",
    "ai-agents",
    "ai-teams",
)


def _commit(value: str, name: str) -> str:
    """Require a full Git object id; tags and abbreviated hashes are not pins."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError(f"{name} must be a full 40-character lowercase Git commit hash")
    return value


def _image_digest(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise ValueError("candidate_image_id must be a pinned sha256 image id")
    return value


def _git_archive(repo: Path, commit: str, destination: Path, paths: tuple[str, ...] = ()) -> str:
    repo = Path(repo).resolve()
    if not repo.is_dir():
        raise ValueError(f"source repository does not exist: {repo}")
    kind = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-t", commit],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if kind.returncode or kind.stdout.strip() != "commit":
        raise ValueError(f"pinned object is not a commit in {repo.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    argv = ["git", "-C", str(repo), "archive", "--format=tar", commit]
    argv.extend(paths)
    with temporary.open("wb") as output:
        result = subprocess.run(argv, stdout=output, stderr=subprocess.PIPE, timeout=120)
    if result.returncode:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"git archive failed for {repo.name} at {commit}")
    os.replace(temporary, destination)
    return sha256(destination)


def _extract(archive: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with tarfile.open(archive) as stream:
        extract_archive(stream, destination)


def _runner_binary(source: Path, destination: Path, source_commit: str) -> str:
    env = os.environ.copy()
    env.update({"CGO_ENABLED": "0", "GOOS": "linux"})
    argv = [
        "go", "build", "-mod=readonly", "-trimpath",
        "-ldflags=-w -s "
        f"-X github.com/refractionPOINT/ai-sessions/internal/runner.GitTag=eval "
        f"-X github.com/refractionPOINT/ai-sessions/internal/runner.GitCommit={source_commit}",
        "-o", str(destination), "./cmd/session-runner",
    ]
    result = subprocess.run(argv, cwd=source, env=env, capture_output=True, text=True, timeout=900)
    if result.returncode:
        # Avoid including command environments or credentials in errors/manifests.
        detail = result.stderr.strip().splitlines()[-1:] or ["unknown Go compiler error"]
        raise RuntimeError(f"native session-runner build failed: {detail[0][:500]}")
    destination.chmod(0o755)
    return sha256(destination)


def _dockerfile(base: str, include_launcher: bool) -> str:
    packages = " ".join(f"{name}=={version}" for name, version in SDK_PINS.items())
    launcher = "COPY workspace_runner.py /opt/lc-eval/workspace_runner.py\n" if include_launcher else ""
    return f"""# Reduced eval dependency image: native AI Sessions runner + bridge, not the cloud-tool production image.
FROM {base}
USER root
RUN python3 -m pip install --no-cache-dir {packages}
COPY session-runner /usr/local/bin/session-runner
COPY ai-sessions/scripts/sdk_bridge.py /opt/sdk_bridge.py
COPY ai-sessions/scripts/bridge /opt/bridge
COPY ai-sessions/scripts/run_with_limits.sh /opt/run_with_limits.sh
COPY ai-sessions/runtime-plugins/lc-ai-terminal-cards /opt/lc-ai-terminal-cards
COPY ai-sessions/runtime-plugins/lc-agent-workspace /opt/lc-agent-workspace
COPY lc-ai/marketplace/plugins/lc-essentials /opt/lc-essentials
COPY lc-ai/marketplace/plugins/lc-advanced-skills /opt/lc-advanced-skills
COPY lc-ai/marketplace/plugins/lc-fundamentals /opt/lc-fundamentals
COPY lc-ai/marketplace/plugins/lc-compliance /opt/lc-compliance
COPY lc-ai/ai-agents /opt/lc-eval/lc-ai/ai-agents
COPY lc-ai/ai-teams /opt/lc-eval/lc-ai/ai-teams
COPY documentation /opt/lc-eval/documentation
{launcher}RUN chmod 755 /usr/local/bin/session-runner /opt/run_with_limits.sh && \\
    mkdir -p /work && ln -s /work /workspace && \\
    chown -R 1000:1000 /work
ENV SESSION_RUNNER=/usr/local/bin/session-runner
ENV PYTHONPATH=/opt
ENV PATH=/opt/lc-agent-workspace/bin:/opt/lc-ai-terminal-cards/bin:$PATH
WORKDIR /workspace
USER 1000:1000
CMD ["sleep", "infinity"]
"""


def build_workspace_image(config, source_path: Path, source_commit: str, lc_ai_commit: str) -> dict:
    """Build a pinned local image containing the genuine AI Sessions runner."""
    source_commit = _commit(source_commit, "source_commit")
    lc_ai_commit = _commit(lc_ai_commit, "lc_ai_commit")
    docs_commit = _commit(config.sources.docs.commit, "docs commit")
    base = _image_digest(config.sources.candidate_image_id)

    root = Path(config.run_data_dir) / "build" / "workspace" / source_commit[:12]
    root.mkdir(parents=True, exist_ok=True)
    archives = {
        "ai_sessions": root / "ai-sessions.tar",
        "lc_ai": root / "lc-ai.tar",
        "documentation": root / "documentation.tar",
    }
    digests = {
        "ai_sessions": _git_archive(Path(source_path), source_commit, archives["ai_sessions"]),
        "lc_ai": _git_archive(PROJECT.parent, lc_ai_commit, archives["lc_ai"], LC_AI_PATHS),
        "documentation": _git_archive(config.sources.docs.path, docs_commit, archives["documentation"]),
    }

    contexts = {name: root / name.replace("_", "-") for name in archives}
    for name, archive in archives.items():
        _extract(archive, contexts[name])
    skill_corpus = fingerprint_plugin_skills(contexts["lc_ai"])
    policy_overlay = apply_policy_overlay(contexts["ai_sessions"] / "scripts/bridge/claude_native.py")
    binary = root / "session-runner"
    binary_digest = _runner_binary(contexts["ai_sessions"], binary, source_commit)

    launcher_source = PROJECT / "src/lc_eval/execution/workspace_runner.py"
    include_launcher = launcher_source.is_file()
    if include_launcher:
        shutil.copyfile(launcher_source, root / "workspace_runner.py")

    dockerfile = root / "Dockerfile"
    # BuildKit treats a bare sha256 image ID in FROM as a registry name.
    # Resolve a dedicated content-named local tag and verify it before and after build.
    base_tag = "lc-eval-runner-base:" + base.removeprefix("sha256:")
    run(["docker", "tag", base, base_tag])
    if image_id(base_tag) != base:
        raise RuntimeError("runner base image tag does not match pinned image id")
    dockerfile.write_text(_dockerfile(base_tag, include_launcher))
    key_parts = [base, source_commit, lc_ai_commit, docs_commit, binary_digest, *digests.values(), dockerfile.read_text()]
    key_parts.extend(policy_overlay.values())
    if include_launcher:
        key_parts.append(sha256(root / "workspace_runner.py"))
    build_key = _build_key(*key_parts)
    tag = f"lc-eval-workspace:{source_commit[:12]}-{lc_ai_commit[:12]}-{build_key[:12]}"
    build_image(dockerfile, tag, root, build_key)
    if image_id(base_tag) != base:
        raise RuntimeError("runner base image tag changed during build")
    built_id = image_id(tag)
    result = {
        "image_id": built_id,
        "image_tag": tag,
        "base_image_id": base,
        "source_commits": {
            "ai_sessions": source_commit,
            "lc_ai": lc_ai_commit,
            "documentation": docs_commit,
        },
        "source_archive_sha256": digests,
        "sdk_pins": dict(SDK_PINS),
        "go_binary_sha256": binary_digest,
        "build_key": build_key,
        "policy_overlay": policy_overlay,
        "skill_corpus": skill_corpus,
    }
    atomic_json(root / "manifest.json", result)
    return result
