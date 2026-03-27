# add-cloudfunction skill

Step-by-step instructions for adding a new GCP Cloud Function to the project.
Invoked automatically when the user asks to add a cloud function.

Covers:
- Creating the function source directory under `backend/cloud-functions/`
- `pyproject.toml` (uv / PEP 621), `.python-version`, tests
- Terraform configuration in `infrastructure/cloud_functions.tf` via the shared `infrastructure/modules/cloud-function/` module
- GitHub Actions deployment job

---

**TODO:** When internal libraries are introduced to the project, update
`SKILL.md` to document registering the cloud function as a `uv` workspace
member in `backend/pyproject.toml` and referencing internal packages via
`[tool.uv.sources]`.
