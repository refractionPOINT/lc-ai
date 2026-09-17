"""Verify exact key permissions, usable scoped credentials and revocation."""
from .base import assertion


def _permissions(row):
    value = row.get('permissions', row.get('perms', row.get('priv', [])))
    if isinstance(value, str):
        return value.split(',')
    if isinstance(value, dict):
        return [key.replace('+', '.') for key, enabled in value.items() if enabled]
    return value


def _stable_key(row):
    """Discard server-maintained use time while retaining access semantics."""
    stable = {key: value for key, value in row.items() if key not in {'last_used', 'permissions', 'perms', 'priv'}}
    stable['permissions'] = sorted(set(_permissions(row)))
    return stable


def verify(manifest, fixture, frozen, evidence):
    keys = evidence.get('keys')
    if not isinstance(keys, dict):
        return [assertion('access.observed', 'unknown', explanation='Independent key state unavailable.')]
    new = [(h, v) for h, v in keys.items() if v.get('name', v.get('key_name')) == fixture['new_name']]
    permissions = _permissions(new[0][1]) if len(new) == 1 else []
    same = all(h in keys and _stable_key(keys[h]) == _stable_key(row)
               for h, row in fixture['baseline'].items() if h != fixture['old_hash'])
    baseline_hashes = set(fixture['baseline'])
    # Candidate controller credential is created after fixture snapshot.
    candidate_name = 'candidate-' + fixture['trial_id']
    additions = {h for h,v in keys.items()
                 if h not in baseline_hashes and v.get('name', v.get('key_name', '')) != candidate_name}
    checks = [
        ('access.permissions_exact', len(new) == 1 and set(permissions) == set(fixture['expected_permissions'])),
        ('access.secret_matches_key', len(new) == 1 and evidence.get('secret_hash') == new[0][0]),
        ('access.scope_enforced', all(evidence.get('probes', {}).get(k) is True for k in ('new_authenticates','read_allowed','admin_denied'))),
        ('access.old_revoked', fixture['old_hash'] not in keys and evidence.get('old_secret_revoked') is True),
        ('access.unrelated_preserved', same and len(additions) == 1 and bool(new) and new[0][0] in additions),
    ]
    return [assertion(name, 'pass' if value else 'fail', expected=True, observed=bool(value),
                      explanation=name.replace('access.', '').replace('_', ' ') + '.') for name,value in checks]
