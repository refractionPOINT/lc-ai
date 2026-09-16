"""Non-secret local configuration and immutable source discovery."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path

import yaml

from .models import AgentConfig, LCConfig, RunConfig, SourcePin, Sources

PROJECT = Path(__file__).resolve().parents[2]
REPO = PROJECT.parent


def sha256(path: Path) -> str:
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def capture(argv: list[str], timeout: float = 30) -> str:
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"{Path(argv[0]).name} command failed (exit {p.returncode})")
    return p.stdout.strip()


def source_pin(path: Path) -> SourcePin:
    return SourcePin(path=path.resolve(), commit=capture(["git", "-C", str(path), "rev-parse", "HEAD"]),
                     dirty=bool(capture(["git", "-C", str(path), "status", "--porcelain"])))


def atomic_json(path: Path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(path.name + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(value, f, indent=2, default=str, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def load(path: Path) -> RunConfig:
    config = RunConfig.model_validate(yaml.safe_load(Path(path).read_text()))
    data = config.run_data_dir.resolve()
    if data == REPO or REPO in data.parents:
        raise ValueError("run_data_dir must be outside the source repository")
    return config


def save(path: Path, config: RunConfig):
    atomic_json(path, config.model_dump(mode="json"))  # JSON is a YAML subset.


def init_local(run_data: Path, subscription: bool = False) -> RunConfig:
    executable = shutil.which("limacharlie")
    if not executable:
        raise RuntimeError("authenticated local limacharlie executable is missing")
    agents = []
    for name, adapter in (("claude", "claude_code"), ("codex", "codex")):
        exe = shutil.which(name)
        model = None
        auth = None
        if name == "codex":
            cfg = Path.home()/".codex/config.toml"
            if cfg.exists():
                model = tomllib.loads(cfg.read_text()).get("model")
            auth = Path.home()/".codex/auth.json"
        else:
            cfg = Path.home()/".claude/settings.json"
            if cfg.exists():
                model = json.loads(cfg.read_text()).get("model")
            model = model or "sonnet"
            auth = Path.home()/".claude/.credentials.json"
        agents.append(AgentConfig(adapter=adapter, executable=Path(exe) if exe else None,
                                  version=capture([exe, "--version"]) if exe else "missing",
                                  model=model, auth_mode="subscription" if subscription else "unresolved",
                                  auth_file=auth if auth.exists() else None))
    config = RunConfig(run_data_dir=run_data.resolve(), agents=agents,
                       sources=Sources(cli=source_pin(REPO.parent/"python-limacharlie"),
                                       docs=source_pin(REPO.parent/"documentation")),
                       lc=LCConfig(executable=Path(executable), executable_sha256=sha256(Path(executable)),
                                   version=capture([executable, "--version"])))
    if subscription:
        config.limits.budget_mode = "subscription_limits"
    return config


def doctor(config: RunConfig, live: bool = False) -> dict:
    checks = []
    def add(name, fn):
        try:
            detail = fn()
            checks.append({"name": name, "ok": True, "detail": detail})
        except Exception as exc:
            checks.append({"name": name, "ok": False, "detail": str(exc)})
    def verify_cli():
        if sha256(config.lc.executable) != config.lc.executable_sha256:
            raise ValueError("trusted local CLI changed; regenerate configuration deliberately")
        return config.lc.version
    add("local_cli", verify_cli)
    add("docker", lambda: capture(["docker", "version", "--format", "{{.Server.Version}}"] ))
    for name, pin in (("cli", config.sources.cli), ("docs", config.sources.docs)):
        def verify(pin=pin):
            if pin.dirty:
                raise ValueError("source pin was dirty; commit or explicitly snapshot before building")
            if source_pin(pin.path).commit != pin.commit:
                raise ValueError("source HEAD changed; use configured commit archives")
            return pin.commit
        add("source_"+name, verify)
    for agent in config.agents:
        def verify(agent=agent):
            if not agent.executable or not agent.executable.exists():
                raise ValueError("harness executable missing")
            if not agent.model:
                raise ValueError("configure model explicitly")
            if live and agent.auth_mode == "subscription" and not agent.auth_file:
                raise ValueError("subscription auth file missing; run the harness login command")
            if live and agent.auth_mode == "unresolved":
                raise ValueError("model authentication mode unresolved")
            return {"version": agent.version, "model": agent.model, "auth_mode": agent.auth_mode}
        add("agent_"+agent.adapter, verify)
    if any(a.adapter == "ai_sessions" for a in config.agents):
        def verify_runner():
            from .execution.docker import image_id
            if not config.ai_sessions:
                raise ValueError("build-ai-sessions must pin the native runner image first")
            if image_id(config.ai_sessions.image) != config.ai_sessions.image_id:
                raise ValueError("ai_sessions image tag no longer matches its configured digest")
            if config.ai_sessions.build_manifest.get("base_image_id") != config.sources.candidate_image_id:
                raise ValueError("base candidate image changed; rebuild ai_sessions deliberately")
            for agent in config.agents:
                if agent.adapter == "ai_sessions" and agent.auth_mode != "subscription":
                    raise ValueError("ai_sessions currently requires Claude subscription authentication")
            return {"image_id": config.ai_sessions.image_id, "source": config.ai_sessions.source.commit}
        add("ai_sessions_image", verify_runner)
    if live:
        add("lc_auth", lambda: bool(capture([str(config.lc.executable), "auth", "test"])))
        if config.limits.budget_mode == "hard_usd":
            add("budget", lambda: (_ for _ in ()).throw(ValueError("API gateway must be configured for hard USD mode")))
    result = {"schema_version": 1, "mode": "live" if live else "offline", "ok": all(c["ok"] for c in checks), "checks": checks}
    atomic_json(config.run_data_dir/"preflight.json", result)
    return result
