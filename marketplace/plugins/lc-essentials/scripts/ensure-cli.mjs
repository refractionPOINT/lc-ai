#!/usr/bin/env node
// ensure-cli.mjs -- LimaCharlie CLI auto-detection and installation
//
// Used by the lc-essentials SessionStart hook to ensure the `limacharlie` CLI
// is installed and on PATH. Outputs JSON to stdout following the Claude Code
// SessionStart hook protocol.
//
// This is the canonical, readable version. A compacted copy is inlined in
// hooks/hooks.json (because CLAUDE_PLUGIN_ROOT is broken for hooks, see
// https://github.com/anthropics/claude-code/issues/24529). When that bug is
// fixed, hooks.json should reference this file directly:
//   "command": "node \"${CLAUDE_PLUGIN_ROOT}/scripts/ensure-cli.mjs\""
//
// Exit codes:
//   0 -- always (never block session start)

import { execFileSync, execSync } from "child_process";
import { existsSync, appendFileSync } from "fs";
import { homedir, platform } from "os";
import { join, dirname } from "path";

const isWin = platform() === "win32";
const home = homedir();
const envFile = process.env.CLAUDE_ENV_FILE || "";

// ---------------------------------------------------------------------------
// Binary discovery
// ---------------------------------------------------------------------------

function findBinary(name) {
  // 1) Check PATH via which/where
  try {
    const cmd = isWin ? "where" : "which";
    return execFileSync(cmd, [name], {
      encoding: "utf8",
      timeout: 5_000,
    })
      .trim()
      .split("\n")[0];
  } catch {
    /* not on PATH */
  }

  // 2) Check well-known directories
  const dirs = [join(home, ".local", "bin"), join(home, ".uv", "bin")];
  if (isWin) {
    dirs.push(join(home, "AppData", "Roaming", "Python", "Scripts"));
  }
  for (const dir of dirs) {
    const candidate = join(dir, isWin ? `${name}.exe` : name);
    if (existsSync(candidate)) return candidate;
  }

  return null;
}

function getVersion(bin) {
  try {
    return execFileSync(bin, ["--version"], {
      encoding: "utf8",
      timeout: 5_000,
    }).trim();
  } catch {
    return "unknown";
  }
}

// ---------------------------------------------------------------------------
// Installation
// ---------------------------------------------------------------------------

function tryInstall() {
  const methods = [
    { tool: "uv", cmd: "uv tool install limacharlie" },
    { tool: "pipx", cmd: "pipx install limacharlie" },
    { tool: "pip", cmd: "pip install --user limacharlie" },
    { tool: "pip3", cmd: "pip3 install --user limacharlie" },
  ];

  for (const m of methods) {
    if (!findBinary(m.tool)) continue;
    try {
      execSync(m.cmd, { encoding: "utf8", timeout: 120_000, stdio: "pipe" });
      const bin = findBinary("limacharlie");
      if (bin) return { method: m.tool, bin };
    } catch {
      // PEP 668, permission error, network error -- try next method
    }
  }

  return null;
}

// ---------------------------------------------------------------------------
// PATH persistence via CLAUDE_ENV_FILE
// ---------------------------------------------------------------------------

function ensurePath(binPath) {
  if (!envFile || !binPath) return;
  const dir = dirname(binPath);
  const sep = isWin ? ";" : ":";
  if (!(process.env.PATH || "").split(sep).includes(dir)) {
    appendFileSync(envFile, `export PATH="${dir}:$PATH"\n`);
  }
}

// ---------------------------------------------------------------------------
// Output (SessionStart hook protocol)
// ---------------------------------------------------------------------------

function output(systemMessage, additionalContext) {
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "SessionStart",
        additionalContext,
      },
      ...(systemMessage ? { systemMessage } : {}),
    }),
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

let bin = findBinary("limacharlie");

if (bin) {
  // Fast path: already installed (~10ms)
  const ver = getVersion(bin);
  ensurePath(bin);
  output("", `limacharlie CLI is available (${ver}).`);
  process.exit(0);
}

// Not found -- check Python availability (required for the CLI package)
const python = findBinary("python3") || findBinary("python");
if (!python) {
  output(
    "\x1b[33m[lc-essentials] Python 3 not found. Install Python 3.9+ then run: pip install limacharlie\x1b[0m",
    "ERROR: limacharlie CLI is NOT installed. Python 3 is not available. " +
      'The user must install Python 3.9+ and then run "pip install limacharlie".',
  );
  process.exit(0);
}

// Python found -- attempt auto-install
const result = tryInstall();
if (result) {
  ensurePath(result.bin);
  const ver = getVersion(result.bin);
  output(
    `\x1b[32m[lc-essentials] Installed limacharlie CLI (${ver}) via ${result.method}\x1b[0m`,
    `limacharlie CLI was auto-installed (${ver}) via ${result.method} and is ready to use.`,
  );
} else {
  output(
    "\x1b[33m[lc-essentials] Could not auto-install limacharlie CLI. Run: pip install limacharlie\x1b[0m",
    "WARNING: limacharlie CLI is NOT installed. Auto-install failed. " +
      'The user must run "pip install limacharlie" or "pipx install limacharlie" or "uv tool install limacharlie".',
  );
}

process.exit(0);
