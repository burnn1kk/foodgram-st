from django.contrib import admin

from posts.models import Recipe, Ingredient, RecipeIngredient

from users.models import User


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ("ingredient",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "cooking_time")
    list_filter = ("author", "cooking_time")
    search_fields = ("name", "author__username")
    ordering = ("id",)
    inlines = (RecipeIngredientInline,)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    list_filter = ("measurement_unit", "name")
    search_fields = ("name", "measurement_unit")
    ordering = ("id",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username", "first_name", "last_name", "is_active")
    list_filter = ("id", "username", "email", "is_active")
    search_fields = ("email", "username")
    ordering = ("id",)
    list_editable = ("is_active",)
