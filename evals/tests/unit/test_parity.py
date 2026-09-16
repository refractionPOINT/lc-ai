from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from lc_eval.execution import parity


@dataclass
class Environment:
    worker: str = "trial-worker"
    agent: str = "trial-agent"


@pytest.mark.asyncio
async def test_parity_records_hashes_not_raw_output(tmp_path, monkeypatch) -> None:
    secret = b"sensitive-output-that-must-not-be-stored"

    async def fake_run(argv, *, timeout):
        if "curl" in argv:
            return parity._CommandResult(22, secret, b"proxy denied")
        if "/var/run/docker.sock" in " ".join(argv):
            return parity._CommandResult(0, b"", b"")
        if "lc-eval-intentionally-missing" in argv:
            return parity._CommandResult(4, secret, b"missing")
        return parity._CommandResult(0, secret, b"")

    monkeypatch.setattr(parity, "_run_command", fake_run)
    result = await parity.check_parity(Environment(), tmp_path)
    assert result["passed"]
    report_text = (tmp_path / "parity.json").read_text()
    assert secret.decode() not in report_text
    report = json.loads(report_text)
    assert report["raw_output_stored"] is False
    assert report["checks"][0]["direct"]["stdout"]["bytes"] == len(secret)
    assert report["checks"][0]["direct"]["stdout"]["sha256"]
    assert report["boundary_checks"][0]["passed"]


@pytest.mark.asyncio
async def test_parity_reports_stream_or_exit_mismatch_without_raising(tmp_path, monkeypatch) -> None:
    async def fake_run(argv, *, timeout):
        is_brokered = "trial-agent" in argv
        if "curl" in argv:
            return parity._CommandResult(22, b"", b"")
        if "/var/run/docker.sock" in " ".join(argv):
            return parity._CommandResult(0, b"", b"")
        if "lc-eval-intentionally-missing" in argv:
            return parity._CommandResult(4, b"", b"missing")
        return parity._CommandResult(0, b"different" if is_brokered else b"direct", b"")

    monkeypatch.setattr(parity, "_run_command", fake_run)
    result = await parity.check_parity(Environment(), tmp_path)
    assert not result["passed"]
    assert not result["checks"][0]["stdout_equal"]
    assert (tmp_path / "parity.json").stat().st_mode & 0o777 == 0o600


@pytest.mark.asyncio
async def test_parity_uses_direct_fixed_cli_and_candidate_shim_argv(tmp_path, monkeypatch) -> None:
    seen = []

    async def fake_run(argv, *, timeout):
        seen.append(argv)
        if "curl" in argv:
            return parity._CommandResult(22, b"", b"")
        if "/var/run/docker.sock" in " ".join(argv):
            return parity._CommandResult(0, b"", b"")
        code = 4 if "lc-eval-intentionally-missing" in argv else 0
        return parity._CommandResult(code, b"same", b"")

    monkeypatch.setattr(parity, "_run_command", fake_run)
    await parity.check_parity(Environment(), tmp_path)
    direct = next(argv for argv in seen if "trial-worker" in argv)
    brokered = next(argv for argv in seen if "trial-agent" in argv and "/usr/local/bin/limacharlie" in argv)
    assert direct[direct.index("trial-worker") + 1 : direct.index("trial-worker") + 4] == (
        "/usr/local/bin/python",
        "-I",
        "/usr/local/bin/limacharlie",
    )
    assert brokered[brokered.index("trial-agent") + 1] == "/usr/local/bin/limacharlie"
    assert any(
        argv[-4:] == ("--output", "json", "lookup", "list")
        for argv in seen
        if "trial-worker" in argv
    )
