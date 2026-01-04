---
name: add-new-skill
description: Create a new skill for the lc-essentials plugin following best practices and framework conventions. Use when adding LimaCharlie API operations, orchestration workflows, or specialized capabilities to the plugin.
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, TodoWrite
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
- `CALLING_API.md` - API execution architecture
- `SKILL_TEMPLATE.md` - Template structure
- `agents/README.md` - Sub-agent patterns
- `skills/limacharlie-call/SKILL.md` - Core API skill reference

Plugin root: `plugins/lc-essentials/`

## Step 3: CRITICAL FRAMEWORK RULES

**Every skill in lc-essentials MUST follow the LimaCharlie guidelines.**

Run `/init-lc` to load the complete guidelines into your CLAUDE.md. Key rules:

1. **Never call MCP tools directly** - Use Task with `limacharlie-api-executor`
2. **Always load the `limacharlie-call` skill** - prior to using LimaCharlie.
2. **Never write LCQL queries manually** - Use `generate_lcql_query` first
3. **Never generate D&R rules manually** - Use AI generation tools
4. **Never calculate timestamps manually** - Use bash `date` commands
5. **OID is UUID, not org name** - Use `list_user_orgs` to map names to UUIDs
6. **Always specify Return field** for API executor calls
7. **Use sub-agents for parallel operations** - Spawn one agent per item
8. **Use server-side filtering** - `selector` and `online_only` parameters

See `AUTOINIT.md` in the plugin root for complete details.

## Step 4: Skill Structure

Create the skill in: `skills/{skill-name}/SKILL.md` (relative to plugin root)

Required YAML frontmatter:
```yaml
---
name: skill-name-in-kebab-case
description: Clear description with keywords, use cases, and trigger words. Include action verbs (list, get, create, delete) and domain keywords (sensor, rule, detection). Maximum 1024 characters.
allowed-tools: Task, Read, Bash
---
```

**Model Selection** (specified at agent level, not skill level):
- **Haiku**: Fast, cost-effective for straightforward operations (data gathering, API calls, simple analysis)
- **Sonnet**: Complex analysis, entity extraction, multi-step reasoning
- **Opus**: Rarely needed (only for extremely complex tasks)

## Step 5: Skill Categories

Determine which category your skill falls into:

### Category A: API Wrapper Skill
Simple skills that wrap a single API operation.
- Validate parameters
- Delegate to `limacharlie-api-executor`
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
model: haiku|sonnet|opus
skills:
  - lc-essentials:skill-name
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
