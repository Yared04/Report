from rest_framework import serializers
from .models import Database, Node, Query  # Query was already imported
from users.models import (
    Organization,
)  # Required for PrimaryKeyRelatedField if used explicitly


class DatabaseSerializer(serializers.ModelSerializer):
    # Output organization details, but don't take it as input directly from payload.
    # It will be derived from the API key's context.
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = Database
        fields = [
            "id",
            "name",
            "description",
            "host",
            "port",
            "database",
            "username",
            "organization_id",
            "organization_name",
        ]
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "organization_id",
            "organization_name",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not hasattr(request, "organization"):
            raise serializers.ValidationError(
                "Organization context not found. Ensure API key is valid."
            )
        validated_data["organization"] = request.organization
        return super().create(validated_data)


class QuerySerializer(serializers.ModelSerializer):
    # Ensure the selected database belongs to the current organization.
    database = serializers.PrimaryKeyRelatedField(queryset=Database.objects.all())

    class Meta:
        model = Query
        fields = "__all__"  # Or list specific fields: ['id', 'name', 'description', 'sql_query', 'node', 'database']
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_database(self, value):
        request = self.context.get("request")
        if not request or not hasattr(request, "organization"):
            raise serializers.ValidationError(
                "Organization context not available for validation."
            )

        if value.organization != request.organization:
            raise serializers.ValidationError(
                f"The selected database '{value.name}' does not belong to your organization ('{request.organization.name}')."
            )
        return value

    def validate_node(self, value):
        """
        Validate that the node (if provided) belongs to the same database
        as specified in the request data for the query.
        """
        # 'value' here is the Node instance if a node_id is provided and valid.
        # If node is None (optional), this validation doesn't apply.
        if value is None:
            return value

        # Get the database_id from the initial data passed to the serializer
        database_id = self.initial_data.get("database")
        if database_id and value.database_id.__str__() != database_id:
            raise serializers.ValidationError(
                f"The selected node '{value.name}' does not belong to the specified database (ID: {database_id})."
            )
        return value


# New serializer for child nodes to display them one level deep
class NodeChildSerializer(serializers.ModelSerializer):
    # queries = QuerySerializer(many=True, read_only=True) # Children can show their own queries
    # database field will expect/return the ID of the database.
    database = serializers.PrimaryKeyRelatedField(queryset=Database.objects.all())

    class Meta:
        model = Node
        # No 'children' field here to prevent further recursion for this level
        fields = [
            "id",
            "name",
            "description",
            "parent",
            "database",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_database(self, value):
        """
        Validate that the database belongs to the request's organization.
        """
        request = self.context.get("request")
        if not request or not hasattr(request, "organization"):
            raise serializers.ValidationError(
                "Organization context not found in request."
            )
        if value.organization != request.organization:
            raise serializers.ValidationError(
                f"The selected database '{value.name}' does not belong to your organization ('{request.organization.name}')."
            )
        return value


class NodeSerializer(serializers.ModelSerializer):
    queries = QuerySerializer(many=True, read_only=True)
    # This will now use NodeChildSerializer for the children
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Node
        # database field will expect/return the ID of the database.
        fields = [
            "id",
            "name",
            "description",
            "parent",
            "database",
            "queries",
            "children",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def get_children(self, obj):
        # Use NodeChildSerializer to serialize direct children one level deep
        return NodeChildSerializer(
            obj.children.all(), many=True, context=self.context
        ).data

    def validate_database(self, value):
        """
        Validate that the database belongs to the request's organization.
        """
        request = self.context.get("request")
        if not request or not hasattr(request, "organization"):
            raise serializers.ValidationError(
                "Organization context not found in request."
            )
        if value.organization != request.organization:
            raise serializers.ValidationError(
                f"The selected database '{value.name}' does not belong to your organization ('{request.organization.name}')."
            )
        return value
