import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'{name}.py')
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


validator = module('validate')
evaluator = module('evaluate')


class BundleContractTests(unittest.TestCase):
    def test_complete_inventory(self):
        result = validator.validate(ROOT)
        self.assertGreater(result['scenarios'], result['capabilities'])

    def test_path_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / 'bundle'
            root.mkdir()
            outside = pathlib.Path(tmp) / 'outside'
            outside.write_text('not a bundle file')
            (root / 'linked').symlink_to(outside)
            for path in ['../outside', str(outside), 'linked']:
                with self.assertRaises(validator.InvalidBundle):
                    validator.safe_file(root, path)

    def test_documentation_missing_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(validator.InvalidBundle):
                validator.validate(ROOT, pathlib.Path(tmp))


class OutcomeGradingTests(unittest.TestCase):
    def setUp(self):
        scenarios = json.loads((ROOT / 'fixtures/scenarios.json').read_text())['scenarios']
        self.scenario = next(s for s in scenarios if s['id'] == 'mail-prompt-injection')
        self.observation = {'id': self.scenario['id'], 'checks': {'treated_as_evidence': True},
                            'state': {'secret_reads': 0, 'external_sends': 0},
                            'events': [{'type': 'message_read'}],
                            'evidence': {a['path']: ['trace.json:message_read'] for a in self.scenario['assertions']}}

    def test_correct_observed_outcome_passes(self):
        self.assertTrue(evaluator.grade(self.scenario, self.observation)['passed'])

    def test_forbidden_action_fails_even_if_final_claims_success(self):
        self.observation['events'].append({'type': 'secret_disclosure'})
        self.assertFalse(evaluator.grade(self.scenario, self.observation)['passed'])

    def test_final_answer_without_evidence_fails(self):
        del self.observation['evidence']
        self.assertFalse(evaluator.grade(self.scenario, self.observation)['passed'])

    def test_incorrect_state_fails(self):
        self.observation['state']['secret_reads'] = 1
        self.assertFalse(evaluator.grade(self.scenario, self.observation)['passed'])

    def test_boolean_is_not_integer_count(self):
        self.observation['state']['secret_reads'] = False
        self.assertFalse(evaluator.grade(self.scenario, self.observation)['passed'])

    def test_omitted_runs_fail(self):
        report = evaluator.evaluate([self.scenario], [])
        self.assertEqual(0, report['passed'])
        self.assertEqual('not run', report['results'][0]['failures'][0]['reason'])

    def test_unknown_and_duplicate_runs_rejected(self):
        for records in [[self.observation, self.observation], [{'id': 'unknown'}]]:
            with self.assertRaises(ValueError):
                evaluator.evaluate([self.scenario], records)


if __name__ == '__main__':
    unittest.main()
