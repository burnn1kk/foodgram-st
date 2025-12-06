from rest_framework import viewsets, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from django.http import HttpResponse
from http import HTTPStatus
from django.db.models import Sum
from foodgram.settings import BASE_URL

from users.models import User, Subscription
from posts.models import Ingredient, Recipe, RecipeIngredient, Favourite, ShoppingCart
from .serializers import (
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    SubscribtionsSerializer,
    ShortRecipeInfoSerializer,
    AuthorGetSerializer,
    UserCreateSerializer,
    UserSetPasswordSerializer,
    UserAvatarSerializer,
    UserOutputSerializer,
)
from .pagination import RecipePagination, UsersPagination, SubscriptionPagination
from .permissions import OwnerOrReadOnly


class RecipesViewSet(viewsets.ModelViewSet):
    # queryset = Recipe.objects.all()
    pagination_class = RecipePagination
    permission_classes = [
        OwnerOrReadOnly,
    ]
    serializer_class = RecipeGetSerializer

    def get_queryset(self):
        allowed_params = {
            "page",
            "author",
            "is_favorited",
            "limit",
            "is_in_shopping_cart",
        }

        for param in self.request.query_params.keys():
            if param not in allowed_params:
                raise ValidationError({param: "Неизвестный параметр"})

        queryset = Recipe.objects.all().order_by("-pub_date")
        user = self.request.user

        author = self.request.query_params.get("author")
        is_favorited = self.request.query_params.get("is_favorited")

        if author:
            queryset = queryset.filter(author=author)

        if is_favorited is not None:
            if is_favorited not in ("0", "1"):
                raise ValidationError(
                    {"is_favorited": "Параметр должен быть '0' или '1'."}
                )

            if user.is_authenticated:
                if is_favorited == "1":
                    queryset = queryset.filter(favorited_by__user=user)
                else:
                    queryset = queryset.exclude(favorited_by__user=user)
        return queryset

    def create(self, request):
        serializer = RecipePostSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            recipe = serializer.save()
            output = RecipeGetSerializer(
                recipe, context={"request": request}
            )  # возвращает после успешного post
            return Response(
                output.data, status=HTTPStatus.CREATED
            )  # рецепт сериализованный сериализатором для вывода
        return Response(
            serializer.errors, status=HTTPStatus.BAD_REQUEST
        )  # для того чтобы user и ingredients выводились подробно

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if "ingredients" not in request.data:
            return Response(status=HTTPStatus.BAD_REQUEST)
        serializer = RecipePostSerializer(
            instance=instance,
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_data = RecipeGetSerializer(instance, context={"request": request})
        return Response(response_data.data, status=HTTPStatus.OK)

    def list(self, request):
        queryset = self.get_queryset()
        user = request.user

        if request.query_params.get("author") and not queryset.exists():
            return Response(status=HTTPStatus.NOT_FOUND)

        param = request.query_params.get("is_in_shopping_cart")

        if param is not None:
            try:
                param = int(param)
            except ValueError:
                return Response(
                    {"error": "param must be int"}, status=HTTPStatus.BAD_REQUEST
                )

            if user.is_authenticated:
                if param == 1:
                    queryset = queryset.filter(in_carts__user=user)

                elif param == 0:
                    queryset = queryset.exclude(in_carts__user=user)
                else:
                    return Response(
                        {"error": "Parameter must be 0 or 1."},
                        status=HTTPStatus.BAD_REQUEST,
                    )

        page = self.paginate_queryset(queryset)
        serializer = RecipeGetSerializer(page, context={"request": request}, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("pk")
        if Recipe.objects.filter(id=recipe_id).exists():
            recipe = Recipe.objects.get(id=recipe_id)
            serializer = RecipeGetSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=HTTPStatus.OK)

        return Response(status=HTTPStatus.NOT_FOUND)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_name="favorite",
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if not user.favorites.filter(
                recipe=recipe
            ).exists():  # Вместо if not Favourite.objects.filter(user=user, recipe=recipe).exists()
                Favourite.objects.get_or_create(user=user, recipe=recipe)
                resp = ShortRecipeInfoSerializer(recipe)
                return Response(resp.data, status=HTTPStatus.CREATED)
            return Response(status=HTTPStatus.BAD_REQUEST)

        if request.method == "DELETE":
            if user.favorites.filter(recipe=recipe).exists():
                user.favorites.filter(recipe=recipe).delete()
                return Response(status=HTTPStatus.NO_CONTENT)
            return Response(status=HTTPStatus.BAD_REQUEST)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if user.shopping_cart.filter(
                recipe=recipe
            ).exists():  # Использовано related_name
                return Response(status=HTTPStatus.BAD_REQUEST)
            ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            serializer = ShortRecipeInfoSerializer(recipe)
            return Response(serializer.data, status=HTTPStatus.CREATED)
        if request.method == "DELETE":
            if user.shopping_cart.filter(
                recipe=recipe
            ).exists():  # Использовано related_name
                user.shopping_cart.filter(recipe=recipe).delete()
                return Response(status=HTTPStatus.NO_CONTENT)
            return Response(status=HTTPStatus.BAD_REQUEST)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_name="download_shopping_cart",
    )
    def download_shopping_cart(self, request, pk=None):
        user = request.user
        recipes = user.shopping_cart.values_list(  # Использовано related_name
            "recipe", flat=True
        )

        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values(
                "ingredient__name",
                "ingredient__measurement_unit",
            )
            .annotate(total_amount=Sum("amount"))
        )

        lines = []
        for item in ingredients:
            lines.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}"
            )

        text = "\n".join(lines)
        response = HttpResponse(text, content_type="text/plain;charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'

        return response

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        base_url = BASE_URL
        short_url = (
            f"{base_url}/api/short_link/{recipe.short_code}"  # Вместо хардкода URL
        )

        return Response({"short-link": short_url}, status=HTTPStatus.OK)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    filter_backends = [filters.SearchFilter]
    search_fields = ["^name"]

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__startswith=name)
        return qs


class SubscribtionsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscribtionsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(subscribers__subscriber=self.request.user).distinct()

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = UsersPagination

    def get_permissions(self):
        action = self.action
        if action == "list" or action == "create" or action == "retrieve":
            return [
                permissions.AllowAny(),
            ]
        return [
            permissions.IsAuthenticated(),
        ]

    def list(self, request):
        queryset = User.objects.all()
        page = self.paginate_queryset(queryset)
        serializer = AuthorGetSerializer(
            page, context={"request": request}, many=True
        )  # many=True указывает сериализатору что объектов больше 1 => обрабатывать каждый отдельно
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs.get("pk")
        if User.objects.filter(id=user_id).exists():
            user = User.objects.get(
                id=user_id
            )  # здесь был интересный момент когда передавая в serializer queryset при many=False получалась ошибка об отсутсвия поля
            serializer = AuthorGetSerializer(
                user, context={"request": request}
            )  # при many=False в srializer должен передаваться строго 1 объект
            return Response(
                serializer.data, status=HTTPStatus.OK
            )  # queryset из 1 объекта != 1 объект => ошибка
        return Response(status=HTTPStatus.NOT_FOUND)

    def create(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)
        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )  # detail=True требует id в url
    def me(self, request):
        user = request.user
        id = user.id
        serializer = AuthorGetSerializer(user, context={"request": request})
        return Response(serializer.data, status=HTTPStatus.OK)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request):
        user = request.user
        serializer = UserSetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)

        current_password = serializer.validated_data["current_password"]
        new_password = serializer.validated_data["new_password"]

        if current_password == new_password:
            return Response(
                {"new_password": "Новый пароль совпадает со старым"},
                status=HTTPStatus.BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {"current_password": "Неверный пароль"}, status=HTTPStatus.BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscribe",
        url_name="subscribe",
    )
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user

        if request.method == "POST":
            if user == author:
                return Response(
                    {"error": "Нельзя подписаться на себя"},
                    status=HTTPStatus.BAD_REQUEST,
                )

            if user.subscriptions.filter(
                author=author
            ).exists():  # Использовано related_name
                return Response(status=HTTPStatus.BAD_REQUEST)

            Subscription.objects.get_or_create(subscriber=user, author=author)

            Responsedata = UserOutputSerializer(author, context={"request": request})
            return Response(Responsedata.data, status=HTTPStatus.CREATED)

        if request.method == "DELETE":
            if user.subscriptions.filter(
                author=author
            ).exists():  # Использовано related_name
                user.subscriptions.filter(
                    author=author
                ).delete()  # Использовано related_name
                return Response(status=HTTPStatus.NO_CONTENT)
            return Response(status=HTTPStatus.BAD_REQUEST)

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[
            OwnerOrReadOnly,
        ],
        url_path="me/avatar",
    )
    def avatar(self, request, pk=None):
        user = request.user

        if request.method == "PUT":
            serializer = UserAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.OK)

        if request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response(status=HTTPStatus.NO_CONTENT)
