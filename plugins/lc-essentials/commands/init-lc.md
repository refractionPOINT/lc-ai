---
name: init-lc
description: Initialize the current working directory's CLAUDE.md with LimaCharlie guidelines. Merges AUTOINIT.md content into a '# Using LimaCharlie' section. Safe to run multiple times.
allowed-tools: Read, Write, Edit, Bash, Glob
---

# Initialize LimaCharlie Guidelines

You are initializing the current working directory's CLAUDE.md with LimaCharlie-specific guidelines.

## Instructions

### Step 1: Locate the AUTOINIT.md File

The AUTOINIT.md file is located in the lc-essentials plugin directory. Find it by searching for the plugin:

```bash
find ~/.claude -name "AUTOINIT.md" -path "*lc-essentials*" 2>/dev/null | head -1
```

If not found in ~/.claude, try the marketplace directory where this plugin is installed.

Read the AUTOINIT.md file to get the guidelines content.

### Step 2: Check for Existing CLAUDE.md

Check if a CLAUDE.md file exists in the current working directory.

### Step 3: Merge or Create

**If CLAUDE.md does NOT exist:**
- Create a new CLAUDE.md file with the contents of AUTOINIT.md

**If CLAUDE.md exists:**
- Read the existing CLAUDE.md
- Check if a `# Using LimaCharlie` section already exists (search for the heading)
- **If the section exists**: Replace everything from `# Using LimaCharlie` up to the next `# ` level-1 heading (or end of file) with the AUTOINIT.md content
- **If no section exists**: Append the AUTOINIT.md content at the end of the file (with a blank line separator)

### Step 4: Confirm Success

Report what was done:
- Whether CLAUDE.md was created or updated
- Whether an existing `# Using LimaCharlie` section was replaced

## Example Output

```
LimaCharlie guidelines initialized in ./CLAUDE.md
- Created new CLAUDE.md with LimaCharlie guidelines
```

or

```
LimaCharlie guidelines initialized in ./CLAUDE.md
- Updated existing CLAUDE.md
- Replaced existing '# Using LimaCharlie' section with latest guidelines
```
