import io
import tarfile
from types import SimpleNamespace

import pytest

from lc_eval.execution import docker
from lc_eval.models import AgentConfig


def environment(tmp_path, context_mode='legacy'):
    auth = tmp_path / 'claude-auth'
    auth.write_text('subscription-test-only')
    agent = AgentConfig(adapter='ai_sessions', auth_mode='subscription', auth_file=auth,
                        context_mode=context_mode)
    config = SimpleNamespace(
        agents=[agent],
        sources=SimpleNamespace(worker_image='worker', worker_image_id='worker-id',
                                candidate_image='base', candidate_image_id='base-id',
                                docs=SimpleNamespace(path=tmp_path, commit='a' * 40)),
        ai_sessions=SimpleNamespace(image='runner', image_id='runner-id',
                                    build_manifest={'base_image_id': 'base-id'}),
    )
    journal = SimpleNamespace(intent=lambda *a: 'intent', acquired=lambda *a: None)
    return docker.DockerEnvironment(config, 'test-runner', tmp_path / 'trial', journal)


def test_native_runner_uses_selected_image_without_lc_authority(tmp_path, monkeypatch):
    env = environment(tmp_path)
    commands = []
    monkeypatch.setattr(docker, 'image_id', lambda name: name + '-id')
    monkeypatch.setattr(docker, 'run', lambda argv: commands.append(argv) or 'created')
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w'):
        pass
    monkeypatch.setattr(docker.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout=archive.getvalue()))
    env.start('disposable-oid', 'scoped-worker-key', 'ai_sessions')
    containers = [argv for argv in commands if argv[:2] == ['docker', 'run']]
    candidate = next(argv for argv in containers if env.agent in argv)
    worker = next(argv for argv in containers if env.worker in argv)
    assert 'runner-id' in candidate and 'base-id' not in candidate
    assert 'LC_API_KEY=scoped-worker-key' in worker
    assert not any('scoped-worker-key' in arg or arg.startswith('LC_OID=') for arg in candidate)
    assert '--read-only' in candidate and 'no-new-privileges' in candidate
    assert any('dst=/run/lc-eval,readonly' in arg for arg in candidate)
    assert 'CLAUDE_CONFIG_DIR=/auth' in candidate
    assert (env.work / 'lc-ai').readlink().as_posix() == '/opt/lc-eval/lc-ai'
    assert (env.work / 'documentation').readlink().as_posix() == '/opt/lc-eval/documentation'
    assert len(list((env.root / 'auth/selected').iterdir())) == 2


def test_stale_runner_base_rejected_before_provisioning(tmp_path, monkeypatch):
    env = environment(tmp_path)
    env.config.ai_sessions.build_manifest['base_image_id'] = 'stale'
    monkeypatch.setattr(docker, 'image_id', lambda name: name + '-id')
    monkeypatch.setattr(docker, 'run', lambda argv: pytest.fail('must reject before creating resources'))
    with pytest.raises(RuntimeError, match='base candidate image changed'):
        env.start('disposable-oid', 'scoped-worker-key', 'ai_sessions')


def test_native_runner_bare_masks_all_lc_catalogues(tmp_path, monkeypatch):
    env = environment(tmp_path, 'bare')
    commands = []
    monkeypatch.setattr(docker, 'image_id', lambda name: name + '-id')
    monkeypatch.setattr(docker, 'run', lambda argv: commands.append(argv) or 'created')
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w'):
        pass
    monkeypatch.setattr(docker.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout=archive.getvalue()))
    env.start('disposable-oid', 'scoped-worker-key', 'ai_sessions')
    candidate = next(argv for argv in commands if argv[:2] == ['docker', 'run'] and env.agent in argv)
    rendered = ' '.join(candidate)
    assert '/opt/lc-essentials:rw,noexec,nosuid,nodev,size=4k,mode=000' in rendered
    assert '/opt/lc-eval/lc-ai:rw,noexec,nosuid,nodev,size=4k,mode=000' in rendered
    assert not (env.work / 'lc-ai').exists()
    assert (env.work / 'documentation').is_symlink()


def test_ai_sessions_lc_ai_rejects_context_pin_different_from_image(tmp_path, monkeypatch):
    env = environment(tmp_path, 'lc_ai')
    env.config.context = SimpleNamespace(lc_ai=SimpleNamespace(commit='a' * 40))
    env.config.ai_sessions.lc_ai = SimpleNamespace(commit='b' * 40)
    monkeypatch.setattr(docker, 'image_id', lambda name: name + '-id')
    with pytest.raises(RuntimeError, match='does not match'):
        env.start('disposable-oid', 'scoped-worker-key', 'ai_sessions')
