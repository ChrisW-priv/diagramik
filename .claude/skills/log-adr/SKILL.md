---
name: log-adr
description: Creates Architecture Decision Records (ADRs) in the project's `adl/` directory following a strict, consistent format. Use this skill whenever the user wants to document a technical decision, create an ADR or architecture decision record, add to the ADL, record a decision to use or adopt a technology, or write up why a particular approach was chosen. Even if the user just says "document this decision" or "let's write up why we went with X" — use this skill.
---

# ADR Skill

Architecture Decision Records capture significant technical decisions and their
rationale so future contributors understand not just what was decided, but why.
This skill ensures every ADR follows a consistent, searchable format.

## Workflow

1. **Understand the decision** — if the user hasn't given enough context, ask for:

   - The decision being made (in one clear sentence)
   - What options were on the table
   - Why the chosen option won out
     Ask only what you need; don't interrogate if the user has already provided context.

1. **Derive the title** from the decision, expressed as a short declarative phrase.
   Good titles complete the sentence "We decided to...":

   - "Use Redis for Session Storage"
   - "Adopt a Monorepo Structure"
   - "Replace REST with GraphQL for the Mobile API"

1. **Create the `adl/` directory** at the project root if it doesn't already exist.

1. **Derive the filename** by slugifying the title: lowercase, replace spaces and
   non-alphanumeric characters with hyphens, collapse multiple hyphens, strip leading/
   trailing hyphens. Examples:

   - "Use Redis for Session Storage" → `use-redis-for-session-storage.md`
   - "Adopt a Monorepo Structure" → `adopt-a-monorepo-structure.md`

1. **Write the file** at `adl/<slug>.md` using today's date and the template below.

## File Template

Every ADR must follow this exact structure — no more, no less (unless the user
explicitly requests additional sections):

```markdown
---
title: <Title of the Decision>
date: <YYYY-MM-DD>
status: proposed
---

## Context

<The situation, forces, and background that made this decision necessary. What
prompted us to address this? What constraints or requirements are in play?>

## Problem Statement

<The specific question or problem being decided. This should be crisp — one or two
sentences that make clear exactly what decision needs to be made.>

## Options Considered

### <Option Title>

<Short description of this option.>

**Pros:**

- <benefit>

**Cons:**

- <drawback>

### <Option Title>

<Short description of this option.>

**Pros:**

- <benefit>

**Cons:**

- <drawback>

## Decision

**Selected Option:** <name of the chosen option>

### Rationale

<Why this option was chosen. What made it better than the alternatives? What
trade-offs were accepted? This is the most important section — be honest about
both the benefits and the downsides of the choice.>
```

## Format Rules

**Title is the identifier** — there are no numeric prefixes or serial IDs (no
`0001-`, `ADR-001`, etc.). The title itself is unique and searchable.

**No title heading in the body** — the title lives in the frontmatter and the
filename. Starting the document with `# Use Redis for Session Storage` would be
redundant and is not part of the format.

**Headings start at H2** — the four main sections (Context, Problem Statement,
Options Considered, Decision) are all `##` level. Rationale is `###` because it is
a subsection of Decision.

**Each option is an H3 under Options Considered** — use `###` for each option title.
Pros and cons are bold labels (`**Pros:**` / `**Cons:**`) followed by bullet lists,
not headings. Never group all pros and cons together at the bottom.

**Status values:**

- `proposed` — under discussion, not yet decided (default for new ADRs)
- `accepted` — decision is made and active
- `deprecated` — was accepted but no longer applies
- `superseded` — replaced by a newer ADR (consider noting which one in the Rationale)

Use the status the user specifies; default to `proposed` if not mentioned.
