#!/bin/bash

# Скрипт для настройки VPS сервера для развертывания бэкенда с Ollama
# Запускать с правами root или через sudo

set -e  # Остановка при ошибке

echo "🚀 Настройка VPS сервера для развертывания бэкенда с Ollama"

# Проверяем, что скрипт запущен от root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен быть запущен с правами root (sudo)"
   exit 1
fi

# Обновляем систему
echo "📦 Обновляем систему..."
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
echo "📦 Устанавливаем необходимые пакеты..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    curl \
    wget \
    git \
    htop \
    ufw \
    certbot \
    python3-certbot-nginx \
    supervisor \
    build-essential \
    pkg-config \
    libssl-dev \
    libffi-dev \
    python3-dev

# Создаем пользователя для приложения
echo "👤 Создаем пользователя для приложения..."
if ! id "wardrobe" &>/dev/null; then
    useradd -m -s /bin/bash wardrobe
    usermod -aG sudo wardrobe
    echo "wardrobe:wardrobe123" | chpasswd
    echo "✅ Пользователь 'wardrobe' создан"
else
    echo "ℹ️  Пользователь 'wardrobe' уже существует"
fi

# Создаем директории
echo "📁 Создаем директории..."
mkdir -p /opt/wardrobe-app
mkdir -p /var/log/wardrobe
mkdir -p /etc/wardrobe
chown -R wardrobe:wardrobe /opt/wardrobe-app
chown -R wardrobe:wardrobe /var/log/wardrobe
chown -R wardrobe:wardrobe /etc/wardrobe

# Устанавливаем Ollama
echo "🤖 Устанавливаем Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# Создаем systemd сервис для Ollama
echo "⚙️  Создаем systemd сервис для Ollama..."
cat > /etc/systemd/system/ollama.service << EOF
[Unit]
Description=Ollama AI Service
After=network.target

[Service]
Type=simple
User=wardrobe
WorkingDirectory=/home/wardrobe
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=10
Environment=PATH=/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

# Включаем и запускаем Ollama
systemctl daemon-reload
systemctl enable ollama
systemctl start ollama

# Настраиваем firewall
echo "🔥 Настраиваем firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 5001  # Порт бэкенда
ufw allow 11434  # Порт Ollama

# Создаем конфигурацию Nginx
echo "🌐 Настраиваем Nginx..."
cat > /etc/nginx/sites-available/wardrobe-app << EOF
server {
    listen 80;
    server_name _;  # Замените на ваш домен

    # Логи
    access_log /var/log/nginx/wardrobe-access.log;
    error_log /var/log/nginx/wardrobe-error.log;

    # Проксирование на бэкенд
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Таймауты для долгих запросов ИИ
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Статические файлы (если есть)
    location /static/ {
        alias /opt/wardrobe-app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        access_log off;
    }
}
EOF

# Активируем сайт
ln -sf /etc/nginx/sites-available/wardrobe-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

# Создаем systemd сервис для бэкенда
echo "⚙️  Создаем systemd сервис для бэкенда..."
cat > /etc/systemd/system/wardrobe-backend.service << EOF
[Unit]
Description=Wardrobe Backend Service
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=wardrobe
Group=wardrobe
WorkingDirectory=/opt/wardrobe-app
Environment=PATH=/opt/wardrobe-app/venv/bin
ExecStart=/opt/wardrobe-app/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Создаем supervisor конфигурацию для мониторинга
echo "👁️  Настраиваем мониторинг..."
cat > /etc/supervisor/conf.d/wardrobe.conf << EOF
[program:wardrobe-backend]
command=/opt/wardrobe-app/venv/bin/python app.py
directory=/opt/wardrobe-app
user=wardrobe
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/wardrobe/backend.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10

[program:ollama-monitor]
command=/usr/local/bin/ollama list
directory=/home/wardrobe
user=wardrobe
autostart=false
autorestart=false
redirect_stderr=true
stdout_logfile=/var/log/wardrobe/ollama-monitor.log
EOF

# Создаем скрипт для деплоя
echo "📝 Создаем скрипт деплоя..."
cat > /opt/wardrobe-app/deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Деплой приложения..."

# Переходим в директорию приложения
cd /opt/wardrobe-app

# Останавливаем сервисы
sudo systemctl stop wardrobe-backend

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем зависимости
echo "📦 Обновляем зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Создаем .env если его нет
if [ ! -f ".env" ]; then
    echo "⚙️  Создаем .env файл..."
    cat > .env << 'ENVEOF'
# Настройки ИИ генератора капсул
AI_GENERATOR_TYPE=ollama
AI_MODEL_NAME=llama2:7b
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=4000
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=30
USE_FALLBACK_GENERATION=true
LOG_LEVEL=INFO
LOG_FILE=ai_capsules.log
ENABLE_CACHE=true
CACHE_TTL=3600
MAX_WARDROBE_ITEMS=50
MAX_CAPSULES_PER_CATEGORY=8
ENVEOF
fi

# Загружаем модель Ollama если её нет
echo "🤖 Проверяем модель Ollama..."
if ! ollama list | grep -q "llama2:7b"; then
    echo "📥 Загружаем модель llama2:7b..."
    ollama pull llama2:7b
fi

# Запускаем сервисы
echo "▶️  Запускаем сервисы..."
sudo systemctl start wardrobe-backend
sudo systemctl enable wardrobe-backend

echo "✅ Деплой завершен!"
echo "🌐 Приложение доступно по адресу: http://$(curl -s ifconfig.me)"
echo "📊 Логи: sudo journalctl -u wardrobe-backend -f"
EOF

chmod +x /opt/wardrobe-app/deploy.sh
chown wardrobe:wardrobe /opt/wardrobe-app/deploy.sh

# Создаем скрипт для мониторинга
echo "📊 Создаем скрипт мониторинга..."
cat > /opt/wardrobe-app/monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Мониторинг системы"
echo "======================"

echo "💾 Использование памяти:"
free -h

echo ""
echo "🔥 Использование CPU:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}'

echo ""
echo "💿 Использование диска:"
df -h /

echo ""
echo "🤖 Статус Ollama:"
systemctl is-active ollama

echo ""
echo "🌐 Статус бэкенда:"
systemctl is-active wardrobe-backend

echo ""
echo "📈 Логи бэкенда (последние 10 строк):"
journalctl -u wardrobe-backend --no-pager -n 10

echo ""
echo "📈 Логи Ollama (последние 10 строк):"
journalctl -u ollama --no-pager -n 10
EOF

chmod +x /opt/wardrobe-app/monitor.sh
chown wardrobe:wardrobe /opt/wardrobe-app/monitor.sh

echo ""
echo "🎉 Настройка VPS завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Скопируйте код приложения в /opt/wardrobe-app/"
echo "2. Запустите деплой: sudo /opt/wardrobe-app/deploy.sh"
echo "3. Проверьте статус: sudo /opt/wardrobe-app/monitor.sh"
echo ""
echo "🔗 Полезные команды:"
echo "- Логи бэкенда: sudo journalctl -u wardrobe-backend -f"
echo "- Логи Ollama: sudo journalctl -u ollama -f"
echo "- Перезапуск: sudo systemctl restart wardrobe-backend"
echo "- Статус: sudo systemctl status wardrobe-backend"
echo ""
echo "🌐 Приложение будет доступно по адресу: http://$(curl -s ifconfig.me)" 