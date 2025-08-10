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

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_wardrobe_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_wardrobe_updated_at 
    BEFORE UPDATE ON wardrobe 
    FOR EACH ROW 
    EXECUTE FUNCTION update_wardrobe_updated_at();

-- Комментарии к таблице
COMMENT ON TABLE wardrobe IS 'Таблица для хранения гардероба пользователей';
COMMENT ON COLUMN wardrobe.telegram_id IS 'Telegram ID пользователя';
COMMENT ON COLUMN wardrobe.category IS 'Категория одежды (платье, брюки, футболка и т.д.)';
COMMENT ON COLUMN wardrobe.season IS 'Сезонность (лето, зима, осень-весна)';
COMMENT ON COLUMN wardrobe.description IS 'Описание вещи';
COMMENT ON COLUMN wardrobe.image_id IS 'UUID изображения в Storage';
COMMENT ON COLUMN wardrobe.ai_generated IS 'Флаг, указывающий что данные сгенерированы AI'; 