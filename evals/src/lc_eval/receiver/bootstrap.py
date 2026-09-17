"""Pinned cloudflared installer for eval-owned tooling directories."""

from __future__ import annotations

import hashlib
import os
import platform
import re
import tempfile
from pathlib import Path

import httpx


CLOUDFLARED_VERSION = "2026.9.1"
CLOUDFLARED_RELEASE_API = (
    "https://api.github.com/repos/cloudflare/cloudflared/releases/tags/"
    f"{CLOUDFLARED_VERSION}"
)
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024

# Release-body SHA-256 values published by the official Cloudflare repository.
_PINNED_ASSETS = {
    ("linux", "x86_64"): (
        "cloudflared-linux-amd64",
        "03f1f25d1cc93b9ad6c60569d44060bc4f17ed97075760ed8cfca4b12dcd68cc",
    ),
    ("linux", "amd64"): (
        "cloudflared-linux-amd64",
        "03f1f25d1cc93b9ad6c60569d44060bc4f17ed97075760ed8cfca4b12dcd68cc",
    ),
    ("linux", "aarch64"): (
        "cloudflared-linux-arm64",
        "3d97437c71848bd8df68041e12436b484a661d95073ea1937f01a845ce88faa3",
    ),
    ("linux", "arm64"): (
        "cloudflared-linux-arm64",
        "3d97437c71848bd8df68041e12436b484a661d95073ea1937f01a845ce88faa3",
    ),
}


class CloudflaredInstallError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_cloudflared(
    download_dir: str | Path,
    *,
    client: httpx.Client | None = None,
    system: str | None = None,
    machine: str | None = None,
) -> Path:
    """Install the pinned official binary after two-source checksum validation.

    The release metadata and asset are both fetched from Cloudflare's official
    GitHub repository. The metadata checksum must also equal the code pin before
    the temporary file is atomically promoted.
    """
    platform_key = ((system or platform.system()).lower(), (machine or platform.machine()).lower())
    try:
        asset_name, pinned_digest = _PINNED_ASSETS[platform_key]
    except KeyError as error:
        raise CloudflaredInstallError(
            f"cloudflared {CLOUDFLARED_VERSION} is not pinned for {platform_key[0]}/{platform_key[1]}"
        ) from error

    directory = Path(download_dir).expanduser().resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = directory / f"cloudflared-{CLOUDFLARED_VERSION}-{asset_name.removeprefix('cloudflared-')}"
    if target.exists():
        if not target.is_file() or _sha256_file(target) != pinned_digest:
            raise CloudflaredInstallError("existing pinned cloudflared path has the wrong digest")
        os.chmod(target, 0o700)
        return target

    own_client = client is None
    http = client or httpx.Client(
        timeout=httpx.Timeout(60.0, connect=15.0),
        follow_redirects=True,
        headers={"Accept": "application/vnd.github+json"},
    )
    temporary: Path | None = None
    try:
        release_response = http.get(CLOUDFLARED_RELEASE_API)
        release_response.raise_for_status()
        release = release_response.json()
        if not isinstance(release, dict) or release.get("tag_name") != CLOUDFLARED_VERSION:
            raise CloudflaredInstallError("official release metadata has an unexpected tag")
        body = release.get("body")
        if not isinstance(body, str):
            raise CloudflaredInstallError("official release metadata omitted checksums")
        match = re.search(
            rf"(?m)^\s*{re.escape(asset_name)}:\s*([0-9a-f]{{64}})\s*$", body
        )
        if match is None or match.group(1) != pinned_digest:
            raise CloudflaredInstallError("official release checksum does not match the code pin")
        assets = release.get("assets")
        if not isinstance(assets, list):
            raise CloudflaredInstallError("official release metadata omitted assets")
        download_url = next(
            (
                asset.get("browser_download_url")
                for asset in assets
                if isinstance(asset, dict) and asset.get("name") == asset_name
            ),
            None,
        )
        expected_prefix = (
            "https://github.com/cloudflare/cloudflared/releases/download/"
            f"{CLOUDFLARED_VERSION}/"
        )
        if not isinstance(download_url, str) or not download_url.startswith(expected_prefix):
            raise CloudflaredInstallError("official release asset URL is missing or unexpected")

        descriptor, temp_name = tempfile.mkstemp(
            dir=directory, prefix=f".{target.name}.", suffix=".download"
        )
        temporary = Path(temp_name)
        digest = hashlib.sha256()
        size = 0
        try:
            with os.fdopen(descriptor, "wb") as destination:
                with http.stream("GET", download_url) as download:
                    download.raise_for_status()
                    for chunk in download.iter_bytes(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_DOWNLOAD_BYTES:
                            raise CloudflaredInstallError("cloudflared asset exceeded download bound")
                        digest.update(chunk)
                        destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            temporary = None
            raise
        if digest.hexdigest() != pinned_digest:
            raise CloudflaredInstallError("downloaded cloudflared digest does not match release checksum")
        os.chmod(temporary, 0o700)
        os.replace(temporary, target)
        temporary = None
        return target
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if own_client:
            http.close()
