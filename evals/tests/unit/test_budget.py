from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from lc_eval.execution.budget import (
    BudgetExceeded,
    BudgetLedger,
    DuplicateSettlementError,
    InactiveTrial,
    ModelNotAllowed,
)


def ledger(tmp_path, campaign_cap=1_000, trial_cap=800) -> BudgetLedger:
    result = BudgetLedger(tmp_path / "budget.sqlite")
    result.create_campaign("campaign", campaign_cap)
    result.create_trial("trial", "campaign", trial_cap, ["pinned-model"])
    return result


def test_reserve_settle_and_uncertain_exposure(tmp_path) -> None:
    budget = ledger(tmp_path)
    budget.reserve("one", "trial", "pinned-model", 500)
    budget.mark_uncertain("one")
    assert budget.trial_snapshot("trial").reserved_micro_usd == 500
    with pytest.raises(BudgetExceeded):
        budget.reserve("two", "trial", "pinned-model", 400)

    budget.settle("one", 125, {"input_tokens": 10})
    assert budget.trial_snapshot("trial").settled_micro_usd == 125
    assert budget.trial_snapshot("trial").remaining_micro_usd == 675
    budget.reserve("two", "trial", "pinned-model", 400)


def test_duplicate_settlement_must_match_exactly(tmp_path) -> None:
    budget = ledger(tmp_path)
    budget.reserve("request", "trial", "pinned-model", 500)
    first = budget.settle("request", 100, {"output_tokens": 4})
    second = budget.settle("request", 100, {"output_tokens": 4})
    assert first == second
    with pytest.raises(DuplicateSettlementError):
        budget.settle("request", 101, {"output_tokens": 4})


def test_campaign_cap_applies_across_trials(tmp_path) -> None:
    budget = ledger(tmp_path, campaign_cap=1_000, trial_cap=900)
    budget.create_trial("other", "campaign", 900, ["pinned-model"])
    budget.reserve("a", "trial", "pinned-model", 600)
    with pytest.raises(BudgetExceeded, match="campaign"):
        budget.reserve("b", "other", "pinned-model", 500)


def test_trial_status_and_model_are_validated(tmp_path) -> None:
    budget = ledger(tmp_path)
    with pytest.raises(ModelNotAllowed):
        budget.reserve("a", "trial", "surprise-model", 1)
    budget.close_trial("trial")
    with pytest.raises(InactiveTrial):
        budget.reserve("b", "trial", "pinned-model", 1)


def test_concurrent_reservations_are_atomic(tmp_path) -> None:
    budget = ledger(tmp_path, campaign_cap=1_000, trial_cap=1_000)

    def reserve(index: int) -> bool:
        try:
            budget.reserve(f"request-{index}", "trial", "pinned-model", 600)
            return True
        except BudgetExceeded:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(reserve, range(2)))
    assert sorted(results) == [False, True]
    assert budget.campaign_snapshot("campaign").reserved_micro_usd == 600
