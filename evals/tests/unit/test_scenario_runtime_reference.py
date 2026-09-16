from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from lc_eval.fixtures.local_cli import ControlError
from lc_eval.fixtures.scenario_runtime import installation_key, reference


def test_installation_key_selects_adapter_iid() -> None:
    class FakeCLI:
        def invoke(self, args, oid):
            assert args == [
                "installation-key",
                "create",
                "--description",
                "eval-trial",
                "--get",
            ]
            assert oid == "oid"
            return {
                "iid": "00000000-0000-4000-8000-000000000001",
                "key": "binary-rpcm-key",
                "json_key": "encoded-json-sensor-key",
            }

    assert installation_key(FakeCLI(), "oid", "trial") == (
        "00000000-0000-4000-8000-000000000001"
    )


def test_installation_key_rejects_encoded_keys_without_iid() -> None:
    class FakeCLI:
        def invoke(self, args, oid):
            return {"key": "binary-rpcm-key", "json_key": "encoded-json-sensor-key"}

    try:
        installation_key(FakeCLI(), "oid", "trial")
    except ControlError as error:
        assert "iid" in str(error)
    else:
        raise AssertionError("encoded sensor key was accepted for an adapter")


def test_search_reference_projects_rows_from_raw_result_pages(
    tmp_path: Path, monkeypatch
) -> None:
    async def exercise() -> None:
        raw = json.dumps(
            [
                {"type": "stats", "rows": []},
                {
                    "type": "events",
                    "rows": [
                        {
                            "data": {
                                "event": {
                                    "eval_event_id": "one",
                                    "environment": "production",
                                    "message": "first",
                                }
                            },
                            "mtd": {"stream": "event"},
                        }
                    ],
                },
                {
                    "type": "events",
                    "fields": ["data", "mtd"],
                    "rows": [
                        [
                            {
                                "event": {
                                    "eval_event_id": "two",
                                    "environment": "production",
                                    "message": "second",
                                }
                            },
                            {"stream": "event"},
                        ]
                    ],
                },
            ]
        )

        def fake_run(argv, *, timeout):
            assert argv[:4] == ["docker", "exec", "candidate", "limacharlie"]
            assert timeout == 600
            return raw

        monkeypatch.setattr("lc_eval.execution.docker.run", fake_run)
        fixture = {
            "public": {
                "trial_selector": "trial",
                "window_start": 100,
                "window_end": 200,
            }
        }
        env = SimpleNamespace(agent="candidate", work=tmp_path)
        completion = await reference("search-complete-export", fixture, env)
        rows = [
            json.loads(line)
            for line in (tmp_path / "export.jsonl").read_text().splitlines()
        ]
        assert completion == "Exported 2 events"
        assert rows == [
            {
                "eval_event_id": "one",
                "environment": "production",
                "message": "first",
            },
            {
                "eval_event_id": "two",
                "environment": "production",
                "message": "second",
            },
        ]

        await reference("search-complete-export", fixture, env, bad=True)
        assert len((tmp_path / "export.jsonl").read_text().splitlines()) == 1

    asyncio.run(exercise())
