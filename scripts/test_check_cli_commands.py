"""Tests for scripts/check_cli_commands.py, run against the real pinned CLI.

    .venv-cli/bin/python -m unittest discover -s scripts
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_cli_commands as chk  # noqa: E402

TREE = chk.load_tree()


def findings(name: str, text: str) -> list[str]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / name
        p.write_text(text)
        return [f.msg for f in chk.check_file(TREE, p)]


def fenced(cmd: str) -> list[str]:
    return findings("x.md", f"```bash\n{cmd}\n```\n")


class CheckerTest(unittest.TestCase):
    def test_valid_commands_pass(self):
        self.assertEqual(fenced("limacharlie case get --case-number <n> --oid <oid> --output yaml"), [])
        self.assertEqual(fenced("limacharlie --output json case get --case-number 3"), [])
        self.assertEqual(fenced("limacharlie task send --sid $SID --task 'dir_list /tmp'"), [])
        self.assertEqual(fenced("limacharlie case add-note --case-number 3 --type general \\\n  --content 'x'"), [])

    def test_unknown_command_and_option(self):
        self.assertTrue(any("no such command" in m for m in fenced("limacharlie sensor isolate --sid x")))
        msgs = fenced("limacharlie case update --id 4 --status in_progress")
        self.assertTrue(any("no such option --id" in m for m in msgs))
        self.assertTrue(any("--case-number is missing" in m for m in msgs))

    def test_required_option_and_enum(self):
        self.assertTrue(any("--sid is missing" in m for m in fenced("limacharlie task send --task os_processes")))
        self.assertTrue(any("invalid value `recommendation`" in m
                            for m in fenced("limacharlie case add-note --case-number 1 --type recommendation")))
        self.assertTrue(any("takes an integer" in m
                            for m in fenced("limacharlie case update --case-number abc")))

    def test_placeholders_are_not_values(self):
        self.assertEqual(
            fenced("limacharlie case create --severity <critical|high|low> --summary x"), [])
        self.assertEqual(fenced("limacharlie case get --case-number $((N + 1))"), [])

    def test_unknown_top_level_command(self):
        self.assertTrue(any("no such command" in m for m in fenced("limacharlie sensr list --oid x")))
        self.assertTrue(any("no such command" in m for m in fenced("echo | limacharlie sensr list")))
        self.assertTrue(any("no such command" in m
                            for m in findings("x.py", 'run(["limacharlie", "sensr", "list"])\n')))
        self.assertTrue(any("no such command" in m for m in findings("x.sh", "limacharlie sensr list\n")))
        # Prose and the Python SDK are not CLI calls.
        self.assertEqual(findings("x.md", "Then run limacharlie sensr to see sensors.\n"), [])
        self.assertEqual(findings("x.py", "from limacharlie import Hive\n"), [])
        self.assertEqual(findings("x.py", 'msg = "Do not run limacharlie and wait"\n'), [])

    def test_option_equals_placeholder(self):
        self.assertEqual(fenced("limacharlie task send --sid=$SID --task=netstat"), [])
        self.assertEqual(fenced("limacharlie --oid=<oid> task send --sid=<sid> --task x"), [])
        self.assertTrue(any("no such option --bogus" in m
                            for m in fenced("limacharlie --oid=$OID case get --case-number 1 --bogus=$X")))

    def test_prose_checks_only_the_command_path(self):
        self.assertEqual(findings("x.md", "Then run limacharlie sensor list to see sensors.\n"), [])
        self.assertTrue(any("no such command" in m
                            for m in findings("x.md", "Then run limacharlie sensor lst to see sensors.\n")))

    def test_positional_argument_rules(self):
        self.assertTrue(any("unexpected argument" in m
                            for m in fenced("limacharlie secret set okta-key --key a")))

    def test_inline_mentions(self):
        # A bare command name in prose is a mention, not a call.
        self.assertEqual(findings("x.md", "Use `limacharlie ai generate-query` first.\n"), [])
        self.assertEqual(findings("x.md", "Use `limacharlie sync push --dry-run` first.\n").__len__(), 1)
        # A sketch with arrows names commands without their options.
        self.assertEqual(fenced("limacharlie ai generate-detection -> limacharlie dr validate"), [])
        # Prose about the CLI itself.
        self.assertEqual(findings("x.md", "The limacharlie CLI is installed.\n"), [])

    def test_mermaid_and_ignore_marker(self):
        self.assertEqual(findings("x.md", "```mermaid\nA[limacharlie dr set]\n```\n"), [])
        self.assertEqual(fenced("# cli-check: ignore\nlimacharlie case update --id 4"), [])

    def test_python_argv_lists(self):
        src = 'run(["docker", "exec", c, "limacharlie", "task", "reliable-send", "--sid", s, "--task", "x"])\n'
        self.assertTrue(any("no such option --task" in m for m in findings("x.py", src)))
        ok = 'run(["limacharlie", "--output", "json", "task", "request", "--sid", s, "--command", "netstat"])\n'
        self.assertEqual(findings("x.py", ok), [])
        self.assertTrue(any("no such command" in m for m in findings("x.py", 'run_lc(["sensor", "lst"], oid)\n')))
        self.assertEqual(findings("x.py", 'x = ("lookup", "dr-general")\n'), [])


if __name__ == "__main__":
    unittest.main()
