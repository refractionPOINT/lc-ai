import json

import pytest

from lc_eval.controller import freeze, prompt_for, scenario, source_tree_digest
from lc_eval.fixtures.hive import provision
from lc_eval.verifiers import verify_hive


def test_frozen_artifact_is_independent_and_rejects_symlink(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "export.jsonl").write_text('{"eval_event_id":"one"}\n')
    frozen = freeze(work, tmp_path / "frozen.json", "done", 1024)
    (work / "export.jsonl").write_text("changed")
    assert "one" in frozen["export"]["content"]
    assert json.loads((tmp_path / "frozen.json").read_text()) == frozen
    (work / "export.jsonl").unlink()
    (work / "export.jsonl").symlink_to("/etc/passwd")
    result = freeze(work, tmp_path / "symlink.json", "done", 1024)
    assert result["export"]["kind"] == "symlink"
    assert "content" not in result["export"]


def test_prompt_requires_all_variables():
    path, spec, digest = scenario("hive-preserve-update")
    assert len(digest) == 64
    with pytest.raises(ValueError, match="unresolved"):
        prompt_for(path, {"organization_id": "org"})


def test_source_tree_digest_tracks_python_recipe_sources_only(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "fixture.py").write_text("VERSION = 1\n")
    (tmp_path / "nested" / "helper.py").write_text("VALUE = 'a'\n")
    first = source_tree_digest(tmp_path)
    (tmp_path / "runtime.sqlite").write_bytes(b"ignored")
    assert source_tree_digest(tmp_path) == first
    (tmp_path / "nested" / "helper.py").write_text("VALUE = 'b'\n")
    assert source_tree_digest(tmp_path) != first


def test_hive_live_shape_semantics():
    class API:
        def __init__(self):
            self.records = {}

        def api(self, oid, method, path, form=None):
            name = path.split("/")[-2]
            if method == "POST":
                self.records[name] = {k: json.loads(v) for k, v in form.items()}
                self.records[name]["usr_mtd"]["expiry"] = 0
                return {}
            if path.endswith("/data"):
                return self.records[name]
            return self.records

    cli = API()
    f = provision(cli, "oid", 42)
    target = f["target_name"]
    assert f["expected_records"][target]["usr_mtd"] == f["baseline_records"][target]["usr_mtd"]
    assert f["expected_records"][target]["usr_mtd"]["enabled"] is False
    verdict = verify_hive({}, f, {"completion": target}, {"observed_records": f["expected_records"]})
    assert all(a["status"] == "pass" for a in verdict)
