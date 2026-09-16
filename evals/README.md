# LimaCharlie CLI agent eval

Evaluate how effectively and efficiently AI agents operate LimaCharlie through its CLI. Tasks supply the security criteria; this measures platform operation, not cybersecurity judgment.

The initial live loop is implemented and verified: Claude Code and Codex passed all eight planned trials across Hive updates, complete search exports and webhook routing, including two Hive repeats. Development now focuses on adding capabilities and improving experiments.

| I want to… | Start here |
|---|---|
| Set up, run an eval, inspect results or recover cleanup | [Running evals](RUNNING.md) |
| Add a scenario, fixture, verifier or harness | [Adding evals](ADDING_EVALS.md) |
| Understand the implemented lifecycle and trust boundaries | [Architecture](ARCHITECTURE.md) |
| Choose the next capability to cover | [Coverage and expansion](DESIGN.md), [capability catalog](catalog/capabilities.yaml) |
| Inspect the initial proof | [Acceptance record](ACCEPTANCE.md), [sanitized results](results/initial-proof-v2.json) |
| Inspect the AI Sessions runner test | [Harness proof](AI_SESSIONS_PROOF.md), [sanitized results](results/ai-sessions-proof.json) |
| Investigate CLI issues found during evaluation | [CLI findings](CLI_FINDINGS.md) |

The live profile uses existing subscriptions with time/turn/tool limits and token accounting; dollar cost is unknown. Runtime credentials, raw transcripts and fixture evidence stay outside the checkout. Each trial creates and cleans up its own organization.

Scenarios are harness-independent in meaning and grading, but the current implementation still has explicit scenario dispatch. Adding YAML alone does not register an eval. The local `ai_sessions` adapter runs the native Go runner and SDK bridge with pinned plugins and documentation; the hosted Workspace adapter remains unsupported. See [Running evals](RUNNING.md) for setup and scope.

The [initial build history](history/README.md) is retained for provenance, not as the active backlog. Keep the running and extension guides current when changing behavior; preserve dated evidence rather than rewriting old results.
