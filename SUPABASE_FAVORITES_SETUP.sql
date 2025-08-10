-- Создание таблицы для избранных капсул
CREATE TABLE IF NOT EXISTS favorites (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  telegram_id TEXT NOT NULL,
  capsule_id TEXT NOT NULL,
  capsule_name TEXT NOT NULL,
  capsule_description TEXT,
  capsule_category TEXT,
  capsule_data JSONB NOT NULL, -- Полные данные капсулы
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Уникальный индекс для предотвращения дублирования
  UNIQUE(telegram_id, capsule_id)
);

-- Создание индексов для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_favorites_telegram_id ON favorites(telegram_id);
CREATE INDEX IF NOT EXISTS idx_favorites_category ON favorites(capsule_category);
CREATE INDEX IF NOT EXISTS idx_favorites_created_at ON favorites(created_at);

-- RLS политики для безопасности
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;

-- Политика для чтения: пользователь может видеть только свои избранные
CREATE POLICY "Users can view their own favorites" ON favorites
FOR SELECT USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для вставки: пользователь может добавлять только свои избранные
CREATE POLICY "Users can insert their own favorites" ON favorites
FOR INSERT WITH CHECK (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для обновления: пользователь может обновлять только свои избранные
CREATE POLICY "Users can update their own favorites" ON favorites
FOR UPDATE USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Политика для удаления: пользователь может удалять только свои избранные
CREATE POLICY "Users can delete their own favorites" ON favorites
FOR DELETE USING (telegram_id = current_setting('app.telegram_id', true)::text);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_favorites_updated_at 
    BEFORE UPDATE ON favorites 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Комментарии к таблице
COMMENT ON TABLE favorites IS 'Таблица для хранения избранных капсул пользователей';
COMMENT ON COLUMN favorites.telegram_id IS 'Telegram ID пользователя';
COMMENT ON COLUMN favorites.capsule_id IS 'Уникальный ID капсулы';
COMMENT ON COLUMN favorites.capsule_data IS 'JSON с полными данными капсулы (предметы, описания и т.д.)';
COMMENT ON COLUMN favorites.capsule_category IS 'Категория капсулы (casual, business, evening и т.д.)'; 