from django.urls import path
from .views import (
    DiagramListCreate,
    DiagramDetail,
    DiagramVersionCreate,
    DiagramVersionDelete,
    DiagramVersionImage,
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
        "diagrams/<uuid:diagram_id>/versions/<uuid:version_id>/",
        DiagramVersionDelete.as_view(),
        name="diagram-version-delete",
    ),
    path(
        "diagrams/<uuid:diagram_id>/versions/<uuid:version_id>/image/",
        DiagramVersionImage.as_view(),
        name="diagram-version-image",
    ),
]
