from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=16)

class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,related_name='recipes')
    name = models.CharField(max_length=128)
    picture = models.ImageField()
    description = models.TextField()
    ingredients = models.ManyToManyField(Ingredient,through='RecipeIngredient',related_name='recipes')
    cook_time = models.PositiveIntegerField(help_text="Время в минутах")

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.FloatField()

    class Meta:
        unique_together = ('recipe', 'ingredient') #чтобы один ингредиент не повторялся в рецепте несколько раз