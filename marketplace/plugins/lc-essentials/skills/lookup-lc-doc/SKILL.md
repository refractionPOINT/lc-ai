---
name: lookup-lc-doc
description: Search and retrieve LimaCharlie documentation from the local docs/ folder. Use when users ask about LimaCharlie platform features, SDKs, APIs, D&R rules, LCQL, sensors, outputs, extensions, integrations, or any LimaCharlie-related topics. Covers platform documentation, Python SDK, and Go SDK.
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
- **Any LimaCharlie topic**: General questions about capabilities or how to use features

## What This Skill Does

This is a thorough documentation lookup tool that:

1. Searches comprehensively for relevant keywords across the `docs/` folder
2. Identifies ALL relevant documentation files (not just one)
3. Reads multiple files to gather complete information
4. Returns comprehensive content to fully answer the user's question

## How to Use - BE THOROUGH

When a user asks about LimaCharlie, gather information from MULTIPLE sources:

### 1. Search Comprehensively

Use Grep with multiple searches to find ALL relevant files:

- **Try multiple keywords**: Search for variations and related terms
  - Example: For D&R rules, search for "D&R", "detection", "response", "rules"
- **Search multiple locations**:
  - `docs/limacharlie/` for platform documentation
  - `docs/python-sdk/` for Python SDK docs
  - `docs/go-sdk/` for Go SDK docs
- **Use different patterns**: Try both specific terms and broader searches
- **Check file paths**: Look at Grep results to identify promising files from their paths

### 2. Read Multiple Files

**IMPORTANT**: Don't stop at the first file. Read ALL relevant files found:

- Read the top 3-5 most relevant files (or more if needed)
- Read files with different perspectives (overview, examples, API reference, tutorials)
- If files reference related topics, read those too
- Combine information from multiple sources for a complete answer

### 3. Provide Comprehensive Response

- Include information from all files read
- Organize content logically (overview → details → examples)
- Mention which files the information came from
- If the answer spans multiple topics, include all relevant documentation

## Search Strategy

For thorough results, follow this pattern:

**Step 1**: Initial broad search
```
Grep for main keyword in docs/limacharlie/
Grep for main keyword in docs/python-sdk/ (if SDK-related)
```

**Step 2**: Review results and search for related terms
```
Look at file paths to identify relevant sections
Search for synonyms or related concepts
```

**Step 3**: Read multiple files in parallel
```
Read top 3-5 relevant files using multiple Read calls
Don't just read one file - gather comprehensive information
```

## Example Workflow (Thorough)

```
User: "How do I write LCQL queries?"

1. Search:
   - Grep for "LCQL" in docs/limacharlie/
   - Grep for "query" in docs/limacharlie/
   - Review results: find syntax docs, examples, reference guides

2. Read multiple files:
   - Read LCQL syntax documentation
   - Read LCQL examples file
   - Read getting started with LCQL
   - Read any query-related tutorials

3. Respond with comprehensive answer combining all sources
```

## Key Principle: COMPLETENESS

- **Don't stop at one file**: Read multiple relevant files
- **Don't skip examples**: If there are example files, read them
- **Don't ignore SDK docs**: If question involves SDKs, check SDK folders too
- **Don't assume**: If unsure, search for related terms and read more files

Be thorough - it's better to provide complete information from multiple files than incomplete information from just one.
