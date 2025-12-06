# Foodgram

Foodgram — это веб-приложение, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. 

---

## Технологии

Проект разработан с использованием следующих технологий:

* Backend: Python/Django Rest Framework
* Frontend: HTML, CSS, JavaScript
* База данных: PostgreSQL
* Аутентификация и управление пользователями: Djoser
* Контейнеризация и деплой: Docker, Docker Compose

---

## Установка и запуск

1. Клонируйте репозиторий:

```bash
git clone https://github.com/burnn1kk/foodgram-st
cd foodgram
```

2. Создайте виртуальное окружение и установите зависимости:

```bash
python3 -m venv venv
source venv/bin/activate
cd backend/foodgram
pip install -r requirements.txt 
```

3. Создайте файлы с переменными окружения (находясь в директории foodgram/infra)
Пример файла
```txt
DJANGO_SECRET_KEY="<SECRET_KEY>"
ALLOWED_HOSTS=localhost,127.0.0.1
BASE_URL=http://127.0.0.1:8000
POSTGRES_DB=foodgram_bd
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

```
4. Скопируйте этот файл в директорию foodgram/backend/foodgram
```bash
cp foodgram/infra/.env foodgram/backend/foodgram
```

5. Разверните контейнеры Docker
```bash
cd foodgram/infra
docker compose build
docker compose up
```

Ингредиенты для рецептов подгружаются в БД при постройке образов с помощью скрипта import_ingredients.py

---

## Тестовые данные
Если вы хотите проверить работоспособность проекта с уже готовым пользователями и рецептами, то на этот случай заготовлена коллекция postman.
Для запуска необходимо иметь Node.js и сам postman.

```bash
sudo apt install nodejs npm
npm install -g newman
cd backend/foodgram
newman run add_users_and_recipes.postman_collection.json 
```
Если вы собираетесь использовать тестовые данные не на localhost, то измените переменную baseUrl в add_users_and_recipes.postman_collection.json.

После этого на сайте будет несколько рецептов (без картинок) от разных пользователей. Данные для входа под любым из пользователей так же можно посмотреть в add_users_and_recipes.postman_collection.json.


