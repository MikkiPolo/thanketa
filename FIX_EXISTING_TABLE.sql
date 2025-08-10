-- Исправление существующей таблицы wardrobe
-- Изменяем тип поля image_id на UUID

-- Проверяем текущую структуру таблицы
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'wardrobe' 
ORDER BY ordinal_position;

-- Изменяем тип поля image_id на UUID
-- Если поле содержит данные, которые нельзя конвертировать, сначала очистим их
UPDATE wardrobe SET image_id = NULL WHERE image_id IS NOT NULL;

-- Теперь изменяем тип
ALTER TABLE wardrobe ALTER COLUMN image_id TYPE UUID USING image_id::UUID;

-- Проверяем результат
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'wardrobe' AND column_name = 'image_id'; 