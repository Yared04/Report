from .views import (
    DatabaseView,
    NodeView,
    NodeDetailView,
    QueryView,
)
from django.urls import path


urlpatterns = [
    path("database/", DatabaseView.as_view(), name="database-list"),
    path(
        "database/<uuid:database_id>/nodes/",
        NodeView.as_view(),
        name="node-list-by-database",
    ),
    path("nodes/<uuid:pk>/", NodeDetailView.as_view(), name="node-detail-view"),
    path(
        "database/<uuid:database_id>/queries/",
        QueryView.as_view(),
        name="query-create-by-database",
    ),
]
