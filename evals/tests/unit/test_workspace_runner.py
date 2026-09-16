from __future__ import annotations

import json

import pytest
from aiohttp import ClientSession, web

from lc_eval.execution.workspace_runner import (
    ALLOWED_TOOLS,
    DENIED_TOOLS,
    PLUGINS,
    PROFILE_INSTRUCTIONS,
    LocalControlPlane,
    ProtocolError,
    read_oauth_token,
    validate_completion,
)


def control() -> LocalControlPlane:
    return LocalControlPlane(
        trial_id="trial-123",
        session_token="session-secret",
        config_token="config-secret",
        oauth_token="oauth-secret",
        model="claude-test",
        max_turns=30,
        prompt="perform the task",
    )


@pytest.mark.parametrize(
    "document",
    [
        {"accessToken": "token"},
        {"oauthData": {"accessToken": "token"}},
        {"claudeAiOauth": {"accessToken": "token"}},
        {"claudeOauth": {"accessToken": "token"}},
    ],
)
def test_read_oauth_token_supported_native_shapes(tmp_path, document) -> None:
    path = tmp_path / ".credentials.json"
    path.write_text(json.dumps(document))
    assert read_oauth_token(path) == "token"


def test_read_oauth_token_rejects_missing_or_ambiguous_values(tmp_path) -> None:
    path = tmp_path / ".credentials.json"
    path.write_text("{}")
    with pytest.raises(ProtocolError, match="no unique"):
        read_oauth_token(path)
    path.write_text(json.dumps({"accessToken": "one", "oauthData": {"accessToken": "two"}}))
    with pytest.raises(ProtocolError, match="no unique"):
        read_oauth_token(path)


async def start(control_plane: LocalControlPlane):
    runner = web.AppRunner(control_plane.app())
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    control_plane.base_url = f"http://127.0.0.1:{port}"
    return runner


async def test_config_exchange_is_authenticated_and_fresh() -> None:
    cp = control()
    runner = await start(cp)
    try:
        async with ClientSession() as session:
            response = await session.post(
                cp.base_url + "/internal/config/exchange",
                headers={"X-Session-Token": cp.session_token},
                json={"session_id": cp.trial_id, "config_token": cp.config_token},
            )
            assert response.status == 200
            body = await response.json()
            assert body == {
                "session_id": cp.trial_id,
                "session_token": cp.session_token,
                "provider": "anthropic",
                "cred_type": "oauth_token",
                "credential": "oauth-secret",
                "interaction_proxy_url": cp.base_url,
                "permission_mode": "acceptEdits",
                "allowed_tools": ALLOWED_TOOLS,
                "denied_tools": DENIED_TOOLS,
                "system_prompt_suffix": PROFILE_INSTRUCTIONS,
                "max_turns": 30,
                "initial_prompt": "perform the task",
                "model": "claude-test",
                "one_shot": True,
                "plugins": PLUGINS,
                "profile_memories": [],
                "resume_mode": False,
            }
            # Persistence and LimaCharlie authority must never enter the runner config.
            assert not {
                "lc_credentials",
                "profile_id",
                "workspace_binding",
                "sdk_session_id",
                "archive_path",
            }.intersection(body)

            denied = await session.post(
                cp.base_url + "/internal/config/exchange",
                headers={"X-Session-Token": cp.session_token},
                json={"session_id": cp.trial_id, "config_token": "wrong"},
            )
            assert denied.status == 401
    finally:
        await runner.cleanup()


async def test_runner_websocket_relays_native_events(capsys) -> None:
    cp = control()
    runner = await start(cp)
    try:
        async with ClientSession() as session:
            ws = await session.ws_connect(
                cp.base_url + f"/internal/runner/{cp.trial_id}/ws",
                headers={"X-Session-Token": cp.session_token},
            )
            event = {
                "type": "result",
                "payload": {"input_tokens": 4, "output_tokens": 2, "subtype": "success"},
            }
            await ws.send_json(event)
            await ws.close()
        assert cp.ws_connected.is_set()
        assert cp.saw_result
        assert json.loads(capsys.readouterr().out) == event
    finally:
        await runner.cleanup()


async def test_runner_paths_tokens_status_and_archive_are_scoped() -> None:
    cp = control()
    runner = await start(cp)
    headers = {"X-Session-Token": cp.session_token}
    try:
        async with ClientSession() as session:
            assert (await session.post(
                cp.base_url + f"/internal/sessions/{cp.trial_id}/heartbeat", headers=headers
            )).status == 204
            assert (await session.post(
                cp.base_url + "/internal/sessions/other/heartbeat", headers=headers
            )).status == 401
            assert (await session.post(
                cp.base_url + f"/internal/sessions/{cp.trial_id}/heartbeat",
                headers={"X-Session-Token": "wrong"},
            )).status == 401

            bad = await session.post(
                cp.base_url + f"/internal/sessions/{cp.trial_id}/status",
                headers=headers,
                json={"status": "pending"},
            )
            assert bad.status == 400
            terminal = await session.post(
                cp.base_url + f"/internal/sessions/{cp.trial_id}/status",
                headers=headers,
                json={"status": "terminated"},
            )
            assert terminal.status == 204
            assert cp.terminal_status == "terminated"

            upload = await session.post(
                cp.base_url + f"/internal/sessions/{cp.trial_id}/workspace-upload-url",
                headers=headers,
            )
            upload_url = (await upload.json())["upload_url"]
            assert f"/internal/archive/{cp.trial_id}?token=" in upload_url
            assert (await session.put(upload_url, data=b"archive bytes")).status == 201
            assert (await session.put(
                cp.base_url + f"/internal/archive/{cp.trial_id}?token=wrong", data=b"x"
            )).status == 401
            assert (await session.post(
                cp.base_url + f"/internal/sessions/{cp.trial_id}/workspace-archived",
                headers=headers,
            )).status == 200
    finally:
        await runner.cleanup()


def test_completion_requires_clean_native_result_and_terminal_status() -> None:
    cp = control()
    with pytest.raises(ProtocolError, match="status 7"):
        validate_completion(7, cp)
    with pytest.raises(ProtocolError, match="top-level result"):
        validate_completion(0, cp)
    cp.ws_connected.set()
    cp.saw_result = True
    cp.terminal_status = "failed"
    with pytest.raises(ProtocolError, match="successful terminal"):
        validate_completion(0, cp)
    cp.terminal_status = "terminated"
    validate_completion(0, cp)


async def test_websocket_rejects_bad_token_and_wrong_session() -> None:
    cp = control()
    runner = await start(cp)
    try:
        async with ClientSession() as session:
            with pytest.raises(Exception):
                await session.ws_connect(
                    cp.base_url + f"/internal/runner/{cp.trial_id}/ws?token=wrong"
                )
            with pytest.raises(Exception):
                await session.ws_connect(
                    cp.base_url + "/internal/runner/other/ws?token=session-secret"
                )
    finally:
        await runner.cleanup()
