# Expansion work — September 16, 2026

Authorized scope: five independently graded workflows (Cases, native endpoint onboarding, Cloud Security findings, configuration reconciliation, scoped-access rotation), plus explicit bare versus pinned lc-ai skill contexts. Work stays on `eval/limacharlie-cli-ai`.

## Execution checklist

- [x] Inspect executable builds, authentication copying, mounts and launch arguments for local-context inheritance.
- [x] Add explicit context selection, pinned corpus identity and context-isolation checks.
- [x] Prove bare and skills-enabled contexts with real native harness probes.
- [x] Implement each scenario's deterministic fixture, public contract, reference, negative reference and verifier.
- [x] Integrate scenario selection, permissions, bounded broker surface, artifact capture and reports.
- [ ] Calibrate feasible scenarios on real disposable organizations; distinguish unavailable prerequisites from agent failures.
- [ ] Run new agent trials with explicit context labels, bounded subscription usage and independent cleanup.
- [ ] Publish verified coverage, measurements and remaining prerequisites in the public README.

Bare means no LimaCharlie skill corpus, personal settings, personal skills, memory or prior conversations. Provider built-in behavior and public CLI/documentation remain available and must be disclosed. Skills-enabled runs use an archived repository revision, never the user's installed plugin directories. Existing historical runs retain their actual context identity; do not relabel them as a matched comparison.

Each scenario must prove platform effects independently. Native sensors must run in disposable isolated containers, never on the user's host. Cloud Security fixtures must use real backend findings rather than mocked responses. Cases, keys and configurations remain inside evaluator-owned organizations. Org teardown is the final resource cleanup boundary.

## Calibration notes

- Offline suite: 320 tests passed; Ruff and whitespace checks passed.
- All six final context probes passed: bare and pinned LC skills for Claude Code, Codex and AI Sessions. Probes establish context availability/isolation, not platform task scores.
- Configuration reconciliation, key rotation, Cases maintenance and Cloud Security each have a correct reference pass and a deliberately bad reference failure on real disposable organizations, with clean teardown.
- Native onboarding enrolled a real isolated Linux endpoint and independently observed its marker process. Final positive/negative calibration is running after correcting online-state verification to use the platform's online sensor listing.
- The deployed Cases backend rejects the pinned CLI's native `case create --detection` representation. Existing-case maintenance is supported; clean-state creation is explicitly unavailable, not a scored agent failure. See [CLI findings](CLI_FINDINGS.md).
- Access revocation verifies fresh token issuance, not invalidation of previously issued JWTs. Native tasking requires signed modules in an executable private data tmpfs; no host mounts, host networking, host PID namespace or added capabilities are used.

## Initial scored expansion matrix

Run seed 51002 sequentially. Compare bare versus pinned skills for Codex on all five new scenarios, and for Claude Code and AI Sessions on configuration reconciliation. This is an initial operational proof, not a statistical estimate of skill benefit. Publish every genuine task outcome and mark the remaining harness/scenario/context combinations untested. Expand the matrix and repetitions after this first proof.
