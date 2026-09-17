from types import SimpleNamespace

import pytest

from lc_eval.execution import docker
from lc_eval.models import AgentConfig


def test_immutable_base_uses_repository_digest(monkeypatch):
    monkeypatch.setattr(
        docker,
        "run",
        lambda argv: '["python@sha256:abc", "mirror.example/python@sha256:def"]',
    )
    assert docker.immutable_image_reference("python:3.11-slim") == "python@sha256:abc"


def test_volta_codex_resolution_finds_native_platform_binary(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "volta-shim"
    shim.write_text("shim")
    executable = bin_dir / "codex"
    executable.symlink_to(shim)
    volta = bin_dir / "volta"
    volta.write_text("volta")

    package = tmp_path / "packages" / "@openai" / "codex"
    launcher = package / "bin" / "codex"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("node launcher")
    native = package / "lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64/bin/codex"
    native.parent.mkdir(parents=True)
    native.write_bytes(b"\x7fELFnative")
    monkeypatch.setattr(
        docker.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=str(launcher) + "\n"),
    )

    assert docker.resolve_codex_native(executable) == native.resolve()


def test_trial_requires_one_explicit_harness_when_run_has_multiple(tmp_path):
    agents = [
        AgentConfig(adapter="claude_code"),
        AgentConfig(adapter="codex"),
    ]
    environment = docker.DockerEnvironment(
        SimpleNamespace(agents=agents), "trial", tmp_path, SimpleNamespace()
    )
    with pytest.raises(ValueError, match="select exactly one"):
        environment._selected_agent(None)
    assert environment._selected_agent("codex") is agents[1]


def test_docker_cleanup_is_idempotent_when_exact_object_is_already_absent(tmp_path, monkeypatch):
    class Journal:
        cleaned_intents = []
        failed_intents = []

        def cleaned(self, intent):
            self.cleaned_intents.append(intent)

        def cleanup_failed(self, intent, error):
            self.failed_intents.append((intent, error))

    journal = Journal()
    environment = docker.DockerEnvironment(SimpleNamespace(), "trial", tmp_path, journal)
    environment.handles = [("docker_container", "exact-container", "intent")]
    monkeypatch.setattr(docker, "run", lambda argv: (_ for _ in ()).throw(RuntimeError("missing")))
    monkeypatch.setattr(
        docker.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )

    environment.cleanup()
    assert journal.cleaned_intents == ["intent"]
    assert journal.failed_intents == []


def test_stop_candidate_rejects_a_container_that_remains_running(tmp_path, monkeypatch):
    environment = docker.DockerEnvironment(SimpleNamespace(), "trial", tmp_path, SimpleNamespace())

    def fake_run(argv, **kwargs):
        if argv[1:3] == ["container", "inspect"]:
            return SimpleNamespace(returncode=0, stdout="true\n", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="kill failed")

    monkeypatch.setattr(docker.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="still running"):
        environment.stop_candidate()
