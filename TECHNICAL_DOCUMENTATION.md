# Полная техническая документация `tganketa-copy`

Документ предназначен для инженеров, которые должны воспроизвести функциональность проекта «Гардероб Стилиста» без доступа к исходному коду. Описаны архитектура, зависимости, интерфейсы, структуры данных и алгоритмы.

---

## 1. Обзор системы

- **Назначение:** Сервис для Telegram WebApp, который принимает фотографии вещей, удаляет фон, анализирует предмет гардероба и формирует персональные капсульные подборки с учетом погоды и брендов-партнеров.
- **Компоненты:** React/Vite SPA (frontend), Flask API (backend), Supabase (PostgreSQL + Storage), Redis, OpenAI API, публичный API брендов.
- **Основные сценарии:** загрузка и разметка вещей, AI-анализ, генерация капсул (пользовательские + брендовые товары), отображение гардероба и избранных образов, администрирование через Supabase.

---

## 2. Технологический стек и зависимости

### 2.1 Backend (Python 3.11)

| Библиотека | Назначение | Версия |
| --- | --- | --- |
| Flask | REST API | 3.1.1 |
| flask-cors | CORS заголовки | 4.0.1 |
| numpy | численные операции (совместимость rembg) | 1.26.4 |
| rembg | удаление фона (u2net) | 2.0.67 |
| Pillow, pillow-heif | обработка изображений и HEIC | 11.3.0 / ≥0.16.0 |
| onnxruntime | inference модели rembg | 1.18.0 |
| requests | HTTP клиент | 2.32.4 |
| python-dotenv | загрузка `.env` | 1.0.1 |
| openai | GPT анализ одежды | 1.99.6 |
| anthropic | альтернативный AI (опционально) | 0.62.0 |
| redis | кэширование капсул и метрик | 6.4.0 |
| supabase | вызовы Supabase API | 2.10.0 |
| gunicorn | запуск в продакшне | 21.2.0 |

### 2.2 Frontend (Node.js 20+)

| Пакет | Назначение | Версия |
| --- | --- | --- |
| react, react-dom | UI | ^19.1.0 |
| vite | сборка и dev server | ^7.0.4 |
| @vitejs/plugin-react | интеграция React/Vite | ^4.6.0 |
| axios | HTTP клиент | ^1.10.0 |
| @supabase/supabase-js | Supabase SDK | ^2.75.0 |
| lucide-react | иконки | ^0.536.0 |
| eslint и плагины | линтинг | ^9.30.1 |
| tailwindcss, postcss, autoprefixer | стилизация (частично) | ^3.4.17 / ^8.5.6 / ^10.4.21 |

---

## 3. Архитектура и иерархия модулей

### 3.1 Слои системы

1. **Клиент (React/Vite)**
   - Менеджмент состояния через React hooks.
   - REST обращения к Flask и Supabase.
   - Telegram WebApp оболочка (`telegramWebApp.js`).
2. **Сервисный слой (Flask)**
   - HTTP API.
   - Очистка фона и анализ вещей.
   - Генерация капсул и интеграция с брендами.
   - Кэширование и метрики.
3. **Данные и интеграции**
   - Supabase (PostgreSQL + Storage) — гардероб, избранное, профили.
   - Redis — кэш ответов и метрик.
   - Внешние AI и брендовые сервисы.

### 3.2 Структура репозитория

```
tganketa-copy/
├── backend/
│   ├── app.py                # Flask приложение, маршруты и оркестрация
│   ├── capsule_engine_v6.py  # Основной rule-based движок капсул
│   ├── capsule_engine_enhanced.py
│   ├── brand_service_v5.py   # Смешивание брендов
│   ├── brand_service_v4.py   # Генерация брендовых капсул
│   ├── ai_wardrobe_analyzer.py
│   ├── huggingface_generator.py
│   ├── capsule_generator.py
│   ├── config.py
│   └── requirements.txt
├── src/
│   ├── App.jsx, App.css
│   ├── CapsulePage.jsx, WardrobePage.jsx, ...
│   ├── AddWardrobeItem.jsx, WardrobeItemDetail.jsx
│   ├── backendService.js
│   ├── supabase.js
│   ├── services/brandItemsService.js
│   └── utils/textUtils.js
├── Dockerfile                # фронтенд (nginx)
├── backend/Dockerfile        # backend (gunicorn)
└── TECHNICAL_DOCUMENTATION.md
```

---

## 4. Интеграции и внешние сервисы

| Интеграция | Назначение | Метод доступа |
| --- | --- | --- |
| OpenAI API (Chat Completions) | Анализ изображений и генерация описаний | HTTPS, Bearer token (`OPENAI_API_KEY`) |
| Supabase PostgreSQL | Хранение гардероба, профиля, избранного | `@supabase/supabase-js`, `supabase` Python client |
| Supabase Storage (`wardrobe-images`) | Хранение PNG изображений вещей | Signed public URL, upsert |
| Redis | Кэш капсул и метрик | TCP (`redis://host:port`) |
| Linapolo public API | Получение брендовых товаров | GET `https://linapolo.ru/api/public/items/capsule?season=...` |
| OpenWeather API (или иной) | Получение погоды | HTTP через `WeatherService.js` |

---

## 5. Переменные окружения

| Название | Где используется | Описание / пример |
| --- | --- | --- |
| `OPENAI_API_KEY` | backend | Ключ OpenAI для GPT анализа |
| `ANTHROPIC_API_KEY` | backend (опц.) | Для альтернативных моделей |
| `AI_GENERATOR_TYPE` | backend/config.py | `gpt` \| `ollama` \| `huggingface` \| `semantic` |
| `AI_MODEL_NAME` | backend/config.py | Модель генерации (по умолчанию `phi3:mini` для Ollama, `gpt-4o-mini` для GPT) |
| `AI_TEMPERATURE`, `AI_MAX_TOKENS` | backend/config.py | Параметры генерации |
| `REDIS_URL` | backend/RedisCache | `redis://user:pass@host:6379/0` |
| `CACHE_TTL`, `REDIS_TTL` | backend/config.py | TTL кэша в секундах |
| `HF_MODEL_NAME`, `HF_USE_GPU` | backend/huggingface_generator | Настройки Hugging Face |
| `OLLAMA_HOST`, `OLLAMA_TIMEOUT` | backend/config.py | Локальный Ollama сервер |
| `MAX_WARDROBE_ITEMS`, `MAX_CAPSULES_PER_CATEGORY` | backend/config.py | Ограничения вычислений |
| `VITE_SUPABASE_URL` | frontend `.env` | URL Supabase проекта |
| `VITE_SUPABASE_ANON_KEY` | frontend `.env` | Public anon key Supabase |
| `VITE_OPENWEATHER_KEY` | frontend (опц.) | Ключ погоды |

---

## 6. Backend: API и алгоритмы

### 6.1 REST API

#### `/health` (GET)
- **Назначение:** Проверка доступности сервиса и зависимостей.
- **Ответ 200:**
```json
{
  "status": "ok",
  "redis": true,
  "service": "wardrobe-background-removal"
}
```

#### `/remove-background` (POST)
- **Вход:** multipart/form-data, поле `image` (PNG/JPG/JPEG/WebP).
- **Выход:** PNG файл с удаленным фоном. Используется редко, так как основной поток работает через `/analyze-wardrobe-item`.
- **Ошибки:** 400 (тип файла), 500 (ошибка обработки).

#### `/analyze-wardrobe-item` (POST)
- **Вход:** multipart/form-data  
  - `image` — обязательный файл (≤10 МБ).  
  - Дополнительно можно передать `telegram_id`.
- **Обработка:**
  1. Чтение изображения, трансформация EXIF, приведение к RGB.
  2. Масштабирование до 1024 по длинной стороне.
  3. Удаление фона через `remove_bg` (rembg + u2net).
  4. Вызов `GPTAnalyzer.analyze()` (GPT-4o-mini Vision) → JSON {type, season, description}.  
     Fallback — `RuleBasedAnalyzer`.
  5. Сжатие результата (512x512 JPEG) и кодирование в base64.
- **Ответ 200:**
```json
{
  "success": true,
  "image_base64": "<base64 PNG без фона>",
  "analysis": {
    "category": "водолазка",
    "season": "осень-весна",
    "description": "Водолазка приталенного кроя, белого цвета, с высоким воротом"
  },
  "is_from_cache": false
}
```
- **Ошибки:** 400 (ошибка открытия изображения), 413 (слишком большой файл), 500 (AI недоступен).

#### `/generate-capsules` (POST)
- **Назначение:** Формирование до 20 капсул.
- **Вход JSON:**
```json
{
  "wardrobe": [
    {
      "id": "1",
      "category": "Верх",
      "season": "Осень",
      "description": "Водолазка приталенного кроя, белого цвета",
      "image_id": "uuid",
      "is_suitable": true
    }
  ],
  "profile": {
    "telegram_id": "123",
    "style_preferences": ["casual"]
  },
  "weather": {
    "main": { "temp": 9.19 }
  },
  "no_cache": true,
  "enable_brand_mixing": true,
  "exclude_combinations": [["1", "2", "3", "4"]]
}
```
- **Основные поля ответа:**
```json
{
  "meta": {
    "engine": "rule",
    "insufficient": false,
    "temperature": 9.19,
    "season": "Осень"
  },
  "categories": [
    {
      "id": "casual",
      "name": "Повседневный стиль",
      "fullCapsules": [
        {
          "id": "casual_full_1",
          "name": "Повседневный - Капсула 1",
          "items": [
            {
              "id": "user-uuid",
              "is_brand_item": false,
              "imageUrl": "https://...supabase...png?v=timestamp"
            },
            {
              "id": "brand_c8_item3",
              "is_brand_item": true,
              "image_url": "https://linapolo.ru/images/item.png"
            }
          ],
          "description": "Образ для прохладной осени",
          "reasoning": "Вещи пользователя дополнены брендовыми товарами для завершенности"
        }
      ]
    }
  ]
}
```
- **Поведение:**
  - Запрашиваемая температура определяет фильтрацию тканей и категорий.
  - При `enable_brand_mixing = true` запускается V5/V4 логика.
  - Результат кэшируется в Redis на 24 часа (если не указан `no_cache`).

#### `/ai-feedback` (POST)
- **Назначение:** Сохранение пользовательского фидбэка по AI-анализу.
- **Вход:**
```json
{
  "user_id": "123",
  "item_id": "wardrobe-456",
  "rating": "positive",
  "correction": {
    "category": "свитшот",
    "season": "всесезон"
  }
}
```
- **Выход:** `{ "status": "ok" }`

#### `/ai-performance` (GET)
- Возвращает агрегированные метрики AI (accuracy, timestamps) из Redis.

#### `/ai-explanation` (POST)
- Генерирует текстовое объяснение решения AI (использует сохраненные метаданные).

#### `/wardrobe-recommendations` (POST)
- Дополнительные советы по гардеробу на основе анализа. Формат входа аналогичен `/generate-capsules`.

#### `/looks` (POST)
- Сохранение набора образов (используется LookShelf, структура JSON схожа с `fullCapsules`).

### 6.2 Алгоритмы и сервисы

#### Удаление фона (`remove_bg`)
1. Инициализация u2net модели при первом обращении.
2. Настройка alpha matting (foreground 240, background 10, erode 10).
3. Возврат RGBA изображения; при ошибке возвращается оригинал.

#### AI-анализ (`GPTAnalyzer.analyze`)
1. Формирование системного промпта с правилами (см. `ai_wardrobe_analyzer.py`).
2. Отправка data URL изображения (base64) в Chat Completions (`gpt-4o-mini`).
3. Парсинг ответа JSON; если невалиден — fallback.

#### Rule-based fallback
- `RuleBasedAnalyzer` ищет ключевые слова по категориям, сезонам, стилям и цветам.
- Возвращает `AnalysisResult` с уверенностью 0.6.

#### Генерация капсул (`capsule_engine_v6.generate_capsules`)
1. **Категоризация:**  
   - `tokenize_category` делит описание на токены (первые 6 символов каждого слова ≥3).  
   - `translate_category` сопоставляет токены с группами: `tops`, `bottoms`, `outerwear`, `shoes`, `bags`, `accessories`, `other`. Учтены вариации («свитшо», «водола» и т.д.).
2. **Аксессуары:**  
   - `accessory_subtype` определяет `earrings`, `necklace`, `belt`, `headwear`, `gloves`, `scarf`, `watch`, `sunglasses`.
3. **Анализ тканей:**  
   - `detect_fabric` ищет ключевые слова («лен», «шерсть», «трикотаж»...).  
   - `is_fabric_suitable_for_temp` сопоставляет ткань с температурными зонами (≥26°C, 21-25°, 15-20°, 10-14°, 5-9°, 0-4°, <0°).
4. **Фильтрация по сезону:**  
   - `is_suitable_for_temp_and_season` проверяет `season` («всесезон», «зим», «демисезон», «лето») и категорию (аксессуары, сумки).
5. **Сбор капсул:**  
   - В обязательный набор входят верх+низ (или платье), обувь, сумка, аксессуары.  
   - В холодную погоду добавляется верхняя одежда, головной убор, шарф, перчатки.  
   - Используются очереди `deque` и счетчики для равномерного распределения вещей.
6. **Лимит итераций:** по умолчанию 100. Если не удалось собрать капсул → подключается смесь брендов.

#### Подмешивание брендовых товаров (`brand_service_v5.mix_brand_items_v5`)
1. Проверяет, достаточно ли пользовательских капсул (целевое количество 20).
2. Если <20, вызывает `brand_service_v4.supplement_capsules_with_brand_items`:
   - Загружает бренды через API (фильтр по `season`).
   - Добавляет user wardrobe (после фильтра `is_suitable_for_temp_and_season`), помечает `is_brand_item: false`, нормализует `name`, `image_url`.
   - Сортирует товары по числу использований, приоритет user items.
   - Ограничение: одна вещь не используется более 2 раз в наборе 20 капсул.
3. Если user капсул ≥20 — распределяет бренды по шаблону 7/6/3/3/1.
4. Возвращает обновленные `fullCapsules` с объединенными вещами.

---

## 7. Данные и хранение

### 7.1 Supabase таблицы

#### `wardrobe`

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | UUID (string) | Уникальный идентификатор вещи |
| `telegram_id` | text | Связь с пользователем |
| `category` | text | Категория (в свободной форме) |
| `season` | text | Сезонность (всесезон, осень, зима...) |
| `description` | text | Описание вещи |
| `image_id` | text | Имя файла в Storage |
| `is_suitable` | boolean | Прошла ли модерацию/фильтр |
| `ban_reason` | text | Причина отклонения (если `is_suitable = false`) |
| `created_at` | timestamptz | Автоматическое поле |
| `updated_at` | timestamptz | Автоматическое поле |

Изображения хранятся в Storage `wardrobe-images` по пути `${telegram_id}/${image_id}.png`. Получение URL:
```js
const { data } = supabase.storage
  .from('wardrobe-images')
  .getPublicUrl(`${telegramId}/${imageId}.png`);
return `${data.publicUrl}?v=${Date.now()}`; // bust cache
```

#### `user_profile`

| Поле | Тип | Описание |
| --- | --- | --- |
| `telegram_id` | text | PK/unique |
| `name`, `age`, `figura` | text | Базовые данные |
| `style_preferences` | jsonb | Массив предпочтений |

#### `favorites`

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | bigint | PK |
| `telegram_id` | text | Пользователь |
| `capsule_id` | text | Идентификатор капсулы |
| `capsule_name`, `capsule_description`, `capsule_category` | text | Метаданные |
| `capsule_data` | jsonb | Полный JSON капсулы |
| `created_at` | timestamptz | Дата добавления |

### 7.2 Redis ключи

- `capsules:<sha256>` — кэш запроса `/generate-capsules` (TTL 86400).
- `ai_metrics:<model>:<date>` — агрегированные метрики AI.

---

## 8. Frontend: архитектура и взаимодействие

### 8.1 Основные страницы и компоненты

| Компонент | Назначение |
| --- | --- |
| `App.jsx` | Точка входа, загрузка данных, переключение вкладок, интеграция с Telegram WebApp |
| `CapsulePage.jsx` | Отображение сгенерированных капсул, запуск генерации |
| `WardrobePage.jsx` | Список вещей, фильтры, карточки, открытие деталей |
| `AddWardrobeItem.jsx` | Мастер добавления вещи (загрузка → анализ → редактирование → сохранение) |
| `WardrobeItemDetail.jsx` | Детальная карточка вещи (удалить, изменить статус) |
| `FavoritesPage.jsx` | Список избранных капсул |
| `ProfilePage.jsx` | Анкета пользователя |
| `ShopPage.jsx` | Просмотр брендовых товаров |

### 8.2 Сервисы и утилиты

- `backendService.js`:
  - `generateCapsules(payload)` — POST `/generate-capsules`.
  - `analyzeWardrobeItem(file)` — POST `/analyze-wardrobe-item`.
  - `base64ToBlob`, `aggressiveCompressImage` — обработка изображений перед загрузкой.
- `supabase.js`:
  - `profileService` (`getProfile`, `saveProfile`).
  - `wardrobeService` (`getWardrobe`, `addItem`, `updateItem`, `deleteItem`, `setItemSuitability`, `uploadImage`, `deleteImage`, `getImageUrl`).
  - `favoritesService` (`getFavorites`, `addToFavorites`, `removeFromFavorites`, `isInFavorites`, `getFavoritesStats`).
- `services/brandItemsService.js`:
  - Кэширование и фильтрация брендовых товаров для магазина.
- `utils/textUtils.js`:
  - Нормализация текста (удаление лишних пробелов, приведение к нижнему регистру).

### 8.3 UI/UX особенности

- **Добавление вещи:** Drag&Drop + выбор файла, проверка MIME и размера (≤10 МБ). После анализа отображается превью без фона и заполненная форма.
- **Сетка гардероба:** CSS Grid, карточки 2 колонки на мобильных. Для предотвращения перекрытия нижней навигацией добавлены `wardrobe-spacer`.
- **Изображения:** В `WardrobePage` и других компонентах используется `object-fit: contain`, размеры ограничены `max-width: 80%`.
- **Telegram WebApp:** `telegramWebApp.js` подключает `window.Telegram.WebApp` и регулирует размеры, веб-приложение должно быть доступно по HTTPS.

---

## 9. Построение и деплой

### 9.1 Локальная разработка

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py  # запустит Flask на 0.0.0.0:5001

# Frontend
cd ..
npm install
npm run dev  # Vite (http://localhost:5173)
```

Необходимы запущенные Redis (`redis-server`) и доступ к Supabase (настройка `.env` в корне фронта).

### 9.2 Docker

- **Backend:** `backend/Dockerfile`  
  - Основа: `python:3.11-slim`  
  - Установка `build-essential` для компиляции зависимостей.  
  - Запуск `gunicorn` с воркерами `gthread` (настраиваются переменными).  
  - Порт 5001.

- **Frontend:** `Dockerfile`  
  - Основа: `nginx:alpine`.  
  - Копирует собранный `dist` и `nginx.conf`.  
  - Порт 80.  
  - При деплое убедитесь, что backend доступен фронту (через nginx proxy или CORS).

### 9.3 Продакшн окружение

- Backend и frontend разворачиваются в отдельных контейнерах или на отдельных серверах.
- Redis и Supabase доступны по сети (желательно через VPN/SSL).
- Набор переменных окружения размещается в секретах CI/CD.
- Для Telegram WebApp требуется HTTPS домен и корректный WebApp URL.

---

## 10. Гайд по воспроизведению функционала

1. **Настройте инфраструктуру:**
   - Supabase проект (таблицы `wardrobe`, `user_profile`, `favorites`).
   - Хранилище `wardrobe-images` c public доступом.
   - Redis инстанс.
   - Получите ключи OpenAI и (опционально) OpenWeather.
2. **Подготовьте backend:**
   - Скопируйте структуру `backend/`.
   - Настройте `.env` согласно переменным.
   - Убедитесь, что rembg/u2net доступна (нужны веса, устанавливаются автоматически).
3. **Подготовьте frontend:**
   - Создайте проект на Vite + React.
   - Импортируйте компоненты и сервисы (`App.jsx`, `frontend` структура).
   - Вставьте `telegramWebApp.js` для корректного взаимодействия.
4. **Реализуйте API-вызовы:**  
   - `/analyze-wardrobe-item` для анализа изображений.  
   - `/generate-capsules` для получения капсул.  
   - CRUD через Supabase SDK.
5. **Реализуйте генерацию:**
   - Имплементируйте `capsule_engine_v6` с логикой категорий, тканей, температур.
   - Добавьте `brand_service_v5/v4` для смешивания брендов.
6. **Тестируйте:**
   - Загружайте тестовые вещи (минимум 6 предметов: верх, низ, обувь, сумка, верхняя одежда, аксессуар).
   - Проверяйте ответы `/generate-capsules` при разных температурах.
   - Валидируйте отображение на мобильной версии.

---

## 11. Мониторинг, логирование и безопасность

- **Логирование backend:** стандартные `print` и `logging` (INFO). Рекомендуется интегрировать централизованный сбор (например, Sentry или ELK).
- **Метрики AI:** `/ai-performance` собирает данные точности по фидбэку.
- **Безопасность:**
  - Проверка типа и размера файла на фронте и бэке.
  - Хранение секретов в переменных окружения.
  - HTTPS обязательный.
  - Ограничение использования вещей в капсулах (не более 2 раз).
  - Публичные URL Supabase следует защищать (по возможности использовать Signed URLs).

---

## 12. Дополнительные сведения и рекомендации

- **Тестирование:** интеграционные тесты для `/generate-capsules` можно строить через фиктивные Wardrobe наборы. Для фронта подходят Cypress/Playwright.
- **Расширяемость:**  
  - Можно добавить GraphQL слой для запросов гардероба.  
  - Настроить панель администрирования (Supabase Studio или кастомная).
- **Оптимизации:**  
  - Кэширование погодных данных.  
  - Ограничение количества обращений к OpenAI (использование кэша AI-анализов по хешу изображения).
  - Использование CDN для изображений с Supabase.
- **Варианты деплоя:**  
  - Docker Compose (backend + frontend + redis).  
  - Kubernetes (две службы + stateful Redis).  
  - CI/CD: GitHub Actions с шагами `npm ci && npm run build`, `pip install && pytest (опц.)`, docker publish.

---

Документ описывает все компоненты, зависимости, интерфейсы и алгоритмы проекта «Гардероб Стилиста». При следовании описанным шагам инженер может воспроизвести функциональность системы или перенести её в другое окружение. Use this guide как базовый reference для разработки, аудита или миграции.

