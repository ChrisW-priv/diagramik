---
title: Main Editor Panel Layout Design
date: 2026-04-20
status: accepted
---

## Context

Diagramik is a diagram-as-code editor that must serve users on both desktop
(large-screen, pointer-driven) and mobile (small-screen, touch-driven) devices.
The core editing surface consists of two elements that compete for screen
real-estate: a sidebar (workspace/diagram navigator) and an editor panel
(prompt input on the left, rendered diagram on the right).

Because the frontend is deployed as static HTML to a GCS bucket with no server
at runtime, all layout switching must be handled client-side via CSS and Vue
reactive state. Viewport size cannot drive conditional rendering; only CSS
media queries and CSS custom properties are used for layout differences.

## Problem Statement

How should the sidebar and editor panels be arranged on mobile versus desktop
so that the full feature set is accessible on small screens without wasting
real-estate on large screens?

## Decision

**Selected Option:** Mobile overlay sidebar with top bar; desktop inline
sidebar; single `md` breakpoint throughout.

### Rationale

**Overall structure (`DiagramsPage.vue`):**
The page is a full-viewport flex container. The single breakpoint used
everywhere is Tailwind's `md:` (768 px). No intermediate breakpoints exist.

**Mobile-only top bar (`DiagramsPage.vue`):**

- A slim header bar (`flex md:hidden`) is the first element in the page
  layout on mobile. It does not exist on desktop.
- Contains the hamburger button (sets `mobileSidebarOpen = true`) and the
  app brand name.

**Sidebar — desktop (≥ 768 px) (`DiagramsSidebar.vue`):**

- Rendered as an inline flex item, always visible alongside the main content.
- Width is driven by a CSS custom property `--sidebar-w` and transitions
  smoothly between 56 px (icon-only rail) and 256 px (expanded) via
  `width 200 ms ease-in-out`.
- A collapse-toggle button (`hidden md:flex`) lets users shrink the sidebar
  to the icon rail without hiding it.
- There is no hamburger button on desktop.

**Sidebar — mobile (< 768 px) (`DiagramsSidebar.vue`):**

- Hidden off-screen by default (`transform: translateX(-100%)`).
- Revealed as a full-height fixed overlay (`z-50`, `w-64`) that slides in
  from the left (200 ms ease-in-out) when the user taps the hamburger button.
- A semi-transparent black backdrop (`z-40`, rendered in `DiagramsPage.vue`)
  covers the main content while the overlay is open; tapping it closes the sidebar.
- The sidebar also closes automatically when the user selects a diagram.

**Editor panels — desktop (`DiagramView.vue`):**

- The prompt input area (`WorkTab.vue`) and the diagram preview area
  (`DisplayTab.vue`) sit side-by-side as flex children of the main content zone.
- A resizer divider between them allows the split to be adjusted.

**Editor panels — mobile (`DiagramView.vue`):**

- The two panels are surfaced as tabs (Edit / Preview) at the top of the main
  content zone (`flex md:hidden` tab bar in `DiagramView.vue`).
- Only one panel is visible at a time, filling the full remaining width.

**Hydration safety:**

- No JS viewport checks drive conditional rendering.
- The `mobileSidebarOpen` boolean is owned by `DiagramsPage.vue` and passed
  as a prop to `DiagramsSidebar.vue` to avoid Vue block-tree corruption.
- `--sidebar-w` ensures a stable initial layout before JS executes.
