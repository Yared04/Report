from .views import (
    DatabaseDetailView,
    DatabaseView,
    NodeView,
    NodeDetailView,
    QueryDetailView,
    QueryView,
    QueryExecutionViewSet,
)
from django.urls import path


urlpatterns = [
    path("database/", DatabaseView.as_view(), name="database-list"),
    path(
        "database/<uuid:pk>/",
        DatabaseDetailView.as_view(),
        name="database-detail",
    ),
    path(
        "nodes/",
        NodeView.as_view(),
        name="node-list-by-database",
    ),
    path("nodes/<uuid:pk>/", NodeDetailView.as_view(), name="node-detail-view"),
    path(
        "database/<uuid:database_id>/queries/",
        QueryView.as_view(),
        name="query-create-by-database",
    ),
    path(
        "queries/<uuid:pk>/execute/",
        QueryExecutionViewSet.as_view({"get": "execute"}),
        name="query-execute",
    ),
    path(
        "queries/<uuid:pk>/",
        QueryDetailView.as_view(),
        name="query-detail",
    ),
]
