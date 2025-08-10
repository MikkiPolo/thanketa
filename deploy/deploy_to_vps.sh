#!/bin/bash

# Скрипт для деплоя приложения на VPS
# Использование: ./deploy_to_vps.sh user@server.com

set -e

if [ $# -eq 0 ]; then
    echo "❌ Укажите адрес сервера: ./deploy_to_vps.sh user@server.com"
    exit 1
fi

SERVER=$1
REMOTE_DIR="/opt/wardrobe-app"

echo "🚀 Деплой на VPS: $SERVER"

# Проверяем подключение к серверу
echo "🔍 Проверяем подключение к серверу..."
ssh -o ConnectTimeout=10 $SERVER "echo '✅ Подключение успешно'" || {
    echo "❌ Не удается подключиться к серверу"
    exit 1
}

# Создаем архив с кодом
echo "📦 Создаем архив с кодом..."
tar -czf wardrobe-app.tar.gz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    -C .. .

# Копируем архив на сервер
echo "📤 Копируем код на сервер..."
scp wardrobe-app.tar.gz $SERVER:/tmp/

# Копируем скрипты деплоя
echo "📤 Копируем скрипты деплоя..."
scp vps_setup.sh $SERVER:/tmp/
scp docker-compose.yml $SERVER:/tmp/
scp nginx.conf $SERVER:/tmp/

# Выполняем настройку на сервере
echo "⚙️  Настраиваем сервер..."
ssh $SERVER << 'EOF'
    set -e
    
    echo "📦 Распаковываем код..."
    sudo mkdir -p $REMOTE_DIR
    sudo tar -xzf /tmp/wardrobe-app.tar.gz -C $REMOTE_DIR --strip-components=1
    sudo chown -R wardrobe:wardrobe $REMOTE_DIR
    
    echo "⚙️  Запускаем настройку VPS..."
    sudo bash /tmp/vps_setup.sh
    
    echo "🚀 Запускаем деплой..."
    sudo $REMOTE_DIR/deploy.sh
    
    echo "🧹 Очищаем временные файлы..."
    rm -f /tmp/wardrobe-app.tar.gz /tmp/vps_setup.sh /tmp/docker-compose.yml /tmp/nginx.conf
EOF

# Очищаем локальные файлы
rm -f wardrobe-app.tar.gz

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "📋 Информация о сервере:"
echo "- IP адрес: $(ssh $SERVER 'curl -s ifconfig.me')"
echo "- Статус сервисов: ssh $SERVER 'sudo /opt/wardrobe-app/monitor.sh'"
echo "- Логи бэкенда: ssh $SERVER 'sudo journalctl -u wardrobe-backend -f'"
echo "- Логи Ollama: ssh $SERVER 'sudo journalctl -u ollama -f'"
echo ""
echo "🌐 Приложение доступно по адресу: http://$(ssh $SERVER 'curl -s ifconfig.me')"
echo ""
echo "🔗 Полезные команды:"
echo "- Перезапуск: ssh $SERVER 'sudo systemctl restart wardrobe-backend'"
echo "- Обновление: ssh $SERVER 'sudo $REMOTE_DIR/deploy.sh'"
echo "- Мониторинг: ssh $SERVER 'sudo /opt/wardrobe-app/monitor.sh'" 