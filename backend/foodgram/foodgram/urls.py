from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from posts.views import RecipesViewSet, IngredientsViewSet
from users.views import UserViewSet

router = DefaultRouter()
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientsViewSet)
router.register('users', UserViewSet,basename='users')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/',include('djoser.urls.authtoken'))
]   