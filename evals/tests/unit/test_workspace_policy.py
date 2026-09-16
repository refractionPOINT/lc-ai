import pytest

from lc_eval.execution.workspace_policy import apply_policy_overlay
from lc_eval.execution.workspace_runner import ALLOWED_TOOLS, DENIED_TOOLS
from lc_eval.smoke import native_policy_checks


SOURCE = '''
class Bridge:
    def options(self):
        opts = ClaudeAgentOptions(
        )
        return opts

    def message(self, subtype, data):
            if subtype == "init" and data.get("session_id"):
                pass
'''


def test_overlay_restricts_options_and_verifies_real_inventory(tmp_path):
    path = tmp_path / 'bridge.py'
    path.write_text(SOURCE)
    record = apply_policy_overlay(path)
    assert record['original_bridge_sha256'] != record['patched_bridge_sha256']
    namespace = {'ClaudeAgentOptions': lambda **kwargs: kwargs}
    exec(compile(path.read_text(), str(path), 'exec'), namespace)
    bridge = namespace['Bridge']()
    assert bridge.options() == {'tools': ALLOWED_TOOLS, 'disallowed_tools': DENIED_TOOLS}
    events = []
    bridge.send_system = lambda *args: events.append(args)
    bridge.message('init', {'session_id': 'session', 'tools': ALLOWED_TOOLS})
    assert events == [('eval_tool_inventory', {'tools': ALLOWED_TOOLS})]
    for tool in DENIED_TOOLS:
        with pytest.raises(RuntimeError, match='forbidden'):
            bridge.message('init', {'session_id': 'session', 'tools': [tool]})
    with pytest.raises(RuntimeError, match='omitted'):
        bridge.message('init', {'session_id': 'session'})


def test_overlay_refuses_changed_source_and_double_application(tmp_path):
    path = tmp_path / 'bridge.py'
    path.write_text('unknown bridge')
    with pytest.raises(ValueError, match='bridge changed'):
        apply_policy_overlay(path)
    assert path.read_text() == 'unknown bridge'
    path.write_text(SOURCE)
    apply_policy_overlay(path)
    # A fresh archive is required; never silently stack policy edits.
    with pytest.raises(ValueError, match='bridge changed'):
        apply_policy_overlay(path)


def test_native_probe_requires_inventory_and_leaf_help(tmp_path):
    (tmp_path / 'agent.stdout').write_text('')
    checks = native_policy_checks(tmp_path)
    assert not checks['sdk_tool_inventory_observed']
    assert not checks['delegation_and_scheduling_absent']
    assert not checks['leaf_help_has_pipeline_example']
