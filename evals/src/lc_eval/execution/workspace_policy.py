"""Explicit, fingerprinted eval-only overlay for the native SDK bridge.

Production permission callbacks do not remove every built-in SDK tool. The
controlled profile restricts the built-in tool inventory as well as seeding
the native callbacks. Never apply this overlay to a sibling working tree.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .workspace_runner import ALLOWED_TOOLS, DENIED_TOOLS


def apply_policy_overlay(bridge: Path) -> dict[str, str]:
    source = bridge.read_text()
    original = hashlib.sha256(source.encode()).hexdigest()
    options_anchor = "        opts = ClaudeAgentOptions(\n"
    init_anchor = '            if subtype == "init" and data.get("session_id"):\n'
    if (source.count(options_anchor) != 1 or source.count(init_anchor) != 1
            or '"eval_tool_inventory"' in source):
        raise ValueError("native bridge changed; review the eval tool-policy overlay")
    source = source.replace(
        options_anchor,
        options_anchor
        + f"            tools={ALLOWED_TOOLS!r},\n"
        + f"            disallowed_tools={DENIED_TOOLS!r},\n",
    )
    # Retain the actual CLI inventory, not just our intended option strings.
    source = source.replace(
        init_anchor,
        init_anchor
        + '                inventory = data.get("tools")\n'
        + '                if not isinstance(inventory, list):\n'
        + '                    raise RuntimeError("SDK omitted tool inventory")\n'
        + f'                if set(inventory).intersection({DENIED_TOOLS!r}):\n'
        + '                    raise RuntimeError("SDK exposed a forbidden eval tool")\n'
        + '                self.send_system("eval_tool_inventory", {"tools": inventory})\n',
    )
    compile(source, str(bridge), "exec")
    bridge.write_text(source)
    return {
        "profile": "controlled-cli-v1-native-tools-v1",
        "original_bridge_sha256": original,
        "patched_bridge_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "overlay_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
