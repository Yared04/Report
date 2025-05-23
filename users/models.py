from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings

from report.models import BaseModel
from .constants import USER_TYPE_CHOICES, USER

class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default=USER)

class Organization(BaseModel):
    """
    Model representing an organization in the report management system.
    """
    name = models.CharField(max_length=255, unique=True) # Added unique=True
    description = models.TextField(blank=True, null=True) # Made description optional
    api_key_salt = models.CharField(max_length=16, editable=False, default=uuid.uuid4().hex[:16])

    def __str__(self):
        return self.name

    def generate_api_key(self):
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt=self.api_key_salt)
        return serializer.dumps(str(self.id))

    @staticmethod
    def get_organization_from_api_key(api_key):
        # Find the salt first. This is a simplified approach.
        # In a real-world scenario, you might need a more robust way to get the salt
        # or store API keys separately if salts are unique per key rather than per organization.
        # This example assumes you can iterate or query for an org that could match the key structure.
        
        # This is a placeholder for how you might find the salt. 
        # For this to work, you'd need a way to identify the organization or a list of possible salts.
        # A more robust solution would be to store API keys in a separate model or have a fixed salt for all API keys (less secure).
        
        # As a simplified (and less secure for multiple orgs) approach, if you have a limited number of orgs or a way to get the salt:
        # For demonstration, let's assume we can retrieve the organization by some other means to get its salt, 
        # or if the salt is globally known (not recommended for production).
        
        # Correct approach: You would typically have a separate APIKey model where each key is stored with its salt or a reference to the org.
        # Since we are not creating a separate APIKey model as per the request, 
        # decoding requires knowing the salt used for that specific organization.
        
        # If we assume we can iterate through organizations (not efficient for many orgs):
        for org in Organization.objects.all():
            try:
                serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt=org.api_key_salt)
                org_id = serializer.loads(api_key, max_age=None) # max_age=None for non-expiring keys, or set a duration
                if str(org.id) == org_id:
                    return org
            except Exception: # Catches BadSignature, SignatureExpired
                continue
        return None