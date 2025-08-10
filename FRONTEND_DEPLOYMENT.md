# 🚀 Деплой Frontend на VPS

## 📋 Что уже настроено

✅ **Backend развернут на VPS**  
✅ **Nginx настроен для проксирования**  
✅ **Frontend конфигурация обновлена**  
✅ **Docker файлы созданы**  
✅ **Компонент мониторинга подключения добавлен**

## 🔧 Шаги для деплоя

### 1. Подготовка локально

```bash
# Установка зависимостей
npm install

# Создание .env.local файла
echo "VITE_BACKEND_URL=http://your-vps-domain.com" > .env.local

# Сборка проекта
npm run build
```

### 2. Деплой на VPS

#### Вариант A: Через Docker (рекомендуется)

```bash
# На VPS сервере
cd /path/to/your/project

# Сборка и запуск frontend
docker build -t wardrobe-frontend .
docker run -d -p 3000:80 --name wardrobe-frontend wardrobe-frontend

# Или используя docker-compose
docker-compose -f docker-compose.full.yml up -d frontend
```

#### Вариант B: Статические файлы

```bash
# Скопировать папку dist на VPS
scp -r dist/ user@your-vps:/var/www/wardrobe/

# Настроить nginx для раздачи статических файлов
sudo nano /etc/nginx/sites-available/wardrobe

# Активировать конфигурацию
sudo ln -s /etc/nginx/sites-available/wardrobe /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Настройка домена

В файле `src/config.js` замените `your-vps-domain.com` на реальный домен:

```javascript
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://your-real-domain.com';
```

### 4. Проверка работоспособности

1. Откройте приложение в браузере
2. Проверьте индикатор статуса backend в правом нижнем углу
3. Попробуйте загрузить изображение
4. Проверьте консоль браузера на ошибки

## 🔍 Отладка

### Проверка подключения к backend

```javascript
// В консоли браузера
import { backendService } from './src/backendService.js';
backendService.healthCheck().then(console.log).catch(console.error);
```

### Логи nginx

```bash
# На VPS
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Логи Docker контейнеров

```bash
docker logs wardrobe-frontend
docker logs wardrobe-backend
```

## 🐳 Docker Compose (полный стек)

Для запуска всего приложения:

```bash
# Остановить старые контейнеры
docker-compose -f deploy/docker-compose.yml down

# Запустить полный стек
docker-compose -f docker-compose.full.yml up -d

# Проверить статус
docker-compose -f docker-compose.full.yml ps
```

## 📁 Структура файлов

```
tganketa-copy/
├── src/
│   ├── config.js              # Конфигурация API
│   ├── backendService.js      # Сервис для работы с backend
│   └── BackendStatus.jsx      # Компонент мониторинга
├── Dockerfile                 # Docker для frontend
├── nginx.conf                 # Конфигурация nginx
├── docker-compose.full.yml    # Полный стек
└── deploy/
    └── deploy_frontend.sh     # Скрипт деплоя
```

## ✅ Готово!

После выполнения всех шагов у вас будет:
- Frontend на порту 3000 (или 80 через nginx)
- Backend на порту 5001
- Автоматическая проверка подключения
- Проксирование API запросов через nginx 