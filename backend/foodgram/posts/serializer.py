from rest_framework import serializers

from .models import Ingredient, Recipe, RecipeIngredient, User
from .pagination import RecipePagination

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")

class AuthorGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email", "id", "username",
            "first_name", "last_name",
            "is_subscribed", "avatar"
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
        many=True,
        source="recipeingredient_set"
    )
    pagination_class = RecipePagination
    class Meta:
        model = Recipe
        fields = ("id","author","ingredients","is_favorited","is_in_shopping_cart","name","image","text","cooking_time")

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

class IngredientInRecipeSerializer(serializers.Serializer): # IngredientS_SerializerPOST
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ингредиента с таким id не существует")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество ингредиента должно быть больше 0")
        return value

class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source="recipeingredient_set"
    )

    class Meta:
        model = Recipe
        fields = ("author", "ingredients", "image", "name", "text", "cooking_time")
        read_only_fields = ("author",)

    def create(self, validated_data):
        ingredients = validated_data.pop("recipeingredient_set")  #необходимо тк в модели recipe: ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")
        author = self.context["request"].user #поэтому ожидается набор объектов Ingredient, но там нет поля amount => ошибка
        recipe = Recipe.objects.create(author=author, **validated_data) #source позволяет переопределить, откуда именно сериализатор возьмёт данные.

        for ing in ingredients:
            ingredient_obj = Ingredient.objects.get(id=ing["id"])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj,
                amount=ing["amount"]
            )

        return recipe
    
    def validate_name(self, value):
        if Recipe.objects.filter(name=value).exists():
            raise serializers.ValidationError("Рецепт с таким названием уже существует")
        return value
    
    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError("Время приготовления должно быть больше 0")
        return value

    