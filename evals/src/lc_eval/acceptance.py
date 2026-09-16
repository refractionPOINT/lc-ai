"""Evidence-only acceptance checks; never promote a missing trial to success."""

from __future__ import annotations

import json
from pathlib import Path

from .config import atomic_json
from .journal import Journal

SCENARIOS = ("hive-preserve-update", "search-complete-export", "webhook-production-routing")
BAD_ASSERTIONS = {
    "hive-preserve-update": "hive.target.data_exact",
    "search-complete-export": "export.membership",
    "webhook-production-routing": "routing.negatives_excluded",
}


def validate_references(run_root: Path, campaign: str | None = None):
    journal = Journal(run_root)
    try:
        trials = [row["result"] for row in journal.trials(campaign) if row["result"]]
        checks = []
        for scenario in SCENARIOS:
            good = [
                t
                for t in trials
                if t["scenario_id"] == scenario
                and t["adapter"] == "reference"
                and t["grade"] == "pass"
                and t["cleanup_status"] == "clean"
            ]
            bad = [
                t
                for t in trials
                if t["scenario_id"] == scenario
                and t["adapter"] == "reference_bad"
                and t["grade"] == "fail"
                and t["cleanup_status"] == "clean"
                and any(
                    a["id"] == BAD_ASSERTIONS[scenario] and a["status"] == "fail" for a in t["assertions"]
                )
            ]
            checks.append(
                {
                    "scenario": scenario,
                    "good_trial_ids": [t["trial_id"] for t in good],
                    "bad_trial_ids": [t["trial_id"] for t in bad],
                    "required_bad_assertion": BAD_ASSERTIONS[scenario],
                    "passed": bool(good and bad),
                }
            )
        passed = all(check["passed"] for check in checks)
        result = {"reference_validation_passed": passed, "checks": checks}
        atomic_json(run_root / "reference-validation.json", result)
        proof_path = run_root / "proof.json"
        proof = json.loads(proof_path.read_text()) if proof_path.exists() else {}
        proof.update(
            reference_validation_passed=passed, reference_validation_evidence="reference-validation.json"
        )
        atomic_json(proof_path, proof)
        return result
    finally:
        journal.close()


def write_acceptance(report_path: Path):
    report = json.loads(report_path.read_text())
    acceptance = report.get("acceptance") or {"status": "unknown", "criteria": {}}
    lines = [
        "# Initial loop acceptance",
        "",
        f"Status: **{acceptance['status']}**",
        "",
        "Billing: existing subscriptions; reported tokens are usage measurements. Dollar cost is unknown.",
        "",
        "| Criterion | Status | Observed |",
        "|---|---|---|",
    ]
    for name, check in acceptance["criteria"].items():
        observed = (
            json.dumps(check.get("observed"), ensure_ascii=False).replace("|", "\\|").replace("\n", " ")
        )
        lines.append(f"| {name} | {check['status']} | {observed} |")
    lines += ["", "| Trial | Scenario | Harness | Execution | Grade | Cleanup |", "|---|---|---|---|---|---|"]
    for trial in report["trials"]:
        lines.append(
            "| "
            + " | ".join(
                str(trial.get(k, ""))
                for k in ("trial_id", "scenario_id", "adapter", "execution_status", "grade", "cleanup_status")
            )
            + " |"
        )
    lines += [
        "",
        "This small calibration suite supports no statistical-significance claim. See the adjacent JSON/HTML report and private trial evidence for details.",
        "",
    ]
    dest = report_path.with_name("ACCEPTANCE.md")
    dest.write_text("\n".join(lines))
    return dest
