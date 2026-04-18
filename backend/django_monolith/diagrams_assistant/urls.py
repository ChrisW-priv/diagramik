from django.urls import path
from .views import (
    DiagramListCreate,
    DiagramDetail,
    DiagramVersionCreate,
    DiagramVersionDelete,
    DiagramVersionImage,
    DiagramShareLinkCreate,
    DiagramShareLinkResolve,
    WorkspaceListCreate,
    WorkspaceDetail,
    DiagramWorkspaceAssign,
)

urlpatterns = [
    path("diagrams/", DiagramListCreate.as_view(), name="diagram-list-create"),
    path("diagrams/<uuid:pk>/", DiagramDetail.as_view(), name="diagram-detail"),
    path(
        "diagrams/<uuid:pk>/workspace/",
        DiagramWorkspaceAssign.as_view(),
        name="diagram-workspace-assign",
    ),
    path(
        "diagrams/<uuid:diagram_id>/versions/",
        DiagramVersionCreate.as_view(),
        name="diagram-version-create",
    ),
    path(
        "diagrams/<uuid:diagram_id>/versions/<uuid:version_id>/",
        DiagramVersionDelete.as_view(),
        name="diagram-version-delete",
    ),
    path(
        "diagrams/<uuid:diagram_id>/versions/<uuid:version_id>/image/",
        DiagramVersionImage.as_view(),
        name="diagram-version-image",
    ),
    path(
        "diagrams/<uuid:diagram_id>/versions/<uuid:version_id>/share/",
        DiagramShareLinkCreate.as_view(),
        name="diagram-share-link-create",
    ),
    path(
        "share/<uuid:token>/",
        DiagramShareLinkResolve.as_view(),
        name="diagram-share-link-resolve",
    ),
    path("workspaces/", WorkspaceListCreate.as_view(), name="workspace-list-create"),
    path("workspaces/<uuid:pk>/", WorkspaceDetail.as_view(), name="workspace-detail"),
]
