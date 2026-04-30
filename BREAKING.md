# Breaking changes

Track plugin/skill removals and renames here. The CI validator
(`scripts/validate.py`) reads this file: a skill that exists on `master`
and disappears from a PR will fail CI **unless** its plugin/skill name
appears somewhere in this document.

Format per entry: heading with the date, plugin, and PR; one-line summary;
migration note for users.

---

## 2026-04-30 — `lc-essentials` carve-out (#85)

`lc-essentials` 1.0.0 → 3.1.0. The following skills moved from
`lc-essentials` to the new `lc-advanced-skills` plugin:

- `adapter-assistant`
- `fp-pattern-finder`
- `graphic-output`
- `limacharlie-iac`
- `onboard-new-org`
- `parsing-helper`
- `reporting`
- `sensor-coverage`
- `test-limacharlie-adapter`
- `test-limacharlie-edr`
- `threat-report-evaluation`

**Migration:** install `lc-advanced-skills@lc-marketplace` alongside
`lc-essentials` to retain access. `lc-advanced-skills` requires
`lc-essentials`.

The skill `limacharlie-call` was removed in #85 with no direct
replacement and is tracked in
refractionPOINT/tracking#4229 for follow-up.
