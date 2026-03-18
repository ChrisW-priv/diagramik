from django.urls import path
from .views import (
    DiagramListCreate,
    DiagramDetail,
    DiagramVersionCreate,
    DiagramVersionDelete,
    DiagramVersionImage,
    CheckpointListCreate,
    CheckpointDelete,
    CheckpointBranch,
    DirectRender,
)

urlpatterns = [
    path("diagrams/", DiagramListCreate.as_view(), name="diagram-list-create"),
    path("diagrams/<uuid:pk>/", DiagramDetail.as_view(), name="diagram-detail"),
    path(
        "diagrams/<uuid:diagram_id>/versions/",
        DiagramVersionCreate.as_view(),
        name="diagram-version-create",
    ),
    path(
        "diagrams/<uuid:diagram_id>/versions/render/",
        DirectRender.as_view(),
        name="diagram-direct-render",
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
        "diagrams/<uuid:diagram_id>/checkpoints/",
        CheckpointListCreate.as_view(),
        name="checkpoint-list-create",
    ),
    path(
        "diagrams/<uuid:diagram_id>/checkpoints/<uuid:checkpoint_id>/",
        CheckpointDelete.as_view(),
        name="checkpoint-delete",
    ),
    path(
        "diagrams/<uuid:diagram_id>/checkpoints/<uuid:checkpoint_id>/branch/",
        CheckpointBranch.as_view(),
        name="checkpoint-branch",
    ),
]
