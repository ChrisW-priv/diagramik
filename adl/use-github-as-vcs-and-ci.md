---
title: Use GitHub as VCS and CI/CD Platform
date: 2026-04-20
status: accepted
---

## Decision

GitHub is the version control host and CI/CD platform. CI is implemented via GitHub Actions workflows in `.github/workflows/`. Container images are stored in GitHub Container Registry (GHCR). Claude Code integration is provided via the GitHub Actions Claude workflow.

## Rationale

Best-in-class developer tooling with broad ecosystem familiarity. GitHub Actions integrates tightly with the repository — secrets management, OIDC federation for GCP authentication, and GHCR for container image storage all require no additional infrastructure to operate. Developer familiarity with GitHub reduces onboarding friction and keeps the operational surface small.
