"""Exact local child-process ownership and crash recovery."""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path
from typing import Any


def process_start_time(pid: int) -> int:
    """Return Linux /proc starttime ticks, which disambiguate PID reuse."""
    raw = Path(f"/proc/{pid}/stat").read_text()
    tail = raw.rsplit(")", 1)
    if len(tail) != 2:
        raise RuntimeError("process stat has an unsupported shape")
    fields = tail[1].split()
    if len(fields) <= 19:
        raise RuntimeError("process stat omitted starttime")
    return int(fields[19])


def process_handle(
    *,
    executable: str | Path,
    argv: list[str] | tuple[str, ...],
    config_dir: str | Path,
    pid: int | None = None,
) -> dict[str, Any]:
    """Build the durable identity recorded before and after child launch."""
    executable_path = Path(executable).expanduser().resolve()
    config_path = Path(config_dir).expanduser().resolve()
    expected = [str(item) for item in argv]
    if not expected or Path(expected[0]).expanduser().resolve() != executable_path:
        raise ValueError("process argv must start with the exact executable")
    if str(config_path) not in expected and str(config_path / "config.yml") not in expected:
        raise ValueError("process argv must contain its unique configuration path")
    handle: dict[str, Any] = {
        "pid": pid,
        "start_time": None,
        "executable": str(executable_path),
        "config_dir": str(config_path),
        "argv": expected,
    }
    if pid is not None:
        handle["start_time"] = process_start_time(pid)
    return handle


def _cmdline(pid: int) -> list[str]:
    raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    return [part.decode("utf-8", "surrogateescape") for part in raw.split(b"\0") if part]


def _matches(pid: int, handle: dict[str, Any], *, require_start: bool) -> bool:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)
        if len(stat) != 2 or stat[1].split()[0] == "Z":
            return False
        executable = Path(os.readlink(f"/proc/{pid}/exe")).resolve()
        if executable != Path(handle["executable"]).resolve():
            return False
        if _cmdline(pid) != handle["argv"]:
            return False
        if require_start and process_start_time(pid) != int(handle["start_time"]):
            return False
        return True
    except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, OSError):
        return False


def matching_pids(handle: dict[str, Any]) -> list[int]:
    """Find only exact executable+argv matches for an ambiguous launch."""
    config_dir = Path(handle["config_dir"]).resolve()
    if str(config_dir) not in handle["argv"] and str(config_dir / "config.yml") not in handle["argv"]:
        raise ValueError("process handle has no unique configuration path in argv")
    matches: list[int] = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit() and _matches(int(entry.name), handle, require_start=False):
            matches.append(int(entry.name))
    return sorted(matches)


def cleanup(
    resource: dict[str, Any],
    journal: Any,
    *,
    terminate_seconds: float = 10.0,
) -> None:
    """Terminate one journal-owned child and mark it clean after exit."""
    if resource.get("kind") != "local_process":
        raise ValueError("wrong resource kind")
    if terminate_seconds <= 0:
        raise ValueError("terminate_seconds must be positive")
    handle = resource.get("handle")
    if not isinstance(handle, dict):
        raise ValueError("local process resource omitted its handle")

    pid_value = handle.get("pid")
    pid = int(pid_value) if isinstance(pid_value, int | str) and str(pid_value).isdigit() else None
    matches: list[int]
    if (
        pid is not None
        and handle.get("start_time") is not None
        and _matches(pid, handle, require_start=True)
    ):
        matches = [pid]
    else:
        matches = matching_pids(handle)
    if len(matches) > 1:
        raise RuntimeError("multiple processes match the exact owned command")
    if not matches:
        journal.cleaned(resource["intent"])
        return

    owned_pid = matches[0]
    os.kill(owned_pid, signal.SIGTERM)
    deadline = time.monotonic() + terminate_seconds
    while time.monotonic() < deadline:
        if not _matches(owned_pid, handle, require_start=handle.get("start_time") is not None):
            journal.cleaned(resource["intent"])
            return
        time.sleep(0.05)
    if _matches(owned_pid, handle, require_start=handle.get("start_time") is not None):
        os.kill(owned_pid, signal.SIGKILL)
    deadline = time.monotonic() + terminate_seconds
    while time.monotonic() < deadline:
        if not _matches(owned_pid, handle, require_start=handle.get("start_time") is not None):
            journal.cleaned(resource["intent"])
            return
        time.sleep(0.05)
    raise RuntimeError("owned local process did not terminate")
