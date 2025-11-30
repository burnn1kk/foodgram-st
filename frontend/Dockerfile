# === Stage 1: Build React App ===
FROM node:21.7.1-alpine AS build

WORKDIR /app

# Копируем package.json и package-lock.json / yarn.lock
COPY package*.json ./
COPY yarn.lock ./

# Ставим зависимости
RUN npm install

# Копируем весь исходник
COPY . ./

# Сборка фронта
RUN npm run build

# === Stage 2: Nginx ===
FROM nginx:1.25.4-alpine

# Удаляем дефолтный html
RUN rm -rf /usr/share/nginx/html/*

# Копируем собранный фронт
COPY --from=build /app/build /usr/share/nginx/html

# Копируем кастомный конфиг nginx
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Открываем порт
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]

