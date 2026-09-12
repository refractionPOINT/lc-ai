#!/usr/bin/env python3
"""Grade observed scenario outcomes; never executes an agent or calls production.

Observations must be collected by an independent runner/adjudicator from tool
traces and resulting resource state, not copied from an agent's final answer.
"""
import argparse
import json
import pathlib
import sys

MISSING = object()


def get_path(value, path):
    for key in path.split('.'):
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return value


def grade(scenario, observation):
    failures = []
    for assertion in scenario['assertions']:
        actual = get_path(observation, assertion['path'])
        expected = assertion['equals']
        # bool and int equality is not evidence equivalence.
        if actual is MISSING or type(actual) is not type(expected) or actual != expected:
            failures.append({'path': assertion['path'], 'expected': expected,
                             'actual': '<missing>' if actual is MISSING else actual})
    events = observation.get('events')
    if not isinstance(events, list) or not all(isinstance(e, dict) and isinstance(e.get('type'), str) for e in events):
        failures.append({'reason': 'missing or invalid event trace'})
        events = []
    forbidden = set(scenario.get('forbidden_events', []))
    for event in events:
        if event['type'] in forbidden:
            failures.append({'reason': 'forbidden event', 'type': event['type']})
    # Require an independently captured evidence reference for every asserted fact.
    evidence = observation.get('evidence', {})
    for assertion in scenario['assertions']:
        refs = evidence.get(assertion['path']) if isinstance(evidence, dict) else None
        if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r.strip() for r in refs):
            failures.append({'path': assertion['path'], 'reason': 'missing evidence reference'})
    return {'id': scenario['id'], 'passed': not failures, 'failures': failures}


def evaluate(scenarios, observations):
    by_id = {}
    for observation in observations:
        sid = observation.get('id')
        if not isinstance(sid, str) or sid in by_id:
            raise ValueError('missing or duplicate observation id')
        by_id[sid] = observation
    known = {s['id'] for s in scenarios}
    unknown = set(by_id) - known
    if unknown:
        raise ValueError(f'unknown scenarios: {sorted(unknown)}')
    results = []
    for scenario in scenarios:
        if scenario['id'] not in by_id:
            results.append({'id': scenario['id'], 'passed': False, 'failures': [{'reason': 'not run'}]})
        else:
            results.append(grade(scenario, by_id[scenario['id']]))
    return {'passed': sum(r['passed'] for r in results), 'total': len(results), 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('observations', type=pathlib.Path)
    parser.add_argument('--scenarios', type=pathlib.Path, default=pathlib.Path(__file__).parent / 'fixtures/scenarios.json')
    args = parser.parse_args()
    try:
        scenarios = json.loads(args.scenarios.read_text())['scenarios']
        observations = json.loads(args.observations.read_text())['observations']
        result = evaluate(scenarios, observations)
        print(json.dumps(result, indent=2))
        return 0 if result['passed'] == result['total'] else 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'INVALID EVALUATION: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
