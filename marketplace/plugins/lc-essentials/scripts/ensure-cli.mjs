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

// Minimum CLI version the plugin's skills require. The `ai-memory` command
// first shipped in 5.4.0; anything older is upgraded rather than accepted.
const MIN_VERSION = "5.4.0";

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

// "limacharlie, version 5.5.4" -> [5, 5, 4]; null when no version is present.
function parseVersion(text) {
  const m = /(\d+)\.(\d+)\.(\d+)/.exec(text || "");
  return m ? [+m[1], +m[2], +m[3]] : null;
}

// "limacharlie, version 5.3.0" -> "5.3.0", for messages that read as prose.
function shortVersion(text) {
  const v = parseVersion(text);
  return v ? v.join(".") : text;
}

// Unparseable versions are left alone -- an unrecognized build is not worth
// a reinstall loop on every session start.
function isBelowMin(text) {
  const v = parseVersion(text);
  const min = parseVersion(MIN_VERSION);
  if (!v) return false;
  for (let i = 0; i < 3; i++) {
    if (v[i] !== min[i]) return v[i] < min[i];
  }
  return false;
}

// ---------------------------------------------------------------------------
// Installation
// ---------------------------------------------------------------------------

// Releases after 5.3.0 depend on a pre-release package (toon_format>=0.9.0b1),
// which uv refuses to resolve unless --prerelease=allow is passed -- without it
// uv silently settles on 5.3.0. pipx/pip accept the pre-release dependency.
// --prerelease=if-necessary is not a substitute: uv still prefers the older
// all-stable solve and lands back on 5.3.0.
// The force/upgrade flags make these idempotent: this runs only when the CLI is
// missing or below MIN_VERSION, so overwriting an existing install is intended.
function tryInstall() {
  const methods = [
    { tool: "uv", cmd: "uv tool install --force --prerelease=allow limacharlie" },
    { tool: "pipx", cmd: "pipx install --force limacharlie" },
    { tool: "pip", cmd: "pip install --user --upgrade limacharlie" },
    { tool: "pip3", cmd: "pip3 install --user --upgrade limacharlie" },
  ];

  for (const m of methods) {
    if (!findBinary(m.tool)) continue;
    try {
      execSync(m.cmd, { encoding: "utf8", timeout: 120_000, stdio: "pipe" });
      // Accept only if the binary now on PATH actually meets the floor: a
      // method can "succeed" yet leave an older install shadowing it earlier
      // on PATH, in which case the next method should get a turn.
      const bin = findBinary("limacharlie");
      if (bin && !isBelowMin(getVersion(bin))) return { method: m.tool, bin };
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
// Version of an existing but too-old install, if any -- drives the messaging
// below, since "outdated" and "missing" need different guidance.
let outdated = "";

if (bin) {
  // Fast path: already installed and new enough (~10ms)
  const ver = getVersion(bin);
  if (!isBelowMin(ver)) {
    ensurePath(bin);
    output("", `limacharlie CLI is available (${ver}).`);
    process.exit(0);
  }
  outdated = shortVersion(ver);
}

// Missing or outdated -- check Python availability (required for the CLI package)
const python = findBinary("python3") || findBinary("python");
if (!python) {
  if (outdated) {
    ensurePath(bin);
    output(
      `\x1b[33m[lc-essentials] limacharlie CLI ${outdated} predates ${MIN_VERSION}; Python 3 not found to upgrade it.\x1b[0m`,
      `WARNING: limacharlie CLI ${outdated} is installed but older than ${MIN_VERSION}, so commands such as "ai-memory" are unavailable. ` +
        "Python 3 is not available to upgrade it. The user must install Python 3.9+ and then run " +
        '"uv tool install --force --prerelease=allow limacharlie".',
    );
    process.exit(0);
  }
  output(
    "\x1b[33m[lc-essentials] Python 3 not found. Install Python 3.9+ then run: pip install limacharlie\x1b[0m",
    "ERROR: limacharlie CLI is NOT installed. Python 3 is not available. " +
      'The user must install Python 3.9+ and then run "pip install limacharlie".',
  );
  process.exit(0);
}

// Python found -- attempt auto-install / upgrade
const result = tryInstall();
if (result) {
  ensurePath(result.bin);
  const ver = getVersion(result.bin);
  const verb = outdated ? "Upgraded" : "Installed";
  output(
    `\x1b[32m[lc-essentials] ${verb} limacharlie CLI (${ver}) via ${result.method}\x1b[0m`,
    `limacharlie CLI was auto-${outdated ? "upgraded" : "installed"} (${ver}) via ${result.method} and is ready to use.`,
  );
} else if (outdated) {
  ensurePath(bin);
  output(
    `\x1b[33m[lc-essentials] limacharlie CLI ${outdated} predates ${MIN_VERSION} and auto-upgrade failed. Run: uv tool install --force --prerelease=allow limacharlie\x1b[0m`,
    `WARNING: limacharlie CLI ${outdated} is installed but older than ${MIN_VERSION}, so commands such as "ai-memory" are unavailable. Auto-upgrade failed. ` +
      'The user must run "uv tool install --force --prerelease=allow limacharlie" or "pipx install --force limacharlie".',
  );
} else {
  output(
    "\x1b[33m[lc-essentials] Could not auto-install limacharlie CLI. Run: pip install limacharlie\x1b[0m",
    "WARNING: limacharlie CLI is NOT installed. Auto-install failed. " +
      'The user must run "pip install limacharlie" or "pipx install limacharlie" or ' +
      '"uv tool install --prerelease=allow limacharlie".',
  );
}

process.exit(0);
