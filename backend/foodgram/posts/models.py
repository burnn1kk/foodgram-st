from django.db import models
from django.contrib.auth import get_user_model

from users.models import User

class Ingredient(models.Model):
    name = models.CharField(max_length=128, blank=False)
    measurement_unit = models.CharField(max_length=16, blank=False)

class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,related_name='recipes', blank=False)
    name = models.CharField(max_length=128, blank=False)
    image = models.ImageField(upload_to='recipes/images/',null=False,blank=True)
    text = models.TextField(blank=False)
    ingredients = models.ManyToManyField(Ingredient)
    cooking_time = models.PositiveIntegerField(help_text="Время в минутах", blank=False)

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites"   
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by"  
    )

class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_carts"
    )
