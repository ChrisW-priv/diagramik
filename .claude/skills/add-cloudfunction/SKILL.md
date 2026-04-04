______________________________________________________________________

## name: add-cloudfunction description: Step by step instructions on how to add cloud functions to the project. Use when user asks you to add a cloud function.

# Add Cloud Functions

Cloud Functions in this project follow a two-phase deployment pattern. All
Cloud Functions are deployed as GCP Cloud Run Functions (v2). They are first
provisioned with "sentinel" Terraform, which uses a throwaway zip to create the
infrastructure (service account, env vars, secrets, scaling config, etc.).
Once the infrastructure exists, subsequent code deployments build a container
image via Cloud Build (using Google Cloud Buildpacks) and update the underlying
Cloud Run service to use the new image.

**Sentinel pattern:** The `infrastructure/modules/cloud-function/` module
generates a minimal `main.py` at plan time and uploads it as a zip to a shared
GCS bucket. This lets Terraform own the infrastructure lifecycle without
requiring real function code to exist first. The module uses
`lifecycle { ignore_changes = [build_config] }` so subsequent `terraform apply`
runs do not revert the image that CI has deployed.

**CI deployment (two steps):**

1. `gcloud builds submit --pack` builds a container image from the function
   source using Google Cloud Buildpacks and pushes it to Artifact Registry.
1. `gcloud run services update --image` swaps the image on the underlying
   Cloud Run service (Cloud Functions v2 is backed by Cloud Run).

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

### Step 3 – Wire up GitHub Actions CI/CD

Two workflow files need changes.

#### `.github/workflows/main-push.yml` — add a deploy job

Add a new job that runs on every push to main. It builds the container image
with Cloud Build (buildpacks) and then swaps the image on the underlying Cloud
Run service. Use direct WIF auth (no `service_account` impersonation) — see the
existing `deploy-share-diagram-image` job as a reference.

```yaml
deploy-<function-name>:
  name: Deploy <function-name>
  runs-on: ubuntu-latest
  needs: [build-and-push]
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

    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v2

    - name: Build image with Cloud Build buildpack
      run: |
        gcloud builds submit backend/cloud-functions/<function-name> \
          --pack image=${{ vars.GOOGLE_REGION }}-docker.pkg.dev/${{ vars.GOOGLE_PROJECT_ID }}/diagramik/<function-name>:${{ github.sha }} \
          --project=${{ vars.GOOGLE_PROJECT_ID }}

    - name: Update Cloud Function to use new image
      run: |
        gcloud run services update <function-name> \
          --image=${{ vars.GOOGLE_REGION }}-docker.pkg.dev/${{ vars.GOOGLE_PROJECT_ID }}/diagramik/<function-name>:${{ github.sha }} \
          --region=${{ vars.GOOGLE_REGION }} \
          --project=${{ vars.GOOGLE_PROJECT_ID }}
```

Do **not** add `service_account` to the auth step. The WIF principal has direct
permissions and SA impersonation is not used in this project.

#### `.github/workflows/release.yml` — build before terraform, deploy after

The release workflow owns the full lifecycle: build → terraform (sentinel) →
deploy real image. Two insertions are needed:

**1. Build step** — add after "Tag and push as latest to GHCR" and before "Run
Terraform", grouped with the other image builds:

```yaml
      - name: Build cloud function image with Cloud Build buildpack
        run: |
          gcloud builds submit backend/cloud-functions/<function-name> \
            --pack image=${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/diagramik/<function-name>:${{ steps.get_tag.outputs.tag }} \
            --project=${{ env.GCP_PROJECT_ID }}
```

**2. Deploy step** — add after "Run Terraform" and before "Install frontend
dependencies":

```yaml
      - name: Deploy cloud function image to Cloud Run
        run: |
          gcloud run services update <function-name> \
            --image=${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/diagramik/<function-name>:${{ steps.get_tag.outputs.tag }} \
            --region=${{ env.GCP_REGION }} \
            --project=${{ env.GCP_PROJECT_ID }}
```

The deploy step must come after terraform because terraform creates the Cloud
Run service (via the sentinel zip) on the function's first deployment. The
`gcloud run services update` command can only target a service that already
exists.

The image is pushed to the `diagramik` Artifact Registry repository (the same
repo used by Cloud Run services). Cloud Build's default SA needs write access
to that repository; this is handled by the existing
`google_artifact_registry_repository_iam_member` writer binding in the
`django-monolith` module (WIF principal for the GitHub repo).

### Summary of files to create/modify

| Action     | Path                                                         |
| ---------- | ------------------------------------------------------------ |
| **Create** | `backend/cloud-functions/<function-name>/main.py`            |
| **Create** | `backend/cloud-functions/<function-name>/pyproject.toml`     |
| **Create** | `backend/cloud-functions/<function-name>/uv.lock`            |
| **Create** | `backend/cloud-functions/<function-name>/.python-version`    |
| **Create** | `backend/cloud-functions/<function-name>/.gitignore`         |
| **Create** | `backend/cloud-functions/<function-name>/tests/conftest.py`  |
| **Create** | `backend/cloud-functions/<function-name>/tests/test_main.py` |
| **Modify** | `infrastructure/cloud_functions.tf`                          |
| **Modify** | `.github/workflows/main-push.yml`                            |
| **Modify** | `.github/workflows/release.yml`                              |
