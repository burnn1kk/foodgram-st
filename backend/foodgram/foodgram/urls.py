from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework.authtoken import views

from posts.views import RecipesViewSet, IngredientsViewSet

router = SimpleRouter()
router.register('recipes', RecipesViewSet)
router.register('ingredients', IngredientsViewSet)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/', include('djoser.urls.authtoken')),
    path('api/',include(router.urls))
]