---
title: Sidebar Behaviour and Interactions
date: 2026-04-20
status: accepted
---

## Context

The sidebar (`DiagramsSidebar.vue`) is the primary navigation and management
surface in Diagramik. The interaction model for acting on individual items
differs between mobile (touch-only, no hover, limited width) and desktop
(pointer, hover states available) because the available input primitives differ.

## Problem Statement

What purpose should the sidebar serve, and how should each responsibility
behave across mobile and desktop?

## Decision

**Selected Option:** A single sidebar component covers search, workspace and
diagram management, diagram selection, and user profile access — with
environment-specific interaction patterns for item-level actions.

### Features

**Search (`DiagramsSidebar.vue`, search section):**

A text input with `MagnifyingGlassIcon` filters diagrams and workspaces with
fuzzy matching in real time. While a query is active all workspace sections
collapse and expand only for matching results.

**Workspace & diagram management (`DiagramsSidebar.vue`, workspace and diagram
sections):**

Diagrams are grouped under collapsible workspace sections. Each section is
toggled open or closed via a `ChevronRightIcon` that rotates 90° when expanded.
An "Unassigned" section at the bottom holds diagrams that belong to no
workspace. A `FolderPlusIcon` button at the top creates new workspaces.

Item-level actions (rename, delete, new diagram in workspace) are exposed
differently depending on whether the target is a workspace or a diagram:

- *Workspace kebab menu* (`EllipsisHorizontalIcon`, both mobile and desktop):
  A 3-dot button on each workspace header opens a menu with New diagram,
  Rename, and Delete. The menu is teleported to `<body>` and positioned via
  `getBoundingClientRect()` to escape overflow clipping.

- *Diagram actions — desktop* (`EllipsisHorizontalIcon`, `hidden sm:flex`): A
  3-dot button appears on hover for each diagram item, offering Rename and
  Delete. Same teleport/positioning approach as the workspace menu.

- *Diagram actions — mobile* (`sm:hidden`): The diagram kebab is hidden.
  Instead, swiping a diagram item left slides out a 160 px action panel (two
  80 px buttons): `PencilIcon` (blue, Rename) and `TrashIcon` (red, Delete).
  A 40 px displacement threshold snaps the panel fully open; a rightward swipe
  or displacement below 8 px closes it. Only one item can be open at a time.
  Action buttons fade in progressively as the panel reveals.

- *Drag-and-drop* (`DiagramsSidebar.vue`, drag handlers): On both platforms,
  diagrams can be dragged onto any workspace section or the Unassigned section
  to reassign them. The dragged item renders at 40 % opacity; the target section
  highlights with a blue outline. A drop onto the diagram's current workspace is
  a no-op.

**Diagram selection (`DiagramsSidebar.vue`, diagram item click handler):**

Clicking or tapping a diagram item loads it into the editor. On mobile this
also closes the sidebar overlay.

**User profile & settings (`DiagramsSidebar.vue`, footer section):**

The footer shows the user's avatar (DiceBear identicon or initials fallback)
and display name. Clicking it opens a menu with a link to `/settings`
(`Cog6ToothIcon`) and a sign-out action. Menu position is calculated from the
bottom-left of the viewport to always appear above the footer button.
