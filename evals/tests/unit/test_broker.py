from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import PurePosixPath

import pytest
from aiohttp import ClientSession, web

from lc_eval.execution.broker import (
    Broker,
    CommandPolicy,
    PolicyError,
    StreamingRedactor,
    read_workspace_file,
)


def test_policy_allows_only_initial_scenario_commands_and_flags() -> None:
    policy = CommandPolicy(allowed_oids=("trial-oid",))
    validated = policy.validate(
        [
            "--oid",
            "trial-oid",
            "--output=jsonl",
            "search",
            "run",
            "--query",
            "* | LC_EVAL_EXPORT",
            "--start",
            "1",
            "--end=2",
            "--stream",
            "event",
        ],
        "/work",
    )
    assert validated.command == ("search", "run")
    assert validated.file_arguments == ()

    lookup = policy.validate(
        ["lookup", "set", "--key", "target", "--input-file=record.yaml", "--tag", "existing"],
        "/work",
    )
    assert lookup.file_arguments == ((4, PurePosixPath("/work/record.yaml")),)

    generic = policy.validate(
        ["hive", "get", "--hive-name", "lookup", "--key", "target"], "/work"
    )
    assert generic.command == ("hive", "get")


@pytest.mark.parametrize(
    "argv",
    [
        ["--oid", "trial-oid", "--output", "json", "lookup", "list"],
        ["lookup", "--oid", "trial-oid", "list", "--output", "json"],
        ["lookup", "--output=json", "list", "--oid=trial-oid"],
        ["lookup", "list", "--output=JSON", "--oid", "trial-oid", "--quiet"],
        ["--filter", "--debug", "lookup", "list"],
        ["search", "validate", "--query=--debug", "--oid", "trial-oid"],
    ],
)
def test_policy_hoists_safe_globals_from_every_native_position(argv) -> None:
    validated = CommandPolicy(allowed_oids=("trial-oid",)).validate(argv, "/work")
    assert validated.argv == tuple(argv)


@pytest.mark.parametrize(
    "argv,command",
    [
        (["--ai-help"], ("meta", "help")),
        (["lookup", "--output=json", "--ai-help"], ("lookup", "help")),
        (
            ["lookup", "--oid", "trial-oid", "list", "--output", "yaml", "--ai-help"],
            ("lookup", "list"),
        ),
    ],
)
def test_policy_allows_ai_help_at_root_group_and_leaf(argv, command) -> None:
    validated = CommandPolicy(allowed_oids=("trial-oid",)).validate(argv, "/work")
    assert validated.argv == tuple(argv)
    assert validated.command == command


@pytest.mark.parametrize(
    "argv",
    [
        ["--oid", "trial-oid", "lookup", "list", "--oid", "wrong-oid"],
        ["lookup", "--oid=wrong-oid", "list", "--oid=trial-oid"],
        ["--output", "json", "lookup", "list", "--output=yamlx"],
    ],
)
def test_policy_validates_every_duplicate_global_value(argv) -> None:
    with pytest.raises(PolicyError):
        CommandPolicy(allowed_oids=("trial-oid",)).validate(argv, "/work")


def test_policy_retains_original_file_index_with_interleaved_globals() -> None:
    argv = [
        "lookup",
        "--oid",
        "trial-oid",
        "set",
        "--output=json",
        "--key",
        "target",
        "--input-file",
        "record.yaml",
    ]
    validated = CommandPolicy(allowed_oids=("trial-oid",)).validate(argv, "/work")
    assert validated.argv == tuple(argv)
    assert validated.file_arguments == ((8, PurePosixPath("/work/record.yaml")),)


@pytest.mark.parametrize(
    "argv",
    [
        ["auth", "get-token"],
        ["api", "--input-file", "/proc/self/environ"],
        ["--debug-curl", "lookup", "list"],
        ["--debug-full", "lookup", "list"],
        ["--profile", "personal", "lookup", "list"],
        ["--env", "production", "lookup", "list"],
        ["lookup", "--debug-curl", "list"],
        ["lookup", "list", "--profile=personal"],
        ["lookup", "delete", "--key", "target", "--confirm"],
        ["hive", "get", "--hive-name", "secret", "--key", "credential"],
        ["search", "run", "--checkpoint", "/tmp/worker-file"],
        ["output", "create", "--name", "x", "--module", "s3", "--type", "detect"],
        ["dr", "get", "--key", "x", "--namespace", "managed"],
    ],
)
def test_policy_denies_credentials_debug_destructive_and_unscoped_surfaces(argv) -> None:
    with pytest.raises(PolicyError):
        CommandPolicy().validate(argv, "/work")


@pytest.mark.parametrize("cwd", [None, 7, "", "/", "/work/subdir", "/work/../tmp"])
def test_policy_rejects_malformed_or_unsafe_cwd(cwd) -> None:
    with pytest.raises(PolicyError, match="cwd /work"):
        CommandPolicy().validate(["lookup", "list"], cwd)


@pytest.mark.parametrize(
    "path",
    ["/proc/self/environ", "/work/../proc/self/environ", "../secret", "/work", ""],
)
def test_policy_rejects_file_arguments_outside_workspace(path) -> None:
    with pytest.raises(PolicyError):
        CommandPolicy().validate(
            ["lookup", "set", "--key", "target", "--input-file", path], "/work"
        )


def test_workspace_reader_rejects_symlinks_and_nonregular_files(tmp_path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    (workspace / "safe.yaml").write_text("owner: platform-ops")
    assert read_workspace_file(workspace, PurePosixPath("/work/safe.yaml"), 100) == b"owner: platform-ops"

    outside = tmp_path / "credential"
    outside.write_text("worker-secret")
    (workspace / "link.yaml").symlink_to(outside)
    with pytest.raises(PolicyError, match="symlink"):
        read_workspace_file(workspace, PurePosixPath("/work/link.yaml"), 100)

    (workspace / "linked-dir").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(PolicyError, match="symlink"):
        read_workspace_file(workspace, PurePosixPath("/work/linked-dir/credential"), 100)

    (workspace / "directory").mkdir()
    with pytest.raises(PolicyError, match="regular file"):
        read_workspace_file(workspace, PurePosixPath("/work/directory"), 100)

    fifo = workspace / "pipe"
    fifo.parent.mkdir(exist_ok=True)
    os.mkfifo(fifo)
    with pytest.raises(PolicyError, match="regular file"):
        read_workspace_file(workspace, PurePosixPath("/work/pipe"), 100)


def test_streaming_redactor_covers_secrets_split_across_chunks() -> None:
    redactor = StreamingRedactor((b"super-secret", b"token"))
    output = b"".join(
        [
            redactor.feed(b"before super-"),
            redactor.feed(b"secret and to"),
            redactor.feed(b"ken after"),
            redactor.feed(b"", final=True),
        ]
    )
    assert output == b"before [REDACTED] and [REDACTED] after"
    assert b"secret" not in output
    assert b"token" not in output


def test_profile_description_discloses_material_restrictions() -> None:
    description = CommandPolicy.describe()
    assert "checkpoint" in description
    assert "debug" in description
    assert "lookup hive only" in description
    assert "/work/export.jsonl" in description


class _Request:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        if isinstance(self.payload, BaseException):
            raise self.payload
        return self.payload


@pytest.mark.asyncio
async def test_malformed_request_is_a_terminal_http_error(tmp_path) -> None:
    broker = Broker("worker", tmp_path / "socket", tmp_path / "events.jsonl")
    with pytest.raises(web.HTTPBadRequest):
        await broker.execute(_Request(json.JSONDecodeError("bad", "{", 1)))  # type: ignore[arg-type]
    with pytest.raises(web.HTTPBadRequest):
        await broker.execute(_Request([]))  # type: ignore[arg-type]
    with pytest.raises(web.HTTPBadRequest):
        await broker.execute(
            _Request({"argv": ["lookup", "list"], "cwd": "/work", "stdin": "not base64!"})
        )  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_spawn_failure_is_a_terminal_http_error(tmp_path, monkeypatch) -> None:
    broker = Broker("worker", tmp_path / "socket", tmp_path / "events.jsonl")

    async def fail_spawn(*args, **kwargs):
        raise OSError("docker unavailable")

    monkeypatch.setattr("lc_eval.execution.broker.asyncio.create_subprocess_exec", fail_spawn)
    request = _Request(
        {
            "argv": ["lookup", "list"],
            "cwd": "/work",
            "stdin": base64.b64encode(b"").decode(),
        }
    )
    with pytest.raises(web.HTTPServiceUnavailable):
        await broker.execute(request)  # type: ignore[arg-type]
    event = json.loads((tmp_path / "events.jsonl").read_text().splitlines()[-1])
    assert event["type"] == "command_end"
    assert event["code"] == 125


@pytest.mark.asyncio
async def test_rejected_invocation_evidence_never_records_argument_values(tmp_path) -> None:
    broker = Broker("worker", tmp_path / "socket", tmp_path / "events.jsonl")
    secret = "candidate-supplied-secret"
    request = _Request(
        {
            "argv": ["--profile", secret, "auth", "get-token"],
            "cwd": "/work/secret-directory",
            "stdin": "",
        }
    )
    with pytest.raises(web.HTTPForbidden):
        await broker.execute(request)  # type: ignore[arg-type]
    evidence = (tmp_path / "events.jsonl").read_text()
    assert secret not in evidence
    event = json.loads(evidence)
    assert event["type"] == "command_rejected"
    assert event["argv_sha256"]
    assert event["cwd"] == "[INVALID]"


@pytest.mark.asyncio
async def test_input_file_is_snapshotted_and_rewritten_to_worker_private_path(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    (workspace / "record.yaml").write_bytes(b"data: original")
    broker = Broker(
        "worker",
        tmp_path / "socket",
        tmp_path / "events.jsonl",
        workspace=workspace,
    )
    copied: list[bytes] = []

    class Copier:
        returncode = 0

        async def communicate(self, content):
            copied.append(content)
            return b"", b""

        def kill(self):
            self.returncode = -9

        async def wait(self):
            return self.returncode

    async def fake_spawn(*args, **kwargs):
        return Copier()

    monkeypatch.setattr("lc_eval.execution.broker.asyncio.create_subprocess_exec", fake_spawn)
    validated = broker.policy.validate(
        ["lookup", "set", "--key", "target", "--input-file", "record.yaml"], "/work"
    )
    argv, staged = await broker._stage_files(validated, "command")
    assert copied == [b"data: original"]
    assert argv[-1] == "/tmp/lc-eval-input-command-0"
    assert staged == ["/tmp/lc-eval-input-command-0"]


@pytest.mark.asyncio
async def test_broker_redacts_stdout_and_stderr_before_delivery(tmp_path, monkeypatch) -> None:
    secret = b"worker-api-secret"

    class Stdin:
        def write(self, data):
            pass

        async def drain(self):
            pass

        def close(self):
            pass

    class Process:
        returncode = 0
        stdin = Stdin()

        def __init__(self):
            self.stdout = asyncio.StreamReader()
            self.stdout.feed_data(b"out worker-api-")
            self.stdout.feed_data(b"secret end\n")
            self.stdout.feed_eof()
            self.stderr = asyncio.StreamReader()
            self.stderr.feed_data(b"err worker-api-secret end\n")
            self.stderr.feed_eof()

        async def wait(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    async def fake_spawn(*args, **kwargs):
        return Process()

    monkeypatch.setattr("lc_eval.execution.broker.asyncio.create_subprocess_exec", fake_spawn)
    broker = Broker(
        "worker",
        tmp_path / "socket",
        tmp_path / "events.jsonl",
        redactions=(secret,),
    )
    app = web.Application()
    app.router.add_post("/execute", broker.execute)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    sockets = site._server.sockets  # type: ignore[union-attr]
    url = f"http://127.0.0.1:{sockets[0].getsockname()[1]}/execute"
    try:
        async with ClientSession() as session:
            async with session.post(
                url,
                json={"argv": ["lookup", "list"], "cwd": "/work", "stdin": ""},
            ) as response:
                assert response.status == 200
                events = [json.loads(line) for line in (await response.text()).splitlines()]
        delivered = b"".join(
            base64.b64decode(event["data"])
            for event in events
            if event["type"] in {"stdout", "stderr"}
        )
        assert secret not in delivered
        assert delivered.count(b"[REDACTED]") == 2
        assert secret.decode() not in (tmp_path / "events.jsonl").read_text()
    finally:
        await runner.cleanup()
