#!/bin/bash
set -e

python manage.py migrate

python import_ingredients.py

python manage.py collectstatic --noinput

exec "$@"

