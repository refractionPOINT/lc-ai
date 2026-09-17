"""Explicit scenario registration; imports are lazy to keep tool startup small."""
from importlib import import_module
import inspect

INITIAL_SCENARIOS = ('hive-preserve-update', 'search-complete-export', 'webhook-production-routing')
EXPANSION = {
    'case-maintain-records': 'cases',
    'native-sensor-onboarding': 'native_sensor',
    'cloudsec-findings-triage': 'cloudsec',
    'config-reconcile-preserve': 'reconcile',
    'access-key-rotation': 'access',
}
SCENARIOS = (*INITIAL_SCENARIOS, *EXPANSION)


def fixture_module(name):
    return import_module('.fixtures.' + EXPANSION[name], package='lc_eval')


def verifier(name):
    return import_module('.verifiers.' + EXPANSION[name], package='lc_eval').verify


async def invoke(function, *args, **kwargs):
    value = function(*args, **kwargs)
    return await value if inspect.isawaitable(value) else value
