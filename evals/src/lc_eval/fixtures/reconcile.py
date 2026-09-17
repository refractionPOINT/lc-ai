"""Reconcile multiple configuration records while preserving unrelated state."""
from copy import deepcopy
import asyncio
import hashlib
import json

from .hive import set_record, snapshot
from ..execution.broker import CommandSpec, _COMMANDS

PERMISSIONS = ['org.get', 'lookup.get', 'lookup.get.mtd', 'lookup.set', 'lookup.set.mtd',
               'dr.list', 'dr.set']
COMMANDS = {('hive', verb): CommandSpec(
    value_options=frozenset({'--hive-name', '--key', '--input-file', '--comment', '--tag-add', '--tag-rm'}),
    flag_options=frozenset({'--enabled', '--disabled'}),
    path_options=frozenset({'--input-file'}),
    fixed_values=(('--hive-name', frozenset({'lookup', 'dr-general'})),))
    for verb in ('list', 'get', 'set')}
COMMANDS = {**{command: spec for command, spec in _COMMANDS.items()
               if command[0] in {'lookup', 'dr'}}, **COMMANDS}


def state(cli, oid):
    return {h: snapshot(cli, oid, h) for h in ('lookup', 'dr-general')}


def provision(config, cli, journal, trial_id, oid, seed, root):
    suffix = hashlib.sha256(str(seed).encode()).hexdigest()[:10]
    lookup, rule = 'owners-' + suffix, 'prod-rule-' + suffix
    record = {'data': {'lookup_data': {'application': {'owner': 'platform', 'tier': 'critical'}}},
              'usr_mtd': {'enabled': True, 'tags': ['eval', 'managed'], 'comment': 'Managed ownership'}}
    detection = {'data': {'detect': {'event': 'LC_EVAL_CONFIG', 'op': 'is', 'path': 'event/environment', 'value': 'production'},
                          'respond': [{'action': 'report', 'name': 'eval-config-production'}]},
                 'usr_mtd': {'enabled': True, 'tags': ['eval', 'managed'], 'comment': 'Managed production rule'}}
    desired = {'lookup': {lookup: record}, 'dr-general': {rule: detection}}
    # Every variant has an unrelated record; partial variants include stale and
    # already-correct records so blind append/replace strategies are observable.
    distractor = deepcopy(record)
    distractor['usr_mtd']['comment'] = 'Unrelated: retain exactly'
    set_record(cli, oid, 'lookup', lookup + '-archive', distractor)
    if seed % 3 != 0:
        stale = deepcopy(record)
        stale['data']['lookup_data']['application']['owner'] = 'legacy'
        set_record(cli, oid, 'lookup', lookup, stale)
    if seed % 3 == 2:
        set_record(cli, oid, 'dr-general', rule, detection)
    baseline = state(cli, oid)
    expected = deepcopy(baseline)
    for hive, records in desired.items():
        for name, value in records.items():
            # Server metadata carries defaults; preserve them for existing rows.
            current = deepcopy(baseline[hive].get(name, {'data': {}, 'usr_mtd': {'enabled': True, 'tags': None, 'comment': '', 'expiry': 0, 'ui_actions': None}}))
            current['data'] = value['data']
            current['usr_mtd'].update(value['usr_mtd'])
            expected[hive][name] = current
    return {'desired': desired, 'baseline': baseline, 'expected': expected,
            'public': {'organization_id': oid},
            'public_files': {'desired-records.json': json.dumps(desired, indent=2)},
            'cli_notice': 'For this scenario hive list/get/set also supports dr-general. Reconcile the supplied records using any permitted CLI commands; do not replace entire collections.'}


def collect(config, cli, oid, fixture, root):
    return {'state': state(cli, oid)}


async def reference(fixture, env, bad=False):
    from ..execution.docker import run
    if bad:
        return 'Intentionally made no configuration changes.'
    for hive, records in fixture['desired'].items():
        for name, value in records.items():
            (env.work / 'record.json').write_text(json.dumps(value))
            await asyncio.to_thread(run, ['docker', 'exec', env.agent, 'limacharlie', 'hive', 'set',
                '--hive-name', hive, '--key', name, '--input-file', '/work/record.json'])
    return 'Reconciled the named lookup and rule.'
