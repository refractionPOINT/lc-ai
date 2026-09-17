"""Exact desired-state and preservation checks across multiple Hive families."""
from copy import deepcopy

from .base import assertion


_DERIVED_LOOKUP_DATA = {'_LC_INDICATORS': None, '_LC_METADATA': None}


def _semantic_record(hive, record):
    """Normalize unordered tags and the known backend-generated lookup index."""
    value = deepcopy(record)
    if hive == 'lookup' and isinstance(value, dict):
        data = value.get('data')
        if isinstance(data, dict) and data.get('optimized_lookup_data') == _DERIVED_LOOKUP_DATA:
            data.pop('optimized_lookup_data')
    if isinstance(value, dict):
        metadata = value.get('usr_mtd')
        if isinstance(metadata, dict):
            tags = metadata.get('tags')
            if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
                metadata['tags'] = sorted(tags)
    return value


def verify(manifest, fixture, frozen, evidence):
    observed = evidence.get('state')
    if not isinstance(observed, dict):
        return [assertion('config.observed', 'unknown', explanation='Independent configuration snapshot missing.')]
    target_ok = True
    unrelated_ok = True
    membership_ok = True
    for hive, expected in fixture['expected'].items():
        current = observed.get(hive, {})
        membership_ok &= set(current) == set(expected)
        for name, value in expected.items():
            actual = _semantic_record(hive, current.get(name, {}))
            wanted = _semantic_record(hive, value)
            if name in fixture['desired'][hive]:
                target_ok &= actual.get('data') == wanted['data']
                target_ok &= actual.get('usr_mtd') == wanted['usr_mtd']
            else:
                unrelated_ok &= actual == wanted
    return [assertion(ident, 'pass' if passed else 'fail', expected=True, observed=bool(passed), explanation=why)
            for ident, passed, why in [
                ('config.desired_exact', target_ok, 'Named records have requested data and metadata.'),
                ('config.unrelated_preserved', unrelated_ok, 'Unrelated configuration is unchanged.'),
                ('config.record_sets_exact', membership_ok, 'No missing or duplicate additional records exist.')]]
