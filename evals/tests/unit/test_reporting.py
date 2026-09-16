import json
from pathlib import Path

import pytest
import yaml

from lc_eval.reporting.compare import compare_pair, compare_results
from lc_eval.reporting.html import render_html
from lc_eval.reporting.results import acceptance_summary, build_report, dumps_json


def _trial(trial_id, grade="pass", **changes):
    value = {
        "trial_id": trial_id,
        "scenario_id": "hive-preserve-update",
        "scenario_revision": 1,
        "scenario_hash": "scenario-digest",
        "variant_seed": 7,
        "repetition": 1,
        "adapter": "codex",
        "model": "fixed-model",
        "effort": "medium",
        "docs_digest": "docs",
        "fixture_recipe_digest": "fixture",
        "tools_digest": "tools",
        "permission_profile": "scoped",
        "execution_profile": "controlled-cli-v1",
        "limits": {"seconds": 600},
        "grade": grade,
        "execution_status": "finished",
        "cleanup_status": "clean",
        "usage": {"cost_usd": 1.0, "input_tokens": 10},
    }
    value.update(changes)
    return value


def test_html_escapes_agent_controlled_values():
    trial = _trial(
        "trial-1",
        assertions=[
            {
                "id": "<img src=x onerror=alert(1)>",
                "status": "fail",
                "expected": "safe",
                "observed": "</pre><script>alert(1)</script>",
                "evidence": ["javascript:bad"],
                "explanation": "<b>bad</b>",
            }
        ],
    )
    output = render_html(build_report([trial]), title="<script>title</script>")
    assert "<script>" not in output
    assert "&lt;script&gt;" in output
    assert "<img src=x" not in output


def test_json_and_aggregates_keep_missing_usage_null():
    report = build_report([_trial("one"), _trial("two", usage={})])
    cost = report["summary"]["metrics"]["cost_usd"]
    assert cost["total"] is None
    assert cost["known_total"] == 1.0
    assert cost["missing_count"] == 1
    assert json.loads(dumps_json(report))["summary"]["metrics"]["cost_usd"]["total"] is None


def test_comparison_requires_compatibility_and_both_success_for_efficiency():
    left = _trial("left")
    right = _trial("right", usage={"cost_usd": 0.7, "input_tokens": 7})
    pair = compare_pair(left, right)
    assert pair["included_in_efficiency"] is True
    assert pair["efficiency"]["cost_usd"]["delta_right_minus_left"] == pytest.approx(-0.3)

    failed = compare_pair(left, _trial("failed", grade="fail"))
    assert failed["included_in_efficiency"] is False
    assert failed["efficiency"]["cost_usd"]["delta_right_minus_left"] is None

    incompatible = compare_pair(left, _trial("different", docs_digest="other"))
    assert incompatible["compatibility"]["compatible"] is False
    assert "mismatched controlled field: docs_digest" in incompatible["compatibility"]["reasons"]

    repeat = compare_pair(left, _trial("repeat", repetition=2))
    assert repeat["compatibility"]["compatible"] is True


def test_compare_results_includes_all_attempt_spend_and_null_unknown_total():
    comparison = compare_results([_trial("left")], [_trial("right", usage={})])
    right_cost = comparison["right"]["all_attempt_metrics"]["cost_usd"]
    assert right_cost["total"] is None
    assert right_cost["missing_count"] == 1


def test_acceptance_does_not_invent_missing_live_evidence():
    result = acceptance_summary([])
    assert result["status"] == "unknown"
    assert result["criteria"]["scenario_ai_success"]["status"] == "unknown"


def test_initial_suite_has_six_matrix_trials_and_two_hive_aa_repeats():
    eval_root = Path(__file__).parents[2]
    suite = yaml.safe_load((eval_root / "suites" / "initial-loop.yaml").read_text())
    assert len(suite["trials"]) == 8
    matrix = {
        (item["scenario"], item["adapter"]) for item in suite["trials"] if item.get("experiment") != "aa"
    }
    assert matrix == {
        (scenario, adapter)
        for scenario in ("hive-preserve-update", "search-complete-export", "webhook-production-routing")
        for adapter in ("claude_code", "codex")
    }
    repeats = [item for item in suite["trials"] if item.get("experiment") == "aa"]
    assert {item["adapter"] for item in repeats} == {"claude_code", "codex"}
    assert all(item["scenario"] == "hive-preserve-update" and item["pair_with"] for item in repeats)


def test_catalog_registers_every_design_family():
    eval_root = Path(__file__).parents[2]
    catalog = yaml.safe_load((eval_root / "catalog" / "capabilities.yaml").read_text())
    assert len(catalog["families"]) == 14
    assert {item["coverage"] for item in catalog["families"]} == {"initial", "planned"}


def test_calibration_and_fault_drills_do_not_dilute_model_success_rate():
    report = build_report(
        [
            _trial("model"),
            _trial("reference", adapter="reference"),
            _trial("fault", grade="not-run", adapter="fault_injection"),
        ]
    )
    assert report["summary"]["trials"] == 1
    assert report["summary"]["recorded_trials"] == 3
    assert report["summary"]["success_rate"] == 1
    assert len(report["trials"]) == 3
