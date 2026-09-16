"""Read-only live parity and candidate-boundary checks."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import atomic_json


_CLI_CASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("version", ("--version",)),
    ("lookup_help", ("lookup", "--help")),
    ("root_ai_help", ("--ai-help",)),
    ("lookup_ai_help", ("lookup", "--ai-help")),
    ("lookup_list_ai_help", ("lookup", "list", "--ai-help")),
    ("lookup_list_json_postcommand", ("lookup", "list", "--output", "json")),
    ("lookup_missing", ("lookup", "get", "--key", "lc-eval-intentionally-missing")),
)
_PROXY_ENV = ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy", "all_proxy")


@dataclass(frozen=True)
class _CommandResult:
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    timed_out: bool = False


async def _run_command(argv: tuple[str, ...], *, timeout: float) -> _CommandResult:
    process = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        if process.returncode is None:
            process.kill()
        await process.wait()
        return _CommandResult(process.returncode, b"", b"", timed_out=True)
    return _CommandResult(process.returncode, stdout, stderr)


def _stream_record(data: bytes) -> dict[str, Any]:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _result_record(result: _CommandResult) -> dict[str, Any]:
    return {
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "stdout": _stream_record(result.stdout),
        "stderr": _stream_record(result.stderr),
    }


def _direct_argv(worker: str, arguments: tuple[str, ...]) -> tuple[str, ...]:
    return (
        "docker", "exec", "-i", "--workdir", "/work", worker,
        "/usr/local/bin/python", "-I", "/usr/local/bin/limacharlie", *arguments,
    )


def _shim_argv(agent: str, arguments: tuple[str, ...]) -> tuple[str, ...]:
    return (
        "docker", "exec", "-i", "--workdir", "/work", agent,
        "/usr/local/bin/limacharlie", *arguments,
    )


async def check_parity(env: Any, root: Path) -> dict[str, Any]:
    """Compare fixed direct/transport CLI calls and verify candidate isolation.

    The caller must start the trial broker before this function. The function
    performs read-only operations in the trial's already-created organization;
    it creates no LimaCharlie or Docker resources.
    """
    checks = []
    for name, arguments in _CLI_CASES:
        direct, brokered = await asyncio.gather(
            _run_command(_direct_argv(env.worker, arguments), timeout=60),
            _run_command(_shim_argv(env.agent, arguments), timeout=60),
        )
        stdout_equal = direct.stdout == brokered.stdout
        stderr_equal = direct.stderr == brokered.stderr
        exits_equal = direct.exit_code == brokered.exit_code
        timed_out = direct.timed_out or brokered.timed_out
        expected_nonzero = name == "lookup_missing"
        exit_semantics_ok = (
            direct.exit_code is not None
            and ((direct.exit_code != 0) if expected_nonzero else (direct.exit_code == 0))
        )
        checks.append(
            {
                "name": name,
                "arguments": list(arguments),
                "direct": _result_record(direct),
                "brokered": _result_record(brokered),
                "exit_codes_equal": exits_equal,
                "stdout_equal": stdout_equal,
                "stderr_equal": stderr_equal,
                "expected_nonzero": expected_nonzero,
                "passed": exits_equal and stdout_equal and stderr_equal and exit_semantics_ok and not timed_out,
            }
        )

    boundary = await _boundary_checks(env.agent)
    result = {
        "schema_version": 1,
        "profile": "controlled-cli-v1",
        "checks": checks,
        "boundary_checks": boundary,
        "passed": all(check["passed"] for check in checks)
        and all(check["passed"] for check in boundary),
        "raw_output_stored": False,
    }
    atomic_json(Path(root) / "parity.json", result)
    return result


async def _boundary_checks(agent: str) -> list[dict[str, Any]]:
    curl = (
        "curl", "--fail", "--silent", "--show-error", "--output", "/dev/null",
        "--connect-timeout", "3", "--max-time", "5", "https://api.limacharlie.io/",
    )
    through_proxy_argv = ("docker", "exec", agent, *curl)
    clear_proxy = tuple(value for name in _PROXY_ENV for value in ("--env", f"{name}="))
    direct_argv = ("docker", "exec", *clear_proxy, "--env", "NO_PROXY=", "--env", "no_proxy=", agent, *curl)
    docker_socket_script = (
        "import socket,sys; s=socket.socket(socket.AF_UNIX); "
        "p='/var/run/docker.sock'; "
        "\ntry: s.settimeout(1); s.connect(p)\n"
        "except OSError: sys.exit(0)\n"
        "else: s.close(); sys.exit(1)"
    )
    socket_argv = (
        "docker", "exec", agent, "/usr/local/bin/python", "-I", "-c", docker_socket_script,
    )
    proxy_result, direct_result, socket_result = await asyncio.gather(
        _run_command(through_proxy_argv, timeout=10),
        _run_command(direct_argv, timeout=10),
        _run_command(socket_argv, timeout=5),
    )
    definitions = (
        ("lc_api_denied_by_proxy", proxy_result, "nonzero", proxy_result.exit_code not in (None, 0)),
        ("lc_api_direct_egress_denied", direct_result, "nonzero", direct_result.exit_code not in (None, 0)),
        ("host_docker_socket_unreachable", socket_result, "zero", socket_result.exit_code == 0),
    )
    return [
        {
            "name": name,
            "expected_exit": expected,
            "result": _result_record(command_result),
            "passed": passed and not command_result.timed_out,
        }
        for name, command_result, expected, passed in definitions
    ]
