from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Ingredient, Recipe, RecipeIngredient
from .serializer import IngredientSerializer, RecipeGetSerializer, RecipePostSerializer
from .pagination import RecipePagination
from .permissions import OwnerOrReadOnly

class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = RecipePagination
    permission_classes = [OwnerOrReadOnly,]
    serializer_class = RecipeGetSerializer

    def create(self, request):
        serializer = RecipePostSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    def list(self, request):
        queryset = Recipe.objects.all()
        page = self.paginate_queryset(queryset)
        serializer = RecipeGetSerializer(page, context={"request" : request}, many=True)
        return self.get_paginated_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("pk")
        if Recipe.objects.filter(id=recipe_id).exists():
            recipe = Recipe.objects.get(id = recipe_id)
            serializer = RecipeGetSerializer(recipe, context={"request" : request})
            return Response(serializer.data)
        return Response(status=404)
        


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']