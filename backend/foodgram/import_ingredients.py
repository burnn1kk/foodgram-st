# Скрипт для загрузки ингредиентов в БД
import csv
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodgram.settings")
django.setup()

from posts.models import Ingredient

with open("ingredients.csv", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        name = row[0].strip()
        measurement_unit = row[1].strip()
        Ingredient.objects.get_or_create(name=name, measurement_unit=measurement_unit)

print("Ingredients imported successfully!")
