# Простой Dockerfile для frontend
FROM nginx:alpine

# Копирование собранных файлов
COPY dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx-frontend.conf /etc/nginx/nginx.conf

# Открытие порта
EXPOSE 80

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"] 