# Способы получения Telegram ID

## 1. Telegram Web App API (Рекомендуемый)

### Как это работает:
- Приложение запускается внутри Telegram как Web App
- Telegram автоматически передает данные пользователя
- Самый безопасный и надежный способ

### Реализация:
```javascript
import telegramWebApp from './telegramWebApp';

// Инициализация
telegramWebApp.init();

// Получение Telegram ID
const tgId = telegramWebApp.getTelegramId();

// Получение данных пользователя
const userData = telegramWebApp.getUserData();
```

### Преимущества:
- ✅ Автоматическое получение ID
- ✅ Безопасность (проверка подписи)
- ✅ Дополнительные данные пользователя
- ✅ Интеграция с Telegram UI

### Недостатки:
- ❌ Работает только в Telegram WebView
- ❌ Требует настройки бота

## 2. URL параметры (Текущий способ)

### Как это работает:
- Telegram ID передается через URL параметр `tg_id`
- Пример: `https://linapolo.store?tg_id=714402266`

### Реализация:
```javascript
const urlParams = new URLSearchParams(window.location.search);
const tgId = urlParams.get('tg_id');
```

### Преимущества:
- ✅ Простая реализация
- ✅ Работает в любом браузере
- ✅ Легко тестировать

### Недостатки:
- ❌ Небезопасно (ID виден в URL)
- ❌ Пользователь может изменить ID
- ❌ Требует ручной передачи ID

## 3. LocalStorage (Для тестирования)

### Как это работает:
- Telegram ID сохраняется в localStorage браузера
- Используется для тестирования и разработки

### Реализация:
```javascript
// Сохранение
localStorage.setItem('test_telegram_id', '714402266');

// Получение
const tgId = localStorage.getItem('test_telegram_id');
```

### Преимущества:
- ✅ Удобно для тестирования
- ✅ Не требует URL параметров
- ✅ Сохраняется между сессиями

### Недостатки:
- ❌ Только для разработки
- ❌ Небезопасно для продакшена
- ❌ Привязано к конкретному браузеру

## 4. Telegram Bot API (Серверная проверка)

### Как это работает:
- Frontend получает временный токен от бота
- Backend проверяет токен через Telegram Bot API
- Возвращает валидный Telegram ID

### Реализация:
```javascript
// Frontend
const response = await fetch('/api/telegram/auth', {
  method: 'POST',
  body: JSON.stringify({ initData: telegramWebApp.initData })
});
const { telegramId } = await response.json();

// Backend
const isValid = validateTelegramInitData(initData, botToken);
if (isValid) {
  const telegramId = extractTelegramId(initData);
}
```

### Преимущества:
- ✅ Максимальная безопасность
- ✅ Серверная валидация
- ✅ Защита от подделки

### Недостатки:
- ❌ Сложная реализация
- ❌ Требует backend
- ❌ Дополнительные запросы

## 5. Telegram Login Widget

### Как это работает:
- Использование официального виджета входа
- Пользователь авторизуется через Telegram
- Получение данных через callback

### Реализация:
```html
<script async src="https://telegram.org/js/telegram-widget.js?22" 
        data-telegram-login="YourBotName" 
        data-size="large" 
        data-auth-url="https://linapolo.store/auth"
        data-request-access="write">
</script>
```

### Преимущества:
- ✅ Официальный способ
- ✅ Красивый UI
- ✅ Работает везде

### Недостатки:
- ❌ Требует настройки бота
- ❌ Дополнительный шаг авторизации
- ❌ Не подходит для Web Apps

## Рекомендации

### Для продакшена:
1. **Telegram Web App API** - основной способ
2. **Telegram Bot API** - для дополнительной безопасности
3. **URL параметры** - как fallback

### Для разработки:
1. **LocalStorage** - для быстрого тестирования
2. **URL параметры** - для демонстрации
3. **Debugger компонент** - для отладки

### Приоритет получения ID:
```javascript
// 1. Telegram Web App API
if (telegramWebApp.isAvailable) {
  return telegramWebApp.getTelegramId();
}

// 2. URL параметры
const urlParams = new URLSearchParams(window.location.search);
const tgId = urlParams.get('tg_id');
if (tgId) return tgId;

// 3. LocalStorage (только для разработки)
if (process.env.NODE_ENV === 'development') {
  return localStorage.getItem('test_telegram_id');
}

// 4. Ошибка
throw new Error('Telegram ID не найден');
```

## Настройка Telegram Bot для Web App

1. Создайте бота через @BotFather
2. Установите команду `/setmenubutton`
3. Укажите URL вашего приложения
4. Настройте Web App в боте

```javascript
// Пример настройки бота
{
  "type": "web_app",
  "text": "Открыть гардероб",
  "web_app": {
    "url": "https://linapolo.store"
  }
}
```

## Безопасность

### Валидация initData:
```javascript
import crypto from 'crypto';

function validateInitData(initData, botToken) {
  const secret = crypto.createHmac('sha256', 'WebAppData').update(botToken).digest();
  const hash = crypto.createHmac('sha256', secret).update(initData).digest('hex');
  return hash === expectedHash;
}
```

### Проверка источника:
```javascript
function isTelegramWebView() {
  return navigator.userAgent.includes('TelegramWebApp');
}
``` 