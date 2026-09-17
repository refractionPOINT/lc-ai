import json
import asyncio
import os
from types import SimpleNamespace

import pytest

from lc_eval.fixtures.native_sensor import (
    MAX_ENROLLMENT_BYTES,
    _read_enrollment,
    _safe_status,
    _status_sid,
    _runtime_timeout_seconds,
    _sensor_image_build_key,
    _build_sensor_image,
    _default_system_keys_ready,
    DEFAULT_SYSTEM_KEY_DESCRIPTIONS,
    collect,
    NativeSensorRuntime,
)
from lc_eval.models import AgentConfig, LCConfig, RunConfig, SourcePin, Sources
from lc_eval.journal import Journal


def _run_config(tmp_path, *, timeout=600):
    pin = SourcePin(path=tmp_path, commit="a" * 40)
    return RunConfig(
        run_data_dir=tmp_path,
        sources=Sources(cli=pin, docs=pin),
        lc=LCConfig(executable=tmp_path / "limacharlie", executable_sha256="a" * 64, version="test"),
        agents=[AgentConfig(adapter="codex", timeout_seconds=timeout)],
    )


def test_status_sid_accepts_nested_real_uuid_only():
    sid = "11111111-2222-4333-8444-555555555555"
    assert _status_sid({"status": {"sensor_id": sid}}) == sid
    assert _status_sid({"sid": "not-a-uuid"}) is None


def test_enrollment_reader_rejects_symlink_and_oversize(tmp_path):
    secret = tmp_path / "secret"
    secret.write_text('{"installation_key":"must-not-read"}')
    request = tmp_path / "enrollment.json"
    request.symlink_to(secret)
    with pytest.raises(OSError):
        _read_enrollment(request)
    request.unlink()
    request.write_bytes(b"x" * (MAX_ENROLLMENT_BYTES + 1))
    with pytest.raises(ValueError, match="byte limit"):
        _read_enrollment(request)
    request.unlink()
    os.mkfifo(request)
    with pytest.raises(ValueError, match="regular file"):
        _read_enrollment(request)


def test_safe_status_replaces_symlink_without_touching_target(tmp_path):
    target = tmp_path / "target"
    target.write_text("retain")
    status = tmp_path / "enrollment-status.json"
    status.symlink_to(target)
    _safe_status(status, {"state": "registered"})
    assert target.read_text() == "retain"
    assert not status.is_symlink()
    assert json.loads(status.read_text()) == {"state": "registered"}


def test_enrollment_reader_accepts_bounded_regular_json(tmp_path):
    request = tmp_path / "enrollment.json"
    expected = {"schema_version": 1, "deployment": "native_linux_sensor_v1", "installation_key": "opaque"}
    request.write_text(json.dumps(expected))
    assert _read_enrollment(request) == expected


def test_runtime_failure_status_never_echoes_enrollment_secret(tmp_path):
    async def exercise():
        work = tmp_path / "work"
        work.mkdir()
        secret = "native-secret-that-must-not-leak"
        (work / "enrollment.json").write_text(json.dumps({"installation_key": secret}))
        runtime = NativeSensorRuntime(_run_config(tmp_path, timeout=1), None, None, "trial", "oid", tmp_path, "marker")
        await runtime._watch()
        rendered = (work / "enrollment-status.json").read_text()
        assert secret not in rendered
        assert json.loads(rendered)["error"] == "ValueError"
        private = (tmp_path / "native-runtime-error.json").read_text()
        assert secret not in private
        assert json.loads(private)["stage"] == "invalid_request"

    asyncio.run(exercise())


def test_runtime_timeout_uses_real_agent_config_not_limits(tmp_path):
    config = _run_config(tmp_path, timeout=37)
    assert not hasattr(config.limits, "timeout_seconds")
    assert _runtime_timeout_seconds(config) == 37


def test_sensor_image_build_key_covers_base_binary_and_dockerfile():
    original = _sensor_image_build_key("base-a", "binary-a", "FROM worker\nCOPY sensor /sensor\n")
    assert original != _sensor_image_build_key("base-b", "binary-a", "FROM worker\nCOPY sensor /sensor\n")
    assert original != _sensor_image_build_key("base-a", "binary-b", "FROM worker\nCOPY sensor /sensor\n")
    assert original != _sensor_image_build_key("base-a", "binary-a", "FROM other\nCOPY sensor /sensor\n")


def test_default_key_readiness_requires_all_known_system_records_and_tags():
    records = {
        f"iid-{index}": {"desc": description, "tags": f"lc:system,ext:default-{index}"}
        for index, description in enumerate(sorted(DEFAULT_SYSTEM_KEY_DESCRIPTIONS))
    }
    assert _default_system_keys_ready(records)
    incomplete = dict(records)
    incomplete.pop(next(iter(incomplete)))
    assert not _default_system_keys_ready(incomplete)
    wrong_tag = {key: dict(value) for key, value in records.items()}
    wrong_tag[next(iter(wrong_tag))]["tags"] = "lc:system"
    assert not _default_system_keys_ready(wrong_tag)
    decoy = {key: value for key, value in records.items() if value["desc"] != "ext ext-feedback webhook adapter"}
    decoy["forged"] = {"desc": "prefix ext ext-feedback webhook adapter suffix", "tags": ["lc:system", "ext:feedback"]}
    assert not _default_system_keys_ready(decoy)


def test_default_key_readiness_accepts_real_saved_string_and_structured_list_tags():
    descriptions = sorted(DEFAULT_SYSTEM_KEY_DESCRIPTIONS)
    records = {
        "feedback": {"desc": descriptions[0], "tags": "lc:system,ext:ext-feedback"},
        "reliable": {"desc": descriptions[1], "tags": " lc:system , ext:reliable-tasking "},
        "yara": {"desc": descriptions[2], "tags": ["lc:system", "ext:ext-yara"]},
    }
    assert _default_system_keys_ready(records)


def test_derived_image_uses_verified_local_base_and_secret_free_context(monkeypatch, tmp_path):
    config = _run_config(tmp_path)
    config.sources.worker_image = "lc-eval-worker:pinned"
    config.sources.worker_image_id = "sha256:" + "b" * 64
    binary = tmp_path / "downloaded-sensor"
    binary.write_bytes(b"\x7fELFbinary")
    binary_digest = "c" * 64
    built = {}

    def fake_image_id(image):
        return config.sources.worker_image_id if image == config.sources.worker_image else "sha256:" + "d" * 64

    def fake_build(dockerfile, tag, context, build_key):
        built.update(dockerfile=dockerfile.read_text(), tag=tag, files=sorted(path.name for path in context.iterdir()), build_key=build_key)

    monkeypatch.setattr("lc_eval.fixtures.native_sensor.image_id", fake_image_id)
    monkeypatch.setattr("lc_eval.fixtures.native_sensor.build_image", fake_build)
    tag, derived_id, build_key = _build_sensor_image(config, tmp_path, binary, binary_digest)
    assert built["dockerfile"].startswith("FROM lc-eval-worker:pinned\n")
    assert built["files"] == ["Dockerfile", "native-sensor.bin"]
    assert "key" not in built["dockerfile"].lower()
    assert tag == built["tag"]
    assert derived_id == "sha256:" + "d" * 64
    assert build_key == built["build_key"]


def test_launch_records_real_sqlite_journal_on_event_loop_thread(monkeypatch, tmp_path):
    async def exercise():
        config = _run_config(tmp_path)
        config.sources.worker_image_id = "sha256:worker"
        journal = Journal(tmp_path / "journal")
        journal.create_trial("trial", "campaign", {})
        runtime = NativeSensorRuntime(config, None, journal, "trial", "oid", tmp_path, "marker")
        runtime.sensor_image = "lc-eval-native-sensor:test"
        runtime.sensor_image_id = "sha256:derived"
        binary = tmp_path / "sensor"
        binary.write_bytes(b"\x7fELF")
        calls = []

        def fake_run(argv, **_kwargs):
            calls.append(argv)
            if argv[:3] == ["docker", "image", "inspect"]:
                return "sha256:derived"
            if argv[:2] == ["docker", "create"]:
                return "container-id"
            if argv[:2] == ["docker", "inspect"]:
                return json.dumps([{"HostConfig": {"NetworkMode": "bridge", "Privileged": False, "CapDrop": ["ALL"], "Binds": None, "ReadonlyRootfs": True, "PidsLimit": 128}, "Mounts": []}])
            return ""

        monkeypatch.setattr("lc_eval.fixtures.native_sensor.run", fake_run)
        monkeypatch.setattr("lc_eval.fixtures.native_sensor.image_id", lambda _image: "sha256:derived")
        await runtime._launch_owned(binary, "native-key-value-long-enough")
        resources = journal.resources("trial")
        assert resources[0]["status"] == "active"
        assert resources[0]["resource_id"] == "container-id"
        assert not any(argv[:2] == ["docker", "cp"] for argv in calls)
        journal.close()

    asyncio.run(exercise())


def test_stop_waits_for_inflight_launch_before_container_removal(monkeypatch, tmp_path):
    async def exercise():
        runtime = NativeSensorRuntime(None, None, None, "trial", "oid", tmp_path, "marker")
        launched = False

        async def launch():
            nonlocal launched
            await asyncio.sleep(0.01)
            launched = True

        runtime.launch_task = asyncio.create_task(launch())
        runtime.task = asyncio.create_task(asyncio.sleep(30))

        def fake_run(*_args, **_kwargs):
            raise AssertionError("an unjournaled container name must not be inspected or removed")

        monkeypatch.setattr("lc_eval.fixtures.native_sensor.subprocess.run", fake_run)
        await runtime.stop()
        assert runtime.launch_task.done()

    asyncio.run(exercise())


def test_stop_rejects_container_name_collision_without_removal(monkeypatch, tmp_path):
    async def exercise():
        cleaned = []
        journal = SimpleNamespace(cleaned=lambda intent: cleaned.append(intent))
        runtime = NativeSensorRuntime(None, None, journal, "trial-owned", "oid", tmp_path, "marker")
        runtime.intent = "intent-1"
        runtime.container_id = "expected-id"
        calls = []

        def fake_run(argv, **_kwargs):
            calls.append(argv)
            return SimpleNamespace(returncode=0, stdout=json.dumps([{"Id": "other-id", "Config": {"Labels": {"lc-eval.trial": "another-trial"}}}]), stderr="")

        monkeypatch.setattr("lc_eval.fixtures.native_sensor.subprocess.run", fake_run)
        with pytest.raises(RuntimeError, match="ownership mismatch"):
            await runtime.stop()
        assert len(calls) == 1
        assert cleaned == []

    asyncio.run(exercise())


def test_stop_does_not_treat_docker_daemon_failure_as_absence(monkeypatch, tmp_path):
    async def exercise():
        cleaned = []
        journal = SimpleNamespace(cleaned=lambda intent: cleaned.append(intent))
        runtime = NativeSensorRuntime(None, None, journal, "trial-owned", "oid", tmp_path, "marker")
        runtime.intent = "intent-1"
        runtime.container_id = "expected-id"

        monkeypatch.setattr(
            "lc_eval.fixtures.native_sensor.subprocess.run",
            lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="Cannot connect to the Docker daemon"),
        )
        with pytest.raises(RuntimeError, match="inventory failed"):
            await runtime.stop()
        assert cleaned == []

    asyncio.run(exercise())


def test_collect_cancels_waiter_immediately_when_candidate_omits_request(tmp_path):
    async def exercise():
        config = _run_config(tmp_path, timeout=600)
        config.limits.verification_seconds = 600

        class CLI:
            def invoke(self, args, _oid, **_kwargs):
                if args[:2] == ["installation-key", "list"]:
                    return {}
                if args[:2] == ["sensor", "list"]:
                    return []
                raise AssertionError(args)

        runtime = NativeSensorRuntime(config, CLI(), None, "trial", "oid", tmp_path, "marker")
        runtime.task = asyncio.create_task(runtime._watch())
        started = asyncio.get_running_loop().time()
        evidence = await collect(config, runtime.cli, "oid", {"_runtime": runtime, "baseline_findings": {}}, tmp_path)
        elapsed = asyncio.get_running_loop().time() - started
        assert elapsed < 1
        assert evidence["enrollment_state"] == "missing"
        assert evidence["error_stage"] == "missing_request"

    asyncio.run(exercise())


def test_private_diagnostics_exclude_config_and_bound_raw_outputs(monkeypatch, tmp_path):
    runtime = NativeSensorRuntime(None, None, None, "trial", "oid", tmp_path, "marker")
    runtime.container_id = "container-id"
    inspected = {
        "Id": "container-id",
        "Config": {"Labels": {"lc-eval.trial": "trial"}, "Env": ["LC_INSTALLATION_KEY=secret"]},
        "State": {"Running": False, "ExitCode": 2, "Error": ""},
    }

    def fake_run(argv, **_kwargs):
        if argv[:2] == ["docker", "logs"]:
            return SimpleNamespace(returncode=0, stdout="x" * 100_000, stderr="")
        return SimpleNamespace(returncode=0, stdout="hcp_hbs_status.json 42 bytes\n", stderr="")

    monkeypatch.setattr("lc_eval.fixtures.native_sensor.subprocess.run", fake_run)
    runtime._capture_private_diagnostics("test", inspected)
    path = tmp_path / "native-runtime-diagnostics.json"
    value = json.loads(path.read_text())
    assert value["container_state"]["ExitCode"] == 2
    assert len(value["logs"].encode()) <= 64 * 1024
    assert "LC_INSTALLATION_KEY" not in path.read_text()
    assert path.stat().st_mode & 0o777 == 0o600


def test_registration_detects_early_container_exit_and_captures_diagnostics(monkeypatch, tmp_path):
    async def exercise():
        runtime = NativeSensorRuntime(None, None, None, "trial", "oid", tmp_path, "marker")
        runtime.container_id = "container-id"
        inspected = {"Id": "container-id", "Config": {"Labels": {"lc-eval.trial": "trial"}}, "State": {"Running": False, "ExitCode": 1}}

        def fake_run(argv, **_kwargs):
            if argv[:3] == ["docker", "container", "inspect"]:
                return SimpleNamespace(returncode=0, stdout=json.dumps([inspected]), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        monkeypatch.setattr("lc_eval.fixtures.native_sensor.subprocess.run", fake_run)
        with pytest.raises(RuntimeError, match="exited before registration"):
            await runtime._wait_registered(asyncio.get_running_loop().time() + 10)
        diagnostic = json.loads((tmp_path / "native-runtime-diagnostics.json").read_text())
        assert diagnostic["reason"] == "early_exit"
        assert diagnostic["container_state"]["ExitCode"] == 1

    asyncio.run(exercise())
