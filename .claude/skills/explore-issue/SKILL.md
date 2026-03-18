---
name: explore-issue
description: Given ID of a GitHub issue, explore all related code and spaces to prepare for planning stage.
tools:
  - Read
  - Search
  - Fetch
  - Web Search
  - Bash(gh issue view *)
  - Bash(gh issue list *)
  - Bash(gh pr view *)
  - Bash(gh pr list *)
  - Bash(gh pr diff *)
  - Bash(gh repo view *)
  - Bash(gh search *)
---

Analyze and explore related code, documentation and context for the GitHub issue: $ARGUMENTS.

1. Use `gh issue view` to get the issue details
2. Understand the problem described in the issue
3. Find all related issues and sub-issues
4. Read comments and find related PRs
5. Find all relevand documentation
6. Find all relevant code 
7. Start Plan Agent that will implement a solution
