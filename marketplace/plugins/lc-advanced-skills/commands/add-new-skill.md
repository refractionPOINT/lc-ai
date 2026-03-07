---
name: add-new-skill
description: Create a new skill for the lc-essentials plugin following best practices and framework conventions. Use when adding LimaCharlie API operations, orchestration workflows, or specialized capabilities to the plugin.
allowed-tools:
  - Task
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebFetch
  - WebSearch
  - TodoWrite
argument-hint: "description of what the skill should do"
---

# Add New Skill to lc-essentials Plugin

You are creating a new skill for the **lc-essentials** Claude Code plugin based on the user's description below.

## User's Skill Description

**The user wants a skill that:** $ARGUMENTS

Your job is to create a skill that fulfills this description while conforming to the established framework patterns and conventions.

## Step 1: Research Claude Code Skills Best Practices

First, use the Task tool with `subagent_type="claude-code-guide"` to look up:
- Official Claude Code documentation on creating skills (SKILL.md format)
- Best practices for skill descriptions and discovery optimization
- How skills interact with sub-agents and the Task tool

## Step 2: Review Plugin Framework Documentation

Read these files to understand the lc-essentials framework (paths relative to plugin root):
- `ARCHITECTURE.md` - Plugin hierarchy and design rules
- `skills/_shared/SKILL_TEMPLATE.md` - Canonical skill template (USE THIS)
- `CALLING_API.md` - CLI usage patterns and examples
- `agents/README.md` - Sub-agent patterns

Plugin root: `plugins/lc-essentials/`

## Step 3: CRITICAL FRAMEWORK RULES

**Every skill in lc-essentials MUST follow the LimaCharlie guidelines.**

Run `/init-lc` to load the complete guidelines into your CLAUDE.md. Key rules:

1. **Use the `limacharlie` CLI via Bash** - Never call MCP tools or spawn api-executor agents
2. **Never write LCQL queries manually** - Use `limacharlie ai generate-query` first
3. **Never generate D&R rules manually** - Use `limacharlie ai generate-*` commands
4. **Never calculate timestamps manually** - Use bash `date` commands
5. **OID is UUID, not org name** - Use `limacharlie org list` to map names to UUIDs
6. **Use sub-agents for parallel operations** - Spawn one agent per item
7. **Use server-side filtering** - `selector` and `online_only` parameters

See `AUTOINIT.md` in the plugin root for complete details.

## Step 4: Skill Structure

Create the skill in: `skills/{skill-name}/SKILL.md` (relative to plugin root)

### Frontmatter (YAML List Format Required)

```yaml
---
name: skill-name-in-kebab-case
description: Clear description with keywords, use cases, and trigger words. Include action verbs (list, get, create, delete) and domain keywords (sensor, rule, detection). Maximum 1024 characters.
allowed-tools:
  - Task
  - Read
  - Bash
  - AskUserQuestion   # Only if needed
  - Skill             # Only if invoking other skills
---
```

### Required Preamble (for LimaCharlie-using skills)

After the title and brief description, include this standardized section:

```markdown
---

## LimaCharlie Integration

> **Prerequisites**: Run `/init-lc` to initialize LimaCharlie context.

### LimaCharlie CLI Access

All LimaCharlie operations use the `limacharlie` CLI directly:

\`\`\`bash
limacharlie <noun> <verb> --oid <oid> --output yaml [flags]
\`\`\`

For command help and discovery: `limacharlie <command> --ai-help`

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
```

Add skill-specific rows to Critical Rules table:
- D&R skills: Add row for `limacharlie ai generate-*` requirement
- Parsing skills: Add row for `parsing-helper` skill requirement

**Reference**: See `skills/_shared/SKILL_TEMPLATE.md` for the complete template.

### Model Selection (at agent level)

- **Sonnet**: Fast, cost-effective for straightforward operations (data gathering, API calls, simple analysis)
- **Sonnet**: Complex analysis, entity extraction, multi-step reasoning
- **Opus**: Rarely needed (only for extremely complex tasks)

## Step 5: Skill Categories

Determine which category your skill falls into:

### Category A: API Wrapper Skill
Simple skills that wrap a single API operation.
- Validate parameters
- Execute via `Bash("limacharlie ...")`
- Format and return results

### Category B: Orchestration Skill
Complex skills that coordinate multiple operations.
- Parse user queries
- Fetch required data (e.g., org list)
- Spawn parallel sub-agents (one per item)
- Aggregate and format results

### Category C: Research Skill
Skills that search and combine information.
- Search multiple sources with various keywords
- Read multiple files to gather complete info
- Combine information from multiple sources

## Step 6: Create Supporting Files (if needed)

If your skill needs a dedicated sub-agent, create it in:
`agents/{agent-name}.md` (relative to plugin root)

Agent frontmatter:
```yaml
---
name: agent-name
description: What it does and when to use (determines when Claude invokes it)
model: sonnet|opus
skills: []
---
```

## Step 7: Update Documentation

After creating the skill:
1. Add entry to `SKILLS_SUMMARY.md` (in plugin root)
2. If creating an agent, update `agents/README.md`

## Your Task

Based on the user's description above, create a skill that fulfills their requirements.

**Workflow:**
1. Research Claude Code skills documentation using the `claude-code-guide` agent
2. Read the plugin framework files listed in Step 2
3. Analyze the user's description to determine:
   - What LimaCharlie API functions are needed
   - Which skill category applies (API Wrapper, Orchestration, or Research)
   - Whether a dedicated sub-agent is needed
   - An appropriate skill name (kebab-case)
4. Ask clarifying questions if the description is ambiguous
5. Create the skill following ALL rules in Step 3
6. Create any supporting agents if needed
7. Update documentation files (SKILLS_SUMMARY.md, agents/README.md if applicable)
8. Report what was created with a summary of the skill's capabilities

**Remember:** Every rule in Step 3 is CRITICAL. If the skill violates any of these rules, it WILL break the plugin or produce incorrect results.

## Validation Checklist

Before completing, verify:

- [ ] Frontmatter uses YAML list format for `allowed-tools`
- [ ] Has "LimaCharlie Integration" section with Critical Rules table (if LC-using skill)
- [ ] All LimaCharlie operations use `Bash("limacharlie ...")` directly
- [ ] All Task spawns use `subagent_type=` (not `subagent=`)
- [ ] All Task spawns include `model="sonnet"` (or appropriate model)
- [ ] Timestamps use bash `date +%s` commands (never LLM calculations)
- [ ] OID is always UUID, never org name
- [ ] LCQL queries use `limacharlie ai generate-query` first
- [ ] D&R rules use `limacharlie ai generate-*` commands
- [ ] Updated SKILLS_SUMMARY.md
- [ ] Updated agents/README.md (if new agent created)
