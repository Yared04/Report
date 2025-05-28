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
            "password",
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
    type = serializers.CharField(default="file", read_only=True)

    class Meta:
        model = Query
        fields = ["id", "name", "description", "sql_query", "node", "database", "type"]
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


# New serializer for child nodes to display them one level deep
class NodeChildSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="folder", read_only=True)

    class Meta:
        model = Node
        fields = [
            "id",
            "name",
            "description",
            "parent",
            "organization",
            "type",  # This will always be 'folder' for Node
        ]
        read_only_fields = ("id", "created_at", "updated_at")


class NodeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="folder", read_only=True)
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Node
        # database field will expect/return the ID of the database.
        fields = [
            "id",
            "name",
            "description",
            "parent",
            "organization",
            "children",
            "type",  # This will always be 'folder' for Node
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def get_children(self, obj):
        # Use NodeChildSerializer to serialize direct children one level deep
        return [
            *NodeChildSerializer(
                obj.children.all(), many=True, context=self.context
            ).data,
            *QuerySerializer(obj.queries.all(), many=True, context=self.context).data,
        ]
