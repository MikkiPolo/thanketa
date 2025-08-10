#!/bin/bash

# Скрипт для деплоя frontend на VPS
set -e

echo "🚀 Начинаем деплой frontend на VPS..."

# Проверяем наличие необходимых файлов
if [ ! -f "package.json" ]; then
    echo "❌ Ошибка: package.json не найден"
    exit 1
fi

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
npm ci

# Собираем проект
echo "🔨 Собираем проект..."
npm run build

# Проверяем, что сборка прошла успешно
if [ ! -d "dist" ]; then
    echo "❌ Ошибка: папка dist не создана"
    exit 1
fi

echo "✅ Frontend собран успешно!"

# Создаем архив для передачи на VPS
echo "📦 Создаем архив..."
tar -czf frontend.tar.gz dist/ nginx.conf Dockerfile

echo "📤 Архив создан: frontend.tar.gz"
echo ""
echo "📋 Следующие шаги:"
echo "1. Скопируйте frontend.tar.gz на VPS"
echo "2. Распакуйте архив на VPS"
echo "3. Запустите Docker контейнер"
echo ""
echo "Команды для VPS:"
echo "scp frontend.tar.gz user@your-vps:/path/to/deploy/"
echo "ssh user@your-vps"
echo "cd /path/to/deploy/"
echo "tar -xzf frontend.tar.gz"
echo "docker build -t wardrobe-frontend ."
echo "docker run -d -p 3000:80 --name wardrobe-frontend wardrobe-frontend" 