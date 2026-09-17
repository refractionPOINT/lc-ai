from types import SimpleNamespace

import pytest

from lc_eval.fixtures.local_cli import ControlError
from lc_eval.fixtures.organization import Organizations, exact_owned_org


def test_ambiguous_create_cannot_be_cleared_using_invalid_inventory():
    class CLI:
        def invoke(self, *args, **kwargs):
            return {"error": "inventory unavailable"}

    class Journal:
        def cleaned(self, intent):
            pytest.fail("must not certify deletion from invalid inventory")

    with pytest.raises(ControlError):
        Organizations(CLI(), Journal()).cleanup(
            {"kind": "org", "resource_id": None, "name": "lc-eval-owned", "intent": "intent"}
        )


def test_exact_owned_inventory_is_filtered_and_checks_identity():
    class CLI:
        def __init__(self):
            self.args = None

        def invoke(self, args):
            self.args = args
            return [{"name": "lc-eval-owned", "oid": "oid-1"}]

    cli = CLI()
    assert exact_owned_org(cli, "lc-eval-owned", "oid-1") == {
        "name": "lc-eval-owned",
        "oid": "oid-1",
    }
    assert cli.args == [
        "org",
        "list",
        "--filter",
        "lc-eval-owned",
        "--limit",
        "200",
        "--offset",
        "0",
    ]
    with pytest.raises(ControlError, match="another OID"):
        exact_owned_org(cli, "lc-eval-owned", "other-oid")


def test_acquired_org_requires_confirmed_delete_before_sustained_absence(monkeypatch):
    class Clock:
        value = 0.0

        def monotonic(self):
            return self.value

        def time(self):
            return 1_000 + self.value

        def sleep(self, seconds):
            self.value += seconds

    clock = Clock()
    monkeypatch.setattr("lc_eval.fixtures.organization.time.monotonic", clock.monotonic)
    monkeypatch.setattr("lc_eval.fixtures.organization.time.time", clock.time)
    monkeypatch.setattr("lc_eval.fixtures.organization.time.sleep", clock.sleep)
    monkeypatch.setattr("lc_eval.fixtures.organization.MINIMUM_ABSENCE_SECONDS", 6)

    class CLI:
        config = SimpleNamespace(deletion_seconds=30, readiness_seconds=30)

        def __init__(self):
            self.deleted = False
            self.calls = []

        def invoke(self, args, oid=None):
            self.calls.append((args, oid))
            if args[:2] == ["org", "list"]:
                return [] if self.deleted else [{"name": "lc-eval-owned", "oid": "oid-1"}]
            if args == ["org", "delete"]:
                return {"confirmation": "confirmation-value"}
            if args[:2] == ["org", "delete"] and "--confirm-token" in args:
                self.deleted = True
                return {"success": True}
            raise AssertionError(args)

    class Journal:
        def __init__(self):
            self.updated = None
            self.cleaned_intent = None

        def acquired(self, intent, oid, handle):
            self.updated = (intent, oid, handle)

        def cleaned(self, intent):
            self.cleaned_intent = intent

    cli, journal = CLI(), Journal()
    Organizations(cli, journal).cleanup(
        {
            "kind": "org",
            "resource_id": "oid-1",
            "name": "lc-eval-owned",
            "intent": "intent",
            "handle": {"name": "lc-eval-owned", "oid": "oid-1"},
        }
    )
    assert journal.updated[2]["delete_confirmed"] is True
    assert journal.cleaned_intent == "intent"
    assert clock.value >= 6


def test_absent_acquired_org_without_delete_confirmation_fails_closed():
    class CLI:
        config = SimpleNamespace(deletion_seconds=30, readiness_seconds=0)

        def invoke(self, args, oid=None):
            assert args[:2] == ["org", "list"]
            return []

        def api(self, *_args):
            raise ControlError("inventory lag without authoritative status")

    class Journal:
        def cleaned(self, _intent):
            pytest.fail("absence alone must not certify acquired-org deletion")

    with pytest.raises(ControlError, match="never became visible"):
        Organizations(CLI(), Journal()).cleanup(
            {
                "kind": "org",
                "resource_id": "oid-1",
                "name": "lc-eval-owned",
                "intent": "intent",
                "handle": {"name": "lc-eval-owned", "oid": "oid-1"},
            }
        )


def test_independent_identity_allows_delete_during_inventory_lag(monkeypatch):
    monkeypatch.setattr("lc_eval.fixtures.organization.MINIMUM_ABSENCE_SECONDS", 0)

    class CLI:
        config = SimpleNamespace(deletion_seconds=30, readiness_seconds=30)

        def invoke(self, args, oid=None):
            if args[:2] == ["org", "list"]:
                return []
            if args == ["org", "delete"]:
                return {"confirmation": "confirmation-value"}
            if args[:2] == ["org", "delete"] and "--confirm-token" in args:
                return {"success": True}
            raise AssertionError(args)

        def api(self, oid, method, path):
            assert (oid, method, path) == ("oid-1", "GET", "orgs/oid-1")
            return {"oid": "oid-1", "name": "lc-eval-owned"}

    class Journal:
        def __init__(self):
            self.cleaned_intent = None

        def acquired(self, *_args):
            pass

        def cleaned(self, intent):
            self.cleaned_intent = intent

    journal = Journal()
    Organizations(CLI(), journal).cleanup(
        {
            "kind": "org",
            "resource_id": "oid-1",
            "name": "lc-eval-owned",
            "intent": "intent",
            "handle": {"name": "lc-eval-owned", "oid": "oid-1"},
        }
    )
    assert journal.cleaned_intent == "intent"
