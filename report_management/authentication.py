from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.models import Organization

class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class to authenticate users using an API key
    passed in the 'X-API-Key' header.
    """
    def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return None # No API key provided, pass to next authentication method or fail

        organization = Organization.get_organization_from_api_key(api_key)
        if not organization:
            raise AuthenticationFailed('Invalid API Key.')

        # Return (user, auth) tuple. user is None as API key represents an org, not a specific user.
        return (None, organization) # request.user will be AnonymousUser, request.auth will be the Organization