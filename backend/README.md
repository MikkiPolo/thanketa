# Wardrobe Backend API

Backend сервер для удаления фона изображений и анализа гардероба с помощью AI.

## 🚀 Быстрый запуск

### С Docker Compose:
```bash
docker-compose up --build
```

### С Docker:
```bash
docker build -t wardrobe-backend .
docker run -p 5000:5000 wardrobe-backend
```

### Локально:
```bash
pip install -r requirements.txt
python app.py
```

## 📡 API Endpoints

### Health Check
```
GET /health
```

### Удаление фона
```
POST /remove-background
Content-Type: multipart/form-data
Body: image (file)
```

### Анализ гардероба
```
POST /analyze-wardrobe-item
Content-Type: multipart/form-data
Body: image (file)
```

## 🔧 Настройка

1. Создайте `.env` файл на основе `.env.example`
2. Добавьте API ключи:
   - `OPENAI_API_KEY` - для ChatGPT Vision
   - `SUPABASE_SERVICE_KEY` - для работы с Supabase

## 🐳 Docker

### Сборка образа:
```bash
docker build -t wardrobe-backend .
```

### Запуск контейнера:
```bash
docker run -p 5000:5000 wardrobe-backend
```

## 📝 Логи

Логи сохраняются в `./logs/` директории при использовании Docker Compose.

## 🔒 Безопасность

- CORS настроен для React приложения
- Валидация типов файлов
- Обработка ошибок
- Health checks 