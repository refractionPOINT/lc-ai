#!/usr/bin/env python3
"""Validate a capability bundle and its documentation/CLI compatibility, offline."""
import argparse
import json
import pathlib
import re
import subprocess
import sys


class InvalidBundle(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidBundle(message)


def safe_file(root, relative):
    require(isinstance(relative, str) and relative, 'reference must be a nonempty string')
    path = pathlib.Path(relative)
    require(not path.is_absolute() and '..' not in path.parts, f'unsafe reference: {relative}')
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root.resolve()), f'reference escapes root: {relative}')
    require(resolved.is_file(), f'missing file: {relative}')
    return resolved


def string_list(value, label, nonempty=True):
    require(isinstance(value, list), f'{label}: expected list')
    require(not nonempty or bool(value), f'{label}: empty list')
    require(all(isinstance(x, str) and x.strip() for x in value), f'{label}: invalid entry')
    require(len(value) == len(set(value)), f'{label}: duplicate entry')


def cli_help(cli, command):
    try:
        result = subprocess.run([cli, *command.split(), '--ai-help'], capture_output=True,
                                text=True, timeout=20, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise InvalidBundle(f'CLI command unavailable: {command or "root"}: {exc}') from exc
    require('AI Help' in result.stdout, f'CLI did not return AI help: {command}')
    return result.stdout


def validate(root, docs_root=None, cli=None):
    catalog = json.loads(safe_file(root, 'catalog.json').read_text())
    require(catalog.get('schema_version') == 1, 'unsupported catalog schema_version')
    require(re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', catalog.get('version', '')), 'invalid version')
    require(safe_file(root, 'CORE.md').stat().st_size > 0, 'empty CORE.md')
    capabilities = catalog.get('capabilities')
    require(isinstance(capabilities, list) and capabilities, 'empty capabilities')
    ids, mapped_roots = set(), set()
    for cap in capabilities:
        require(isinstance(cap, dict), 'invalid capability')
        cid = cap.get('id')
        require(isinstance(cid, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', cid), 'invalid capability id')
        require(cid not in ids, f'duplicate capability: {cid}')
        ids.add(cid)
        for key in ['name', 'description']:
            require(isinstance(cap.get(key), str) and cap[key].strip(), f'{cid}: missing {key}')
        for key in ['keywords', 'cli_roots', 'references', 'permissions', 'operations']:
            string_list(cap.get(key), f'{cid}.{key}')
        expected_path = f'capabilities/{cid}/SKILL.md'
        require(cap.get('instructions') == expected_path, f'{cid}: noncanonical instruction path')
        body = safe_file(root, expected_path).read_text()
        require(body.startswith('---\n'), f'{cid}: missing frontmatter')
        front, sep, content = body[4:].partition('\n---\n')
        require(sep and content.strip(), f'{cid}: empty instructions')
        fields = dict(line.split(':', 1) for line in front.splitlines() if ':' in line)
        require(fields.get('name', '').strip() == cid, f'{cid}: frontmatter name mismatch')
        description = fields.get('description', '').strip()
        try:
            description = json.loads(description) if description.startswith('"') else description
        except ValueError as exc:
            raise InvalidBundle(f'{cid}: invalid description') from exc
        require(description == cap['description'], f'{cid}: description mismatch')
        for ref in cap['references']:
            require(not pathlib.Path(ref).is_absolute() and '..' not in pathlib.Path(ref).parts, f'{cid}: unsafe documentation path')
            require(f'`{ref}`' in body, f'{cid}: undiscoverable reference {ref}')
            if docs_root:
                safe_file(docs_root, ref)
        mapped_roots.update(cap['cli_roots'])
    disk_ids = {p.parent.name for p in (root / 'capabilities').glob('*/SKILL.md')}
    require(ids == disk_ids, f'uncataloged or missing capability directories: {ids ^ disk_ids}')
    surface = json.loads(safe_file(root, 'fixtures/cli-surface.json').read_text())
    string_list(surface.get('roots'), 'CLI roots')
    known = set(surface['roots'])
    excluded = surface.get('excluded_roots', {})
    require(isinstance(excluded, dict) and all(isinstance(v, str) and v for v in excluded.values()), 'exclusions need reasons')
    require(not mapped_roots.intersection(excluded), 'mapped roots also excluded')
    require(mapped_roots | set(excluded) == known, f'CLI coverage mismatch: {(mapped_roots | set(excluded)) ^ known}')
    scenarios = json.loads(safe_file(root, 'fixtures/scenarios.json').read_text())
    require(scenarios.get('schema_version') == 1, 'unsupported scenario schema')
    scenario_ids, covered = set(), set()
    for scenario in scenarios.get('scenarios', []):
        sid = scenario.get('id')
        require(isinstance(sid, str) and sid and sid not in scenario_ids, 'missing/duplicate scenario id')
        scenario_ids.add(sid)
        require(scenario.get('capability') in ids, f'{sid}: unknown capability')
        covered.add(scenario['capability'])
        require(isinstance(scenario.get('initial_state'), dict), f'{sid}: missing initial state')
        require(isinstance(scenario.get('prompt'), str) and scenario['prompt'].strip(), f'{sid}: missing prompt')
        assertions = scenario.get('assertions')
        require(isinstance(assertions, list) and assertions, f'{sid}: no observable acceptance assertions')
        for assertion in assertions:
            require(isinstance(assertion.get('path'), str) and assertion['path'] and 'equals' in assertion, f'{sid}: invalid assertion')
        string_list(scenario.get('forbidden_events'), f'{sid}: forbidden events', False)
        require(scenario.get('evidence_required') is True, f'{sid}: evidence must be required')
    require(covered == ids, f'capabilities without acceptance scenarios: {ids-covered}')
    if cli:
        live = set(re.findall(r'^- \*\*([^*]+)\*\*', cli_help(cli, ''), re.M))
        require(live == known, f'live CLI root coverage drift: {live ^ known}; update catalog or explicit exclusions')
        required = set(surface.get('required_commands', [])) | set(surface.get('required_options', {}))
        for command in sorted(required):
            help_text = cli_help(cli, command)
            for option in surface.get('required_options', {}).get(command, []):
                require(option in help_text, f'CLI option missing: {command} {option}')
    return {'capabilities': len(ids), 'cli_roots': len(mapped_roots), 'scenarios': len(scenario_ids),
            'documentation_checked': docs_root is not None, 'cli_checked': cli is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle-root', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent)
    parser.add_argument('--docs-root', type=pathlib.Path)
    parser.add_argument('--cli', help='Pinned CLI executable; only --ai-help is invoked, no API calls')
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.bundle_root, args.docs_root, args.cli), sort_keys=True))
    except (InvalidBundle, ValueError, OSError, TypeError, KeyError) as exc:
        print(f'INVALID: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
