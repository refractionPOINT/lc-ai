from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

from lc_eval.receiver import bootstrap


def test_ensure_cloudflared_verifies_official_metadata_and_asset(
    tmp_path: Path, monkeypatch
) -> None:
    asset = b"fake pinned cloudflared binary"
    digest = hashlib.sha256(asset).hexdigest()
    name = "cloudflared-linux-amd64"
    monkeypatch.setitem(bootstrap._PINNED_ASSETS, ("linux", "test64"), (name, digest))
    asset_url = (
        "https://github.com/cloudflare/cloudflared/releases/download/"
        f"{bootstrap.CLOUDFLARED_VERSION}/{name}"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == bootstrap.CLOUDFLARED_RELEASE_API:
            return httpx.Response(
                200,
                request=request,
                json={
                    "tag_name": bootstrap.CLOUDFLARED_VERSION,
                    "body": f"SHA256 Checksums:\n{name}: {digest}\n",
                    "assets": [{"name": name, "browser_download_url": asset_url}],
                },
            )
        assert str(request.url) == asset_url
        return httpx.Response(200, request=request, content=asset)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        executable = bootstrap.ensure_cloudflared(
            tmp_path, client=client, system="linux", machine="test64"
        )
    assert executable.read_bytes() == asset
    assert executable.stat().st_mode & 0o777 == 0o700


def test_ensure_cloudflared_rejects_release_checksum_drift(
    tmp_path: Path, monkeypatch
) -> None:
    name = "cloudflared-linux-amd64"
    pinned = "a" * 64
    monkeypatch.setitem(bootstrap._PINNED_ASSETS, ("linux", "test64"), (name, pinned))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={
                "tag_name": bootstrap.CLOUDFLARED_VERSION,
                "body": f"{name}: {'b' * 64}\n",
                "assets": [],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        try:
            bootstrap.ensure_cloudflared(
                tmp_path, client=client, system="linux", machine="test64"
            )
        except bootstrap.CloudflaredInstallError as error:
            assert "checksum" in str(error)
        else:
            raise AssertionError("release checksum drift was accepted")
