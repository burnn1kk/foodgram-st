from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import User, Subscription
from .serializers import (
    UserOutputSerializer,
    UserCreateSerializer,
    UserSetPasswordSerializer,
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        action = self.action
        if action == "list" or action == "create" or action == "retrieve":
            return [
                AllowAny(),
            ]
        return [
            IsAuthenticated(),
        ]

    def list(self, request):
        queryset = User.objects.all()
        page = self.paginate_queryset(queryset)
        serializer = UserOutputSerializer(
            page, context={"request": request}, many=True
        )  # many=True указывает сериализатору что объектов больше 1 => обрабатывать каждый отдельно
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs.get("pk")
        user = User.objects.get(
            id=user_id
        )  # здесь был интересный момент когда передавая в serializer queryset при many=False получалась ошибка об отсутсвия поля
        serializer = UserOutputSerializer(
            user, context={"request": request}
        )  # при many=False в srializer должен передаваться строго 1 объект
        return Response(serializer.data)  # queryset из 1 объекта != 1 объект => ошибка

    def create(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )  # detail=True требует id в url
    def me(self, request):
        user = request.user
        id = user.id
        serializer = UserOutputSerializer(user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def set_password(self, request):
        user = request.user
        serializer = UserSetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        current_password = serializer.validated_data["current_password"]
        new_password = serializer.validated_data["new_password"]

        if current_password == new_password:
            return Response(
                {"new_password": "Новый пароль совпадает со старым"}, status=400
            )

        if not user.check_password(current_password):
            return Response({"current_password": "Неверный пароль"}, status=400)

        user.set_password(new_password)
        user.save()

    @action(detail=True, methods=["post","delete"], permission_classes=[IsAuthenticated], url_name='subscribe')
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response({"error": "Нельзя подписаться на себя"}, status=400)

            Subscription.objects.get_or_create(
                subsciber=user,
                author=author
            )
            return Response({"status": "subscribed"}, status=201)
        
        if request.method == 'DELETE':
            Subscription.objects.filter(
                subsciber=user,
                author=author
            ).delete()
            return Response({"status": "unsubscribed"}, status=204)
        