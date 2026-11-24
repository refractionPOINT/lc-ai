#!/usr/bin/env python3
"""Check every `limacharlie ...` command written in this repo against the CLI.

The prompts, skills and docs in this repo tell agents to run `limacharlie`
commands. When the CLI renames a command or an option, those texts keep
working-looking commands that the CLI rejects. This script finds every
invocation and checks it against the installed CLI's real click command tree
(no hard-coded command list):

  * the command path (`case entity add`) exists
  * every option (`--case`, `-q`) exists on that command or is a global option
  * required options and required arguments are present
  * literal values of enum options (`click.Choice`) are valid
  * literal values of integer options are integers

Placeholders (`<sid>`, `$SID`, `{{ x }}`, `...`) are never checked as values.
Commands whose invocation shows `--help`, `-h` or `--ai-help` skip the
required-option check.

Run it against the pinned CLI (see scripts/requirements-cli-check.txt):

    python -m venv .venv-cli && .venv-cli/bin/pip install -r scripts/requirements-cli-check.txt
    .venv-cli/bin/python scripts/check_cli_commands.py

Exit status is 1 when anything is found. To silence a line that is not meant
to be a real command (for example an example of a wrong command), put
`cli-check: ignore` on that line or on the line above it.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click

ROOT = Path(__file__).resolve().parent.parent

# File types that can hold commands. Everything else (images, lock files) is skipped.
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".sh", ".py", ".txt", ".toml", ".tmpl", ".j2"}
SKIP_DIRS = {".git", ".venv", ".venv-cli", "node_modules", "__pycache__", ".uv-cache"}
# Files that describe the CLI check itself or contain deliberately wrong commands.
SKIP_FILES = {Path("scripts/check_cli_commands.py"), Path("scripts/test_check_cli_commands.py")}

IGNORE_MARK = "cli-check: ignore"

# `limacharlie` as a command word: not part of a path, a URL, a name or a package.
CMD_RE = re.compile(r"(?<![\w/.@:=-])limacharlie(?=[ \t]+\S)")
SHELL_OPS = {"|", "||", "&", "&&", ";", ";;", "(", ")", "((", "))", ">", ">>", "<", "<<", "2>", "2>&1", "&>", "#", "->", "=>", "→", "│", "┃", "—"}
ELISION = {"...", "…"}
# What may directly precede `limacharlie` when it starts a command (not prose).
COMMAND_LEADERS = ("|", "&&", "||", ";", "(", "`", "$", "&", "{", '"', "'", ">", "-", "*", ":", "\\")
PROSE_BREAKS ={"->", "=>", "→", "│", "┃", "—"}
PLACEHOLDER_RE = re.compile(r"@@PH@@|[<>$`{}]|\.\.\.|\*|^\[|\]$|^\(|\)$|^\?|^\\$")
HELP_FLAGS = {"--help", "-h", "--ai-help"}


def is_placeholder(tok: str) -> bool:
    return bool(PLACEHOLDER_RE.search(tok)) or tok == ""


@dataclass
class Finding:
    path: Path
    line: int
    text: str
    msg: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.msg}\n    {self.text.strip()[:200]}"


@dataclass
class Opt:
    param: click.Parameter
    takes_value: bool


@dataclass
class Tree:
    root: click.Group
    ctx: click.Context
    version: str = ""
    _cache: dict = field(default_factory=dict)

    def sub(self, group: click.Group, name: str):
        if group is self.root:
            return group.get_command(self.ctx, name)
        return group.commands.get(name) if hasattr(group, "commands") else None

    def options(self, cmd: click.Command) -> dict[str, Opt]:
        out: dict[str, Opt] = {}
        for p in cmd.params:
            if not isinstance(p, click.Option):
                continue
            for name in p.opts:
                out[name] = Opt(p, not p.is_flag and not p.count)
            for name in p.secondary_opts:
                out[name] = Opt(p, False)
        return out


def load_tree() -> Tree:
    try:
        import limacharlie
        from limacharlie.cli import cli
    except ImportError as e:  # pragma: no cover
        sys.exit(f"cannot import the limacharlie CLI ({e}); install scripts/requirements-cli-check.txt")
    ctx = click.Context(cli)
    return Tree(cli, ctx, getattr(limacharlie, "__version__", "?"))


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

def iter_files(paths: list[Path]):
    for base in paths:
        if base.is_file():
            yield base
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix not in TEXT_SUFFIXES:
                continue
            rel = p.relative_to(ROOT) if p.is_relative_to(ROOT) else p
            if any(part in SKIP_DIRS for part in rel.parts) or rel in SKIP_FILES:
                continue
            yield p


def logical_lines(text: str, is_json: bool):
    """Yield (first_line_number, joined_text, in_fence) joining `\\` continuations.

    `in_fence` is True inside ``` fences, which is where commands are meant to
    be run rather than described.
    """
    lines = text.split("\n")
    in_fence = False
    fence_lang = ""
    i = 0
    while i < len(lines):
        raw = lines[i]
        start = i + 1
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            fence_lang = stripped.lstrip("`~").strip().lower() if in_fence else ""
            i += 1
            continue
        if in_fence and fence_lang == "mermaid":
            i += 1  # diagram labels, not commands
            continue
        joined = raw
        while re.search(r"\\\\?$", joined.rstrip()) and i + 1 < len(lines):
            joined = re.sub(r"\\\\?$", " ", joined.rstrip()) + lines[i + 1].strip()
            i += 1
        if is_json:
            joined = joined.replace('\\"', '"').replace("\\n", " ")
        yield start, joined, in_fence, (lines[start - 2] if start >= 2 else "")
        i += 1


def inline_spans_with_cmd(line: str) -> list[str]:
    return [s for s in inline_spans(line) if "limacharlie" in s]


def inline_spans(line: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", line)


def tokenize(segment: str) -> list[str]:
    """Split a shell fragment into tokens, tolerating an unbalanced quote."""
    # `<sid>`-style placeholders contain shell operator characters; hide them.
    segment = re.sub(r"\{\{.*?\}\}|\{%.*?%\}", "@@PH@@", segment)  # Jinja
    segment = segment.replace("\\n", " ")  # literal newline escapes in source strings
    segment = re.sub(r"\$\(\([^()]*\)\)|\$\([^()]*\)", "@@PH@@", segment)  # $((a - b)) and $(cmd)
    segment = re.sub(r"<(?![<\s])[^<>\n]{1,80}?>", "@@PH@@", segment)
    for attempt in (segment, segment + '"', segment + "'", segment.rstrip("\"'")):
        try:
            lex = shlex.shlex(attempt, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            lex.commenters = ""
            return list(lex)
        except ValueError:
            continue
    return segment.split()


def commands_in(line: str, strict: bool):  # noqa: D103
    """Yield the token list of each `limacharlie ...` invocation in `line`.

    `strict` is True where the text is meant to be run (fences, scripts,
    backtick spans); in plain prose only the command path is checked.
    """
    for m in CMD_RE.finditer(line):
        prefix = line[:m.start()].rstrip()
        if re.search(r"\b(from|import)$", prefix):
            continue  # `from limacharlie import Hive`: the Python SDK, not the CLI
        if prefix.endswith(('"', "'")) and prefix != "":
            at_pos = "quoted"  # `echo "limacharlie not installed"`: a command only if it has options
        else:
            at_pos = prefix == "" or prefix.endswith(COMMAND_LEADERS) or bool(re.search(r"\b(sudo|then|do|else|exec)$", prefix))
        toks = tokenize(line[m.end():])
        cut = []
        for t in toks:
            if t in SHELL_OPS or t.startswith(("2>", ">", "&>")):
                if t in PROSE_BREAKS:
                    cut.append("…")  # a sketch like `a → b`: the command is not complete
                break
            end = t.endswith("`")
            t = t.rstrip("`")
            if t.startswith("--"):
                t = t.rstrip(".,;:")
            if t:
                cut.append(t)
            if end:
                break
        yield cut, strict, at_pos


# --------------------------------------------------------------------------
# Checking
# --------------------------------------------------------------------------

def check_invocation(tree: Tree, toks: list[str], strict: bool, in_fence: bool, at_pos: bool | str = True) -> list[str]:
    """Return a list of problems with one invocation (tokens after `limacharlie`)."""
    problems: list[str] = []
    root_opts = tree.options(tree.root)
    help_asked = any(t in HELP_FLAGS for t in toks) or any(t in ELISION for t in toks)
    toks = [t for t in toks if t not in ELISION]
    # Option usage notation like `[--oid <oid>]` or `[-q]`: drop the brackets.
    toks = [t.strip("[]") if t.startswith("[") or t.endswith("]") else t for t in toks]
    toks = [t for t in toks if t != ""]

    node: click.Command = tree.root
    path: list[str] = []
    i = 0
    # Walk the command path. Global options may sit anywhere.
    while i < len(toks) and isinstance(node, click.Group):
        t = toks[i]
        if t == "--":
            i += 1
            break
        if t.startswith("-") and not is_placeholder(t.split("=", 1)[0]):
            name = t.split("=", 1)[0]
            opts = {**root_opts, **tree.options(node)}
            if name in opts:
                i += 1 if ("=" in t or not opts[name].takes_value) else 2
                continue
            if strict:
                problems.append(f"unknown option {name} before the command (after `limacharlie {' '.join(path)}`)")
            return problems
        if is_placeholder(t):
            return problems
        if "/" in t:
            return problems  # `config-get/config-set`: a mention of two commands
        mention = t.endswith((":", ","))  # `limacharlie org list: discovery` is prose
        t = t.rstrip(":,")
        sub = tree.sub(node, t)
        if sub is None:
            if not path and not (in_fence or (strict and at_pos)):
                return problems  # prose such as `limacharlie CLI`
            # An unknown word right after `limacharlie` is only reported where
            # the text is meant to be run (fence, script, backtick span, argv list).
            looks_like_call = at_pos is True or (at_pos == "quoted" and any(x.startswith("-") for x in toks[i + 1:]))
            if path or (looks_like_call and re.fullmatch(r"[a-z][a-z0-9-]*", t)):
                problems.append(f"`limacharlie {' '.join(path + [t])}`: no such command"
                                f" (available: {', '.join(sorted(list_subcommands(tree, node)))})")
            return problems
        path.append(t)
        node = sub
        i += 1
        if mention:
            return problems
    if not path:
        return problems
    rest = toks[i:]
    if isinstance(node, click.Group):
        # A group on its own is fine (it prints help); a trailing option is checked above.
        return problems
    if not strict or (not rest and not in_fence):
        return problems  # prose, or a bare `limacharlie x y` named in backticks

    cmdname = "limacharlie " + " ".join(path)
    opts = {**root_opts, **tree.options(node)}  # the command's own options win
    opts.update(tree.options(node))
    seen: set[str] = set()
    positionals: list[str] = []
    j = 0
    after_dd = False
    while j < len(rest):
        t = rest[j]
        if after_dd:
            positionals.append(t)
            j += 1
            continue
        if t == "--":
            after_dd = True
            j += 1
            continue
        if t.startswith("-") and len(t) > 1 and not re.fullmatch(r"-\d+(\.\d+)?", t) \
                and not is_placeholder(t.split("=", 1)[0]):
            name, eq, val = t.partition("=")
            o = opts.get(name)
            if o is None:
                problems.append(f"{cmdname}: no such option {name}")
                j += 1 if eq or (j + 1 >= len(rest) or rest[j + 1].startswith("-")) else 2  # skip its value
                continue
            seen.add(o.param.name)
            if o.takes_value:
                nargs = max(o.param.nargs, 1)
                if eq:
                    vals = [val]
                    j += 1
                else:
                    vals = rest[j + 1: j + 1 + nargs]
                    if len(vals) < nargs:
                        problems.append(f"{cmdname}: option {name} needs a value")
                    j += 1 + nargs
                for v in vals:
                    problems.extend(check_value(cmdname, name, o.param, v))
            else:
                j += 1
            continue
        positionals.append(t)
        j += 1

    if not help_asked:
        for p in node.params:
            if isinstance(p, click.Option) and p.required and p.name not in seen \
                    and not p.envvar and not p.prompt and p.default is None:
                problems.append(f"{cmdname}: required option {p.opts[0]} is missing")
        args = [p for p in node.params if isinstance(p, click.Argument)]
        need = sum(max(a.nargs, 1) for a in args if a.required and a.nargs > 0)
        if len([p for p in positionals if True]) < need and not any(is_placeholder(p) for p in positionals):
            names = ", ".join(a.name.upper() for a in args if a.required)
            problems.append(f"{cmdname}: missing required argument(s) {names}")
        unlimited = any(a.nargs < 0 for a in args)
        if not unlimited and args:
            cap = sum(max(a.nargs, 1) for a in args)
            if len(positionals) > cap:
                problems.append(f"{cmdname}: unexpected extra argument `{positionals[cap]}`"
                                f" (options start with `--`; takes {cap} positional)")
        if not args and positionals:
            problems.append(f"{cmdname}: unexpected argument `{positionals[0]}`"
                            " (this command takes no positional arguments)")
    return problems


def check_value(cmdname: str, optname: str, param: click.Parameter, value: str) -> list[str]:
    if is_placeholder(value):
        return []
    t = param.type
    if isinstance(t, click.Choice):
        choices = list(t.choices)
        ok = value in choices if t.case_sensitive else value.lower() in [c.lower() for c in choices]
        if not ok:
            return [f"{cmdname}: invalid value `{value}` for {optname} (choose from {', '.join(choices)})"]
    elif isinstance(t, (click.types.IntParamType, click.types.IntRange)):
        if not re.fullmatch(r"[+-]?\d+", value):
            return [f"{cmdname}: option {optname} takes an integer, got `{value}`"]
    return []


def list_subcommands(tree: Tree, group: click.Group) -> list[str]:
    return group.list_commands(tree.ctx)


def root_command_names(tree: Tree) -> set[str]:
    if "root" not in tree._cache:
        tree._cache["root"] = set(tree.root.list_commands(tree.ctx))
    return tree._cache["root"]


def check_file(tree: Tree, path: Path) -> list[Finding]:
    try:
        text = path.read_text()
    except (UnicodeDecodeError, OSError):
        return []
    if "limacharlie" not in text and path.suffix != ".py":  # .py: wrapper argv lists omit the name
        return []
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    findings: list[Finding] = []
    is_md = path.suffix == ".md"
    whole_file_is_code = path.suffix in {".sh", ".py"}
    is_json = path.suffix == ".json"
    seen: set[tuple[int, str]] = set()
    for lineno, line, in_fence, prev in logical_lines(text, is_json):
        if "limacharlie" not in line:
            continue
        if IGNORE_MARK in line or IGNORE_MARK in prev:
            continue
        strict_all = (in_fence and not (is_md and inline_spans_with_cmd(line))) or whole_file_is_code or is_json
        candidates: list[tuple[str, bool]] = []
        if strict_all:
            candidates.append((line, True))
        else:
            spans = inline_spans(line)
            for s in spans:
                candidates.append((s, True))
            outside = re.sub(r"`[^`\n]+`", " ", line)
            candidates.append((outside, False))  # prose: command path only
        for chunk, strict in candidates:
            sketch = any(a in chunk for a in PROSE_BREAKS)  # `a → b → c`: bare names, not calls
            for toks, strict_cmd, at_pos in commands_in(chunk, strict):
                if sketch and "…" not in toks:
                    toks = toks + ["…"]
                for msg in check_invocation(tree, toks, strict_cmd, strict_all, at_pos):
                    key = (lineno, msg)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(Finding(rel, lineno, line, msg))
    if path.suffix == ".py":
        lines = text.split("\n")
        for lineno, toks, strict in argv_lists(text, root_command_names(tree)):
            if IGNORE_MARK in lines[lineno - 1] or (lineno >= 2 and IGNORE_MARK in lines[lineno - 2]):
                continue
            for msg in check_invocation(tree, toks, strict, True):
                findings.append(Finding(rel, lineno, lines[lineno - 1], msg))
    return findings


def argv_lists(source: str, root_names: set[str]):
    """Yield (line, tokens) for argv lists like ["limacharlie", "case", "get", "--case-number", n].

    Parsed with `ast`; anything that is not a string literal becomes a
    placeholder, and `*args` becomes an elision (the rest is unknown).
    """
    try:
        module = ast.parse(source)
    except SyntaxError:
        return
    call_args = {id(a) for n in ast.walk(module) if isinstance(n, ast.Call) for a in n.args}
    for node in ast.walk(module):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        for idx, el in enumerate(node.elts):
            if isinstance(el, ast.Constant) and el.value == "limacharlie":
                toks: list[str] = []
                for e in node.elts[idx + 1:]:
                    if isinstance(e, ast.Constant) and isinstance(e.value, str):
                        toks.append(e.value)
                    elif isinstance(e, ast.Starred):
                        toks.append("...")
                    else:
                        toks.append("@@PH@@")
                yield node.lineno, toks, True
                break
        else:
            # A wrapper that adds the binary itself: run_lc(["sensor", "list"]).
            # Only the command path is checked: the wrapper may append options.
            if isinstance(node, ast.List) and id(node) in call_args and len(node.elts) >= 2 \
                    and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts) \
                    and node.elts[0].value in root_names:
                yield node.lineno, [e.value for e in node.elts], False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path, help="files or directories (default: the whole repo)")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    args = ap.parse_args()
    paths = [p.resolve() for p in args.paths] or [ROOT]
    tree = load_tree()
    findings: list[Finding] = []
    n_files = 0
    for f in iter_files(paths):
        n_files += 1
        findings.extend(check_file(tree, f))
    if args.json:
        print(json.dumps([{"path": str(f.path), "line": f.line, "msg": f.msg} for f in findings], indent=1))
    else:
        for f in findings:
            print(f)
    print(f"\nchecked {n_files} files against limacharlie {tree.version}: {len(findings)} problem(s)",
          file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
