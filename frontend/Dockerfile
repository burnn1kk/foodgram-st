# === Stage 1: Build React App ===
FROM node:21.7.1-alpine AS build

WORKDIR /app

# Копируем package.json и package-lock.json / yarn.lock
COPY package*.json ./
COPY yarn.lock ./

# Устанавливаем зависимости
RUN npm install

# Копируем весь исходник
COPY . ./

# Сборка фронта
RUN npm run build

# Stage 2: только результат сборки
FROM alpine:latest AS frontend-build
WORKDIR /app
COPY --from=build /app/build /app/build

