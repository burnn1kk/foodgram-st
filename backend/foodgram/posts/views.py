from rest_framework import viewsets, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError

from .models import Ingredient, Recipe, RecipeIngredient, Favourite, ShoppingCart
from .serializer import IngredientSerializer, RecipeGetSerializer, RecipePostSerializer, SubscribtionsSerializer, RecipeInShoppingCartSerializer    
from .pagination import RecipePagination
from .permissions import OwnerOrReadOnly

from users.models import User

class RecipesViewSet(viewsets.ModelViewSet):
    #queryset = Recipe.objects.all()
    pagination_class = RecipePagination
    permission_classes = [OwnerOrReadOnly,]
    serializer_class = RecipeGetSerializer

    def get_queryset(self):
        allowed_params = {'page','author', 'is_favorited', 'limit', 'is_in_shopping_cart'}

        for param in self.request.query_params.keys():
            if param not in allowed_params:
                raise ValidationError({param: "Неизвестный параметр"})
            
        queryset = Recipe.objects.all().order_by('id')  
        user = self.request.user

        author = self.request.query_params.get('author')
        is_favorited = self.request.query_params.get('is_favorited')

        if author:
            queryset = queryset.filter(author=author)

        if is_favorited is not None:
            if is_favorited not in ('0', '1'):
                raise ValidationError({"is_favorited": "Параметр должен быть '0' или '1'."})

            if user.is_authenticated:
                if is_favorited == '1':
                    queryset = queryset.filter(favorited_by__user=user)
                else:
                    queryset = queryset.exclude(favorited_by__user=user)
        return queryset

    def create(self, request):
        serializer = RecipePostSerializer(data=request.data, context={"request": request})
        
        if serializer.is_valid():
            recipe = serializer.save()
            output = RecipeGetSerializer(recipe, context = {"request" : request}) #возвращает после успешного post
            return Response(output.data, status=201)#рецепт сериализованный сериализатором для вывода
        return Response(serializer.errors, status=400)#для того чтобы user и ingredients выводились подробно
    
    def update(self, request, *args, **kwargs):
            partial = kwargs.pop('partial', False)   
            instance = self.get_object()
        
            serializer = RecipePostSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            response_data = RecipeGetSerializer(serializer.data,context={"request": request})
            return Response(response_data, status=200)

    def list(self, request):
        queryset = self.get_queryset()
        if request.query_params.get('author') and not queryset.exists():
            return Response(status=404)
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
            if Favourite.objects.filter(user=user, recipe=recipe).exists():
                Favourite.objects.get_or_create(user=user,recipe = recipe)
                return Response({"status":"added to favourite"}, status=201)
            return Response(status=400)
        
        if request.method == "DELETE":
            if Favourite.objects.filter(user=user,recipe=recipe).exists():
                Favourite.objects.filter(user=user,recipe=recipe).delete()
                return Response(status=204)
            return Response(status=400)
    
    @action(detail=True, methods=["post","delete"],  permission_classes=[permissions.IsAuthenticated], url_name='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        serializer = RecipeInShoppingCartSerializer(recipe)
        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(status=400)
            ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            return Response({"status" : "added to shopping cart"}, status=201)
        if request.method == "DELETE":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
                return Response(status=204)
            return Response(status=400)

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