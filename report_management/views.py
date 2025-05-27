from .authentication import APIKeyAuthentication
from .permissions import IsOrganizationMember
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Database, Node, Query  # Query was already imported
from report_management.serializers import (
    NodeSerializer,
    QuerySerializer,
    DatabaseSerializer,
)  # Import the serializers
from rest_framework.generics import RetrieveAPIView

# Create your views here.


class DatabaseView(APIView):
    """
    View to manage database connections.
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsOrganizationMember]

    def get(self, request):
        """
        List database connections for the authenticated organization.
        """
        # request.organization is set by IsOrganizationMember
        databases = Database.objects.filter(organization=request.organization)
        serializer = DatabaseSerializer(
            databases, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new database connection.
        """
        # Serializer's create method will use request.organization from context
        serializer = DatabaseSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NodeDetailView(RetrieveAPIView):
    """
    Retrieve a specific node with its direct child nodes (one level deep)
    and associated queries for both the node and its children.
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsOrganizationMember]

    # Optimized prefetch for the node's queries, its children, and its children's queries
    queryset = (
        Node.objects.select_related("database")
        .prefetch_related(
            "queries",
            "children__queries__database",
            "children__queries",  # Also prefetch db for children's queries
        )
        .all()
    )
    serializer_class = NodeSerializer
    lookup_field = "pk"
    # Note: If Nodes were directly organization-scoped, this queryset would need filtering
    # or get_object would need overriding for stricter object-level permission.
    # The current IsOrganizationMember.has_object_permission allows Node access if general org auth is fine.

    def get_serializer_context(self):
        # Ensure request is passed to the serializer context
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class NodeView(APIView):
    """
    View to manage nodes.
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsOrganizationMember]

    def get(self, request, database_id=None):
        """
        List root nodes (nodes with no parent) along with their direct children
        (one level deep) and associated queries.
        Also lists queries that are not associated with any node, scoped to the organization.

        Now filters nodes and queries based on the provided database_id.
        """

        if not database_id:
            return Response(
                {"error": "Please provide a database ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            database = Database.objects.get(
                id=database_id, organization=request.organization
            )
        except Database.DoesNotExist:
            return Response(
                {
                    "error": "Invalid database ID or database not found for your organization"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        root_nodes = (
            Node.objects.filter(parent__isnull=True, database=database)
            .select_related("database")
            .prefetch_related("queries", "children__queries")
        )

        unparented_queries = Query.objects.filter(
            node__isnull=True, database=database
        ).select_related("database")

        root_nodes_serializer = NodeSerializer(
            root_nodes, many=True, context={"request": request}
        )
        unparented_queries_serializer = QuerySerializer(
            unparented_queries, many=True, context={"request": request}
        )

        data = {
            "root_nodes": root_nodes_serializer.data,
            "unparented_queries": unparented_queries_serializer.data,
        }
        return Response(data)

    def post(self, request, database_id=None):
        """
        Create a new node.
        """

        if not database_id:
            return Response(
                {"error": "Please provide a database ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            Database.objects.get(id=database_id, organization=request.organization)
        except Database.DoesNotExist:
            return Response(
                {
                    "error": "Invalid database ID or database not found for your organization"
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = NodeSerializer(
            data={
                **request.data.dict(),
                "database": database_id,
                "parent": request.data.get("parent_id", None),
            },
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QueryView(APIView):
    """
    View to manage queries, specifically for creation under a given database.
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsOrganizationMember]

    def post(self, request, database_id=None):
        """
        Create a new query associated with the given database_id.
        The parent node_id can be optionally provided in the request data.
        """
        if not database_id:
            return Response(
                {"error": "Database ID is required in the URL path."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Validate that the database exists and belongs to the organization
            database = Database.objects.get(
                id=database_id, organization=request.organization
            )
        except Database.DoesNotExist:
            return Response(
                {
                    "error": "Invalid database ID or database not found for your organization."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prepare data for the serializer
        # The 'database' field in the serializer expects the database ID.
        # The 'node' field (if provided) expects the node ID.
        query_data = {**request.data.dict(), "database": str(database.id)}

        serializer = QuerySerializer(
            data=query_data, context={"request": request, "database": database}
        )

        if serializer.is_valid():
            serializer.save()  # The serializer's create method will handle the rest
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
