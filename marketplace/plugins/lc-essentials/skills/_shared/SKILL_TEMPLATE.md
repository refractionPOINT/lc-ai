# Skill Template

This is the canonical template for lc-essentials skills. Use this as a reference when creating or updating skills.

## Frontmatter

```yaml
---
name: skill-name
description: Clear description with trigger keywords. Use when [specific scenarios].
allowed-tools:
  - Task              # Required for spawning sub-agents
  - Read              # Required for reading files
  - Bash              # Required for shell commands (limacharlie CLI, timestamps, etc.)
  - Skill             # Only if skill invokes other skills
  - AskUserQuestion   # Only if skill prompts user
  - WebFetch          # Only if skill fetches web content
  - WebSearch         # Only if skill searches web
  - Glob              # Only if skill searches files
  - Grep              # Only if skill searches content
---
```

**Important**: Never include `mcp__*` tools in allowed-tools. Skills use the `limacharlie` CLI directly via Bash.

## Structure

```markdown
# Skill Title

Brief description of what this skill does.

---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

```bash
limacharlie <noun> <verb> --oid <oid> --output yaml [flags]
```

For command help: `limacharlie <command> --ai-help`
For command discovery: `limacharlie discover`

### Critical Rules

| Rule | Wrong | Right |
|------|-------|-------|
| **CLI Access** | Call MCP tools or spawn api-executor | Use `Bash("limacharlie ...")` directly |
| **Output Format** | `--output json` | `--output yaml` (more token-efficient) |
| **Filter Output** | Pipe to jq/yq | Use `--filter JMESPATH` to select fields |
| **LCQL Queries** | Write query syntax manually | Use `limacharlie ai generate-query` first |
| **Timestamps** | Calculate epoch values | Use `date +%s` or `date -d '7 days ago' +%s` |
| **OID** | Use org name | Use UUID (call `limacharlie org list` if needed) |

---

## When to Use

Use this skill when:
- [Scenario 1]
- [Scenario 2]
- [Scenario 3]

## Workflow

### Phase 1: [Name]

[Description]

### Phase 2: [Name]

[Description]

## [Additional sections as needed]
```

## Skill-Specific Additions

### For Detection Skills

Add after the Critical Rules table:

```markdown
### D&R Rule Generation

Never write D&R YAML manually:
1. `limacharlie ai generate-detection --description "..." --oid <oid> --output yaml` - Generate detection logic
2. `limacharlie ai generate-response --description "..." --oid <oid> --output yaml` - Generate response actions
3. `limacharlie rule validate --detect '...' --respond '...' --oid <oid>` - Validate before deploy
```

### For Multi-Org Skills

Add parallel spawning pattern:

```markdown
### Parallel Execution

Spawn one agent per organization in a SINGLE message:

```
Task(subagent_type="lc-essentials:...", prompt="...org1...")
Task(subagent_type="lc-essentials:...", prompt="...org2...")
Task(subagent_type="lc-essentials:...", prompt="...org3...")
```

**CRITICAL**: All Task calls must be in one message for true parallelism.
```

## Documentation-Only Skills

Skills that don't use LimaCharlie APIs (like `lookup-lc-doc`, `ask`, `add-new-skill`) skip the "LimaCharlie Integration" section entirely.
