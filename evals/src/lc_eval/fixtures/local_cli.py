"""Privileged CLI subprocess adapter: never exposes auth-bearing stdout in logs."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import httpx

from ..config import sha256
from ..models import LCConfig


class ControlError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def decode_json(text: str):
    decoder = json.JSONDecoder()
    for offset, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[offset:])
            return obj
        except json.JSONDecodeError:
            continue
    raise ControlError("trusted CLI returned no JSON document")


class LocalCLI:
    def __init__(self, config: LCConfig):
        self.config = config
        self.tokens: dict[str, tuple[float, str]] = {}

    def invoke(self, args: list[str], oid: str | None = None, json_output: bool = True,
               stdin: str | None = None, timeout: int = 90):
        if sha256(self.config.executable) != self.config.executable_sha256:
            raise ControlError("trusted CLI executable digest changed")
        argv = [str(self.config.executable)]
        if oid:
            argv += ["--oid", oid]
        if self.config.environment:
            argv += ["--env", self.config.environment]
        if json_output:
            argv += ["--output", "json"]
        argv += args
        env = dict(os.environ)
        # CLI owns the user's supported auth flow; remove debug only.
        env.pop("LC_DEBUG", None)
        result = subprocess.run(argv, input=stdin, capture_output=True, text=True, env=env, timeout=timeout)
        if result.returncode:
            # Never include stdout, stderr or arguments that may contain tokens.
            raise ControlError(f"trusted CLI {args[0]} {args[1] if len(args)>1 else ''} failed (exit {result.returncode})")
        return decode_json(result.stdout) if json_output else result.stdout

    def token(self, oid: str, refresh: bool = False) -> str:
        cached = self.tokens.get(oid)
        if not refresh and cached and cached[0] > time.time()+120:
            return cached[1]
        data = self.invoke(["auth", "get-token", "--hours", "1", "--format", "json"], oid)
        if not isinstance(data, dict) or not isinstance(data.get("token"), str):
            raise ControlError("invalid token response")
        self.tokens[oid] = (time.time()+3500, data["token"])
        return data["token"]

    def api(self, oid: str, method: str, path: str, *, root: str = "https://api.limacharlie.io/v1",
            body=None, params=None, form=None, timeout=60):
        url = root.rstrip("/")+"/"+path.lstrip("/")
        for attempt in range(2):
            response = httpx.request(method, url, headers={"Authorization": "Bearer "+self.token(oid, bool(attempt))},
                                     json=body, params=params, data=form, timeout=timeout)
            if response.status_code == 401 and attempt == 0:
                continue
            if response.is_error:
                # Body intentionally private: may contain submitted credentials.
                raise ControlError(
                    f"independent API {method} {path.split('/')[0]} HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            return response.json() if response.content else {}
        raise ControlError("authentication refresh failed")

    def get_urls(self, oid: str) -> dict[str, str]:
        """Resolve the organization's regional service endpoints."""
        data = self.api(oid, "GET", f"orgs/{oid}/url")
        if not isinstance(data, dict):
            raise ControlError("invalid organization URL response")
        urls = data.get("url", data)
        if not isinstance(urls, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in urls.items()
        ):
            raise ControlError("invalid organization URL mapping")
        return dict(urls)

    def write_json(self, path: Path, value):
        from ..config import atomic_json
        atomic_json(path, value)
