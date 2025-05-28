from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Organization, CustomUser  # Import the Organization model
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .serializers import CustomUserSerializer, OrganizationSerializer
from rest_framework import viewsets
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password

# Create your views here.


class OrganizationView(APIView):
    """
    View to create a new organization and return an API key.
    """

    permission_classes = [IsAdminUser]  # Changed to IsAdminUser

    def post(self, request):
        org_name = request.data.get("name")
        description = request.data.get("description", "")  # Optional description

        if not org_name:
            return Response(
                {"error": "Organization name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Organization.objects.filter(name=org_name).exists():
            return Response(
                {"error": "Organization with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            organization = Organization.objects.create(
                name=org_name, description=description
            )
            api_key = organization.generate_api_key()
            # Note: The API key is not stored directly in the DB in this setup, it's generated.
            # If you need to store it, you would add an api_key field to the Organization model or a separate APIKey model.
            return Response(
                {
                    "organization_id": str(organization.id),
                    "name": organization.name,
                    "api_key": api_key,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": f"Could not create organization: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        """
        List all organizations.
        """
        organizations = Organization.objects.all()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# CustomUser ViewSet
class CustomUserViewSet(viewsets.ModelViewSet):

    user_permissions = {
        "create": [],
        "retrieve": [],
        "update": [],
        "destroy": [],
        "list": [],
    }

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
