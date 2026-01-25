# Backend Refactoring Action Plan (Revised)

## 1. Current Backend Implementation Analysis

The backend is a Django application that uses a `FastAgent` to generate diagrams based on user text prompts.

- **Diagram Generation:** The process is initiated in `diagrams_assistant/views.py` within the `DiagramListCreate` and `DiagramVersionCreate` views. These views call an agent function from `diagrams_assistant/agent.py`.
- **Agent and MCP:** The agent communicates with a diagramming tool hosted as an MCP server (`mcp_diagrams/server.py`). This tool generates a diagram, saves it to a GCS bucket, and returns a `gs://` URI for the saved image.
- **Data Model:** The `diagrams_assistant/models.py` defines the `DiagramVersion` model, which has an `image_uri` field. This field is a `CharField` intended to store `gs://` URIs.
- **Signed URL Generation:** In `diagrams_assistant/views.py`, the `create_publicly_accessible_url` function takes the `gs://` URI from the agent, generates a temporary signed GCS URL. A new `DiagramVersionImage` view has been added to handle redirects to these signed URLs.
- **API Response:** The `DiagramVersionSerializer` in `diagrams_assistant/serializers.py` now exposes `id`, `diagram_id`, and `created_at`. The `image_path` field has been removed.

### Current State:

1. **Internal URI Storage:** The `DiagramVersion` model stores the internal `gs://` URI in the `image_uri` field.
1. **Redirect Endpoint:** A dedicated endpoint `/api/v1/diagrams/{diagram_id}/versions/{version_id}/image/` exists to generate a signed URL and redirect to the image.
1. **Frontend Responsibility:** The frontend is now responsible for constructing the image URL for display.

## 2. TODO List for Refactoring

Here is a list of changes that have been made and the remaining task for frontend integration.

### Phase 1: Database and Model Adjustments (Completed)

- [x] **1.1. Rename `image_url` field:** In `backend/backend/diagrams_assistant/models.py`, renamed the `image_url` field in the `DiagramVersion` model to `image_uri` to accurately reflect that it stores a `gs://` URI.
- [x] **1.2. Create a database migration:** (Assumed completed by user) Generated and applied a migration to rename the field in the database schema.

### Phase 2: Backend Logic and Endpoint Implementation (Completed)

- [x] **2.1. Update views to store URI:** In `backend/backend/diagrams_assistant/views.py`, modified `DiagramListCreate` and `DiagramVersionCreate` to save the raw `gs://` URI (`agent_response.media_uri`) into the new `image_uri` field of the `DiagramVersion` model, instead of a signed URL.
- [x] **2.2. Create new image redirect view:** In `backend/backend/diagrams_assistant/views.py`, created a new `APIView` named `DiagramVersionImage` that retrieves the `DiagramVersion` object, generates a signed URL from the stored `image_uri`, and returns an HTTP 302 redirect to the signed URL.
- [x] **2.3. Add new URL pattern:** In `backend/backend/diagrams_assistant/urls.py`, added a new path `diagrams/<uuid:diagram_id>/versions/<uuid:version_id>/image/` that maps to the new `DiagramVersionImage` view.

### Phase 3: API Response and Documentation (Completed)

- [x] **3.1. Update serializer:** In `backend/backend/diagrams_assistant/serializers.py`, changed the `DiagramVersionSerializer` to remove the `image_path` field and its associated method. It now exposes `id`, `diagram_id`, and `created_at`.
- [x] **3.2. Update OpenAPI documentation:** In `backend/openapi-schema.yml`, updated the `DiagramVersion` schema to remove `image_path` and adjusted its description.

### Phase 4: Frontend Adjustments (Completed)

- [x] **4.1. Update `DisplayTab.vue`:** Modified `frontend/src/components/DisplayTab.vue` to construct the image URL using `diagram_id` and `id` (version_id) from the `DiagramVersionSerializer` for both displaying and downloading the image. The URL format is `/api/v1/diagrams/{diagram_id}/versions/{version_id}/image/`.
