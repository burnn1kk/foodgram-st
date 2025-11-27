from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import User, Subscription
from .serializers import (
    UserOutputSerializer,
    UserCreateSerializer,
    UserSetPasswordSerializer,
    UserAvatarSerializer
)
from .permissions import OwnerOrReadOnly
from .pagination import UsersPagination
from posts.serializer import SubscribtionsSerializer, AuthorGetSerializer
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = UsersPagination
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
        serializer = AuthorGetSerializer(
            page, context={"request": request}, many=True
        )  # many=True указывает сериализатору что объектов больше 1 => обрабатывать каждый отдельно
        return  self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs.get("pk")
        if User.objects.filter(id=user_id).exists():
            user = User.objects.get(
                id=user_id
            )  # здесь был интересный момент когда передавая в serializer queryset при many=False получалась ошибка об отсутсвия поля
            serializer = AuthorGetSerializer(
                user, context={"request": request}
            )  # при many=False в srializer должен передаваться строго 1 объект
            return Response(serializer.data, status=200)  # queryset из 1 объекта != 1 объект => ошибка
        return Response(status=404)
    def create(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )  # detail=True требует id в url
    def me(self, request):
        user = request.user
        id = user.id
        serializer = AuthorGetSerializer(user, context={"request": request})
        return Response(serializer.data, status=200)

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
        return Response(status=204)

    @action(detail=True, methods=["post","delete"], permission_classes=[IsAuthenticated], url_name='subscribe')
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response({"error": "Нельзя подписаться на себя"}, status=400)

            if Subscription.objects.filter(subsciber=user, author=author).exists():
                return Response(status=400)

            Subscription.objects.get_or_create(
                subsciber=user,
                author=author
            )

            Responsedata = UserOutputSerializer(author, context={"request" : request})
            return Response(Responsedata.data, status=201)
        
        if request.method == 'DELETE':
            if Subscription.objects.filter(
                subsciber=user,
                author=author
            ).exists():
                Subscription.objects.filter(
                    subsciber=user,
                    author=author
                ).delete()
                return Response({"status": "unsubscribed"}, status=204)
            return Response(status=400)
            
    @action(detail=False, methods=["put", "delete"], permission_classes=[OwnerOrReadOnly,], url_path = 'me/avatar')
    def avatar(self, request, pk=None):
        user = request.user

        if request.method == 'PUT':
            serializer = UserAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=200)
        
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=204)