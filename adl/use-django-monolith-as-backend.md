---
title: Use Django as Backend Framework (Monolith Architecture)
date: 2026-04-20
status: accepted
---

## Decision

The backend REST API is implemented as a Django monolith (`django_monolith/`) using Django REST Framework. All domain logic — authentication, diagram management, workspace management, quota enforcement, email delivery — lives in a single deployable unit.

## Rationale

Pragmatic choice driven by developer familiarity and long-term maintainability. Django's batteries-included approach (ORM, admin, auth, migrations, email) reduces boilerplate and keeps the codebase coherent without premature service decomposition. Wide ecosystem support and extensive community resources lower the cost of onboarding new contributors. Django's maturity and LTS release policy make it well suited for enterprise-grade, long-term project maintenance.
