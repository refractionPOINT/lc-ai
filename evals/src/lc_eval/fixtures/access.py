"""Rotate a scoped integration key and verify its authority independently."""
import asyncio
import hashlib
import json
import time

import httpx

from .organization import unwrap
from ..execution.broker import CommandSpec

PERMISSIONS = ['org.get', 'apikey.ctrl']
COMMANDS = {
    ('api-key', 'list'): CommandSpec(value_options=frozenset({'--name'})),
    ('api-key', 'create'): CommandSpec(value_options=frozenset({'--name', '--permissions'})),
    ('api-key', 'delete'): CommandSpec(value_options=frozenset({'--key-hash'}), flag_options=frozenset({'--confirm'})),
}


def inventory(cli, oid):
    data = cli.api(oid, 'GET', f'orgs/{oid}/keys')
    return data.get('api_keys', data)


def stable_inventory(cli, oid, timeout_seconds, retry_seconds=2, stable_samples=3):
    """Wait for default extension-owned keys to finish materializing."""
    deadline = time.monotonic() + timeout_seconds
    previous = None
    consecutive = 0
    latest = None
    while time.monotonic() < deadline:
        latest = inventory(cli, oid)
        identity = {(key_hash, row.get('name', row.get('key_name')))
                    for key_hash, row in latest.items()}
        platform_ready = any(
            isinstance(name, str) and name.startswith('_ext-') for _, name in identity
        )
        if not platform_ready:
            previous = None
            consecutive = 0
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(retry_seconds, remaining))
            continue
        if identity == previous:
            consecutive += 1
            if consecutive >= stable_samples:
                return latest
        else:
            previous = identity
            consecutive = 1
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(retry_seconds, remaining))
    raise RuntimeError('Default organization API keys did not stabilize')


def mint(secret, oid):
    response = httpx.post('https://jwt.limacharlie.io', data={'secret': secret, 'oid': oid, 'expiry': 60}, timeout=30)
    if response.status_code == 200:
        token = response.json().get('jwt')
        if not isinstance(token, str):
            raise RuntimeError('Scoped-key verification token missing')
        return response.status_code, token
    if response.status_code not in (400, 401, 403):
        raise RuntimeError('Scoped-key authentication service unavailable')
    return response.status_code, None


def wait_for_fresh_token_denial(secret, oid, timeout_seconds, retry_seconds=2,
                                consecutive_denials=2):
    """Observe API-key revocation after the JWT service's 10-second key cache.

    This requests a new JWT on every attempt. It does not test or claim that a
    JWT issued before deletion has been revoked.
    """
    started = time.monotonic()
    deadline = started + timeout_seconds
    attempts = []
    denied_in_a_row = 0
    while time.monotonic() < deadline:
        code, _ = mint(secret, oid)
        denied = code in (400, 401, 403)
        denied_in_a_row = denied_in_a_row + 1 if denied else 0
        attempts.append({
            'attempt': len(attempts) + 1,
            'status_code': code,
            'fresh_token_denied': denied,
            'elapsed_seconds': max(0, time.monotonic() - started),
        })
        if denied_in_a_row >= consecutive_denials:
            return {
                'state': 'revoked',
                'attempt_count': len(attempts),
                'consecutive_denials': denied_in_a_row,
                'elapsed_seconds': max(0, time.monotonic() - started),
                'attempts': attempts,
                'scope': 'fresh_token_issuance',
            }
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(retry_seconds, remaining))
    return {
        'state': 'timeout',
        'attempt_count': len(attempts),
        'consecutive_denials': denied_in_a_row,
        'elapsed_seconds': max(0, time.monotonic() - started),
        'attempts': attempts,
        'scope': 'fresh_token_issuance',
    }


def provision(config, cli, journal, trial_id, oid, seed, root):
    suffix = hashlib.sha256(str(seed).encode()).hexdigest()[:10]
    old, new, unrelated = (prefix + suffix for prefix in ('integration-old-', 'integration-new-', 'unrelated-'))
    stable_inventory(cli, oid, min(90, config.lc.readiness_seconds), stable_samples=8)
    created = unwrap(cli.invoke(['api-key', 'create', '--name', old, '--permissions', 'org.get,sensor.list'], oid))
    old_secret = next(created[k] for k in ('api_key', 'secret', 'key') if isinstance(created.get(k), str))
    cli.invoke(['api-key', 'create', '--name', unrelated, '--permissions', 'org.get'], oid)
    baseline = stable_inventory(cli, oid, min(30, config.lc.readiness_seconds))
    old_hash = next(k for k, v in baseline.items() if v.get('name', v.get('key_name')) == old)
    code, _ = mint(old_secret, oid)
    if code != 200:
        raise RuntimeError('Initial integration key did not authenticate')
    return {'baseline': baseline, 'old_hash': old_hash, '_old_secret': old_secret, 'new_name': new,
            'trial_id': trial_id,
            'expected_permissions': ['org.get', 'sensor.list'],
            'public': {'organization_id': oid, 'old_key_name': old, 'new_key_name': new},
            'cli_notice': 'For this scenario api-key list/create/delete are permitted. New keys are restricted to read-only scopes. Write the new key creation JSON to /work/integration-key.json; do not include its secret in the final response.'}


def collect(config, cli, oid, fixture, root):
    frozen = json.loads((root / 'frozen.json').read_text())
    artifact = frozen.get('files', {}).get('/work/integration-key.json', {})
    secret = None
    if artifact.get('kind') == 'file':
        try:
            value = unwrap(json.loads(artifact['content']))
            secret = next((value[k] for k in ('api_key', 'secret', 'key') if isinstance(value.get(k), str)), None)
        except (ValueError, TypeError, AttributeError):
            pass
    after = inventory(cli, oid)
    probes = {'new_authenticates': False, 'read_allowed': False, 'admin_denied': False}
    if secret:
        _, token = mint(secret, oid)
        if token:
            headers = {'Authorization': 'Bearer ' + token}
            read = httpx.get(f'https://api.limacharlie.io/v1/sensors/{oid}', headers=headers, timeout=30)
            denied = httpx.get(f'https://api.limacharlie.io/v1/orgs/{oid}/keys', headers=headers, timeout=30)
            if read.status_code >= 500 or denied.status_code >= 500:
                raise RuntimeError('Scoped-key probe service unavailable')
            probes.update(new_authenticates=True, read_allowed=read.status_code == 200,
                          admin_denied=denied.status_code in (401, 403))
    if fixture['old_hash'] in after:
        revocation = {
            'state': 'old_key_present', 'attempt_count': 0,
            'consecutive_denials': 0, 'elapsed_seconds': 0,
            'attempts': [], 'scope': 'fresh_token_issuance',
        }
    else:
        revocation = wait_for_fresh_token_denial(
            fixture['_old_secret'], oid, config.limits.verification_seconds)
    return {'keys': after, 'probes': probes, 'old_secret_revoked': revocation['state'] == 'revoked',
            'revocation_observation': revocation,
            'secret_hash': hashlib.sha256(secret.lower().encode()).hexdigest() if secret else None}


async def reference(fixture, env, bad=False):
    from ..execution.docker import run
    # Quiet ensures the secret artifact contains one JSON document, not prose.
    value = await asyncio.to_thread(run, ['docker', 'exec', env.agent, 'limacharlie', '--output', 'json',
        'api-key', 'create', '--name', fixture['new_name'], '--permissions', 'org.get,sensor.list'])
    from .local_cli import decode_json
    (env.work / 'integration-key.json').write_text(json.dumps(unwrap(decode_json(value))))
    if not bad:
        await asyncio.to_thread(run, ['docker', 'exec', env.agent, 'limacharlie', 'api-key', 'delete',
            '--key-hash', fixture['old_hash'], '--confirm'])
    return 'New integration key created; rotation completed.'
