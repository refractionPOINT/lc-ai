---
name: lookup-lc-doc
description: Search and retrieve LimaCharlie documentation from GitHub repositories. Use when users ask about LimaCharlie platform features, SDKs, APIs, D&R rules, LCQL, sensors, outputs, extensions, integrations, AI skills, agents, or any LimaCharlie-related topics.
allowed-tools:
  - WebFetch
  - Read
---

# Looking Up LimaCharlie Documentation

Use this skill proactively whenever a user asks about LimaCharlie features, configuration, or implementation.

## When to Use

Invoke this skill when users ask about:

- **Platform features**: D&R rules, LCQL queries, sensors, events, outputs, extensions
- **APIs**: REST API usage, authentication, endpoints
- **SDKs**: Python SDK or Go SDK usage, examples, methods
- **Configuration**: Setting up integrations, adapters, outputs
- **Getting started**: Tutorials, quick start guides, installation
- **AI capabilities**: Skills, agents, commands available in LimaCharlie AI
- **Any LimaCharlie topic**: General questions about capabilities or how to use features

## Documentation Sources

Documentation is fetched from two GitHub repositories using WebFetch:

| Repository | Base URL |
|------------|----------|
| Platform docs | `https://raw.githubusercontent.com/refractionPOINT/documentation/master/` |
| AI skills/agents | `https://raw.githubusercontent.com/refractionPOINT/lc-ai/master/` |

## How to Use - DYNAMIC DISCOVERY

### Step 1: Discover Available Content

**ALWAYS start by fetching index/navigation files to discover the current structure:**

```
# For platform documentation - fetch the main index
WebFetch: https://raw.githubusercontent.com/refractionPOINT/documentation/master/docs/index.md

# For AI skills/agents - fetch the summary files
WebFetch: https://raw.githubusercontent.com/refractionPOINT/lc-ai/master/marketplace/plugins/lc-essentials/README.md
WebFetch: https://raw.githubusercontent.com/refractionPOINT/lc-ai/master/marketplace/plugins/lc-essentials/SKILLS_SUMMARY.md
```

These index files contain links to all available documentation. Parse the links to discover:
- Available categories and sections
- File paths for specific topics
- Related documentation that may be relevant

### Step 2: Follow Links from Index Files

After fetching index files, extract the file paths from links in the markdown content:
- Links appear as `[text](path/to/file.md)` or `[:icon: text](path/to/file.md)`
- Construct full URLs by combining base URL + path
- Identify which links are relevant to the user's question

### Step 3: Fetch Relevant Documentation

Based on what you discovered in the index files, fetch the specific documentation:

```
# Construct URLs dynamically from discovered paths
WebFetch: {base_url}/{discovered_path}
```

**Fetch multiple relevant files in parallel** - don't stop at one file.

### Step 4: Provide Comprehensive Response

- Include information from all files fetched
- Organize content logically (overview -> details -> examples)
- Mention which documentation sources the information came from
- If the answer spans multiple topics, include all relevant documentation

## Example Workflow

```
User: "How do I write D&R rules?"

1. Discover structure:
   WebFetch: https://raw.githubusercontent.com/refractionPOINT/documentation/master/docs/index.md
   -> Parse the markdown to find links related to "Detection", "Response", "D&R", "rules"
   -> Discover paths like: limacharlie/doc/Detection_and_Response/detection-and-response-rules.md

2. Fetch discovered docs (in parallel):
   WebFetch: https://raw.githubusercontent.com/refractionPOINT/documentation/master/docs/{discovered_path_1}
   WebFetch: https://raw.githubusercontent.com/refractionPOINT/documentation/master/docs/{discovered_path_2}
   (paths extracted from index file links)

3. Respond with comprehensive answer combining all sources
```

## Key Principles

- **Dynamic discovery**: NEVER hardcode file paths - always discover them from index files
- **Use WebFetch**: All documentation is fetched via raw.githubusercontent.com URLs
- **Parse links**: Extract file paths from markdown links in index/summary files
- **Be thorough**: Fetch multiple relevant files, not just one
- **Parallel fetches**: Use multiple WebFetch calls in parallel for efficiency
- **Combine sources**: Information may span both repositories
