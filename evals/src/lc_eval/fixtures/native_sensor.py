"""Native Linux sensor deployment in an evaluator-owned isolated container."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import stat
import subprocess
import time
import traceback
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx

from ..execution.broker import CommandSpec
from ..execution.docker import build_image, image_id, run
from .local_cli import ControlError
from .organization import unwrap

DOWNLOAD_URL = "https://downloads.limacharlie.io/sensor/linux/64"
REQUEST_PATH = "enrollment.json"
STATUS_PATH = "enrollment-status.json"
OBSERVATION_PATH = "/work/process-observation.json"
MAX_ENROLLMENT_BYTES = 16 * 1024
MAX_DIAGNOSTIC_BYTES = 64 * 1024
DEFAULT_SYSTEM_KEY_DESCRIPTIONS = frozenset({
    "ext ext-feedback webhook adapter",
    "reliable tasking webhook",
    "ext ext-yara webhook adapter",
})
SENSOR_DOCKERFILE = """FROM {base_image}\nCOPY native-sensor.bin /opt/lc-native-sensor\nRUN chmod 755 /opt/lc-native-sensor\n"""


# Native task request opens a temporary Spout; output_portal-go requires output.set.
PERMISSIONS = ["org.get", "sensor.list", "sensor.get", "sensor.tag", "sensor.task", "ikey.list", "ikey.set", "output.set"]
COMMANDS = {
    ("installation-key", "list"): CommandSpec(),
    ("installation-key", "get"): CommandSpec(value_options=frozenset({"--iid"})),
    ("installation-key", "create"): CommandSpec(value_options=frozenset({"--description", "--tags"}), flag_options=frozenset({"--get"})),
    ("sensor", "list"): CommandSpec(value_options=frozenset({"--selector", "--tag", "--hostname", "--ip", "--limit", "--offset"}), flag_options=frozenset({"--online"})),
    ("sensor", "get"): CommandSpec(value_options=frozenset({"--sid"})),
    ("tag", "add"): CommandSpec(value_options=frozenset({"--sid", "--tag", "--ttl"})),
    ("tag", "list"): CommandSpec(value_options=frozenset({"--sid"})),
    ("task", "request"): CommandSpec(value_options=frozenset({"--sid", "--command", "--timeout"}), fixed_values=(("--command", frozenset({"os_processes"})),)),
}


def _ikeys(cli, oid):
    value = cli.invoke(["installation-key", "list"], oid)
    return value if isinstance(value, (dict, list)) else {}


def _default_system_keys_ready(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    by_description = {}
    for record in value.values():
        if not isinstance(record, Mapping) or not isinstance(record.get("desc"), str):
            continue
        by_description[record["desc"]] = record
    for description in DEFAULT_SYSTEM_KEY_DESCRIPTIONS:
        record = by_description.get(description)
        if not isinstance(record, Mapping):
            return False
        tags = record.get("tags")
        if not isinstance(tags, list) or "lc:system" not in tags or not any(
            isinstance(tag, str) and tag.startswith("ext:") for tag in tags
        ):
            return False
    return True


async def _wait_for_default_system_keys(config, cli, oid) -> tuple[dict[str, Any], dict[str, Any]]:
    """Wait for authoritative default-extension key inventory before baseline."""
    deadline = time.monotonic() + config.lc.readiness_seconds
    attempts = 0
    last: Any = None
    while time.monotonic() < deadline:
        attempts += 1
        last = _ikeys(cli, oid)
        if _default_system_keys_ready(last):
            return last, {"state": "ready", "attempts": attempts,
                          "required_descriptions": sorted(DEFAULT_SYSTEM_KEY_DESCRIPTIONS)}
        await asyncio.sleep(min(2, max(0, deadline - time.monotonic())))
    raise RuntimeError("default extension installation keys did not reach authoritative readiness")


def _sensors(cli, oid, *, online=False):
    args = ["sensor", "list", "--limit", "1000"]
    if online:
        args.append("--online")
    value = cli.invoke(args, oid)
    return value if isinstance(value, list) else []


def _status_sid(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    for key in ("sid", "sensor_id", "id"):
        candidate = value.get(key)
        try:
            uuid.UUID(candidate)
            return candidate
        except (TypeError, ValueError, AttributeError):
            pass
    for nested in value.values():
        if isinstance(nested, dict) and (candidate := _status_sid(nested)):
            return candidate
    return None


def _read_enrollment(path: Path) -> dict[str, Any]:
    """Read one bounded regular file without following a candidate symlink."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("enrollment request is not a regular file")
        if info.st_size > MAX_ENROLLMENT_BYTES:
            raise ValueError("enrollment request exceeds the byte limit")
        raw = os.read(descriptor, MAX_ENROLLMENT_BYTES + 1)
        if len(raw) > MAX_ENROLLMENT_BYTES:
            raise ValueError("enrollment request exceeds the byte limit")
        return json.loads(raw.decode("utf-8"))
    finally:
        os.close(descriptor)


def _safe_status(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically replace a candidate-visible status path without following links."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temp, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        descriptor = -1
        os.replace(temp, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _runtime_timeout_seconds(config) -> int:
    """Bound request waiting by the longest configured candidate session."""
    values = [agent.timeout_seconds for agent in config.agents]
    if not values:
        raise ValueError("native sensor runtime requires a configured agent")
    return max(values)


def _sensor_image_build_key(base_image_id: str, binary_sha256: str, dockerfile: str) -> str:
    return hashlib.sha256((base_image_id + "\0" + binary_sha256 + "\0" + dockerfile).encode()).hexdigest()


def _build_sensor_image(config, root: Path, binary: Path, binary_sha256: str) -> tuple[str, str, str]:
    """Build a secret-free sensor image from the verified local worker tag."""
    base_tag = config.sources.worker_image
    base_id = config.sources.worker_image_id
    if not base_tag or not base_id or image_id(base_tag) != base_id:
        raise RuntimeError("pinned local worker image is unavailable for native sensor build")
    context = root / "native-sensor-image"
    context.mkdir(mode=0o700, exist_ok=True)
    copied = context / "native-sensor.bin"
    shutil.copyfile(binary, copied)
    copied.chmod(0o500)
    dockerfile_text = SENSOR_DOCKERFILE.format(base_image=base_tag)
    dockerfile = context / "Dockerfile"
    dockerfile.write_text(dockerfile_text)
    worker_token = base_id.removeprefix("sha256:")[:12]
    tag = f"lc-eval-native-sensor:{binary_sha256[:12]}-{worker_token}"
    build_key = _sensor_image_build_key(base_id, binary_sha256, dockerfile_text)
    build_image(dockerfile, tag, context, build_key)
    derived_id = image_id(tag)
    return tag, derived_id, build_key


class NativeSensorRuntime:
    def __init__(self, config, cli, journal, trial_id: str, oid: str, root: Path, marker: str):
        self.config, self.cli, self.journal = config, cli, journal
        self.trial_id, self.oid, self.root, self.marker = trial_id, oid, root, marker
        self.work = root / "work"
        self.name = "lce-native-" + trial_id[-20:].lower()
        self.task: asyncio.Task | None = None
        self.intent = None
        self.container_id = None
        self.sid = None
        self.binary_sha256 = None
        self.binary_path = None
        self.sensor_image = None
        self.sensor_image_id = None
        self.sensor_image_build_key = None
        self.deployment = None
        self.launch_task: asyncio.Task | None = None
        self.stopping = False
        self.enrollment_state = "waiting"
        self.error_stage = None
        self.error = None

    def start(self):
        self.task = asyncio.create_task(self._watch())

    async def _watch(self):
        try:
            preparation_deadline = time.monotonic() + self.config.lc.readiness_seconds
            while time.monotonic() < preparation_deadline and not self.work.is_dir():
                await asyncio.sleep(0.5)
            if not self.work.is_dir():
                raise TimeoutError("candidate workspace was not prepared")
            deadline = time.monotonic() + _runtime_timeout_seconds(self.config)
            request_path = self.work / REQUEST_PATH
            while time.monotonic() < deadline:
                try:
                    request = _read_enrollment(request_path)
                    break
                except FileNotFoundError:
                    pass
                except Exception:
                    self.enrollment_state = "invalid"
                    self.error_stage = "invalid_request"
                    raise ValueError("invalid enrollment request") from None
                await asyncio.sleep(0.5)
            else:
                self.enrollment_state = "missing"
                self.error_stage = "missing_request"
                raise TimeoutError("candidate did not submit the endpoint enrollment request")
            if set(request) != {"schema_version", "deployment", "installation_key"} or request.get("schema_version") != 1 or request.get("deployment") != "native_linux_sensor_v1":
                self.enrollment_state = "invalid"
                self.error_stage = "invalid_request"
                raise ValueError("enrollment request does not match endpoint-deployment.json")
            key = request.get("installation_key")
            if not isinstance(key, str) or len(key) < 16:
                self.enrollment_state = "invalid"
                self.error_stage = "invalid_request"
                raise ValueError("enrollment request omitted the native installation key")
            self.enrollment_state = "validated"
            if self.binary_path is None:
                self.error_stage = "download"
                self.binary_path = await asyncio.to_thread(self._download)
            self.enrollment_state = "deploying"
            self.error_stage = "launch"
            self.launch_task = asyncio.create_task(self._launch_owned(self.binary_path, key))
            await asyncio.shield(self.launch_task)
            self.error_stage = "registration"
            await self._wait_registered(deadline)
            self.enrollment_state = "registered"
            self.error_stage = None
        except asyncio.CancelledError:
            raise
        except Exception as error:
            # Error text is deliberately not propagated: subprocess failures and
            # malformed candidate documents can contain the enrollment credential.
            self.error = type(error).__name__
            diagnostic = {
                "error_type": type(error).__name__,
                "stage": self.error_stage,
                "traceback": traceback.format_list(traceback.extract_tb(error.__traceback__)),
            }
            private_error = self.root / "native-runtime-error.json"
            _safe_status(private_error, diagnostic)
            private_error.chmod(0o600)
            if not self.stopping:
                _safe_status(self.work / STATUS_PATH, {"schema_version": 1, "state": "failed", "error": self.error})

    def _download(self):
        response = httpx.get(DOWNLOAD_URL, follow_redirects=True, timeout=120)
        response.raise_for_status()
        if not response.content.startswith(b"\x7fELF"):
            raise RuntimeError("trusted native sensor download is not an ELF binary")
        path = self.root / "native-sensor.bin"
        path.write_bytes(response.content)
        path.chmod(0o500)
        self.binary_sha256 = hashlib.sha256(response.content).hexdigest()
        return path

    async def _launch_owned(self, binary: Path, key: str):
        self.intent = self.journal.intent(self.trial_id, "docker_container", self.name, {"name": self.name, "purpose": "native_sensor"})
        container_id = await asyncio.to_thread(self._launch_docker, binary, key)
        self.container_id = container_id
        self.journal.acquired(self.intent, container_id, {"name": self.name})

    def _launch_docker(self, binary: Path, key: str):
        del binary
        if not self.sensor_image or not self.sensor_image_id or image_id(self.sensor_image) != self.sensor_image_id:
            raise RuntimeError("derived native sensor image identity changed")
        image = self.sensor_image_id
        # Docker defaults tmpfs to noexec. LC loads signed modules with dlopen
        # from its private data directory (MemoryModule/posix/MemoryModule.c).
        # The sensor loads its signed collection modules from LC_DATA_DIRECTORY
        # with MemoryModule/dlopen; Docker tmpfs defaults to noexec and prevents
        # enrollment from completing, so this private sensor-only tmpfs is exec.
        container_id = run(["docker", "create", "--name", self.name, "--label", "lc-eval.trial=" + self.trial_id,
             "--network", "bridge", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
             "--pids-limit", "128", "--memory", "256m", "--cpus", "1", "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
             "--tmpfs", "/sensor-data:rw,exec,nosuid,nodev,size=32m", "-e", "LC_INSTALLATION_KEY=" + key,
             "-e", "LC_DATA_DIRECTORY=/sensor-data", image, "bash", "-c",
             f"python -c 'import time; time.sleep(100000)' {self.marker} & exec /opt/lc-native-sensor -d -"])
        run(["docker", "start", self.name])
        inspected = json.loads(run(["docker", "inspect", self.name]))[0]
        host = inspected.get("HostConfig", {})
        self.deployment = {"network_mode": host.get("NetworkMode"), "privileged": host.get("Privileged"),
                           "cap_drop": host.get("CapDrop"), "binds": host.get("Binds"), "mounts": inspected.get("Mounts"),
                           "read_only": host.get("ReadonlyRootfs"), "pids_limit": host.get("PidsLimit"),
                           "tmpfs": host.get("Tmpfs")}
        return container_id

    async def _wait_registered(self, deadline):
        while time.monotonic() < deadline:
            state_probe = subprocess.run(["docker", "container", "inspect", self.name], capture_output=True, text=True, timeout=15)
            if state_probe.returncode == 0:
                try:
                    inspected = json.loads(state_probe.stdout)[0]
                except (json.JSONDecodeError, IndexError, TypeError):
                    inspected = None
                if isinstance(inspected, Mapping):
                    labels = inspected.get("Config", {}).get("Labels", {})
                    if inspected.get("Id") != self.container_id or labels.get("lc-eval.trial") != self.trial_id:
                        raise RuntimeError("native sensor container ownership changed during registration")
                    state = inspected.get("State", {})
                    if isinstance(state, Mapping) and state.get("Running") is False:
                        await asyncio.to_thread(self._capture_private_diagnostics, "early_exit", inspected)
                        raise RuntimeError("native sensor container exited before registration")
            probe = subprocess.run(["docker", "exec", self.name, "cat", "/sensor-data/hcp_hbs_status.json"], capture_output=True, text=True, timeout=15)
            if probe.returncode == 0:
                try:
                    self.sid = _status_sid(json.loads(probe.stdout))
                except json.JSONDecodeError:
                    pass
                if self.sid:
                    try:
                        value = self.cli.invoke(["sensor", "get", "--sid", self.sid], self.oid)
                    except ControlError:
                        value = None
                    if isinstance(value, dict):
                        _safe_status(self.work / STATUS_PATH, {"schema_version": 1, "state": "registered", "sensor_id": self.sid})
                        return
            await asyncio.sleep(2)
        raise TimeoutError("native sensor did not reach independently observed registration")

    @staticmethod
    def _bounded(text: str) -> str:
        raw = text.encode("utf-8", errors="replace")
        if len(raw) <= MAX_DIAGNOSTIC_BYTES:
            return text
        return raw[-MAX_DIAGNOSTIC_BYTES:].decode("utf-8", errors="replace")

    def _capture_private_diagnostics(self, reason: str, inspected: Mapping[str, Any] | None = None):
        """Persist bounded private runtime evidence without container Config/env."""
        if inspected is None:
            probe = subprocess.run(["docker", "container", "inspect", self.name], capture_output=True, text=True, timeout=20)
            if probe.returncode:
                inspected = None
            else:
                try:
                    inspected = json.loads(probe.stdout)[0]
                except (json.JSONDecodeError, IndexError, TypeError):
                    inspected = None
        diagnostic: dict[str, Any] = {"reason": reason, "captured_at": time.time()}
        if isinstance(inspected, Mapping):
            labels = inspected.get("Config", {}).get("Labels", {})
            if inspected.get("Id") == self.container_id and labels.get("lc-eval.trial") == self.trial_id:
                diagnostic["container_state"] = inspected.get("State")
                logs = subprocess.run(["docker", "logs", "--tail", "200", self.name], capture_output=True, text=True, timeout=20)
                diagnostic["logs"] = self._bounded(logs.stdout + logs.stderr)
                files = subprocess.run(["docker", "exec", self.name, "sh", "-c", "find /sensor-data -maxdepth 2 -type f -printf '%P %s bytes\\n' | sort"], capture_output=True, text=True, timeout=20)
                diagnostic["sensor_data_files"] = self._bounded(files.stdout + files.stderr)
                status = subprocess.run(["docker", "exec", self.name, "sh", "-c", "test -f /sensor-data/hcp_hbs_status.json && head -c 65536 /sensor-data/hcp_hbs_status.json || true"], capture_output=True, text=True, timeout=20)
                diagnostic["sensor_status"] = self._bounded(status.stdout + status.stderr)
            else:
                diagnostic["capture_error"] = "ownership_mismatch"
        else:
            diagnostic["capture_error"] = "container_inventory_unavailable"
        path = self.root / "native-runtime-diagnostics.json"
        _safe_status(path, diagnostic)
        path.chmod(0o600)

    async def stop(self):
        self.stopping = True
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.launch_task is not None:
            try:
                await asyncio.shield(self.launch_task)
            except Exception:
                # Cleanup below is authoritative even after partial launch failure.
                pass
        if self.intent is None:
            return

        def absent(result) -> bool:
            diagnostic = (result.stderr + result.stdout).lower()
            return "no such object" in diagnostic or "no such container" in diagnostic

        probe = subprocess.run(["docker", "container", "inspect", self.name], capture_output=True, text=True, timeout=30)
        if probe.returncode:
            if absent(probe):
                self.journal.cleaned(self.intent)
                return
            raise RuntimeError("native sensor container inventory failed during cleanup")
        try:
            inspected = json.loads(probe.stdout)[0]
        except (json.JSONDecodeError, IndexError, TypeError) as error:
            raise RuntimeError("native sensor container inventory had an unsupported shape") from error
        labels = inspected.get("Config", {}).get("Labels", {})
        if not self.container_id or inspected.get("Id") != self.container_id or labels.get("lc-eval.trial") != self.trial_id:
            raise RuntimeError("native sensor container ownership mismatch")
        try:
            await asyncio.to_thread(self._capture_private_diagnostics, "stop", inspected)
        except Exception:
            # Diagnostics are best-effort and must never prevent owned cleanup.
            pass
        removed = subprocess.run(["docker", "rm", "-f", self.name], capture_output=True, text=True, timeout=30)
        if removed.returncode:
            raise RuntimeError("native sensor container removal failed")
        confirmed = subprocess.run(["docker", "container", "inspect", self.name], capture_output=True, text=True, timeout=30)
        if confirmed.returncode == 0 or not absent(confirmed):
            raise RuntimeError("native sensor container absence could not be confirmed")
        self.journal.cleaned(self.intent)


async def provision(config, cli, journal, trial_id, oid, seed, root):
    suffix = hashlib.sha256(f"{trial_id}:{seed}".encode()).hexdigest()[:12]
    marker = "lc_eval_marker_" + suffix
    description = "lc-eval-native-" + suffix
    required_tag = "lc-eval:" + suffix
    distractor = unwrap(cli.invoke(["installation-key", "create", "--description", "lc-eval-distractor-" + suffix, "--get"], oid))
    baseline_keys, key_readiness = await _wait_for_default_system_keys(config, cli, oid)
    baseline_sensors = _sensors(cli, oid)
    contract = {
        "schema_version": 1,
        "deployment": "native_linux_sensor_v1",
        "request_path": "/work/enrollment.json",
        "status_path": "/work/enrollment-status.json",
        "request_schema": {"schema_version": 1, "deployment": "native_linux_sensor_v1", "installation_key": "native binary installation key string"},
        "notes": ["This is an evaluator endpoint deployment contract, not a LimaCharlie API.", "The evaluator starts a real native Linux sensor in an isolated owned container after validating the request."],
    }
    runtime = NativeSensorRuntime(config, cli, journal, trial_id, oid, root, marker)
    runtime.binary_path = await asyncio.to_thread(runtime._download)
    runtime.sensor_image, runtime.sensor_image_id, runtime.sensor_image_build_key = await asyncio.to_thread(
        _build_sensor_image, config, root, runtime.binary_path, runtime.binary_sha256
    )
    runtime.start()
    return {
        "baseline_keys": baseline_keys, "baseline_sensors": baseline_sensors,
        "key_readiness": key_readiness,
        "_distractor_key": distractor, "marker": marker, "required_tag": required_tag,
        "installation_key_description": description,
        "provenance": {"sensor_binary_sha256": runtime.binary_sha256,
                             "derived_image_id": runtime.sensor_image_id,
                             "derived_image_build_key": runtime.sensor_image_build_key,
                             "base_worker_image_id": config.sources.worker_image_id},
        "public_files": {"endpoint-deployment.json": json.dumps(contract, indent=2) + "\n"},
        "public": {"organization_id": oid, "installation_key_description": description, "required_tag": required_tag, "marker_process_name": marker},
        "cli_notice": "This profile permits installation-key list/get/create, sensor list/get, tag list/add, and synchronous task request. The evaluator endpoint deployment contract is /work/endpoint-deployment.json.",
        "_sensor_binary_sha256": runtime.binary_sha256,
        "_runtime": runtime,
    }


async def collect(config, cli, oid, fixture, root):
    runtime = fixture["_runtime"]
    if runtime.task:
        if not runtime.task.done() and runtime.enrollment_state == "waiting":
            try:
                _read_enrollment(root / "work" / REQUEST_PATH)
            except FileNotFoundError:
                runtime.enrollment_state = "missing"
                runtime.error_stage = "missing_request"
                runtime.task.cancel()
            except Exception:
                runtime.enrollment_state = "invalid"
                runtime.error_stage = "invalid_request"
                runtime.task.cancel()
        if runtime.task.cancelled() or (runtime.task.done() and runtime.task.exception() is None):
            pass
        else:
            try:
                await asyncio.wait_for(asyncio.shield(runtime.task), config.limits.verification_seconds)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
    sid = runtime.sid
    sensor = None
    tags = None
    task_result = None
    online_sensors = None
    if sid:
        try:
            sensor = cli.invoke(["sensor", "get", "--sid", sid], oid)
            online_sensors = _sensors(cli, oid, online=True)
            tags = cli.invoke(["tag", "list", "--sid", sid], oid)
            task_result = cli.invoke(["task", "request", "--sid", sid, "--command", "os_processes", "--timeout", "45"], oid, timeout=75)
        except ControlError as error:
            task_result = {"collection_error": str(error)}
    provenance = dict(fixture.get("provenance") or {})
    if isinstance(sensor, Mapping) and isinstance(sensor.get("version"), str):
        provenance["observed_sensor_version"] = sensor["version"]
    return {"sensor_id": sid, "sensor": sensor, "online_sensors": online_sensors,
            "tags": tags, "trusted_task_result": task_result,
            "keys_after": _ikeys(cli, oid), "sensors_after": _sensors(cli, oid),
            "runtime_error": runtime.error, "binary_sha256": runtime.binary_sha256,
            "deployment": runtime.deployment, "enrollment_state": runtime.enrollment_state,
            "error_stage": runtime.error_stage,
            "provenance": provenance}


async def reference(fixture, env, bad=False):
    from .local_cli import decode_json

    public = fixture["public"]
    raw = await asyncio.to_thread(run, ["docker", "exec", env.agent, "limacharlie", "--output", "json", "installation-key", "create", "--description", public["installation_key_description"], "--get"], timeout=90)
    value = unwrap(decode_json(raw))
    key = next((value.get(name) for name in ("key", "installation_key", "json_key") if isinstance(value, dict) and isinstance(value.get(name), str)), None)
    if not key:
        raise RuntimeError("reference installation key response omitted native key")
    _safe_status(env.work / REQUEST_PATH, {"schema_version": 1, "deployment": "native_linux_sensor_v1", "installation_key": key})
    deadline = time.monotonic() + 180
    status = None
    while time.monotonic() < deadline:
        if (env.work / STATUS_PATH).is_file():
            status = json.loads((env.work / STATUS_PATH).read_text())
            if status.get("state") in {"registered", "failed"}:
                break
        await asyncio.sleep(1)
    if not status or status.get("state") != "registered":
        raise RuntimeError(f"reference sensor enrollment failed: {status}")
    sid = status["sensor_id"]
    if not bad:
        await asyncio.to_thread(run, ["docker", "exec", env.agent, "limacharlie", "tag", "add", "--sid", sid, "--tag", public["required_tag"]], timeout=90)
    observed = await asyncio.to_thread(run, ["docker", "exec", env.agent, "limacharlie", "--output", "json", "task", "request", "--sid", sid, "--command", "os_processes", "--timeout", "45"], timeout=75)
    (env.work / "process-observation.json").write_text(observed + "\n")
    if bad:
        (env.work / "process-observation.json").write_text("[]\n")
    return f"Onboarded native sensor {sid}"
