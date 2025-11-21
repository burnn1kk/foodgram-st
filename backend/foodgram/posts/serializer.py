from rest_framework import serializers

from .models import Ingredient, Recipe
from .pagination import PageLimitPagination
class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")

class RecipeGetSerializer(serializers.ModelSerializer):

    pagination_class = PageLimitPagination
    class Meta:
        model = Recipe
        fields = ("id","author","ingredients","is_favorited","is_in_shopping_cart","name","image","text","cooking_time")

class RecipePostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("ingredients","image","name","text","cooking_time")


    