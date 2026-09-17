# Harness context profiles

The evaluator uses locally installed Claude Code and Codex **executables and selected authentication files**, not their user configuration directories. Personal skills, memory, project instructions, MCP configuration and previous conversations are not copied into standalone candidate containers. Authentication through a subscription does not import a local conversation.

Each candidate starts with a fresh `/auth` home, a fresh `/work` directory, pinned public documentation under `/docs`, and the controlled LimaCharlie CLI transport. The evaluator records executable/image identities and only passes the model process the environment needed for its configured execution. Repository directories and the operator's home are not mounted as general workspaces.

## Explicit experimental treatments

| Profile | Standalone Claude Code / Codex | AI Sessions |
|---|---|---|
| `bare` | Fresh user context, no LC skill corpus | Native runner with plugin loading disabled and image-resident LC plugin/catalog paths hidden |
| `lc_ai` | Archived LC skills loaded through native user-skill discovery, with pinned supporting files | Archived LC plugins loaded through the native runner, including their initialization context |
| `legacy` | Historical launch settings | Historical plugin-enabled runner settings |

Bare retains CLI help and the same pinned public documentation. It is not a claim that a provider has no system prompt or built-in skills. Provider built-ins remain provider-controlled and are disclosed in context identity. Historical results are not retroactively relabeled as a matched bare/skills experiment.

Claude Code's bare profile uses `--safe-mode` and `--disable-slash-commands` and excludes the `Skill` tool. Its `lc_ai` profile enables native skill loading and the `Skill` tool, while retaining the fresh home, empty MCP configuration and explicit tool allowlist. Thus this comparison includes enabling the native skill system; it is not a claim that the LC corpus is the only possible prompt/tool difference. Codex retains the same launch flags in both modes. AI Sessions explicitly toggles native plugin loading and initialization.

## Corpus and delivery

The LC corpus comes from a full Git commit pin under `context.lc_ai`, never the operator's installed plugin directories or uncommitted working tree. The initial expansion pin contains 43 skills across `lc-essentials`, `lc-advanced-skills`, `lc-fundamentals` and `lc-compliance`.

Standalone skill names are prefixed with their plugin name because the corpus includes distinct skills with the same original name. Supporting scripts inside each skill remain available. Required shared constants and compliance documents are mounted read-only; plugin-root references are transformed to resolve inside the container. The manifest records original and transformed hashes, supporting-file hashes and the transformation inventory. Standalone skill delivery does not execute plugin hooks or add plugin agents/commands.

AI Sessions retains native plugin names, paths and initialization behavior. Its image's LC commit must match the requested context commit. Therefore the skill source is pinned across harnesses, but plugin initialization and provider behavior are **not identical prompts**. Compare bare versus skills within a harness, and retain these differences when interpreting cross-harness results.

## Evidence rather than assumed loading

Runtime checks verify the intended skill file hash or its absence and the hidden paths for the bare native runner. A separate `context-probe` launches a real subscribed harness without an LC organization or platform authority. It asks the harness to inspect a passive documentation skill and return a body sentence that the prompt does not supply.

Probe evidence distinguishes native skill invocation/startup inventory from an explicit skill-file read. An exact body sentence plus an observed invocation or read demonstrates usable content. A read alone is not labeled native discovery. Bare probes require a completed native transcript and no observed LC canary exposure. These probes supplement mount/configuration isolation checks; they are not an exhaustive proof about a provider's internal state.

See [Running evals](RUNNING.md#compare-bare-and-lc-ai-skills-contexts) for configuration and commands, and [results](README.md) for the latest verified probe and task outcomes. Reports group task results by harness, exact context identity and scenario. Ordinary A/A comparisons reject different context identities instead of treating the treatment change as noise.
