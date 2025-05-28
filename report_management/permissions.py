from rest_framework.permissions import BasePermission
from users.models import Organization
from .models import Node  # For isinstance check


class IsOrganizationMember(BasePermission):
    """
    Custom permission to allow access if a valid API key for an organization is provided.
    It also checks object-level permissions to ensure objects belong to the authenticated organization.
    """

    message = (
        "Invalid or missing API key, or insufficient permissions for the organization."
    )

    def has_permission(self, request, view):
        # APIKeyAuthentication should have set request.auth to the Organization instance
        # if authentication was successful.
        if request.auth and isinstance(request.auth, Organization):
            request.organization = (
                request.auth
            )  # Make org easily accessible as request.organization
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Ensure request.organization is set (should be by has_permission)
        if not hasattr(request, "organization") or not request.organization:
            return False

        # Check if the object belongs to the authenticated organization
        if hasattr(obj, "organization_id"):  # For models like Database
            return obj.organization_id == request.organization.id
        elif hasattr(obj, "database") and hasattr(
            obj.database, "organization_id"
        ):  # For Query model
            return obj.database.organization_id == request.organization.id
        elif isinstance(obj, Node):
            # Nodes are not directly tied to an organization in the current model.
            # Access is granted if the general organization authentication (API key) is valid.
            # If Nodes need to be strictly scoped, an 'organization' ForeignKey should be added to the Node model.
            return True
        return False

class IsOrganizationAdmin(BasePermission):
    """
    Custom permission to allow access only to organization admins, determined by the 'role' header.
    """
    message = "You must be an admin of the organization to perform this action."

    def has_permission(self, request, view):
        # APIKeyAuthentication should have set request.auth to the Organization instance
        if request.auth and isinstance(request.auth, Organization):
            request.organization = request.auth  # Make org easily accessible as request.organization
            role = request.headers.get('role', '').lower()
            return role == 'admin'
        return False

    def has_object_permission(self, request, view, obj):
        # Ensure request.organization is set (should be by has_permission)
        if not hasattr(request, 'organization') or not request.organization:
            return False

        # Only allow if the role header is 'admin'
        role = request.headers.get('role', '').lower()
        if role != 'admin':
            return False

        # Check if the object belongs to the authenticated organization (same as IsOrganizationMember)
        if hasattr(obj, 'organization_id'):
            return obj.organization_id == request.organization.id
        elif hasattr(obj, 'database') and hasattr(obj.database, 'organization_id'):
            return obj.database.organization_id == request.organization.id
        elif isinstance(obj, Node):
            return True
        return False