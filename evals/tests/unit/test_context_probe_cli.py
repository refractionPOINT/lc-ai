import json

from click.testing import CliRunner

from lc_eval import cli


def test_context_probe_cli_requires_explicit_context():
    result = CliRunner().invoke(cli.main, [
        "context-probe", "--campaign", "probe", "--adapter", "codex",
    ])
    assert result.exit_code == 2
    assert "--context" in result.output


def test_context_probe_cli_prints_safe_summary_and_propagates_failure(monkeypatch):
    monkeypatch.setattr(cli, "load", lambda path: object())

    async def fake_probe(config, campaign, adapter, context_mode):
        return {
            "trial_id": "probe-123", "adapter": adapter, "context_mode": context_mode,
            "execution_status": "completed", "grade": "fail", "cleanup_status": "clean",
            "probe_evidence": {"private_phrase": "must-not-print"},
        }

    import lc_eval.context_probe
    monkeypatch.setattr(lc_eval.context_probe, "probe", fake_probe)
    result = CliRunner().invoke(cli.main, [
        "context-probe", "--config", "/tmp/config.json", "--campaign", "probe",
        "--adapter", "codex", "--context", "bare",
    ])
    assert result.exit_code == 1
    value = json.loads(result.output)
    assert value == {
        "trial_id": "probe-123", "adapter": "codex", "context_mode": "bare",
        "execution_status": "completed", "grade": "fail", "cleanup_status": "clean",
    }
    assert "must-not-print" not in result.output


def test_context_probe_cli_prioritizes_cleanup_failure(monkeypatch):
    monkeypatch.setattr(cli, "load", lambda path: object())

    async def fake_probe(*args):
        return {
            "trial_id": "probe-123", "adapter": "ai_sessions", "context_mode": "lc_ai",
            "execution_status": "failed", "grade": "inconclusive", "cleanup_status": "failed",
        }

    import lc_eval.context_probe
    monkeypatch.setattr(lc_eval.context_probe, "probe", fake_probe)
    result = CliRunner().invoke(cli.main, [
        "context-probe", "--campaign", "probe", "--adapter", "ai_sessions",
        "--context", "lc_ai",
    ])
    assert result.exit_code == 4
