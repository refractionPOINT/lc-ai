import pytest

from lc_eval.fixtures.local_cli import ControlError, decode_json
from lc_eval.models import Limits


def test_status_text_around_json():
    assert decode_json('Organization created.\n{"data":{"oid":"expected"}}\nhttps://example') == {"data": {"oid": "expected"}}
    with pytest.raises(ControlError):
        decode_json("successful but no structured data")


def test_budget_limits_are_finite():
    for value in [float("nan"), float("inf"), -1, 51]:
        with pytest.raises(ValueError):
            Limits(model_budget_usd=value)
