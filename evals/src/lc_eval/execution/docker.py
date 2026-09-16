"""Local Docker topology and content-addressed candidate builds."""
from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

from ..config import PROJECT, atomic_json, sha256
from ..models import AgentConfig, RunConfig


def run(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=kwargs.pop("timeout", 120), **kwargs)
    if result.returncode:
        raise RuntimeError(f"{argv[0]} {argv[1]} failed: {result.stderr[-2000:]}")
    return result.stdout.strip()


def image_id(image):
    return run(["docker", "image", "inspect", "--format", "{{.Id}}", image])


def build_image(dockerfile: Path, tag: str, context: Path, build_key: str) -> None:
    """Build and verify a tagged image, tolerating a post-export BuildKit failure."""
    existing = subprocess.run(
        [
            "docker", "image", "inspect", "--format",
            '{{index .Config.Labels "lc-eval.build-key"}}', tag,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if existing.returncode == 0 and existing.stdout.strip() == build_key:
        return
    argv = [
        "docker", "build", "--provenance=false", "--label", f"lc-eval.build-key={build_key}",
        "-f", str(dockerfile), "-t", tag, str(context),
    ]
    try:
        run(argv, timeout=900)
        return
    except RuntimeError:
        # Some Docker/BuildKit hosts report a telemetry failure after naming and
        # unpacking the image. Accept only the exact image labeled by this build.
        observed = run([
            "docker", "image", "inspect", "--format",
            '{{index .Config.Labels "lc-eval.build-key"}}', tag,
        ])
        if observed != build_key:
            raise


def _build_key(*values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def immutable_image_reference(image: str) -> str:
    """Resolve a pulled image tag to a registry digest suitable for ``FROM``."""
    raw = run(["docker", "image", "inspect", "--format", "{{json .RepoDigests}}", image])
    digests = json.loads(raw)
    if not isinstance(digests, list) or not digests or not all(isinstance(item, str) for item in digests):
        raise RuntimeError(f"image {image!r} has no repository digest")
    preferred_name = image.split(":", 1)[0]
    exact = sorted(item for item in digests if item.split("@", 1)[0] == preferred_name)
    matching = exact or sorted(item for item in digests if item.split("@", 1)[0].endswith("/" + preferred_name))
    return (matching or sorted(digests))[0]


def resolve_codex_native(executable: Path) -> Path:
    """Resolve the platform Codex binary behind npm, Volta, or direct installs."""
    executable = executable.expanduser()
    launchers = [executable]
    resolved = executable.resolve()
    if resolved != executable:
        launchers.append(resolved)
    if resolved.name == "volta-shim":
        volta = resolved.with_name("volta")
        if volta.is_file():
            result = subprocess.run(
                [str(volta), "which", executable.name], capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                launchers.append(Path(result.stdout.strip()))

    patterns = (
        "node_modules/@openai/codex-linux-*/vendor/*/codex/codex",
        "node_modules/@openai/codex-linux-*/vendor/*/bin/codex",
        "lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-*/vendor/*/codex/codex",
        "lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-*/vendor/*/bin/codex",
        "vendor/*/codex/codex",
        "vendor/*/bin/codex",
    )
    candidates: set[Path] = set()
    for launcher in launchers:
        if launcher.is_file() and launcher.resolve().name != "volta-shim":
            try:
                with launcher.open("rb") as stream:
                    if stream.read(4) == b"\x7fELF":
                        candidates.add(launcher.resolve())
            except OSError:
                pass
        for root in (launcher.parent, launcher.parent.parent):
            for pattern in patterns:
                candidates.update(path.resolve() for path in root.glob(pattern) if path.is_file())
    if len(candidates) != 1:
        rendered = ", ".join(str(path) for path in sorted(candidates)) or "none"
        raise RuntimeError(f"cannot uniquely resolve installed Codex native executable: {rendered}")
    return candidates.pop()


def extract_archive(tar, destination):
    """Python 3.11.2-compatible extraction of regular git archive entries only."""
    for member in tar.getmembers():
        target = (destination/member.name).resolve()
        if destination.resolve() not in target.parents and target != destination.resolve():
            raise ValueError("archive path escapes destination")
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
        elif member.isfile():
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(member.mode & 0o777)
        else:
            raise ValueError("archive contains unsupported links or devices")


def build_images(config: RunConfig) -> dict:
    root = config.run_data_dir/"build"/config.sources.cli.commit[:12]
    root.mkdir(parents=True, exist_ok=True)
    src = root/"source"
    archive = root/"source.tar"
    if not archive.exists():
        with archive.open("wb") as f:
            subprocess.run(["git", "-C", str(config.sources.cli.path), "archive", config.sources.cli.commit],
                           stdout=f, check=True)
    if not (src/"pyproject.toml").exists():
        src.mkdir(exist_ok=True)
        with tarfile.open(archive) as tar:
            extract_archive(tar, src)
    run(["docker", "pull", "python:3.11-slim"], timeout=300)
    base = immutable_image_reference("python:3.11-slim")
    base_id = image_id("python:3.11-slim")
    worker_tag = "lc-eval-worker:"+config.sources.cli.commit[:12]
    (root/"Dockerfile.worker").write_text(f"""FROM {base}
COPY source /src
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0+eval.{config.sources.cli.commit[:12]}
RUN pip install --no-cache-dir /src && rm -rf /src
WORKDIR /work
CMD ["sleep", "infinity"]
""")
    worker_key = _build_key(base, sha256(archive), (root/"Dockerfile.worker").read_text())
    build_image(root/"Dockerfile.worker", worker_tag, root, worker_key)
    shutil.copyfile(PROJECT/"src/lc_eval/execution/egress.py", root/"egress.py")
    shutil.copyfile(PROJECT/"src/lc_eval/execution/shim.py", root/"limacharlie")
    # Installed Claude is a self-contained native executable. Codex's launcher points to a native bundle.
    claude = next(a for a in config.agents if a.adapter == "claude_code")
    codex = next(a for a in config.agents if a.adapter == "codex")
    shutil.copyfile(claude.executable.resolve(), root/"claude")
    codex_native = resolve_codex_native(codex.executable)
    codex_code_mode_host = codex_native.with_name("codex-code-mode-host")
    if not codex_code_mode_host.is_file():
        raise RuntimeError("installed Codex bundle is missing codex-code-mode-host")
    shutil.copyfile(codex_native, root/"codex")
    shutil.copyfile(codex_code_mode_host, root/"codex-code-mode-host")
    for executable in (root / "claude", root / "codex", root / "codex-code-mode-host"):
        executable.chmod(0o755)
    (root/"Dockerfile.agent").write_text(f"""FROM {base}
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git ripgrep jq curl nodejs && rm -rf /var/lib/apt/lists/*
COPY claude codex codex-code-mode-host limacharlie /usr/local/bin/
COPY egress.py /opt/egress.py
RUN chmod 755 /usr/local/bin/claude /usr/local/bin/codex /usr/local/bin/codex-code-mode-host /usr/local/bin/limacharlie && useradd -m -u 1000 agent
WORKDIR /work
CMD ["sleep", "infinity"]
""")
    candidate_tag = "lc-eval-agent:"+sha256(root/"claude")[:8]+"-"+sha256(root/"codex")[:8]
    agent_key = _build_key(
        base, sha256(root/"claude"), sha256(root/"codex"), sha256(root/"codex-code-mode-host"), sha256(root/"egress.py"),
        sha256(root/"limacharlie"), (root/"Dockerfile.agent").read_text(),
    )
    build_image(root/"Dockerfile.agent", candidate_tag, root, agent_key)
    config.sources.worker_image, config.sources.worker_image_id = worker_tag, image_id(worker_tag)
    config.sources.candidate_image, config.sources.candidate_image_id = candidate_tag, image_id(candidate_tag)
    config.sources.source_archive_sha256 = sha256(archive)
    claude_version = run([str(root / "claude"), "--version"])
    codex_version = run([str(root / "codex"), "--version"])
    claude.version = claude_version
    codex.version = codex_version
    result = {"base_image": base, "base_image_id": base_id, "worker_image": config.sources.worker_image_id,
              "agent_image": config.sources.candidate_image_id,
              "source_archive_sha256": config.sources.source_archive_sha256,
              "cli_commit": config.sources.cli.commit, "claude_sha256": sha256(root/"claude"),
              "codex_sha256": sha256(root/"codex"),
              "codex_code_mode_host_sha256": sha256(root/"codex-code-mode-host"),
              "claude_version": claude_version, "codex_version": codex_version}
    atomic_json(root/"manifest.json", result)
    return result


class DockerEnvironment:
    def __init__(self, config: RunConfig, trial_id: str, root: Path, journal):
        self.config, self.trial_id, self.root, self.journal = config, trial_id, root, journal
        self.prefix = "lce-"+trial_id[-24:].lower()
        self.agent = self.prefix+"-agent"
        self.worker = self.prefix+"-worker"
        self.work = root/"work"
        self.socket_dir = root/"socket"
        self.work.mkdir(parents=True, exist_ok=True)
        self.socket_dir.mkdir(exist_ok=True)
        self.handles = []

    def owned(self, kind, name, create):
        intent = self.journal.intent(self.trial_id, kind, name, {"name": name})
        ident = create()
        self.journal.acquired(intent, ident or name)
        self.handles.append((kind, name, intent))
        return ident

    def _selected_agent(self, selected: AgentConfig | str | None) -> AgentConfig:
        if isinstance(selected, AgentConfig):
            if selected not in self.config.agents:
                raise ValueError("selected agent is not part of the resolved run configuration")
            return selected
        if isinstance(selected, str):
            matches = [agent for agent in self.config.agents if agent.adapter == selected]
        elif selected is None:
            matches = list(self.config.agents)
        else:
            raise TypeError("agent_config must be an AgentConfig, adapter name, or None")
        if len(matches) != 1:
            raise ValueError("select exactly one configured harness for this trial")
        return matches[0]

    def start(self, oid: str, key: str, agent_config: AgentConfig | str | None = None):
        cfg = self.config
        selected_agent = self._selected_agent(agent_config)
        for image, expected in ((cfg.sources.worker_image, cfg.sources.worker_image_id),
                                (cfg.sources.candidate_image, cfg.sources.candidate_image_id)):
            if not expected or image_id(image) != expected:
                raise RuntimeError("build and pin images before running")
        a_net, w_net = self.prefix+"-an", self.prefix+"-wn"
        for net in (a_net, w_net):
            self.owned(
                "docker_network",
                net,
                lambda net=net: run(
                    [
                        "docker", "network", "create", "--internal", "--label",
                        "lc-eval.trial=" + self.trial_id,
                        "--opt", "com.docker.network.bridge.gateway_mode_ipv4=isolated",
                        net,
                    ]
                ),
            )
        for suffix, net, hosts in (("ap", a_net, "api.anthropic.com,*.anthropic.com,anthropic.com,chatgpt.com,*.chatgpt.com,*.openai.com,openai.com"),
                                    ("wp", w_net, "limacharlie.io,*.limacharlie.io")):
            name = self.prefix+"-"+suffix
            self.owned("docker_container", name, lambda name=name, net=net, hosts=hosts: run([
                "docker", "run", "-d", "--name", name, "--label", "lc-eval.trial="+self.trial_id,
                "--network", net, "--network-alias", "proxy", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--pids-limit", "128", "--memory", "256m",
                "-e", "ALLOWED_HOSTS="+hosts, cfg.sources.candidate_image_id,
                "python", "/opt/egress.py"]))
            run(["docker", "network", "connect", "bridge", name])
        common = ["--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
                  "--memory", "2g", "--cpus", "2", "--tmpfs", "/tmp:rw,nosuid,size=256m,mode=1777",
                  "--user", "1000:1000", "--mount", f"type=bind,src={self.work},dst=/work"]
        # Secrets enter the trusted worker only. Docker metadata stays with the host controller.
        self.owned("docker_container", self.worker, lambda: run([
            "docker", "run", "-d", "--name", self.worker, "--label", "lc-eval.trial="+self.trial_id,
            "--network", w_net, *common, "-e", "HOME=/tmp", "-e", "LC_CONFIG_DIR=/tmp/lc",
            "-e", "LC_OID="+oid, "-e", "LC_API_KEY="+key,
            "-e", "HTTPS_PROXY=http://proxy:8080", "-e", "HTTP_PROXY=http://proxy:8080",
            cfg.sources.worker_image_id]))
        auth = self.root/"auth"
        auth.mkdir(mode=0o700, exist_ok=True)
        selected_auth = auth/"selected"
        if selected_auth.exists():
            shutil.rmtree(selected_auth)
        selected_auth.mkdir(mode=0o700)
        if selected_agent.auth_file:
            auth_name = "auth.json" if selected_agent.adapter == "codex" else ".credentials.json"
            shutil.copyfile(selected_agent.auth_file, selected_auth/auth_name)
            os.chmod(selected_auth/auth_name, 0o600)
        # Minimal onboarding state, without user preferences, plugins, or the other harness's credentials.
        if selected_agent.adapter == "claude_code":
            (selected_auth/".claude.json").write_text(json.dumps({"hasCompletedOnboarding": True}))
            os.chmod(selected_auth/".claude.json", 0o600)
        docs = self.root/"docs"
        docs.mkdir(exist_ok=True)
        archive = subprocess.run(["git", "-C", str(cfg.sources.docs.path), "archive", cfg.sources.docs.commit,
                                  "docs"], capture_output=True, check=True)
        import io
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            extract_archive(tar, docs)
        selected_env = [
            "-e", "HOME=/auth",
            "-e", "HTTPS_PROXY=http://proxy:8080", "-e", "HTTP_PROXY=http://proxy:8080",
        ]
        auth_mounts = ["--tmpfs", "/auth:rw,nosuid,nodev,size=64m,uid=1000,gid=1000,mode=0700"]
        auth_initializers = []
        if selected_agent.auth_file:
            auth_name = "auth.json" if selected_agent.adapter == "codex" else ".credentials.json"
            auth_mounts += [
                "--mount",
                f"type=bind,src={selected_auth / auth_name},dst=/run/lc-eval-credential,readonly",
            ]
            auth_initializers.append(f"cp /run/lc-eval-credential /auth/{auth_name}")
        if selected_agent.adapter == "codex":
            selected_env += ["-e", "CODEX_HOME=/auth"]
        elif selected_agent.adapter == "claude_code":
            selected_env += ["-e", "CLAUDE_CONFIG_DIR=/auth"]
            auth_mounts += [
                "--mount",
                f"type=bind,src={selected_auth / '.claude.json'},dst=/run/lc-eval-onboarding,readonly",
            ]
            auth_initializers.append("cp /run/lc-eval-onboarding /auth/.claude.json")
        else:
            raise ValueError(f"Docker environment does not support adapter {selected_agent.adapter!r}")
        # The source credentials are individual read-only mounts.  Each trial gets
        # a private writable tmpfs so the native CLIs can create locks, databases,
        # logs, and refreshed session state without changing the host credential.
        initialize_auth = "; ".join(["umask 077", *auth_initializers, "exec sleep infinity"])
        self.owned("docker_container", self.agent, lambda: run([
            "docker", "run", "-d", "--name", self.agent, "--label", "lc-eval.trial="+self.trial_id,
            "--network", a_net, *common,
            "--mount", f"type=bind,src={self.socket_dir},dst=/run/lc-eval,readonly",
            "--mount", f"type=bind,src={docs},dst=/docs,readonly",
            *auth_mounts,
            *selected_env,
            "-e", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1", "-e", "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1",
            cfg.sources.candidate_image_id, "sh", "-c", initialize_auth]))

    def stop_candidate(self):
        for name in (self.agent, self.worker):
            subprocess.run(["docker", "kill", name], capture_output=True, text=True, timeout=30)
            observed = subprocess.run(
                ["docker", "container", "inspect", "--format", "{{.State.Running}}", name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if observed.returncode == 0:
                state = observed.stdout.strip().lower()
                if state == "false":
                    continue
                if state == "true":
                    raise RuntimeError(f"candidate container {name} is still running")
                raise RuntimeError(f"candidate container {name} returned an unknown running state")
            diagnostic = (observed.stderr + observed.stdout).lower()
            if "no such object" not in diagnostic and "no such container" not in diagnostic:
                raise RuntimeError(f"could not confirm candidate container {name} stopped")

    def cleanup(self):
        errors = []
        for kind, name, intent in reversed(self.handles):
            args = ["docker", "rm", "-f", name] if kind == "docker_container" else ["docker", "network", "rm", name]
            try:
                run(args)
                self.journal.cleaned(intent)
            except Exception as exc:
                object_type = "container" if kind == "docker_container" else "network"
                probe = subprocess.run(
                    ["docker", object_type, "inspect", name], capture_output=True, text=True, timeout=30,
                )
                if probe.returncode:
                    self.journal.cleaned(intent)
                else:
                    self.journal.cleanup_failed(intent, str(exc))
                    errors.append(str(exc))
        auth = self.root/"auth"
        if auth.exists():
            shutil.rmtree(auth)
        if errors:
            raise RuntimeError("; ".join(errors))
