## Overview

These are CI-only workflows. There are no local commands to run from this directory. All workflows execute on GitHub Actions runners.

GCP authentication uses OIDC Workload Identity Federation — there are no long-lived service account keys stored as secrets. Do not add static GCP credentials to the repository.

## Structure Map

Read `README.md` for the full workflow inventory, trigger conditions, and CI pipeline architecture.
