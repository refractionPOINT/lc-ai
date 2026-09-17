"""Operator interface. Runtime data and credentials stay outside the checkout."""

import asyncio
import json
from pathlib import Path

import click
import yaml

from .config import PROJECT, load, save, init_local, doctor, source_pin
from .controller import Controller
from .registry import SCENARIOS
from .execution.docker import build_images
from .acceptance import validate_references, write_acceptance

DEFAULT_CONFIG = Path.home() / ".local/share/lc-eval/config.json"


@click.group()
def main():
    """Run and compare LimaCharlie CLI agent evaluations."""


@main.command("init-local")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option(
    "--subscription",
    is_flag=True,
    help="Use authenticated subscriptions with time/tool bounds, no dollar claim.",
)
def initialize(config, subscription):
    value = init_local(config.parent, subscription=subscription)
    save(config, value)
    click.echo(str(config))


@main.command("doctor")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--offline", is_flag=True)
def diagnose(config, offline):
    result = doctor(load(config), live=not offline)
    click.echo(json.dumps(result, indent=2, default=str))


@main.command("build")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
def build(config):
    cfg = load(config)
    click.echo(json.dumps(build_images(cfg), indent=2))
    save(config, cfg)


@main.command("build-ai-sessions")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--source", type=click.Path(path_type=Path, exists=True), default=PROJECT.parent.parent / "ai-sessions")
def build_ai_sessions(config, source):
    """Pin and build the native runner; add a subscription agent from Claude's profile."""
    from .execution.workspace_build import build_workspace_image
    from .models import AISessionsImage
    cfg = load(config)
    claude = next((a for a in cfg.agents if a.adapter == "claude_code"), None)
    existing = next((a for a in cfg.agents if a.adapter == "ai_sessions"), None)
    template = existing or claude
    if not template or template.auth_mode != "subscription" or not template.auth_file:
        raise click.ClickException("configure a Claude subscription profile before building ai_sessions")
    pin, catalog = source_pin(source), source_pin(PROJECT.parent)
    built = build_workspace_image(cfg, pin.path, pin.commit, catalog.commit)
    cfg.ai_sessions = AISessionsImage(source=pin, lc_ai=catalog, image=built["image_tag"],
                                     image_id=built["image_id"], build_manifest=built)
    import sys
    agent = template.model_copy(update={"adapter": "ai_sessions", "executable": Path(sys.executable),
                                      "version": "session-runner@" + pin.commit})
    cfg.agents = [a for a in cfg.agents if a.adapter != "ai_sessions"] + [agent]
    save(config, cfg)
    click.echo(json.dumps(built, indent=2))


@main.command("run")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign", required=True)
@click.option(
    "--scenario",
    type=click.Choice(SCENARIOS),
)
@click.option("--adapter", type=click.Choice(["claude_code", "codex", "ai_sessions"]), default="claude_code")
@click.option("--context", "context_mode", type=click.Choice(["bare", "lc_ai", "legacy"]), default=None)
@click.option("--seed", type=int, default=42)
@click.option("--repetition", type=click.IntRange(min=1), default=None)
@click.option("--reference", is_flag=True)
@click.option("--bad-reference", is_flag=True, help="Run the named negative-calibration reference.")
def run(config, campaign, scenario, adapter, context_mode, seed, repetition, reference, bad_reference):
    if scenario is None and repetition is not None:
        raise click.UsageError("--repetition requires --scenario")
    if scenario is None and adapter == "ai_sessions":
        raise click.UsageError("ai_sessions currently requires --scenario; the default suite specifies Claude Code and Codex")
    reference = reference or bad_reference
    exit_code = 0
    cfg = load(config)
    if context_mode is not None:
        cfg.agents = [a.model_copy(update={"context_mode": context_mode}) for a in cfg.agents]
    controller = Controller(cfg)
    with controller.journal.exclusive():
        if controller.journal.resources():
            click.echo("Unresolved resources exist; run cleanup first.", err=True)
            raise click.exceptions.Exit(4)
        specs = (
            [
                {
                    "scenario": scenario,
                    "adapter": adapter,
                    "seed": seed,
                    "repetition": repetition or 1,
                }
            ]
            if scenario
            else yaml.safe_load((PROJECT / "suites/initial-loop.yaml").read_text())["trials"]
        )
        for spec in specs:
            reference_name = "reference_bad" if bad_reference else "reference"
            click.echo(f"Starting {spec['scenario']} / {reference_name if reference else spec['adapter']}")
            result = asyncio.run(
                controller.trial(
                    campaign,
                    spec["scenario"],
                    spec["adapter"],
                    spec["seed"],
                    spec.get("repetition", 1),
                    reference=reference,
                    bad_reference=bad_reference,
                )
            )
            click.echo(
                json.dumps(
                    {
                        k: result.get(k)
                        for k in ("trial_id", "execution_status", "grade", "cleanup_status", "error")
                    }
                )
            )
            controller.report(campaign)
            if result["cleanup_status"] != "clean":
                raise click.exceptions.Exit(4)
            if result.get("finalization_failed") or result["grade"] == "inconclusive" or result["execution_status"] != "completed":
                exit_code = max(exit_code, 3)
            elif result["grade"] == "fail":
                exit_code = max(exit_code, 1)
    click.echo(str(controller.report(campaign)))
    if exit_code:
        raise click.exceptions.Exit(exit_code)


@main.command("smoke")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign", default="harness-smoke")
@click.option("--adapter", type=click.Choice(["claude_code", "codex", "ai_sessions"]))
def smoke_command(config, campaign, adapter):
    from .smoke import smoke

    cfg = load(config)
    if adapter:
        cfg.agents = [a for a in cfg.agents if a.adapter == adapter]
        if not cfg.agents:
            raise click.ClickException("requested adapter is not configured")
    results = asyncio.run(smoke(cfg, campaign))
    for result in results:
        click.echo(json.dumps({k: result.get(k) for k in ("adapter", "execution_status", "grade", "error")}))
    if any(result.get("grade") != "pass" for result in results):
        raise click.exceptions.Exit(1)


@main.command("context-probe")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign", required=True)
@click.option("--adapter", type=click.Choice(["claude_code", "codex", "ai_sessions"]), required=True)
@click.option("--context", "context_mode", type=click.Choice(["bare", "lc_ai"]), required=True)
def context_probe_command(config, campaign, adapter, context_mode):
    """Probe native skill discovery without creating a LimaCharlie organization."""
    from .context_probe import probe

    result = asyncio.run(probe(load(config), campaign, adapter, context_mode))
    click.echo(json.dumps({
        key: result.get(key)
        for key in ("trial_id", "adapter", "context_mode", "execution_status", "grade", "cleanup_status", "error")
        if result.get(key) is not None
    }))
    if result.get("cleanup_status") != "clean":
        raise click.exceptions.Exit(4)
    if result.get("execution_status") != "completed":
        raise click.exceptions.Exit(3)
    if result.get("grade") != "pass":
        raise click.exceptions.Exit(1)


@main.command("validate-suite")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign")
def validate_suite(config, campaign):
    result = validate_references(load(config).run_data_dir, campaign)
    click.echo(json.dumps(result, indent=2))
    if not result["reference_validation_passed"]:
        raise click.exceptions.Exit(1)


@main.command("acceptance")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign", required=True)
def acceptance_command(config, campaign):
    controller = Controller(load(config))
    report_dir = controller.report(campaign)
    destination = write_acceptance(report_dir / "report.json")
    click.echo(str(destination))
    report_data = json.loads((report_dir / "report.json").read_text())
    if (report_data.get("acceptance") or {}).get("status") != "pass":
        raise click.exceptions.Exit(1)


@main.command("fault-drill")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign", default="crash-drill")
def crash_drill_command(config, campaign):
    from .crash_drill import run_crash_drill

    cfg = load(config)
    controller = Controller(cfg)
    with controller.journal.exclusive():
        if controller.journal.resources():
            click.echo("Unresolved resources exist; run cleanup first.", err=True)
            raise click.exceptions.Exit(4)
        result = run_crash_drill(config, campaign)
    click.echo(json.dumps({k: result.get(k) for k in ("trial_id", "execution_status", "cleanup_status", "interruption_recovery_passed", "error")}))
    if not result.get("interruption_recovery_passed"):
        raise click.exceptions.Exit(4 if result.get("cleanup_status") != "clean" else 3)


@main.command("cleanup")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--trial")
def cleanup(config, trial):
    controller = Controller(load(config))
    with controller.journal.exclusive():
        result = controller.reconcile(trial, audit_cleaned=True)
    click.echo(json.dumps({"remaining_resources": len(result["unresolved"]), "errors": result["errors"]}))
    if result["unresolved"] or result["errors"]:
        click.echo("Cleanup remains unresolved.", err=True)
        raise click.exceptions.Exit(4)


@main.command("report")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign", required=True)
def report(config, campaign):
    click.echo(str(Controller(load(config)).report(campaign)))


@main.command("status")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
def status(config):
    c = Controller(load(config))
    click.echo(
        json.dumps(
            {
                "trials": [{k: r[k] for k in ("id", "campaign", "state")} for r in c.journal.trials()],
                "pending_resources": len(c.journal.resources()),
            },
            indent=2,
        )
    )
