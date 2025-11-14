# Руководство по развертыванию на новом сервере

## 📋 Требования к серверу

- **CPU**: 6 ядер
- **RAM**: 12 GB
- **Диск**: 70 GB NVMe SSD
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Docker**: установлен и запущен
- **Docker Compose**: установлен

---

## 🚀 Быстрое развертывание

### 1. Подключение к серверу

```bash
ssh root@your-server-ip
# или
ssh user@your-server-ip
```

### 2. Установка Docker и Docker Compose (если не установлены)

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt install docker-compose -y
# или для новой версии
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

### 3. Клонирование репозитория

```bash
# Переход в рабочую директорию
cd /opt
# или
cd /home/user

# Клонирование репозитория
git clone <your-repository-url> tganketa-copy
cd tganketa-copy

# Переход на нужную ветку (если не main)
git checkout main
```

### 4. Настройка переменных окружения

```bash
# Создание .env файла для backend
cd backend
cp env.example .env
nano .env  # или vi .env
```

**Обязательные переменные:**
```env
# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Redis (если используется внешний)
REDIS_URL=redis://localhost:6379

# Gunicorn (опционально, уже настроено в docker-compose)
GUNICORN_WORKERS=4
GUNICORN_THREADS=6
CACHE_TTL=86400
```

### 5. Запуск приложения

```bash
# Возврат в корневую директорию
cd ..

# Запуск всех сервисов
docker-compose -f docker-compose.full.yml up -d

# Проверка статуса
docker-compose -f docker-compose.full.yml ps

# Просмотр логов
docker-compose -f docker-compose.full.yml logs -f backend
```

### 6. Проверка работоспособности

```bash
# Проверка health endpoint
curl http://localhost:5001/health

# Проверка портов
netstat -tlnp | grep -E "5001|80|443|6379"
```

---

## 🔧 Настройка Nginx (если нужен внешний доступ)

### 1. Установка Nginx

```bash
apt install nginx -y
```

### 2. Создание конфигурации

```bash
nano /etc/nginx/sites-available/wardrobe
```

**Конфигурация:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
```

### 3. Активация конфигурации

```bash
ln -s /etc/nginx/sites-available/wardrobe /etc/nginx/sites-enabled/
nginx -t  # Проверка конфигурации
systemctl reload nginx
```

---

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Все сервисы
docker-compose -f docker-compose.full.yml logs -f

# Только backend
docker-compose -f docker-compose.full.yml logs -f backend

# Последние 100 строк
docker-compose -f docker-compose.full.yml logs --tail=100 backend
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование ресурсов системой
htop
# или
top

# Использование диска
df -h

# Использование памяти
free -h
```

### Проверка производительности

```bash
# Количество активных соединений
netstat -an | grep :5001 | wc -l

# CPU и память backend контейнера
docker stats wardrobe-backend --no-stream
```

---

## 🔄 Обновление приложения

### 1. Остановка сервисов

```bash
cd /opt/tganketa-copy  # или путь к проекту
docker-compose -f docker-compose.full.yml down
```

### 2. Обновление кода

```bash
git pull origin main
```

### 3. Пересборка и запуск

```bash
# Пересборка образов (если нужно)
docker-compose -f docker-compose.full.yml build

# Запуск с новой конфигурацией
docker-compose -f docker-compose.full.yml up -d

# Проверка статуса
docker-compose -f docker-compose.full.yml ps
```

---

## 🛠️ Устранение неполадок

### Проблема: Контейнер не запускается

```bash
# Проверка логов
docker-compose -f docker-compose.full.yml logs backend

# Проверка конфигурации
docker-compose -f docker-compose.full.yml config

# Пересоздание контейнера
docker-compose -f docker-compose.full.yml up -d --force-recreate backend
```

### Проблема: Недостаточно памяти

```bash
# Проверка использования памяти
free -h
docker stats

# Если нужно, уменьшите workers
# В docker-compose.full.yml измените GUNICORN_WORKERS=3 или 2
```

### Проблема: Порт занят

```bash
# Проверка занятых портов
lsof -i :5001
netstat -tlnp | grep 5001

# Остановка процесса
kill -9 <PID>
```

### Проблема: Redis не подключается

```bash
# Проверка Redis
docker-compose -f docker-compose.full.yml logs redis
docker-compose -f docker-compose.full.yml exec redis redis-cli ping

# Перезапуск Redis
docker-compose -f docker-compose.full.yml restart redis
```

---

## 🔒 Безопасность

### 1. Firewall

```bash
# Установка UFW
apt install ufw -y

# Разрешение портов
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS

# Включение firewall
ufw enable
```

### 2. SSL сертификат (Let's Encrypt)

```bash
# Установка Certbot
apt install certbot python3-certbot-nginx -y

# Получение сертификата
certbot --nginx -d your-domain.com

# Автоматическое обновление
certbot renew --dry-run
```

---

## 📈 Оптимизация производительности

### 1. Настройка Redis

```bash
# Ограничение памяти Redis
docker-compose -f docker-compose.full.yml exec redis redis-cli CONFIG SET maxmemory 1gb
docker-compose -f docker-compose.full.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 2. Очистка логов

```bash
# Очистка старых логов Docker
docker system prune -a --volumes

# Ротация логов
# Настройте logrotate для /var/lib/docker/containers/
```

### 3. Мониторинг производительности

```bash
# Установка Prometheus и Grafana (опционально)
# Уже включено в docker-compose.full.yml
# Доступ: http://your-server:3001
```

---

## ✅ Чек-лист развертывания

- [ ] Docker и Docker Compose установлены
- [ ] Репозиторий склонирован
- [ ] Переменные окружения настроены (.env файл)
- [ ] Контейнеры запущены (`docker-compose up -d`)
- [ ] Health endpoint отвечает (`curl http://localhost:5001/health`)
- [ ] Redis подключен и работает
- [ ] Nginx настроен (если нужен внешний доступ)
- [ ] Firewall настроен
- [ ] SSL сертификат установлен (для продакшена)
- [ ] Мониторинг настроен
- [ ] Бэкапы настроены

---

## 📞 Полезные команды

```bash
# Перезапуск всех сервисов
docker-compose -f docker-compose.full.yml restart

# Остановка всех сервисов
docker-compose -f docker-compose.full.yml stop

# Удаление всех контейнеров и volumes (ОСТОРОЖНО!)
docker-compose -f docker-compose.full.yml down -v

# Просмотр использования ресурсов
docker stats

# Вход в контейнер backend
docker-compose -f docker-compose.full.yml exec backend bash

# Проверка логов в реальном времени
docker-compose -f docker-compose.full.yml logs -f --tail=50
```

---

## 🎯 Текущая конфигурация

После развертывания у вас будет:
- **Gunicorn Workers**: 4
- **Gunicorn Threads**: 6
- **Одновременных запросов**: 24
- **Пропускная способность**: ~40-60 пользователей
- **TTL кэша**: 24 часа

Удачи с развертыванием! 🚀

