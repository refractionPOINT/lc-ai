# Persistent Memory for AI Agents

The `ai_memory` hive gives every AI agent a persistent, file-system-style memory
that survives across sessions. Each agent has its own record (auto-keyed by the
caller's API-key name), and within that record, individual memories are
addressed by a `--memory-name` like `inventory/subdomains.md`.

This document is the design contract every agent in this repo follows. Read it
before adding `ai-memory` references to a new agent prompt.

## Why Memory Matters

Without memory, every session starts from scratch. That has real costs:

- **Cost** — re-discovering the same asset inventory every day burns budget on
  work that produced the same answer 24 hours ago.
- **Stability** — reports drift day-over-day because the agent reaches slightly
  different conclusions from the same data, depending on prompt order, sample
  size, or which facts it stumbled across first.
- **Continuity** — operator feedback ("this is fine, stop alerting") is lost
  the moment the session ends, unless it gets baked into an FP rule or lookup.
- **Coordination** — agents that run on a schedule have no way to tell
  themselves "I covered X yesterday, focus on Y today."

Memory fixes those, but only if it's used with discipline. An agent that spams
memory with per-event garbage is worse than one that doesn't use memory at all.

## What Belongs in Memory

Memory is for **slow-changing facts the agent itself accumulates**. Three
categories cover almost everything:

### 1. Inventory and Topology

Things the org owns, named by the agent over time:

- Subdomains, IPs, certs (exposure team)
- Tenant orgs and their data sources (MDR pipeline)
- GitHub repos, contributors, automation accounts
- Detection coverage map (which TTPs already have rules)
- Hosts grouped by role (jumphost, build server, dev workstation)

These change weekly or monthly, not per session. The agent rebuilds them
lazily — read from memory, diff against fresh data, write back the canonical
state.

### 2. Operator Feedback

Things a human told the agent that should outlive the conversation:

- "Port 22 on `jumphost-01` is intentional — stop flagging it."
- "Dependabot can push to any repo, don't alert on it."
- "Don't isolate hosts tagged `production-critical`, ever."
- "Severity bumps on detection X should default to medium, not high — the
  category is noisy here."

Without memory, these end up in the operator's head and have to be repeated
every shift. With memory, they accumulate into a stable house style.

### 3. Cached Verdicts

Expensive lookups whose answer is stable per input:

- Hash → analysis verdict (malware analyst)
- Domain → reputation classification (intel team)
- IP → infrastructure classification (CDN, hosting, residential)

The cache is by-key, so partial-merge fits naturally: each new analysis is one
extra entry, never a full rewrite.

## What Does NOT Belong in Memory

Don't write any of these to `ai_memory`:

- **Per-case or per-detection details.** Those live on the case itself
  (notes, entities, telemetry). Memory is org-wide; cases are incident-scoped.
- **High-volume key/value tables.** Memory caps at ~1024 entries per record
  and 10MB total. Use the `lookup` hive for ledgers like `exposure-seen` —
  thousands of rows of `port:1.2.3.4:443` belong there, not in memory.
- **Rapidly-changing state.** If you'd rewrite it every session, it's not
  memory — it's working state. Keep it on the case or in a lookup.
- **Anything fabricated or guessed.** Memory has authority. If you write it,
  future sessions will trust it. Only persist verified facts.
- **Anything already in another hive.** Don't mirror SOPs, FP rules, or
  org_notes into memory. Read from the source.
- **Conversation transcripts.** Memory is a knowledge base, not a log.

## Naming Convention

Memory names are filesystem-style paths. Use a category prefix so a future
session (or a different agent) can list and skim:

```
inventory/<topic>.md     # what the org has
feedback/<topic>.md      # what the operator told us
state/<topic>.md         # last-run pointers (timestamps, cursors)
cache/<topic>.md         # cached verdicts by key
notes/<topic>.md         # free-form, last-resort
```

Keep names short and stable. `inventory/subdomains.md` survives across
versions; `inventory/subdomains_2026_05_07.md` does not (it churns daily and
fills the 1024-entry cap).

## Partial-Merge Semantics

The hive merges per-key on every `set`. This is the most important property
to internalize:

| Operation | Effect |
|-----------|--------|
| `ai-memory set --memory-name a.md --content "x"` | Replaces `a.md` only. Other memories untouched. |
| `ai-memory delete --memory-name a.md` | Drops `a.md` only. Equivalent to setting it to JSON null. |
| `ai-memory list --output yaml` | Lists memory names (no content). Cheap. |
| `ai-memory get --memory-name a.md` | Reads one memory. |

Implications:

- **Never read-modify-write the whole record.** That's how memories get
  clobbered when two agents update at once. Touch only the keys you care about.
- **Read what you need.** `list` first to see what's there, then `get` the
  ones you'll actually use. Don't pull every memory into context "just in case."
- **Update is idempotent.** Re-running an inventory build that produces the
  same result is a no-op for memory.

## Read–Diff–Update Workflow

The standard pattern for any agent that maintains long-lived state:

1. **Read** the relevant memory at session start. If it exists, use it as
   ground truth for what you knew last time.
2. **Collect** fresh data from the API/world. Don't skip this step — memory
   is a starting point, not the answer.
3. **Diff** memory against fresh data. The diff is what you report on (new,
   changed, resolved). The fresh data is what you write back.
4. **Update** memory with the canonical post-diff state. Use `--memory-name`
   per key so unrelated memories survive untouched.
5. **Don't update** if you weren't able to verify. A memory wiped to "" is
   worse than one slightly stale.

For a memory that is only ever appended to (caches, allowlists), you can skip
the diff and just upsert new keys.

## Cross-Agent Coordination

Each agent owns its own memory record. Cross-agent data flows through cases
(notes, entities, tags), not through reading a peer's memory. There are
exceptions — a downstream agent in the same scheduled team may read its
upstream agent's inventory record by passing `--key <upstream-agent-name>`.
When an agent does this, it must be documented in the team README so the
contract is explicit.

Default to writing only to your own record. Read from peers only when the
coordination is part of the team design.

## Permissions

Every agent that uses memory needs three hive permissions on the API key:

```
ai_memory.get    # read memories
ai_memory.set    # write memories
ai_memory.del    # drop memories
```

Add these to the agent's README permission table and the `lc-deployer` will
include them when creating the API key.

## CLI Cheat Sheet

```bash
# List all agents that have memory in this org
limacharlie ai-memory list-records --oid <oid> --output yaml

# List your own memories (auto-keyed by your API-key name)
limacharlie ai-memory list --oid <oid> --output yaml

# Read one memory
limacharlie ai-memory get --memory-name inventory/subdomains.md \
    --oid <oid> --output yaml

# Write one memory (replaces only this name)
limacharlie ai-memory set --memory-name inventory/subdomains.md \
    --content "$(cat /tmp/subdomains.md)" --oid <oid>

# Drop one memory
limacharlie ai-memory delete --memory-name inventory/old-topic.md --oid <oid>

# Read another agent's memory (cross-agent coordination, document this in
# the team README before relying on it)
limacharlie ai-memory get --key exposure-asset-discovery \
    --memory-name inventory/subdomains.md --oid <oid> --output yaml
```

See [marketplace/plugins/lc-essentials/AUTOINIT.md](marketplace/plugins/lc-essentials/AUTOINIT.md)
for the full CLI reference.

## Smell Tests

Before writing a memory, ask:

- **Will a session a week from now want to read this back?** If no, don't
  write it.
- **Is it the kind of fact a senior analyst would write on a sticky note?**
  Stable, prose-level, judgment-laden. Yes → memory. Volatile counts and
  per-event data → not memory.
- **Did I verify it this session?** If you're forwarding something the
  operator said without confirming, mark it as feedback (`feedback/...`) so
  a future session knows it's an assertion, not an observation.
- **Would this overwrite something a peer agent wrote?** If you're writing
  to a name another agent owns, stop and route through cases instead.

When in doubt, prefer the case (notes, entities) over memory. Memory is
precious; cases are abundant.
