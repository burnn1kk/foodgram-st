from rest_framework import viewsets 

from .models import Ingredient
from .serializer import IngredientSerializer, RecipeGetSerializer, RecipePostSerializer
from .pagination import PageLimitPagination

class RecipesViewSet(viewsets.ModelViewSet):
    pass

class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get_serializer_class(self):
        method = self.request.method
        if method == "GET":
            return RecipeGetSerializer
        elif method == "POST":
            return RecipePostSerializer