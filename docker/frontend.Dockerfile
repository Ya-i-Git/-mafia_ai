FROM node:20-alpine

WORKDIR /app

# Копируем package.json и lock-файл
COPY frontend/package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем исходный код фронтенда
COPY frontend/ .

# Открываем порт Vite (по умолчанию 3000)
EXPOSE 3000

# Запускаем dev-сервер на 0.0.0.0 (чтобы был доступен из контейнера)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]