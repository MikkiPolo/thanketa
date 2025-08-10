# Инструкции по настройке проекта

## Переменные окружения

Создайте файл `.env` в корне проекта на основе `env.example`:

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Backend Configuration
VITE_BACKEND_URL=https://your-backend-domain.com

# Telegram Bot Configuration
VITE_TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Weather API Configuration
VITE_OPENWEATHER_API_KEY=your-openweather-api-key

# N8N Configuration (optional)
VITE_N8N_FETCH_URL=https://your-n8n-domain.com/webhook/anketa
VITE_N8N_SAVE_URL=https://your-n8n-domain.com/webhook-test/anketa_save
```

## Установка зависимостей

```bash
# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

## Запуск в режиме разработки

```bash
# Frontend
npm run dev

# Backend
cd backend
python app.py
```

## Сборка для продакшена

```bash
npm run build
```

## Безопасность

1. **Никогда не коммитьте `.env` файл в репозиторий**
2. **Используйте HTTPS в продакшене**
3. **Настройте CORS на backend для ваших доменов**
4. **Валидируйте данные Telegram Web App в продакшене**

## Оптимизации

- Используется code splitting для уменьшения размера бандла
- Добавлена retry логика для сетевых запросов
- Оптимизированы React компоненты с useCallback и useMemo
- Улучшена мобильная адаптация

## Структура проекта

```
src/
├── utils/           # Утилиты (textUtils.js)
├── components/      # React компоненты
├── services/        # API сервисы
└── assets/          # Статические ресурсы
``` 