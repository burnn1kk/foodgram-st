from djoser.serializers import UserSerializer, TokenCreateSerializer, UserCreateSerializer
from django.contrib.auth import password_validation, authenticate
from djoser.serializers import TokenCreateSerializer
from rest_framework import serializers
from .models import User

class UserCreateSerializer(UserSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "password")

        extra_kwargs = {
            "password": {"write_only": True},
            "username": {"required": True}
        }

class CustomUserSerializer(UserSerializer):
    class Meta(UserCreateSerializer.Meta):
        fields = ("id", "email", "username", "first_name", "last_name")

class CustomTokenCreateSerializer(TokenCreateSerializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Неверный email или пароль")

        self.user = user

        return attrs

class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value