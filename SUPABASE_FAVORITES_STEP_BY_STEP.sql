-- Шаг 1: Создание таблицы favorites
CREATE TABLE IF NOT EXISTS favorites (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  telegram_id TEXT NOT NULL,
  capsule_id TEXT NOT NULL,
  capsule_name TEXT NOT NULL,
  capsule_description TEXT,
  capsule_category TEXT,
  capsule_data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Шаг 2: Добавление уникального ограничения
ALTER TABLE favorites 
ADD CONSTRAINT favorites_telegram_capsule_unique 
UNIQUE(telegram_id, capsule_id);

-- Шаг 3: Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_favorites_telegram_id ON favorites(telegram_id);
CREATE INDEX IF NOT EXISTS idx_favorites_category ON favorites(capsule_category);
CREATE INDEX IF NOT EXISTS idx_favorites_created_at ON favorites(created_at);

-- Шаг 4: Включение Row Level Security (RLS)
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;

-- Шаг 5: Создание политик безопасности
-- Политика для чтения
CREATE POLICY "Users can view their own favorites" ON favorites
FOR SELECT USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для добавления
CREATE POLICY "Users can insert their own favorites" ON favorites
FOR INSERT WITH CHECK (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для обновления
CREATE POLICY "Users can update their own favorites" ON favorites
FOR UPDATE USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для удаления
CREATE POLICY "Users can delete their own favorites" ON favorites
FOR DELETE USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Шаг 6: Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Шаг 7: Создание триггера
CREATE TRIGGER update_favorites_updated_at 
    BEFORE UPDATE ON favorites 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Шаг 8: Добавление комментариев
COMMENT ON TABLE favorites IS 'Таблица для хранения избранных капсул пользователей';
COMMENT ON COLUMN favorites.telegram_id IS 'Telegram ID пользователя';
COMMENT ON COLUMN favorites.capsule_id IS 'Уникальный ID капсулы';
COMMENT ON COLUMN favorites.capsule_data IS 'JSON с полными данными капсулы';

-- Шаг 9: Проверка создания таблицы
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'favorites'
ORDER BY ordinal_position; 