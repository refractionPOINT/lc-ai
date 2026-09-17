from lc_eval.fixtures.cloudsec import _sarif, list_all_findings


def test_sarif_fixture_is_deterministic_and_distinct():
    first = _sarif("trial", 4)
    second = _sarif("trial", 4)
    distractor = _sarif("trial-distractor", 4)
    assert first == second
    results = first["runs"][0]["results"]
    assert len(results) == 4
    assert len({item["ruleId"] for item in results}) == 4
    assert results[0]["message"] != distractor["runs"][0]["results"][0]["message"]


def test_list_findings_walks_every_cursor():
    class CLI:
        calls = []

        def api(self, oid, method, path, **kwargs):
            self.calls.append((oid, method, path, kwargs))
            params = dict(kwargs["params"])
            if "cursor" not in params:
                return {"findings": [{"finding_id": "fnd-a"}], "next_cursor": "next"}
            assert params["cursor"] == "next"
            return {"findings": [{"finding_id": "fnd-b"}], "next_cursor": ""}

    cli = CLI()
    assert [row["finding_id"] for row in list_all_findings(cli, "oid", repo="lc-eval/repo")] == ["fnd-a", "fnd-b"]
    assert all(dict(call[3]["params"])["source"] == "ingest" for call in cli.calls)
