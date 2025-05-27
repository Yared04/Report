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
)
from .utils import verify_database_connection, execute_sql_query  # Import utilities
from rest_framework.generics import RetrieveAPIView
from rest_framework import viewsets
from rest_framework.decorators import action
from django.http import HttpResponse
import csv
import io
from drf_yasg.utils import swagger_auto_schema


# Create your views here.


@swagger_auto_schema(request_body=DatabaseSerializer)
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
            validated_data = serializer.validated_data
            db_host = validated_data.get("host")
            db_port = validated_data.get("port")
            db_name = validated_data.get(
                "name"
            )  # This is the database name field from your model
            db_user = validated_data.get("username")
            db_password = validated_data.get(
                "password"
            )  # write_only=True, so it's in validated_data

            # Verify database connection
            can_connect = verify_database_connection(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
            )

            if not can_connect:
                return Response(
                    {
                        "error": "Unable to connect to the database with the provided credentials. "
                        "Please check the host, port, database name, username, and password."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
                **{
                    "name": request.data.get("name"),
                    "description": request.data.get("description"),
                },
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
        query_data = {
            **{
                "name": request.data.get("name"),
                "description": request.data.get("description"),
                "sql_query": request.data.get("sql_query"),
                "node": request.data.get("node"),
            },
            "database": str(database.id),
        }

        serializer = QuerySerializer(
            data=query_data, context={"request": request, "database": database}
        )

        if serializer.is_valid():
            serializer.save()  # The serializer's create method will handle the rest
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QueryExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet to execute a stored query and return results as CSV.
    """

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsOrganizationMember]
    queryset = Query.objects.select_related("database").all()  # Base queryset
    serializer_class = QuerySerializer

    @action(detail=True, methods=["get"], url_path="execute")
    def execute(self, request, pk=None):
        """
        Executes the specified query and returns the results as a CSV file.
        """
        try:
            query_instance = self.get_object()  # Retrieves query by pk, handles 404
        except Query.DoesNotExist:
            return Response(
                {"error": "Query not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Permission check is implicitly handled by get_object if queryset is filtered by org,
        # or explicitly by IsOrganizationMember.has_object_permission
        # Ensure the query's database belongs to the organization
        if query_instance.database.organization != request.organization:
            return Response(
                {"error": "Access to this query is denied for your organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        db_config = query_instance.database

        try:
            column_names, data_rows = execute_sql_query(
                host=db_config.host,
                port=db_config.port,
                dbname=db_config.name,
                user=db_config.username,
                password=db_config.password,
                sql_query=query_instance.sql_query,
            )

            # Create CSV
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)

            if column_names:
                csv_writer.writerow(column_names)
            if data_rows:
                csv_writer.writerows(data_rows)

            csv_buffer.seek(0)
            response = HttpResponse(csv_buffer, content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="query_{query_instance.id}_results.csv"'
            )
            return response

        except psycopg2.Error as e:
            return Response(
                {"error": f"Database error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
