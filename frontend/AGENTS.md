## Commands

In the repository there are `Taskfile.yml` files. They allow definition of
reusable tasks to be run with proper env vars as well as the working directory
context. The app name `go-task` has been aliased to just `t`.

You can assume the dependencies are installed and dev server is already running.
Do NOT run `t install` or `t dev`.

To perform static analysis, use `t check`. To verify the build, run `t build`.

## Rendering Model

Development uses Astro's dev server with hot-reload. Production is built as
**SSG (static HTML)** and deployed to a GCS bucket — there is no server at
runtime. This has design implications:

- No server-side logic at request time — all dynamic behavior must be client-side (Vue components with `client:load`)
- No server-side auth checks on page render; auth gates are enforced in Vue components or via client-side redirects
- API calls always originate from the browser.
- Any feature that would require a Node.js server (SSR, API routes, middleware) is out of scope

## Structure Map

Before making changes or adding features, read `README.md`. It is the definitive
map of every route, component, and library: what each file does, what it owns,
and how pieces connect. Re-exploring the directory is slower and less reliable
than reading that map first.

## Design System

See `.impeccable.md` for color tokens, brand principles, and UI constraints.
