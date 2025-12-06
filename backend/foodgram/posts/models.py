from django.db import models
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from foodgram.common_classes import (
    min_cooking_time,
    max_cooking_time,
    min_ingredient_amount,
    max_ingredient_amount,
)
import uuid
import string
import random


class Ingredient(models.Model):
    name = models.CharField(max_length=256, blank=False)
    measurement_unit = models.CharField(max_length=16, blank=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


def generate_short_code(length=5):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", blank=False
    )
    name = models.CharField(max_length=128, blank=False)
    image = models.ImageField(upload_to="recipes/images/", null=False, blank=True)
    text = models.TextField(blank=False)
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", related_name="recipes"
    )
    cooking_time = models.PositiveSmallIntegerField(
        help_text="Время в минутах",
        blank=False,
        validators=[
            MinValueValidator(
                min_cooking_time,
                message="Время приготовления не может быть меньше 1 минуты",
            ),
            MaxValueValidator(
                max_cooking_time,
                message="Время приготовления не может быть больше 32000 минут",
            ),
        ],
    )
    short_code = models.CharField(max_length=16, unique=True, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pub_date"]  # Сортировка по дате публикации (новые сначала)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def save(self, *args, **kwargs):
        # Генерируем код только один раз — при создании
        if not self.short_code:
            self.short_code = uuid.uuid4().hex[:6]  # например: "3d0a9f"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                min_ingredient_amount,
                message="Кол-во ингредиента не может быть меньше 1",
            ),
            MaxValueValidator(
                max_ingredient_amount,
                message="Кол-во ингрединета не может быть больше 32000",
            ),
        ]
    )

    class Meta:
        ordering = ["ingredient__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_ingredient_per_recipe"
            )
        ]
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount}"


class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by"
    )

    class Meta:
        ordering = ["-recipe__pub_date"]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe_favourite"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="in_carts"
    )

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe_cart"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
