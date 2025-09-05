# Используем официальный образ Node.js в качестве базового образа
FROM node:20-alpine

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем package.json и package-lock.json (или yarn.lock) в рабочую директорию
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install -d

# Добавьте установку недостающего пакета
RUN npm install jsbarcode

# Копируем все файлы проекта в рабочую директорию
COPY . .

# Собираем проект Quasar
RUN npm run build

CMD ["npx", "-y", "http-server", "-p", "8000", "./dist/spa", "-d", "false"]
