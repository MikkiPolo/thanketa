# Настройка Frontend для работы с удаленным Backend

## 1. Настройка переменных окружения

Создайте файл `.env.local` в корне проекта:

```bash
# Для разработки (локальный backend)
VITE_BACKEND_URL=http://localhost:5001

# Для продакшена (VPS backend)
# VITE_BACKEND_URL=http://your-vps-domain.com
```

## 2. Замена домена

В файле `src/config.js` замените `your-vps-domain.com` на реальный домен вашего VPS сервера.

## 3. Проверка подключения

После настройки можно проверить подключение к backend:

```javascript
import { backendService } from './src/backendService.js';

// Проверка здоровья сервера
try {
  const health = await backendService.healthCheck();
  console.log('Backend is healthy:', health);
} catch (error) {
  console.error('Backend connection failed:', error);
}
```

## 4. Запуск в режиме разработки

```bash
npm run dev
```

## 5. Сборка для продакшена

```bash
npm run build
```

## 6. Деплой frontend

### Вариант 1: Статические файлы через nginx

1. Соберите проект: `npm run build`
2. Скопируйте содержимое папки `dist` на VPS
3. Настройте nginx для раздачи статических файлов

### Вариант 2: Docker контейнер

Создайте Dockerfile для frontend:

```dockerfile
FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 7. CORS настройки

Backend уже настроен для работы с CORS. Если возникают проблемы, проверьте:

1. Правильность URL в конфигурации
2. Настройки nginx на VPS
3. CORS заголовки в backend

## 8. Проверка работоспособности

1. Откройте приложение в браузере
2. Попробуйте загрузить изображение
3. Проверьте консоль браузера на ошибки
4. Проверьте Network tab для API запросов 