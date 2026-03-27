______________________________________________________________________

## name: add-cloudfunction description: Step by step instructions on how to add cloud functions to the project. Use when user asks you to add a cloud function.

# Add Cloud Functions

Cloud Functions in this project follow a predictable two-phase pattern. All
Cloud Functions are deployed as GCP Cloud Run Functions (v2). They are first
provisioned with "sentinel" Terraform, which uses a throwaway zip to create the
infrastructure (service account, env vars, secrets, scaling config, etc.).
Once the infrastructure exists, the actual function code is deployed via
`gcloud functions deploy`. Deployment of new code is triggered via GitHub
Actions on push to the relevant branch.

**Sentinel pattern:** The `infrastructure/modules/cloud-function/` module
generates a minimal `main.py` at plan time and uploads it as a zip to a shared
GCS bucket. This lets Terraform own the infrastructure lifecycle without
requiring real function code to exist first. After `terraform apply`, deploy
real code with `gcloud functions deploy <function-name> --source=...`.

## Instructions

function-name = $ARGUMENTS

### Step 1 – Create the function directory and source files

Create `backend/cloud-functions/<function-name>/` with the following files.

**`main.py`** – entry point, must export a function named `main`:

```python
import functions_framework
from flask import Request, jsonify


@functions_framework.http
def main(request: Request):
    return jsonify({"status": "ok"}), 200
```

**`pyproject.toml`** – uv project config (PEP 621):

```toml
[project]
name = "<function-name>"
version = "0.1.0"
description = "<description>"
requires-python = ">=3.13,<3.14"
dependencies = [
  "functions-framework>=3.5.0",
  # add other dependencies here
]

[dependency-groups]
dev = [
  "pytest>=8.4.1",
  "pytest-cov>=7.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --cov=. --cov-report=term-missing"
```

If the function uses internal workspace packages, add them via
`[tool.uv.sources]`. See `backend/agent/` as an existing example of how
workspace members are declared in `backend/pyproject.toml`:

```toml
# [tool.uv.sources]
# agent = { workspace = true }
```

**`.python-version`**:

```
3.13
```

**`tests/conftest.py`** – shared fixtures (Flask app, mock request, mocked GCP
clients). Use an existing conftest.py as reference.

**`tests/test_main.py`** – pytest tests covering success and error paths.

Run locally to verify:

```bash
cd backend/cloud-functions/<function-name>
uv sync
uv run pytest
uv run functions-framework --target=main --debug
# In another terminal:
curl http://localhost:8080
```

### Step 2 – Add Terraform configuration in `infrastructure/cloud_functions.tf`

Cloud Functions are defined through the shared map in
`infrastructure/cloud_functions.tf`. Add a new entry to the `cloud_functions`
local:

```hcl
locals {
  cloud_functions = {
    "<function-name>" = {
      description = "<description>"
      environment_variables = {
        "MY_VAR" = "my-value"
      }

      # For secrets stored in Secret Manager:
      secret_environment_variables = {
        "MY_SECRET" = {
          secret  = google_secret_manager_secret.my_secret.secret_id
          version = "latest"
        }
      }

      # Who can invoke the function. Use "allUsers" for public, or a serviceAccount.
      invoker_members = ["allUsers"]
    }
  }
}
```

If the function should be event-driven, add an optional `event_trigger` block:

```hcl
event_trigger = {
  event_type   = "google.cloud.storage.object.v1.finalized"
  retry_policy = "RETRY_POLICY_RETRY"
  event_filters = [
    {
      attribute = "bucket"
      value     = "my-input-bucket"
    }
  ]
}
```

Key fields available on each function object:

| Field                          | Default       | Purpose                                      |
| ------------------------------ | ------------- | -------------------------------------------- |
| `available_memory`             | `"256M"`      | RAM allocation                               |
| `available_cpu`                | `"1"`         | CPU allocation                               |
| `timeout_seconds`              | `60`          | Execution timeout                            |
| `min_instance_count`           | `0`           | Cold-start vs. warm instances                |
| `max_instance_count`           | `100`         | Scale limit                                  |
| `ingress_settings`             | `"ALLOW_ALL"` | Network ingress                              |
| `sa_iam_roles`                 | `[]`          | Project-level roles for the function's SA    |
| `secret_environment_variables` | `{}`          | Secret Manager-backed env vars               |
| `event_trigger`                | `null`        | Optional Cloud Functions v2 Eventarc trigger |

The shared module automatically creates a dedicated service account
`<function-name>-sa`. Grant it extra permissions via
`google_storage_bucket_iam_member`, `google_project_iam_member`, etc. in root
Terraform after the shared `module "cloud_functions"` block.

If the function needs Secret Manager secrets, declare the secret resources and
grant the function's SA `roles/secretmanager.secretAccessor`:

```hcl
resource "google_secret_manager_secret_iam_member" "my_secret_access" {
  project   = google_secret_manager_secret.my_secret.project
  secret_id = google_secret_manager_secret.my_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.cloud_functions.service_account_emails["<function-name>"]}"
}
```

### Step 3 – Add GitHub Actions CI/CD deployment job

Add a deploy job to `.github/workflows/deploy.yml` (or a dedicated workflow
file). Use the existing Cloud Run deploy jobs as a template:

```yaml
deploy-<function-name>:
  name: Deploy <function-name>
  runs-on: ubuntu-latest
  needs: [terraform]
  if: github.ref == 'refs/heads/main'
  permissions:
    contents: read
    id-token: write
  steps:
    - uses: actions/checkout@v4

    - name: Authenticate to GCP
      uses: google-github-actions/auth@v2
      with:
        workload_identity_provider: ${{ vars.WIF_PROVIDER }}
        service_account: ${{ vars.WIF_SERVICE_ACCOUNT }}

    - name: Deploy Cloud Function
      uses: google-github-actions/deploy-cloud-functions@v3
      with:
        name: <function-name>
        region: ${{ vars.GOOGLE_REGION }}
        project_id: ${{ vars.GOOGLE_PROJECT_ID }}
        source_dir: backend/cloud-functions/<function-name>
        runtime: python313
        entry_point: main
```

### Summary of files to create/modify

| Action     | Path                                                                |
| ---------- | ------------------------------------------------------------------- |
| **Create** | `backend/cloud-functions/<function-name>/main.py`                  |
| **Create** | `backend/cloud-functions/<function-name>/pyproject.toml`           |
| **Create** | `backend/cloud-functions/<function-name>/uv.lock`                  |
| **Create** | `backend/cloud-functions/<function-name>/.python-version`          |
| **Create** | `backend/cloud-functions/<function-name>/.gitignore`               |
| **Create** | `backend/cloud-functions/<function-name>/tests/conftest.py`        |
| **Create** | `backend/cloud-functions/<function-name>/tests/test_main.py`       |
| **Modify** | `infrastructure/cloud_functions.tf`                                 |
| **Modify** | `.github/workflows/deploy.yml`                                      |
