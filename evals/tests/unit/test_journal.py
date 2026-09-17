import sqlite3

import pytest

from lc_eval.journal import Journal


def test_interrupted_create_survives_and_cleanup_is_idempotent(tmp_path):
    j = Journal(tmp_path)
    j.create_trial("trial", "campaign", {})
    j.transition("trial", "provisioning")
    intent = j.intent("trial", "org", "owned-name", {"name": "owned-name"})
    j.close()
    j = Journal(tmp_path)
    assert j.resources()[0]["status"] == "creating"
    j.acquired(intent, "org-id")
    j.cleanup_failed(intent, "temporary outage")
    assert j.resources()[0]["resource_id"] == "org-id"
    j.cleaned(intent)
    j.cleaned(intent)
    assert j.resources() == []
    j.transition("trial", "cleaning")
    j.transition("trial", "finished")
    with pytest.raises(ValueError):
        j.transition("trial", "running")
    with pytest.raises(sqlite3.IntegrityError):
        j.create_trial("trial", "campaign", {})


def test_exclusive_controller_lock(tmp_path):
    a, b = Journal(tmp_path), Journal(tmp_path)
    with a.exclusive():
        with pytest.raises(RuntimeError):
            with b.exclusive():
                pass


def test_unsafe_ids_never_create_trial(tmp_path):
    j = Journal(tmp_path)
    with pytest.raises(ValueError):
        j.create_trial("../../escape", "campaign", {})
