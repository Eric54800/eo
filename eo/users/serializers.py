from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer "profil" (lecture / update éventuel).
    """
    organisation = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "phone",
            "avatar",
            "date_created",
            "role",
            "organisation",
        ]
        read_only_fields = ["id", "date_created", "role", "organisation"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer signup: email + password uniquement.
    (On force username=email pour satisfaire un éventuel champ username requis.)
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]

        # Important: utilise le manager pour hasher le password
        user = User.objects.create_user(
            email=email,
            password=password,
            username=email,  # évite "username required"
        )
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"