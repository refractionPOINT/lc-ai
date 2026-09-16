from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from lc_eval.execution.processes import cleanup, process_handle
from lc_eval.journal import Journal


def test_local_process_cleanup_uses_exact_argv_and_start_time(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "journal")
    trial = "process-trial"
    journal.create_trial(trial, "process-test", {})
    config_dir = tmp_path / "unique-config"
    config_dir.mkdir()
    argv = [
        sys.executable,
        "-c",
        "import time; time.sleep(300)",
        str(config_dir),
    ]
    pending = process_handle(
        executable=sys.executable,
        argv=argv,
        config_dir=config_dir,
    )
    intent = journal.intent(trial, "local_process", "owned-process", pending)
    process = subprocess.Popen(argv)
    try:
        acquired = process_handle(
            executable=sys.executable,
            argv=argv,
            config_dir=config_dir,
            pid=process.pid,
        )
        journal.acquired(intent, str(process.pid), acquired)
        resource = journal.resources(trial)[0]
        cleanup(resource, journal, terminate_seconds=2)
        process.wait(timeout=2)
        assert journal.resources(trial) == []
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        journal.close()


def test_ambiguous_launch_recovery_scans_exact_unique_command(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "journal")
    trial = "ambiguous-process-trial"
    journal.create_trial(trial, "process-test", {})
    config_dir = tmp_path / "ambiguous-config"
    config_dir.mkdir()
    argv = [
        sys.executable,
        "-c",
        "import time; time.sleep(300)",
        str(config_dir),
    ]
    pending = process_handle(
        executable=sys.executable,
        argv=argv,
        config_dir=config_dir,
    )
    intent = journal.intent(trial, "local_process", "ambiguous-process", pending)
    process = subprocess.Popen(argv)
    try:
        resource = journal.resources(trial)[0]
        assert resource["intent"] == intent
        cleanup(resource, journal, terminate_seconds=2)
        process.wait(timeout=2)
        assert journal.resources(trial) == []
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        journal.close()
