from users.models import Organization

class IsOrganizationAdmin:
    """
    Custom permission to check if the user is an organization admin.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and is an organization admin
        apiKey = request.headers.get('x-api-key')
        if not apiKey:
            return False
        try:
            org = Organization.get_organization_from_api_key(apiKey)
        except:
            return False
        if not Organization:
            return False
        if request.data.get('organization') != str(org.id):
            return False
        if request.method  == "GET":
            return True
        
        if request.data.get('role') != 'admin':
            return False
        return True