## Commands

Tasks are defined in `Taskfile.yml` and run via `go-task` (aliased `t`). All commands wrap standard Terraform operations.

```
t init      # Initialize Terraform providers and backend
t fmt       # Format all .tf files
t validate  # Validate configuration
t plan      # Show execution plan
t apply     # Apply changes to GCP
```

**Do not run `t apply` manually in production.** Infrastructure changes are applied by the `release.yml` GitHub Actions workflow when a GitHub release is published. Manual applies are only appropriate for initial setup or emergency fixes.

## Structure Map

Before making changes, read `README.md` for the full module inventory, resource ownership map, and environment configuration details.
