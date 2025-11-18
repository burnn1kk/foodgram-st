from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from posts.views import RecipesViewSet, IngredientsViewSet
from users.views import CustomTokenCreateView, UserViewSet


router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipesViewSet)
router.register('ingredients', IngredientsViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('djoser.urls.authtoken')),

    path('api/', include(router.urls)),
]