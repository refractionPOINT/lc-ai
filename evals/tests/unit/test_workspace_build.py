from pathlib import Path

import pytest

from lc_eval.execution.workspace_build import LC_AI_PATHS, SDK_PINS, _commit, _dockerfile, _image_digest


def test_workspace_image_uses_pinned_base_and_sdk_versions():
    base = "sha256:" + "a" * 64
    rendered = _dockerfile(base, include_launcher=True)

    assert f"FROM {base}" in rendered
    assert "COPY workspace_runner.py /opt/lc-eval/workspace_runner.py" in rendered
    for package, version in SDK_PINS.items():
        assert f"{package}=={version}" in rendered
    assert "COPY session-runner /usr/local/bin/session-runner" in rendered
    assert "COPY ai-sessions/scripts/bridge /opt/bridge" in rendered


def test_lc_ai_archive_allowlist_excludes_private_eval_material():
    assert set(LC_AI_PATHS) == {
        "marketplace/plugins/lc-essentials",
        "marketplace/plugins/lc-advanced-skills",
        "marketplace/plugins/lc-fundamentals",
        "marketplace/plugins/lc-compliance",
        "ai-agents",
        "ai-teams",
    }
    assert all("eval" not in Path(path).parts for path in LC_AI_PATHS)
    rendered = _dockerfile("sha256:" + "b" * 64, include_launcher=False)
    assert "evals" not in rendered
    assert "private" not in rendered
    assert "google-cloud-cli" not in rendered
    assert "awscli" not in rendered
    assert "azure-cli" not in rendered
    assert "LC_API_KEY" not in rendered
    assert "ANTHROPIC_API_KEY" not in rendered


@pytest.mark.parametrize("value", ["", "a" * 39, "A" * 40, "g" * 40, "main", "a" * 41])
def test_commit_requires_bounded_full_hash(value):
    with pytest.raises(ValueError, match="full 40-character"):
        _commit(value, "source_commit")


@pytest.mark.parametrize("value", ["", "sha256:", "a" * 64, "sha256:" + "a" * 63, "latest"])
def test_candidate_image_requires_digest(value):
    with pytest.raises(ValueError, match="pinned sha256"):
        _image_digest(value)
