# Развертывание на VPS

Это руководство поможет вам развернуть приложение с локальной генерацией капсул на VPS сервере.

## 🎯 Требования к VPS

### Минимальные требования:
- **RAM:** 8GB (рекомендуется 16GB)
- **CPU:** 4 ядра
- **Диск:** 50GB SSD
- **ОС:** Ubuntu 20.04+ или Debian 11+

### Рекомендуемые провайдеры:
- **DigitalOcean** - Droplet с 16GB RAM
- **Linode** - Nanode с 16GB RAM
- **Vultr** - High Performance с 16GB RAM
- **Hetzner** - Cloud CX31 (16GB RAM)

## 🚀 Быстрый деплой

### 1. Подготовка локальной машины

```bash
# Перейдите в папку deploy
cd deploy

# Сделайте скрипты исполняемыми
chmod +x vps_setup.sh deploy_to_vps.sh
```

### 2. Настройка SSH ключей

```bash
# Генерируем SSH ключ (если нет)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Копируем ключ на сервер
ssh-copy-id root@your-server-ip
```

### 3. Автоматический деплой

```bash
# Запускаем автоматический деплой
./deploy_to_vps.sh root@your-server-ip
```

## 🔧 Ручная настройка

### 1. Подключение к серверу

```bash
ssh root@your-server-ip
```

### 2. Настройка системы

```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y python3 python3-pip python3-venv nginx curl wget git htop ufw
```

### 3. Установка Ollama

```bash
# Устанавливаем Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Загружаем модель
ollama pull llama2:7b

# Запускаем сервер
ollama serve
```

### 4. Настройка приложения

```bash
# Создаем директорию
mkdir -p /opt/wardrobe-app
cd /opt/wardrobe-app

# Копируем код (через git или scp)
git clone https://github.com/your-repo/wardrobe-app.git .
# или
scp -r /path/to/local/code/* root@server:/opt/wardrobe-app/

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 5. Настройка systemd

```bash
# Создаем сервис для Ollama
cat > /etc/systemd/system/ollama.service << EOF
[Unit]
Description=Ollama AI Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/ollama serve
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Создаем сервис для бэкенда
cat > /etc/systemd/system/wardrobe-backend.service << EOF
[Unit]
Description=Wardrobe Backend
After=network.target ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wardrobe-app
ExecStart=/opt/wardrobe-app/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Включаем и запускаем сервисы
systemctl daemon-reload
systemctl enable ollama wardrobe-backend
systemctl start ollama wardrobe-backend
```

### 6. Настройка Nginx

```bash
# Создаем конфигурацию
cat > /etc/nginx/sites-available/wardrobe-app << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Активируем сайт
ln -sf /etc/nginx/sites-available/wardrobe-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx
```

### 7. Настройка firewall

```bash
# Настраиваем firewall
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 5001
ufw allow 11434
```

## 🐳 Docker развертывание

### 1. Установка Docker

```bash
# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Устанавливаем Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2. Запуск с Docker Compose

```bash
# Копируем файлы
scp -r deploy/* root@server:/opt/wardrobe-app/

# Запускаем
cd /opt/wardrobe-app
docker-compose up -d
```

## 📊 Мониторинг

### 1. Проверка статуса

```bash
# Статус сервисов
systemctl status ollama wardrobe-backend nginx

# Логи
journalctl -u wardrobe-backend -f
journalctl -u ollama -f

# Использование ресурсов
htop
df -h
free -h
```

### 2. Тестирование API

```bash
# Проверка здоровья
curl http://localhost:5001/health

# Тест генерации капсул
curl -X POST http://localhost:5001/generate-capsules \
  -H "Content-Type: application/json" \
  -d '{
    "wardrobe": [
      {"id": 1, "category": "Блузка", "description": "Белая блузка"}
    ],
    "profile": {"name": "Тест", "age": 25}
  }'
```

## 🔒 Безопасность

### 1. Настройка SSL

```bash
# Устанавливаем Certbot
apt install -y certbot python3-certbot-nginx

# Получаем сертификат
certbot --nginx -d your-domain.com

# Автоматическое обновление
crontab -e
# Добавляем: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Настройка пользователя

```bash
# Создаем пользователя
useradd -m -s /bin/bash wardrobe
usermod -aG sudo wardrobe

# Передаем права
chown -R wardrobe:wardrobe /opt/wardrobe-app
```

### 3. Ограничение доступа

```bash
# Настраиваем fail2ban
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

## 🔄 Обновление

### 1. Автоматическое обновление

```bash
# Создаем скрипт обновления
cat > /opt/wardrobe-app/update.sh << 'EOF'
#!/bin/bash
cd /opt/wardrobe-app
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart wardrobe-backend
EOF

chmod +x /opt/wardrobe-app/update.sh
```

### 2. Ручное обновление

```bash
# Останавливаем сервисы
systemctl stop wardrobe-backend

# Обновляем код
cd /opt/wardrobe-app
git pull

# Обновляем зависимости
source venv/bin/activate
pip install -r requirements.txt

# Запускаем сервисы
systemctl start wardrobe-backend
```

## 🛠️ Troubleshooting

### Проблема: Недостаточно памяти

```bash
# Проверяем использование памяти
free -h

# Увеличиваем swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Проблема: Медленная работа ИИ

```bash
# Проверяем использование CPU
htop

# Используем более легкую модель
ollama pull llama2:7b
```

### Проблема: Не запускается Ollama

```bash
# Проверяем логи
journalctl -u ollama -f

# Перезапускаем
systemctl restart ollama

# Проверяем порт
netstat -tlnp | grep 11434
```

## 📈 Масштабирование

### 1. Горизонтальное масштабирование

```bash
# Настраиваем балансировщик нагрузки
apt install -y haproxy

# Конфигурация HAProxy
cat > /etc/haproxy/haproxy.cfg << EOF
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend wardrobe-frontend
    bind *:80
    default_backend wardrobe-backend

backend wardrobe-backend
    balance roundrobin
    server backend1 127.0.0.1:5001 check
    server backend2 127.0.0.1:5002 check
EOF
```

### 2. Вертикальное масштабирование

```bash
# Увеличиваем лимиты системы
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
sysctl -p

# Настраиваем ulimits
echo 'wardrobe soft nofile 65536' >> /etc/security/limits.conf
echo 'wardrobe hard nofile 65536' >> /etc/security/limits.conf
```

## 🔗 Полезные команды

```bash
# Быстрый мониторинг
watch -n 1 'systemctl status ollama wardrobe-backend nginx'

# Просмотр логов в реальном времени
tail -f /var/log/nginx/access.log

# Проверка портов
netstat -tlnp

# Очистка логов
journalctl --vacuum-time=7d
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `journalctl -u wardrobe-backend -f`
2. Проверьте статус сервисов: `systemctl status ollama wardrobe-backend`
3. Проверьте использование ресурсов: `htop`
4. Проверьте сеть: `netstat -tlnp` 