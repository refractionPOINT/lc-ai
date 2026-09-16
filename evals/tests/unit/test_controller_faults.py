import asyncio
import json
import subprocess
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

import lc_eval.cli as cli_module
import lc_eval.controller as controller_module
import lc_eval.execution.parity as parity_module
from lc_eval.controller import Controller
from lc_eval.journal import Journal as RealJournal
from lc_eval.models import AgentConfig
from lc_eval.adapters import AdapterStateError, UnsupportedAdapterError


class FakeJournal:
    def __init__(self, root, pending=None):
        self.root = root
        self.pending = list(pending or [])
        self.transitions = []
        self.finished = []

    def create_trial(self, trial_id, campaign, manifest):
        root = self.root / "trials" / trial_id
        root.mkdir(parents=True)
        return root

    def transition(self, trial_id, state):
        self.transitions.append(state)

    def finish(self, trial_id, result):
        self.finished.append(dict(result))

    def resources(self, trial=None):
        return list(self.pending)


def config(tmp_path):
    limits = SimpleNamespace(
        budget_mode="subscription_limits",
        max_fixture_bytes=100_000,
        max_command_seconds=30,
        max_command_output=10_000,
        model_dump=lambda: {"budget_mode": "subscription_limits"},
    )
    return SimpleNamespace(
        run_data_dir=tmp_path,
        limits=limits,
        lc=SimpleNamespace(location="auto"),
        sources=SimpleNamespace(
            docs=SimpleNamespace(commit="docs-pin"),
            candidate_image_id="agent-pin",
            worker_image_id="worker-pin",
        ),
        agents=[AgentConfig(adapter="codex", model="gpt-test", auth_mode="subscription")],
        profile="controlled-cli-v1",
    )


def controller(tmp_path, pending=None):
    value = Controller.__new__(Controller)
    value.config = config(tmp_path)
    value.journal = FakeJournal(tmp_path, pending)
    value.cli = object()
    value.orgs = SimpleNamespace(create=lambda trial, location: {"oid": "oid"})
    return value


@pytest.mark.asyncio
async def test_provision_exception_is_persisted_inconclusive_and_reconciled(tmp_path, monkeypatch):
    value = controller(tmp_path)
    called = []
    value.reconcile = lambda trial: called.append(trial) or {"unresolved": [], "errors": []}
    monkeypatch.setattr(
        controller_module.hive,
        "provision",
        lambda *args: (_ for _ in ()).throw(RuntimeError("fixture exploded")),
    )

    result = await value.trial("campaign", "hive-preserve-update", "codex")

    assert result["grade"] == "inconclusive"
    assert result["evidence_complete"] is False
    assert result["cleanup_status"] == "clean"
    assert "fixture exploded" in result["error"]
    assert called == [result["trial_id"]]
    assert value.journal.finished[-1]["grade"] == "inconclusive"
    assert value.journal.transitions[-2:] == ["cleaning", "finished"]


@pytest.mark.asyncio
async def test_unsupported_adapter_is_rejected_before_trial_or_org_creation(tmp_path):
    value = controller(tmp_path)
    value.config.agents = [AgentConfig(adapter="workspace")]
    with pytest.raises(UnsupportedAdapterError):
        await value.trial("campaign", "hive-preserve-update", "workspace")
    assert not (tmp_path / "trials").exists()


@pytest.mark.asyncio
async def test_subscription_usage_never_promotes_provider_estimate_to_dollar_cost(
    tmp_path, monkeypatch
):
    class Usage:
        def as_dict(self):
            return {"input_tokens": 10, "cost_micro_usd": 125_000}

    collected = SimpleNamespace(
        usage=Usage(),
        stdout=b"",
        stderr=b"",
        exit_code=0,
        result_text="done",
    )

    class Adapter:
        def __init__(self, config):
            pass

        def prepare(self, prompt):
            pass

        async def start(self):
            pass

        async def events(self):
            if False:
                yield None

        async def collect(self):
            return collected

    monkeypatch.setattr(controller_module, "ClaudeCodeAdapter", Adapter)
    value = Controller.__new__(Controller)
    result = {"usage": {}}
    agent = SimpleNamespace(
        adapter="claude_code",
        model="model",
        max_turns=4,
        effort="medium",
        timeout_seconds=30,
    )
    env = SimpleNamespace(trial_id="trial", agent="agent", stop_candidate=lambda: None)
    tmp_path.mkdir(exist_ok=True)

    await value.run_agent(agent, env, "prompt", result, tmp_path)

    assert result["usage"]["input_tokens"] == 10
    assert result["usage"]["billing_mode"] == "subscription_limits"
    assert result["usage"]["cost_usd"] is None
    assert result["usage"]["cost_micro_usd"] is None


@pytest.mark.asyncio
async def test_agent_startup_hang_is_timed_out_and_stops_candidate(tmp_path, monkeypatch):
    class Adapter:
        instance = None

        def __init__(self, config):
            self.stopped = False
            self.collect_attempted = False
            Adapter.instance = self

        def prepare(self, prompt):
            pass

        async def start(self):
            await asyncio.Event().wait()

        async def stop(self, deadline=None):
            self.stopped = True

        async def collect(self):
            self.collect_attempted = True
            raise AdapterStateError("adapter has not started")

    class Environment:
        trial_id = "trial"
        agent = "candidate"

        def __init__(self):
            self.stopped = False

        def stop_candidate(self):
            self.stopped = True

    monkeypatch.setattr(controller_module, "ClaudeCodeAdapter", Adapter)
    value = Controller.__new__(Controller)
    result = {}
    agent = SimpleNamespace(
        adapter="claude_code",
        model="model",
        max_turns=4,
        effort="medium",
        timeout_seconds=0.01,
    )
    env = Environment()

    completion = await asyncio.wait_for(
        value.run_agent(agent, env, "prompt", result, tmp_path),
        1,
    )

    assert completion is None
    assert env.stopped
    assert Adapter.instance.stopped
    assert Adapter.instance.collect_attempted
    assert result["execution_status"] == "timed_out"
    assert result["timeout_phase"] == "startup"
    assert result["agent_exit_code"] is None
    assert result["usage"]["input_tokens"] is None
    assert (tmp_path / "agent.stdout").read_bytes() == b""
    assert (tmp_path / "agent.stderr").read_bytes() == b""


@pytest.mark.asyncio
async def test_start_and_cleanup_faults_do_not_invent_success_or_skip_persistence(tmp_path, monkeypatch):
    pending = [{"intent": "owned", "kind": "org", "status": "active"}]
    value = controller(tmp_path, pending)
    value.reconcile = lambda trial: (_ for _ in ()).throw(RuntimeError("inventory unavailable"))
    fixture = {"public": {"organization_id": "oid", "target_record_name": "target", "target_asset_key": "asset"}, "target_name": "target", "expected_records": {}, "baseline_records": {}}
    monkeypatch.setattr(controller_module.hive, "provision", lambda *args: fixture)
    monkeypatch.setattr(controller_module.keys, "create", lambda *args: "key")

    class BrokenEnvironment:
        def __init__(self, cfg, trial_id, root, journal):
            self.work = root / "work"
            self.work.mkdir()

        def start(self, *args, **kwargs):
            raise RuntimeError("container start failed")

        def stop_candidate(self):
            raise RuntimeError("container stop failed")

    monkeypatch.setattr(controller_module, "DockerEnvironment", BrokenEnvironment)

    result = await value.trial("campaign", "hive-preserve-update", "codex")

    assert result["grade"] == "inconclusive"
    assert result["cleanup_status"] == "failed"
    assert "container start failed" in result["error"]
    assert {error["stage"] for error in result["cleanup_errors"]} >= {
        "stop_candidate",
        "reconcile",
    }
    assert value.journal.finished
    persisted = json.loads(
        (tmp_path / "trials" / result["trial_id"] / "result.json").read_text()
    )
    assert persisted["grade"] == "inconclusive"


@pytest.mark.asyncio
async def test_verifier_fault_after_execution_stays_inconclusive_and_cleans(tmp_path, monkeypatch):
    value = controller(tmp_path)
    value.reconcile = lambda trial: {"unresolved": [], "errors": []}
    fixture = {"public": {"organization_id": "oid", "target_record_name": "target", "target_asset_key": "asset"}, "target_name": "target", "expected_records": {}, "baseline_records": {}}
    monkeypatch.setattr(controller_module.hive, "provision", lambda *args: fixture)
    monkeypatch.setattr(controller_module.hive, "snapshot", lambda *args: (_ for _ in ()).throw(RuntimeError("snapshot failed")))
    monkeypatch.setattr(controller_module.keys, "create", lambda *args: "key")

    class Environment:
        def __init__(self, cfg, trial_id, root, journal):
            self.trial_id = trial_id
            self.agent = "agent"
            self.worker = "worker"
            self.work = root / "work"
            self.socket_dir = root / "socket"
            self.work.mkdir()
            self.socket_dir.mkdir()

        def start(self, *args, **kwargs):
            pass

        def stop_candidate(self):
            pass

    class FakeBroker:
        count = 1

        def __init__(self, *args, **kwargs):
            self.evidence = args[2]

        async def start(self):
            self.evidence.write_text(
                json.dumps({"type": "command_request", "id": "one"})
                + "\n"
                + json.dumps(
                    {
                        "type": "command_end",
                        "id": "one",
                        "code": 0,
                        "bytes": 9,
                        "seconds": 0.125,
                    }
                )
                + "\n"
            )

        async def close(self):
            pass

    async def reference(*args, **kwargs):
        return "target updated"

    async def parity(*args, **kwargs):
        return {"passed": True}

    monkeypatch.setattr(controller_module, "DockerEnvironment", Environment)
    monkeypatch.setattr(controller_module, "Broker", FakeBroker)
    monkeypatch.setattr(parity_module, "check_parity", parity)
    value.reference = reference

    result = await value.trial(
        "campaign", "hive-preserve-update", "codex", reference=True
    )

    assert result["execution_status"] == "completed", result
    assert result["grade"] == "inconclusive"
    assert result["evidence_complete"] is False
    assert result["cleanup_status"] == "clean"
    assert "snapshot failed" in result["error"]
    assert result["usage"]["output_bytes"] == 9
    assert result["usage"]["cli_seconds"] == 0.125
    assert result["usage"]["cli_failed_commands"] == 0
    assert result["usage"]["rejected_commands"] == 0


@pytest.mark.asyncio
async def test_bad_hive_reference_is_a_named_noop(tmp_path, monkeypatch):
    value = Controller.__new__(Controller)
    calls = []
    monkeypatch.setattr(controller_module, "atomic_json", lambda *args: calls.append(args))
    fixture = {"target_name": "target", "expected_records": {"target": {}}}
    completion = await value.reference(
        "hive-preserve-update", fixture, SimpleNamespace(work=tmp_path), bad=True
    )
    assert "target" in completion
    assert calls == []


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        ({"execution_status": "completed", "grade": "fail", "cleanup_status": "clean"}, 1),
        ({"execution_status": "failed", "grade": "inconclusive", "cleanup_status": "clean"}, 3),
        ({"execution_status": "completed", "grade": "pass", "cleanup_status": "failed"}, 4),
    ],
)
def test_run_command_exit_codes_reflect_trial_outcome(monkeypatch, result, expected):
    class Journal:
        def exclusive(self):
            return nullcontext()

        def resources(self):
            return []

    class FakeController:
        journal = Journal()

        def __init__(self, config):
            pass

        async def trial(self, *args, **kwargs):
            return {"trial_id": "trial", "error": None, **result}

        def report(self, campaign):
            return Path("/tmp/report")

    monkeypatch.setattr(cli_module, "load", lambda path: object())
    monkeypatch.setattr(cli_module, "Controller", FakeController)
    invocation = CliRunner().invoke(
        cli_module.main,
        ["run", "--campaign", "campaign", "--scenario", "hive-preserve-update"],
    )
    assert invocation.exit_code == expected, invocation.output


def test_reconcile_does_not_delete_unknown_network_with_foreign_label(tmp_path, monkeypatch):
    resource = {
        "intent": "intent",
        "trial": "owned-trial",
        "kind": "docker_network",
        "name": "colliding-network",
        "resource_id": None,
        "handle": {"name": "colliding-network"},
    }

    class Journal:
        failures = []

        def resources(self, trial=None):
            return [resource]

        def cleanup_failed(self, intent, error):
            self.failures.append((intent, error))

        def trials(self):
            return []

    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        assert argv[:3] == ["docker", "network", "inspect"]
        value = [{"Id": "foreign-id", "Labels": {"lc-eval.trial": "foreign-trial"}}]
        return SimpleNamespace(returncode=0, stdout=json.dumps(value).encode(), stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    value = Controller.__new__(Controller)
    value.config = SimpleNamespace(run_data_dir=tmp_path)
    value.journal = Journal()
    result = value.reconcile("owned-trial")

    assert result["unresolved"] == [resource]
    assert "label mismatch" in result["errors"][0]["error"]
    assert len(calls) == 1


def test_cleanup_audit_repairs_historical_result_after_reappeared_org(tmp_path, monkeypatch):
    journal = RealJournal(tmp_path)
    trial = "historical-trial"
    root = journal.create_trial(trial, "campaign", {})
    intent = journal.intent(trial, "org", "lc-eval-owned", {"name": "lc-eval-owned"})
    journal.acquired(intent, "00000000-0000-4000-8000-000000000001")
    journal.cleaned(intent)
    original = {
        "trial_id": trial,
        "cleanup_status": "clean",
        "grade": "pass",
    }
    journal.finish(trial, original)
    (root / "result.json").write_text(json.dumps(original))

    value = Controller.__new__(Controller)
    value.config = SimpleNamespace(run_data_dir=tmp_path)
    value.journal = journal
    value.cli = object()

    class Organizations:
        def cleanup(self, resource):
            journal.cleaned(resource["intent"])

    value.orgs = Organizations()
    monkeypatch.setattr(
        controller_module,
        "exact_owned_org",
        lambda cli, name, oid=None: {"name": name, "oid": oid},
    )

    result = value.reconcile(trial, audit_cleaned=True)

    assert result == {"unresolved": [], "errors": []}
    recovered = journal.trials("campaign")[0]["result"]
    assert recovered["grade"] == "pass"
    assert recovered["cleanup_status"] == "clean"
    assert [event["status"] for event in recovered["cleanup_audit"]] == ["failed", "clean"]
    assert json.loads((root / "result.json").read_text()) == recovered
    journal.close()
