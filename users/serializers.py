# CustomUser Serializer
from .models import CustomUser
from rest_framework import serializers
from .models import Organization  # Import here to avoid circular import


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = CustomUser(**validated_data)
        user.set_password(validated_data["password"])
        user.save()

        return user


class OrganizationSerializer(serializers.Serializer):
    """
    Serializer for creating and retrieving organization details.
    """
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)