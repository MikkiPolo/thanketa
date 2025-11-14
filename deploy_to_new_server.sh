#!/bin/bash
# Скрипт для развертывания на новом сервере
# Использование: ./deploy_to_new_server.sh

set -e  # Остановка при ошибке

echo "🚀 Начало развертывания на новом сервере..."
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаю..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаю..."
    apt update
    apt install docker-compose -y
fi

echo "✅ Docker и Docker Compose установлены"
echo ""

# Клонирование репозитория (если еще не склонирован)
if [ ! -d "tganketa-copy" ]; then
    echo "📥 Клонирование репозитория..."
    git clone git@github.com:MikkiPolo/thanketa.git tganketa-copy
    cd tganketa-copy
else
    echo "📂 Репозиторий уже существует. Обновляю..."
    cd tganketa-copy
    git pull origin main
fi

echo "✅ Код получен"
echo ""

# Настройка переменных окружения
if [ ! -f "backend/.env" ]; then
    echo "⚙️ Создание .env файла..."
    cd backend
    cp env.example .env
    echo ""
    echo "⚠️ ВАЖНО: Отредактируйте backend/.env и заполните:"
    echo "   - OPENAI_API_KEY"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_ANON_KEY"
    echo "   - SUPABASE_SERVICE_KEY"
    echo ""
    read -p "Нажмите Enter после заполнения .env файла..."
    cd ..
else
    echo "✅ .env файл уже существует"
fi

# Запуск приложения
echo "🐳 Запуск Docker контейнеров..."
docker-compose -f docker-compose.full.yml up -d

echo ""
echo "⏳ Ожидание запуска сервисов (10 секунд)..."
sleep 10

# Проверка статуса
echo ""
echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.full.yml ps

echo ""
echo "🏥 Проверка health endpoint:"
curl -s http://localhost:5001/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5001/health

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Полезные команды:"
echo "   Просмотр логов: docker-compose -f docker-compose.full.yml logs -f"
echo "   Остановка: docker-compose -f docker-compose.full.yml down"
echo "   Перезапуск: docker-compose -f docker-compose.full.yml restart"
echo "   Статус: docker-compose -f docker-compose.full.yml ps"

