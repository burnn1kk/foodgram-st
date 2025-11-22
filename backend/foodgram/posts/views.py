from rest_framework import viewsets, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Ingredient, Recipe, RecipeIngredient, Favourite, ShoppingCart
from .serializer import IngredientSerializer, RecipeGetSerializer, RecipePostSerializer, SubscribtionsSerializer, RecipeInShoppingCartSerializer
from .pagination import RecipePagination
from .permissions import OwnerOrReadOnly

from users.models import User

class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = RecipePagination
    permission_classes = [OwnerOrReadOnly,]
    serializer_class = RecipeGetSerializer

    def create(self, request):
        serializer = RecipePostSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            recipe = serializer.save()
            output = RecipeGetSerializer(recipe, context = {"request" : request}) #возвращает после успешного post
            return Response(output.data, status=201)#рецепт сериализованный сериализатором для вывода
        return Response(serializer.errors, status=400)#для того чтобы user и ingredients выводились подробно
    
    def list(self, request):
        queryset = Recipe.objects.all()
        page = self.paginate_queryset(queryset)
        serializer = RecipeGetSerializer(page, context={"request" : request}, many=True)
        paginated = self.get_paginated_response(serializer.data)
        return Response(paginated.data, status=200)
    
    def retrieve(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("pk")
        if Recipe.objects.filter(id=recipe_id).exists():
            recipe = Recipe.objects.get(id = recipe_id)
            serializer = RecipeGetSerializer(recipe, context={"request" : request})
            return Response(serializer.data, status=200)
        return Response(status=404)
        
    @action(detail=True, methods=["post","delete"], permission_classes=[permissions.IsAuthenticated], url_name='favorite')
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            Favourite.objects.get_or_create(user=user,recipe = recipe)
            return Response({"status":"added to favourite"}, status=201)
        
        if request.method == "DELETE":
            if Favourite.objects.filter(user=user,recipe=recipe).exists():
                Favourite.objects.filter(user=user,recipe=recipe).delete()
                return Response(status=204)
            return Response(status=404)
    
    @action(detail=True, methods=["post","delete"],  permission_classes=[permissions.IsAuthenticated], url_name='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        serializer = RecipeInShoppingCartSerializer(recipe)
        if request.method == "POST":
            ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            return Response({"status" : "added to shopping cart"}, status=201)
        if request.method == "DELETE":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
                return Response(status=204)
            return Response(status=404)

class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__istartswith=name)
        return qs

class SubscribtionsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscribtionsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(subscribers__subsciber=self.request.user).distinct()