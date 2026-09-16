"""Sequential trial controller: owned setup, isolated execution, frozen grading, cleanup."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import shutil
import stat
import time
import uuid
from pathlib import Path

import yaml

from .config import PROJECT, atomic_json, sha256
from .journal import Journal
from .models import grade_assertions, safe_id
from .fixtures.local_cli import LocalCLI
from .fixtures.organization import Organizations, exact_owned_org
from .fixtures import hive, keys
from .execution.docker import DockerEnvironment
from .execution.broker import Broker, CONTROLLED_CLI_V1_NOTICE
from .adapters import (
    AdapterStateError,
    ClaudeCodeAdapter,
    ClaudeCodeConfig,
    CodexAdapter,
    CodexConfig,
    UnsupportedAdapterError,
    Usage,
)
from .verifiers import verify_hive, verify_export, verify_routing
from .reporting import build_report, render_html, compare_pair, acceptance_summary


def scenario(name):
    safe_id(name)
    path = PROJECT / "scenarios" / name
    if not path.is_dir():
        raise ValueError("unknown scenario")
    spec = yaml.safe_load((path / "task.yaml").read_text())
    digest = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_file():
            digest.update(str(file.relative_to(path)).encode() + b"\0" + file.read_bytes())
    return path, spec, digest.hexdigest()


def source_tree_digest(path: Path) -> str:
    """Hash Python source names and contents without including runtime artifacts."""

    digest = hashlib.sha256()
    for file in sorted(Path(path).rglob("*.py")):
        if "__pycache__" in file.parts:
            continue
        digest.update(str(file.relative_to(path)).encode() + b"\0" + file.read_bytes())
    return digest.hexdigest()


def prompt_for(path, public):
    prompt = (path / "prompt.md").read_text()
    for key, value in public.items():
        prompt = prompt.replace("{{ " + key + " }}", str(value))
    if "{{" in prompt:
        raise ValueError("unresolved public prompt variables")
    return (
        "Work in /work. The limacharlie executable connects to the trial organization. "
        "Use its help and AI help as needed. Local LimaCharlie documentation is under /docs/docs. "
        "Do not access authentication files or invoke authentication/debug commands. "
        "Only files under /work may be used as CLI input/output.\n\n" + prompt
    )


def freeze(work: Path, path: Path, completion: str | None, max_bytes: int):
    result = {"completion": completion}
    source = work / "export.jsonl"
    if source.exists() or source.is_symlink():
        mode = source.lstat().st_mode
        item = {"path": "/work/export.jsonl", "within_workspace": True}
        if not stat.S_ISREG(mode):
            item["kind"] = "symlink" if stat.S_ISLNK(mode) else "device"
        elif source.stat().st_size > max_bytes:
            item.update(kind="oversized", content=None)
        else:
            with source.open("rb") as f:
                raw = f.read(max_bytes + 1)
            item.update(
                kind="file",
                content=raw.decode("utf-8", errors="replace"),
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        result["export"] = item
    atomic_json(path, result)
    return result


class Controller:
    def __init__(self, config):
        self.config = config
        self.journal = Journal(config.run_data_dir)
        self.cli = LocalCLI(config.lc)
        self.orgs = Organizations(self.cli, self.journal, config.limits.max_orgs)

    def _record_cleanup_audit(self, trial_id, status, evidence):
        row = next((item for item in self.journal.trials() if item["id"] == trial_id), None)
        if row is None or row["result"] is None:
            return
        result = row["result"]
        result["cleanup_status"] = status
        result.setdefault("cleanup_audit", []).append(evidence)
        self.journal.finish(trial_id, result)
        atomic_json(
            self.config.run_data_dir / "trials" / trial_id / "result.json",
            result,
        )

    def _audit_cleaned_orgs(self, trial=None):
        affected = set()
        errors = []
        for resource in self.journal.resources(trial, pending=False):
            if resource["kind"] != "org" or resource["status"] != "cleaned":
                continue
            try:
                observed = exact_owned_org(
                    self.cli,
                    resource["name"],
                    resource["resource_id"] or None,
                )
            except Exception as exc:
                message = f"organization cleanup audit failed closed: {exc}"
                self.journal.cleanup_failed(resource["intent"], message)
                affected.add(resource["trial"])
                errors.append(
                    {"intent": resource["intent"], "trial": resource["trial"], "error": message}
                )
                self._record_cleanup_audit(
                    resource["trial"],
                    "failed",
                    {"status": "failed", "resource": resource["intent"], "reason": message},
                )
                continue
            if observed is not None:
                message = "previously cleaned owned organization is present in exact inventory"
                self.journal.cleanup_failed(resource["intent"], message)
                affected.add(resource["trial"])
                self._record_cleanup_audit(
                    resource["trial"],
                    "failed",
                    {
                        "status": "failed",
                        "resource": resource["intent"],
                        "reason": message,
                        "observed_oid": observed.get("oid"),
                    },
                )
        return affected, errors

    def reconcile(self, trial=None, *, audit_cleaned=False):
        """Reconcile exact ledger resources, including interrupted Docker create calls."""
        import subprocess

        affected, errors = self._audit_cleaned_orgs(trial) if audit_cleaned else (set(), [])
        resources = self.journal.resources(trial)
        order = {
            "local_process": 0,
            "docker_container": 1,
            "docker_network": 2,
            "api_key": 3,
            "org": 4,
        }
        for resource in sorted(resources, key=lambda r: order.get(r["kind"], 2)):
            try:
                kind = resource["kind"]
                if kind == "local_process":
                    from .execution.processes import cleanup as cleanup_process

                    cleanup_process(resource, self.journal)
                elif kind.startswith("docker_"):
                    noun = "container" if kind == "docker_container" else "network"
                    check = subprocess.run(["docker", noun, "inspect", resource["name"]], capture_output=True)
                    if check.returncode == 0:
                        obj = json.loads(check.stdout)[0]
                        if resource["resource_id"] and obj["Id"] != resource["resource_id"]:
                            raise RuntimeError("Docker ownership mismatch")
                        labels = (
                            obj.get("Config", {}).get("Labels", {})
                            if noun == "container"
                            else obj.get("Labels", {})
                        )
                        if noun == "container" and labels.get("lc-eval.trial") != resource["trial"]:
                            raise RuntimeError("Docker trial label mismatch")
                        if (
                            noun == "network"
                            and not resource["resource_id"]
                            and labels.get("lc-eval.trial") != resource["trial"]
                        ):
                            raise RuntimeError("Docker network trial label mismatch")
                        args = (
                            ["docker", "rm", "-f", resource["name"]]
                            if noun == "container"
                            else ["docker", "network", "rm", resource["name"]]
                        )
                        removed = subprocess.run(args, capture_output=True)
                        if removed.returncode:
                            raise RuntimeError("Docker removal failed")
                    elif b"No such" not in check.stderr:
                        raise RuntimeError("Docker inventory unavailable")
                    self.journal.cleaned(resource["intent"])
                elif kind == "api_key":
                    keys.cleanup(self.cli, self.journal, resource)
                elif kind == "org":
                    self.orgs.cleanup(resource)
                    # A confirmed absent owned org proves its keys are revoked too.
                    for child in self.journal.resources(resource["trial"]):
                        if child["kind"] == "api_key" and child["handle"]["oid"] == resource["resource_id"]:
                            self.journal.cleaned(child["intent"])
                else:
                    raise RuntimeError("unsupported owned resource kind")
            except Exception as exc:
                self.journal.cleanup_failed(resource["intent"], str(exc))
                errors.append(
                    {
                        "intent": resource["intent"],
                        "trial": resource["trial"],
                        "error": str(exc),
                    }
                )
        for row in self.journal.trials():
            if trial and row["id"] != trial:
                continue
            auth = self.config.run_data_dir / "trials" / row["id"] / "auth"
            if auth.exists():
                shutil.rmtree(auth)
        unresolved = self.journal.resources(trial)
        for trial_id in affected:
            if (
                not any(resource["trial"] == trial_id for resource in unresolved)
                and not any(error.get("trial") == trial_id for error in errors)
            ):
                self._record_cleanup_audit(
                    trial_id,
                    "clean",
                    {
                        "status": "clean",
                        "reason": "reconciled after exact owner-inventory audit",
                    },
                )
        return {"unresolved": unresolved, "errors": errors}

    async def trial(
        self,
        campaign,
        name,
        adapter_name,
        seed=42,
        repetition=1,
        reference=False,
        bad_reference=False,
    ):
        if adapter_name not in {"claude_code", "codex"}:
            raise UnsupportedAdapterError(
                f"adapter {adapter_name!r} is unsupported by the live controlled CLI profile"
            )
        reference = reference or bad_reference
        reference_adapter = "reference_bad" if bad_reference else "reference"
        path, spec, digest = scenario(name)
        agent = next(a for a in self.config.agents if a.adapter == adapter_name)
        if self.config.limits.budget_mode != "subscription_limits":
            raise ValueError(
                "live controller currently supports explicitly selected subscription_limits only"
            )
        trial_id = safe_id(campaign + "-" + uuid.uuid4().hex[:10])
        manifest = {
            "scenario_id": name,
            "scenario_revision": spec["revision"],
            "scenario_hash": digest,
            "variant_seed": seed,
            "docs_digest": self.config.sources.docs.commit,
            "fixture_recipe_digest": sha256(PROJECT / "src/lc_eval/fixtures/hive.py")
            if name.startswith("hive")
            else source_tree_digest(PROJECT / "src/lc_eval/fixtures"),
            "harness": reference_adapter if reference else adapter_name,
            "model": agent.model,
            "effort": agent.effort,
            "tools_digest": hashlib.sha256(
                (
                    self.config.sources.candidate_image_id
                    + sha256(PROJECT / "src/lc_eval/execution/broker.py")
                    + sha256(PROJECT / "src/lc_eval/execution/shim.py")
                ).encode()
            ).hexdigest(),
            "evaluator_digest": hashlib.sha256(
                b"".join(f.read_bytes() for f in sorted((PROJECT / "src/lc_eval").rglob("*.py")))
            ).hexdigest(),
            "cli_digest": self.config.sources.worker_image_id,
            "permission_profile": keys.PERMISSIONS[name],
            "execution_profile": self.config.profile,
            "limits": {
                **self.config.limits.model_dump(),
                "timeout_seconds": agent.timeout_seconds,
                "max_turns": agent.max_turns,
            },
            "repetition": repetition,
            "billing_mode": "subscription_limits",
        }
        root = self.journal.create_trial(trial_id, campaign, manifest)
        atomic_json(root / "manifest.json", manifest)
        result = {
            "schema_version": 1,
            "trial_id": trial_id,
            "campaign_id": campaign,
            "scenario_id": name,
            "adapter": reference_adapter if reference else adapter_name,
            "seed": seed,
            "manifest": manifest,
            "execution_status": "failed",
            "grade": "inconclusive",
            "cleanup_status": "pending",
            "assertions": [],
            "usage": {},
            "timings": {},
            "evidence_complete": False,
        }
        env = None
        broker = None
        fixture = None
        started = time.monotonic()
        try:
            self.journal.transition(trial_id, "provisioning")
            org = self.orgs.create(trial_id, self.config.lc.location)
            oid = org["oid"]
            atomic_json(root / "org.json", org)
            if name == "hive-preserve-update":
                fixture = hive.provision(self.cli, oid, seed)
            else:
                from .fixtures.scenario_runtime import provision

                fixture = await provision(self.config, self.cli, oid, trial_id, name, seed, root)
            public = fixture["public"]
            atomic_json(root / "fixture.json", {k: v for k, v in fixture.items() if not k.startswith("_")})
            key = keys.create(self.cli, self.journal, trial_id, oid, name)
            env = DockerEnvironment(self.config, trial_id, root, self.journal)
            env.start(oid, key, agent_config=agent)
            for rel in spec["public_files"]:
                shutil.copyfile(path / rel, env.work / Path(rel).name)
            for filename, content in fixture.get("public_files", {}).items():
                safe_id(filename)
                (env.work / filename).write_text(content)
            prompt = prompt_for(path, public) + "\n\n" + CONTROLLED_CLI_V1_NOTICE
            atomic_json(root / "public-spec.json", {"prompt": prompt, "public": public})
            broker = Broker(
                env.worker,
                env.socket_dir,
                root / "commands.jsonl",
                max_seconds=self.config.limits.max_command_seconds,
                max_output=self.config.limits.max_command_output,
                redactions=(key,),
                allowed_oids=(oid,),
                workspace=env.work,
            )
            await broker.start()
            if reference and not bad_reference and name == "hive-preserve-update":
                from .execution.parity import check_parity

                parity = await check_parity(env, root)
                if not parity["passed"]:
                    raise RuntimeError("controlled CLI parity or isolation check failed")
            self.journal.transition(trial_id, "ready")
            self.journal.transition(trial_id, "running")
            active = time.monotonic()
            if reference:
                completion = await self.reference(name, fixture, env, bad=bad_reference)
                result["execution_status"] = "completed"
            else:
                completion = await self.run_agent(agent, env, prompt, result, root)
            result["timings"]["active_seconds"] = time.monotonic() - active
            result["usage"]["cli_invocations"] = broker.count
            self.journal.transition(trial_id, "stopping")
            env.stop_candidate()
            await broker.close()
            broker = None
            frozen = freeze(env.work, root / "frozen.json", completion, self.config.limits.max_fixture_bytes)
            self.journal.transition(trial_id, "settling")
            self.journal.transition(trial_id, "verifying")
            verify_started = time.monotonic()
            if name == "hive-preserve-update":
                evidence = {"observed_records": hive.snapshot(self.cli, oid)}
                assertions = verify_hive(manifest, fixture, frozen, evidence)
            else:
                from .fixtures.scenario_runtime import collect

                evidence = await collect(self.config, self.cli, oid, name, fixture)
                verifier = verify_export if name == "search-complete-export" else verify_routing
                assertions = verifier(manifest, fixture, frozen, evidence)
            atomic_json(root / "evidence.json", evidence)
            atomic_json(root / "assertions.json", assertions)
            result.update(assertions=assertions, grade=grade_assertions(assertions), evidence_complete=True)
            result["timings"]["verification_seconds"] = time.monotonic() - verify_started
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            cleanup_errors = []

            def cleanup_error(stage, exc):
                cleanup_errors.append(
                    {"stage": stage, "error": f"{type(exc).__name__}: {exc}"}
                )

            if env:
                try:
                    env.stop_candidate()
                except Exception as exc:
                    cleanup_error("stop_candidate", exc)
            if broker:
                try:
                    await broker.close()
                except Exception as exc:
                    cleanup_error("close_broker", exc)
            if fixture and fixture.get("_runtime"):
                try:
                    await fixture["_runtime"].stop()
                except Exception as exc:
                    cleanup_error("stop_fixture_runtime", exc)
            try:
                self.journal.transition(trial_id, "cleaning")
            except Exception as exc:
                cleanup_error("transition_cleaning", exc)
            try:
                cleanup = self.reconcile(trial_id)
            except Exception as exc:
                cleanup_error("reconcile", exc)
                try:
                    unresolved = self.journal.resources(trial_id)
                except Exception as inventory_exc:
                    cleanup_error("inventory_after_reconcile", inventory_exc)
                    unresolved = [{"status": "unknown"}]
                cleanup = {"unresolved": unresolved, "errors": []}
            cleanup_errors.extend(cleanup.get("errors", []))
            result["cleanup_status"] = (
                "clean" if not cleanup.get("unresolved") and not cleanup_errors else "failed"
            )
            result["cleanup_errors"] = cleanup_errors
            result["timings"]["total_seconds"] = time.monotonic() - started

            # Each persistence operation is independent so one local failure cannot
            # prevent the journal from recording the outcome or reaching terminal state.
            finalization_failed = False
            try:
                atomic_json(root / "result.json", result)
            except Exception as exc:
                cleanup_error("write_result", exc)
                finalization_failed = True
            try:
                self.journal.finish(trial_id, result)
            except Exception as exc:
                cleanup_error("journal_finish", exc)
                finalization_failed = True
            try:
                self.journal.transition(trial_id, "finished")
            except Exception as exc:
                cleanup_error("transition_finished", exc)
                finalization_failed = True

            if finalization_failed:
                result["cleanup_errors"] = cleanup_errors
                result["finalization_failed"] = True
                with contextlib.suppress(Exception):
                    atomic_json(root / "result.json", result)
                with contextlib.suppress(Exception):
                    self.journal.finish(trial_id, result)
        return result

    async def run_agent(self, agent, env, prompt, result, root):
        common = dict(
            trial_id=env.trial_id,
            model=agent.model,
            workdir=Path("/"),
            executable=agent.adapter == "codex" and "codex" or "claude",
            command_prefix=("docker", "exec", "-i", "--workdir", "/work", env.agent),
            environment={
                k: v for k, v in os.environ.items() if k in ("PATH", "DOCKER_HOST", "XDG_RUNTIME_DIR")
            },
        )
        adapter = (
            ClaudeCodeAdapter(
                ClaudeCodeConfig(
                    **common, auth_mode="subscription", max_turns=agent.max_turns, effort=agent.effort
                )
            )
            if agent.adapter == "claude_code"
            else CodexAdapter(
                CodexConfig(
                    **common,
                    auth_mode="subscription",
                    max_tool_calls=80,
                    config_overrides=(f'model_reasoning_effort="{agent.effort}"',),
                )
            )
        )
        adapter.prepare(prompt)
        started = False

        async def consume():
            nonlocal started
            await adapter.start()
            started = True
            async for event in adapter.events():
                if event.event_type == "limit_reached":
                    await adapter.stop(time.monotonic() + 10)
            return await adapter.collect()

        timed_out = False
        try:
            collected = await asyncio.wait_for(consume(), agent.timeout_seconds)
        except asyncio.TimeoutError:
            timed_out = True
            await adapter.stop(time.monotonic() + 10)
            env.stop_candidate()
            try:
                collected = await asyncio.wait_for(adapter.collect(), 10)
            except (asyncio.TimeoutError, AdapterStateError):
                collected = None
        # Private transcript only; never embed it in distributable reports.
        for filename, raw in [
            ("agent.stdout", collected.stdout if collected is not None else b""),
            ("agent.stderr", collected.stderr if collected is not None else b""),
        ]:
            file = root / filename
            file.write_bytes(raw)
            file.chmod(0o600)
        usage = collected.usage if collected is not None else Usage()
        result["usage"] = {
            **usage.as_dict(),
            "cost_usd": None,
            "cost_micro_usd": None,
            "billing_mode": "subscription_limits",
        }
        result["execution_status"] = (
            "timed_out"
            if timed_out
            else "completed"
            if collected is not None and collected.exit_code == 0
            else "failed"
        )
        result["agent_exit_code"] = collected.exit_code if collected is not None else None
        if timed_out:
            result["timeout_phase"] = "execution" if started else "startup"
        return collected.result_text if collected is not None else None

    async def reference(self, name, fixture, env, *, bad=False):
        from .execution.docker import run

        if name == "hive-preserve-update":
            target = fixture["target_name"]
            if bad:
                return target + " owner update intentionally omitted"
            (env.work / "reference.json").write_text(json.dumps(fixture["expected_records"][target]))
            await asyncio.to_thread(
                run,
                [
                    "docker",
                    "exec",
                    env.agent,
                    "limacharlie",
                    "lookup",
                    "set",
                    "--key",
                    target,
                    "--input-file",
                    "/work/reference.json",
                ],
            )
            return target + " owner updated"
        from .fixtures.scenario_runtime import reference

        return await reference(name, fixture, env, bad=bad)

    def report(self, campaign):
        trials = [r["result"] for r in self.journal.trials(campaign) if r["result"]]
        pairs = []
        for current in trials:
            if current["manifest"].get("repetition") == 2:
                first = next(
                    (
                        t
                        for t in trials
                        if t["adapter"] == current["adapter"]
                        and t["scenario_id"] == current["scenario_id"]
                        and t["manifest"].get("repetition") == 1
                    ),
                    None,
                )
                if first:
                    pairs.append(compare_pair(first, current))
        compatible_aa_harnesses = {
            pair["compatibility"]["fields"]["harness"]["left"]
            for pair in pairs
            if pair["compatibility"]["compatible"]
            and pair["compatibility"]["fields"]["scenario_id"]["left"]
            == "hive-preserve-update"
        }
        evidence = {
            "unresolved_resource_count": len(self.journal.resources()),
            "paired_aa_complete": {"claude_code", "codex"} <= compatible_aa_harnesses,
        }
        proof = self.config.run_data_dir / "proof.json"
        if proof.exists():
            evidence.update(json.loads(proof.read_text()))
        report = build_report(
            trials,
            campaign={"id": campaign, "billing_mode": "subscription_limits"},
            comparisons=pairs,
            acceptance=acceptance_summary(trials, evidence),
        )
        dest = self.config.run_data_dir / "reports" / campaign
        dest.mkdir(parents=True, exist_ok=True)
        atomic_json(dest / "report.json", report)
        (dest / "report.html").write_text(render_html(report))
        return dest
