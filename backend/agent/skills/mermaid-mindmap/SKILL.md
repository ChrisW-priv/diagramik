---
name: mermaid-mindmap
description: Create Mermaid mindmap diagrams. Use this skill whenever the user wants to draw a mind map, brainstorm visually, show a concept hierarchy, or organize topics into a tree structure. Triggers on phrases like "draw a mindmap", "make a mind map", "brainstorm diagram", "show topics as a tree", or whenever the user describes a central concept with branching subtopics and wants it visualized.
---

# Mermaid Mindmap Skill

Use this skill to write Mermaid `mindmap` diagrams. Mermaid mindmaps render as hierarchical tree visualizations starting from a root node.

## Basic structure

```mermaid
mindmap
  root((Central Topic))
    Branch A
      Sub-topic 1
      Sub-topic 2
    Branch B
      Sub-topic 3
      Sub-topic 4
```

Indentation defines the hierarchy — each level of indentation is a child of the item above it.

## Config options

Include a YAML frontmatter block to set the title:

```
---
title: My Mindmap
---
```

## Node shapes

| Syntax | Shape |
|--------|-------|
| `id((text))` | Circle |
| `id[text]` | Rectangle |
| `id(text)` | Rounded rectangle |
| `id{{text}}` | Hexagon |
| `id)text(` | Bang/cloud |
| `id>text]` | Asymmetric |
| `text` (no brackets) | Default (rounded) |

Use `((text))` for the root node — it visually anchors the diagram. Use plain text or `[text]` for most branches and leaves.

## Icons and classes

Add icons using Font Awesome (when supported by the renderer):

```
mindmap
  root((Project))
    ::icon(fa fa-book)
    Planning
    ::icon(fa fa-cogs)
    Execution
```

Apply CSS classes for styling:

```
mindmap
  root((Topic))
    A[Branch]:::urgent
    B[Branch]:::normal
```

## Tips for good mindmaps

- Keep the root node short (1–3 words) — it is the visual anchor
- Limit depth to 3–4 levels; deeper trees become hard to read
- Use parallel phrasing within each branch for consistency
- Group related concepts under the same parent
- Prefer nouns for nodes; save verbs for the root or section headings

## Common patterns

**Brainstorming session:**
```mermaid
mindmap
  root((Product Launch))
    Goals
      Increase signups
      Drive awareness
    Marketing
      Social media
      Email campaign
      Paid ads
    Audience
      Developers
      Startup founders
    Metrics
      Conversion rate
      CAC
      NPS
```

**Concept hierarchy:**
```mermaid
mindmap
  root((Machine Learning))
    Supervised
      Classification
      Regression
    Unsupervised
      Clustering
      Dimensionality reduction
    Reinforcement
      Q-learning
      Policy gradient
```

**Project breakdown:**
```mermaid
---
title: Q3 Roadmap
---
mindmap
  root((Q3 Roadmap))
    Frontend
      Redesign dashboard
      Mobile responsiveness
    Backend
      API v2
      Performance tuning
    Infrastructure
      CI/CD improvements
      Cost optimisation
```
