"""Operator interface. Runtime data and credentials stay outside the checkout."""

import asyncio
import json
from pathlib import Path

import click
import yaml

from .config import PROJECT, load, save, init_local, doctor
from .controller import Controller
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


@main.command("run")
@click.option("--config", type=click.Path(path_type=Path), default=DEFAULT_CONFIG)
@click.option("--campaign", required=True)
@click.option(
    "--scenario",
    type=click.Choice(["hive-preserve-update", "search-complete-export", "webhook-production-routing"]),
)
@click.option("--adapter", type=click.Choice(["claude_code", "codex"]), default="claude_code")
@click.option("--seed", type=int, default=42)
@click.option("--reference", is_flag=True)
@click.option("--bad-reference", is_flag=True, help="Run the named negative-calibration reference.")
def run(config, campaign, scenario, adapter, seed, reference, bad_reference):
    reference = reference or bad_reference
    exit_code = 0
    controller = Controller(load(config))
    with controller.journal.exclusive():
        if controller.journal.resources():
            click.echo("Unresolved resources exist; run cleanup first.", err=True)
            raise click.exceptions.Exit(4)
        specs = (
            [{"scenario": scenario, "adapter": adapter, "seed": seed}]
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
def smoke_command(config, campaign):
    from .smoke import smoke

    results = asyncio.run(smoke(load(config), campaign))
    for result in results:
        click.echo(json.dumps({k: result.get(k) for k in ("adapter", "execution_status", "grade", "error")}))
    if any(result.get("grade") != "pass" for result in results):
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
