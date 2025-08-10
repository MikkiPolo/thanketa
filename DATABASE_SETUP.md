# Настройка базы данных

## Проблема
Ошибка "invalid input syntax for type uuid" возникает из-за неправильного типа данных в поле `image_id` таблицы `wardrobe`.

## Решение

### 1. Выполните SQL скрипт в Supabase

Откройте Supabase Dashboard → SQL Editor и выполните скрипт из файла `WARDROBE_TABLE_SETUP.sql`:

```sql
-- Создание таблицы для гардероба
CREATE TABLE IF NOT EXISTS wardrobe (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  telegram_id TEXT NOT NULL,
  category TEXT NOT NULL,
  season TEXT,
  description TEXT,
  image_id UUID, -- Правильный тип UUID для изображения
  ai_generated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Создание индексов для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_wardrobe_telegram_id ON wardrobe(telegram_id);
CREATE INDEX IF NOT EXISTS idx_wardrobe_category ON wardrobe(category);
CREATE INDEX IF NOT EXISTS idx_wardrobe_season ON wardrobe(season);
CREATE INDEX IF NOT EXISTS idx_wardrobe_created_at ON wardrobe(created_at);

-- RLS политики для безопасности
ALTER TABLE wardrobe ENABLE ROW LEVEL SECURITY;

-- Политика для чтения: пользователь может видеть только свои вещи
CREATE POLICY "Users can view their own wardrobe" ON wardrobe
FOR SELECT USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для вставки: пользователь может добавлять только свои вещи
CREATE POLICY "Users can insert their own wardrobe" ON wardrobe
FOR INSERT WITH CHECK (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для обновления: пользователь может обновлять только свои вещи
CREATE POLICY "Users can update their own wardrobe" ON wardrobe
FOR UPDATE USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для удаления: пользователь может удалять только свои вещи
CREATE POLICY "Users can delete their own wardrobe" ON wardrobe
FOR DELETE USING (telegram_id = current_setting('app.telegram_id', true)::text);
```

### 2. Если таблица уже существует

Если таблица `wardrobe` уже существует, выполните скрипт из файла `FIX_EXISTING_TABLE.sql`:

```sql
-- Проверяем текущую структуру таблицы
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'wardrobe' 
ORDER BY ordinal_position;

-- Очищаем поле image_id от некорректных данных
UPDATE wardrobe SET image_id = NULL WHERE image_id IS NOT NULL;

-- Изменяем тип поля image_id на UUID
ALTER TABLE wardrobe ALTER COLUMN image_id TYPE UUID USING image_id::UUID;

-- Проверяем результат
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'wardrobe' AND column_name = 'image_id';
```

### 3. Проверка

После выполнения скрипта проверьте структуру таблицы:

```sql
-- Проверка структуры таблицы
\d wardrobe
```

## Исправления в коде

✅ **Исправлено**: В файле `src/AddWardrobeItem.jsx` изменена генерация UUID:

```javascript
// Было:
const imageId = Date.now().toString(36) + Math.random().toString(36).substr(2);

// Стало:
const imageId = crypto.randomUUID();
```

✅ **Исправлено**: В файле `src/config.js` обновлен URL backend для локальной разработки:

```javascript
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001';
```

## Тестирование

1. Убедитесь, что backend запущен: `http://localhost:5001/health`
2. Убедитесь, что frontend запущен: `http://localhost:5173`
3. Попробуйте добавить вещь в гардероб

Теперь ошибка UUID должна быть исправлена! 