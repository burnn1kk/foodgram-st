from rest_framework import serializers

from posts.models import Ingredient, Recipe, RecipeIngredient
from users.models import User
from .pagination import RecipePagination

from foodgram.common_classes import Base64ImageField


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
    amount = serializers.IntegerField()

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ингредиента с таким id не существует")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Количество ингредиента должно быть больше 0"
            )
        return value


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(many=True, source="recipeingredient_set")
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ("author", "ingredients", "image", "name", "text", "cooking_time")
        read_only_fields = ("author",)

    def create(self, validated_data):
        ingredients = validated_data.pop(
            "recipeingredient_set"
        )  # необходимо тк в модели recipe: ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")
        if len(ingredients) == 0:
            raise serializers.ValidationError("Список ингредиентов пуст")
        for i in range(0, len(ingredients)):  # слегка говнокода (я реально устал)
            for j in range(i + 1, len(ingredients)):
                if ingredients[i] == ingredients[j]:
                    raise serializers.ValidationError(
                        "В рецепте есть повторяющиеся ингредиенты"
                    )
        author = self.context[
            "request"
        ].user  # поэтому ожидается набор объектов Ingredient, но там нет поля amount => ошибка
        recipe = Recipe.objects.create(
            author=author, **validated_data
        )  # source позволяет переопределить, откуда именно сериализатор возьмёт данные.

        for ing in ingredients:
            ingredient_obj = Ingredient.objects.get(id=ing["id"])
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_obj, amount=ing["amount"]
            )

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("recipeingredient_set", None)

        if ingredients is not None:
            if ingredients == []:
                raise serializers.ValidationError("Список ингредиентов пуст")

            else:
                # Проверка на дубликаты
                seen = set()
                for ing in ingredients:
                    if ing["id"] in seen:
                        raise serializers.ValidationError(
                            "В рецепте есть повторяющиеся ингредиенты"
                        )
                    seen.add(ing["id"])

                # Пересоздание списка ингредиентов
                instance.recipeingredient_set.all().delete()
                for ing in ingredients:
                    ingredient_obj = Ingredient.objects.get(id=ing["id"])
                    RecipeIngredient.objects.create(
                        recipe=instance, ingredient=ingredient_obj, amount=ing["amount"]
                    )

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

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Время приготовления должно быть больше 0"
            )
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
        recipes = Recipe.objects.filter(author=obj)
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
        return Recipe.objects.filter(author=obj).count()


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
