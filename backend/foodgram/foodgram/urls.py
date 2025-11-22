from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from django.conf import settings
from django.conf.urls.static import static

from posts.views import RecipesViewSet, IngredientsViewSet, SubscribtionsViewSet
from users.views import UserViewSet



router = DefaultRouter()
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientsViewSet, basename="ingredients")
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/subscriptions/', SubscribtionsViewSet.as_view({'get': 'list'})),
    path('api/', include(router.urls)),
    path('api/auth/',include('djoser.urls.authtoken')),
    
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
