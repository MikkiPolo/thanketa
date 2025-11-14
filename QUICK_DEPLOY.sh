#!/bin/bash
# Быстрое развертывание на новом сервере
# Использование: скопируйте этот файл на сервер и выполните: bash QUICK_DEPLOY.sh

set -e

echo "🚀 Быстрое развертывание приложения"
echo "===================================="
echo ""

# 1. Установка Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# 2. Установка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Установка Docker Compose..."
    apt update
    apt install docker-compose -y
fi

# 3. Клонирование репозитория
if [ ! -d "tganketa-copy" ]; then
    echo "📥 Клонирование репозитория..."
    git clone git@github.com:MikkiPolo/thanketa.git tganketa-copy || {
        echo "⚠️ Если SSH ключ не настроен, используйте HTTPS:"
        git clone https://github.com/MikkiPolo/thanketa.git tganketa-copy
    }
fi

cd tganketa-copy
git checkout main
git pull origin main

# 4. Настройка .env
if [ ! -f "backend/.env" ]; then
    echo "⚙️ Создание .env файла..."
    cd backend
    cp env.example .env
    echo ""
    echo "⚠️ ОТРЕДАКТИРУЙТЕ backend/.env перед продолжением!"
    echo "   nano backend/.env"
    echo ""
    read -p "Нажмите Enter после редактирования .env..."
    cd ..
fi

# 5. Запуск
echo "🐳 Запуск контейнеров..."
docker-compose -f docker-compose.full.yml up -d

echo ""
echo "⏳ Ожидание запуска (15 секунд)..."
sleep 15

# 6. Проверка
echo ""
echo "📊 Статус:"
docker-compose -f docker-compose.full.yml ps

echo ""
echo "🏥 Health check:"
curl -s http://localhost:5001/health || echo "⚠️ Backend еще запускается..."

echo ""
echo "✅ Готово! Приложение развернуто."
echo ""
echo "📝 Полезные команды:"
echo "   Логи: docker-compose -f docker-compose.full.yml logs -f"
echo "   Остановка: docker-compose -f docker-compose.full.yml down"
echo "   Перезапуск: docker-compose -f docker-compose.full.yml restart"

