# Используем официальный образ Node.js в качестве базового образа
FROM node:20-alpine

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем package.json и package-lock.json (или yarn.lock) в рабочую директорию
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install -d

# Копируем все файлы проекта в рабочую директорию
COPY . .

RUN npm install @humanwhocodes/retry@0.3.1 @humanfs/node@0.12.0

# Собираем проект Quasar
RUN npm run build

CMD ["npx", "-y", "http-server", "-p", "8000", "./dist/spa", "-d", "false"]
