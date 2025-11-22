from rest_framework import serializers

from .models import User
from foodgram.common_classes import Base64ImageField

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(
        self, validated_data
    ):  # тк мы не используем стандартные эндпоинты djoser а написали свой вьюсет, то теперь по стандарту пароли не хешируются =>
        password = validated_data.pop(
            "password"
        )  # в бд они появляются в незашифрованном виде
        user = User(
            **validated_data
        )  # интересно что вызываемую функцию хеширования можно задавать, хоть вообще свою написать
        user.set_password(password)  # django.contrib.auth.hashers.make_password
        user.save()
        return user


class UserOutputSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user

        if not user.is_authenticated:
            return False

        return user.subscriptions.filter(author=obj).exists()


class UserSetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, value):
        if value is None:
            raise serializers.ValidationError("avatar cannot be null")
        return value
