from rest_framework import serializers

from posts.models import Ingredient, Recipe, RecipeIngredient
from users.models import User
from .pagination import RecipePagination

from foodgram.common_classes import (
    Base64ImageField,
    min_cooking_time,
    max_cooking_time,
    min_ingredient_amount,
    max_ingredient_amount,
)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class AuthorGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return user.subscriptions.filter(author=obj).exists()


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeGetSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = AuthorGetSerializer(read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source="recipeingredient_set", read_only=True
    )
    image = Base64ImageField()
    pagination_class = RecipePagination

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user

        if not user.is_authenticated:
            return False

        return obj.favorited_by.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user

        if not user.is_authenticated:
            return False

        return obj.in_carts.filter(user=user).exists()


class IngredientInRecipeSerializer(
    serializers.Serializer
):  # IngredientS_SerializerPOST
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=min_ingredient_amount, max_value=max_ingredient_amount
    )

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ингредиента с таким id не существует")
        return value


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(many=True, source="recipeingredient_set")
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(
        min_value=min_cooking_time, max_value=max_cooking_time
    )

    class Meta:
        model = Recipe
        fields = ("author", "ingredients", "image", "name", "text", "cooking_time")
        read_only_fields = ("author",)

    def _validate_unique_ingredient_ids(self, ingredients):
        seen = set()
        for ing in ingredients:
            ingredient_id = ing["id"]
            if ingredient_id in seen:
                raise serializers.ValidationError(
                    "В рецепте есть повторяющиеся ингредиенты"
                )
            seen.add(ingredient_id)
        return seen

    def _create_recipe_ingredients(self, recipe, ingredients):
        """Создание связей ингредиентов с рецептом через bulk_create."""
        # Получаем все ID ингредиентов
        ingredient_ids = [ing["id"] for ing in ingredients]

        # Получаем все объекты ингредиентов одним запросом
        ingredient_objs = Ingredient.objects.filter(id__in=ingredient_ids)
        ingredient_map = {ing.id: ing for ing in ingredient_objs}

        # Создаем список объектов RecipeIngredient для bulk_create
        recipe_ingredients = []
        for ing in ingredients:
            ingredient_id = ing["id"]
            ingredient_obj = ingredient_map.get(ingredient_id)

            if not ingredient_obj:
                raise serializers.ValidationError(
                    f"Ингредиент с ID {ingredient_id} не найден"
                )

            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient_obj, amount=ing["amount"]
                )
            )

        # Создаем все связи одним запросом
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop("recipeingredient_set")

        if not ingredients:
            raise serializers.ValidationError("Список ингредиентов пуст")

        self._validate_unique_ingredient_ids(ingredients)

        author = self.context["request"].user
        recipe = Recipe.objects.create(author=author, **validated_data)

        self._create_recipe_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("recipeingredient_set", None)

        if ingredients is not None:
            if not ingredients:
                raise serializers.ValidationError("Список ингредиентов пуст")

            self._validate_unique_ingredient_ids(ingredients)

            # Пересоздание списка ингредиентов
            instance.recipeingredient_set.all().delete()
            self._create_recipe_ingredients(instance, ingredients)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def validate_name(self, value):
        # Если PATCH не передал name, не валидируем
        if self.partial and "name" not in self.initial_data:
            return self.instance.name

        qs = Recipe.objects.filter(name=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("Рецепт с таким названием уже существует")

        return value


class ShortRecipeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscribtionsSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context["request"]
        limit = request.query_params.get("recipes_limit")

        queryset = obj.recipes.all()

        if limit and limit.isdigit():
            queryset = queryset[: int(limit)]

        serializer = ShortRecipeInfoSerializer(
            queryset, many=True, context=self.context
        )
        return serializer.data

    def get_author(self, obj):
        return AuthorGetSerializer(
            obj.author,
            context=self.context,
        ).data


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
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

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
            "recipes_count",
            "recipes",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user

        if not user.is_authenticated:
            return False

        return user.subscriptions.filter(author=obj).exists()

    def get_recipes(self, obj):
        recipes = obj.recipes.all()  # Вместо Recipe.objects.filter(author=obj)
        request = self.context["request"]
        limit = request.query_params.get("recipes_limit")

        if limit and limit.isdigit():
            recipes = recipes[: int(limit)]
        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url if recipe.image else None,
                "cooking_time": recipe.cooking_time,
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        return obj.recipes.count()  # Вместо Recipe.objects.filter(author=obj).count()


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
