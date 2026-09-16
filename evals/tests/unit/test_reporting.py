import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from lc_eval.reporting.compare import compare_pair, compare_results
from lc_eval.reporting.html import render_html
from lc_eval.reporting.results import acceptance_summary, build_report, command_metrics, dumps_json
from lc_eval.controller import Controller


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
        "evaluator_digest": "evaluator",
        "permission_profile": "scoped",
        "execution_profile": "controlled-cli-v1",
        "limits": {"seconds": 600},
        "grade": grade,
        "execution_status": "completed",
        "evidence_complete": True,
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


def test_command_metrics_aggregate_metadata_without_raw_output(tmp_path):
    path = tmp_path / "commands.jsonl"
    events = [
        {"type": "command_request", "id": "one"},
        {"type": "stdout", "id": "one", "text": "private raw output"},
        {"type": "command_end", "id": "one", "code": 0, "bytes": 5, "seconds": 0.25},
        {"type": "command_rejected", "argv_sha256": "digest"},
        {"type": "command_request", "id": "two"},
        {"type": "command_end", "id": "two", "code": 2, "bytes": 7, "seconds": 0.75},
    ]
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    metrics = command_metrics(path)
    assert metrics == {
        "output_bytes": 12,
        "cli_seconds": 1.0,
        "cli_failed_commands": 1,
        "rejected_commands": 1,
    }
    assert "private raw output" not in json.dumps(metrics)


def test_command_metrics_preserve_unknown_for_missing_end_or_bytes(tmp_path):
    missing_end = tmp_path / "missing-end.jsonl"
    missing_end.write_text(json.dumps({"type": "command_request", "id": "one"}) + "\n")
    result = command_metrics(missing_end)
    assert result["output_bytes"] is None
    assert result["cli_seconds"] is None
    assert result["cli_failed_commands"] is None
    assert result["rejected_commands"] == 0

    missing_bytes = tmp_path / "missing-bytes.jsonl"
    missing_bytes.write_text(
        json.dumps({"type": "command_request", "id": "one"})
        + "\n"
        + json.dumps({"type": "command_end", "id": "one", "code": 125, "seconds": 0.5})
        + "\n"
    )
    result = command_metrics(missing_bytes)
    assert result["output_bytes"] is None
    assert result["cli_seconds"] == 0.5
    assert result["cli_failed_commands"] == 1


def test_command_metrics_are_unknown_when_evidence_is_missing_or_malformed(tmp_path):
    assert all(value is None for value in command_metrics(tmp_path / "absent").values())
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("not-json\n")
    assert all(value is None for value in command_metrics(malformed).values())


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

    evaluator_changed = compare_pair(left, _trial("evaluator-changed", evaluator_digest="other"))
    assert evaluator_changed["compatibility"]["compatible"] is False
    assert "mismatched controlled field: evaluator" in evaluator_changed["compatibility"]["reasons"]
    assert evaluator_changed["efficiency"]["cost_usd"]["delta_right_minus_left"] is None

    repeat = compare_pair(left, _trial("repeat", repetition=2))
    assert repeat["compatibility"]["compatible"] is True


@pytest.mark.parametrize(
    "changes",
    [
        {"execution_status": "failed"},
        {"evidence_complete": False},
        {"cleanup_status": "failed"},
        {"adapter": "reference"},
    ],
)
def test_pair_efficiency_requires_genuine_complete_clean_success(changes):
    pair = compare_pair(_trial("left"), _trial("right", **changes))
    assert pair["paired_success"] is False
    assert pair["included_in_efficiency"] is False
    assert pair["efficiency"]["cost_usd"]["delta_right_minus_left"] is None


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


def test_invalid_attempt_is_retained_but_excluded_from_scored_summary():
    report = build_report([_trial("valid"), _trial("invalid", invalid=True)])
    assert report["summary"]["trials"] == 1
    assert report["summary"]["recorded_trials"] == 2
    assert report["summary"]["invalid_trials"] == 1
    assert report["summary"]["non_scored_trials"] == 1
    assert report["summary"]["successes"] == 1
    assert [trial["trial_id"] for trial in report["trials"]] == ["valid", "invalid"]


@pytest.mark.parametrize(
    "changes",
    [
        {"execution_status": "failed"},
        {"evidence_complete": False},
        {"cleanup_status": "failed"},
        {"invalid": True},
    ],
)
def test_report_success_requires_complete_clean_valid_evidence(changes):
    report = build_report([_trial("attempt", **changes)])
    assert report["summary"]["successes"] == 0


def test_invalid_terminal_attempt_does_not_satisfy_harness_matrix():
    invalid = _trial(
        "invalid",
        invalid=True,
        adapter="codex",
        scenario_id="hive-preserve-update",
        execution_status="completed",
    )
    result = acceptance_summary([invalid])
    assert result["criteria"]["harness_matrix_terminal"]["status"] == "unknown"
    assert "hive-preserve-update:codex" in result["criteria"]["harness_matrix_terminal"]["observed"]
    assert result["criteria"]["scenario_ai_success"]["status"] == "unknown"


def test_smoke_does_not_turn_missing_scored_ai_evidence_into_failure():
    result = acceptance_summary([_trial("smoke", scenario_id="harness-smoke")])
    assert result["criteria"]["scenario_ai_success"]["status"] == "unknown"
    assert result["criteria"]["harness_matrix_terminal"]["status"] == "unknown"
    assert result["criteria"]["billing_accounting"]["status"] == "unknown"


def test_subscription_accounting_requires_unknown_dollar_cost():
    subscription = _trial(
        "subscription",
        manifest={"billing_mode": "subscription_limits"},
        usage={"billing_mode": "subscription_limits", "cost_usd": None, "input_tokens": 10},
    )
    result = acceptance_summary([subscription])
    assert result["criteria"]["billing_accounting"]["status"] == "pass"

    false_claim = _trial(
        "false-claim",
        manifest={"billing_mode": "subscription_limits"},
        usage={"billing_mode": "subscription_limits", "cost_usd": 1.25},
    )
    result = acceptance_summary([false_claim])
    assert result["criteria"]["billing_accounting"]["status"] == "fail"


def test_hard_usd_accounting_remains_supported_when_cost_is_known():
    metered = _trial(
        "metered",
        manifest={"billing_mode": "hard_usd"},
        usage={"billing_mode": "hard_usd", "cost_usd": 0.25},
    )
    result = acceptance_summary([metered])
    assert result["criteria"]["billing_accounting"]["status"] == "pass"


def test_extra_compatible_aa_pairs_are_retained_without_invalidating_coverage(tmp_path):
    trials = []
    for adapter, repetitions in (("claude_code", (1, 2, 2)), ("codex", (1, 2))):
        for index, repetition in enumerate(repetitions):
            trial = _trial(
                f"{adapter}-{repetition}-{index}",
                adapter=adapter,
                repetition=repetition,
            )
            trial["manifest"] = {"repetition": repetition}
            trials.append({"result": trial})

    class Journal:
        def trials(self, campaign=None):
            return trials

        def resources(self):
            return []

    controller = Controller.__new__(Controller)
    controller.journal = Journal()
    controller.config = SimpleNamespace(run_data_dir=tmp_path)
    report_dir = controller.report("campaign")
    report = json.loads((report_dir / "report.json").read_text())

    assert len(report["comparisons"]) == 3
    assert all(pair["compatibility"]["compatible"] for pair in report["comparisons"])
    assert report["acceptance"]["criteria"]["paired_aa"]["status"] == "pass"
