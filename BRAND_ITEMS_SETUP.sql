-- ================================================================================
-- НАСТРОЙКА BRAND ITEMS ДЛЯ ИНТЕГРАЦИИ В МОБИЛЬНОЕ ПРИЛОЖЕНИЕ
-- ================================================================================
-- Версия: 2.0
-- Дата: 2025-10-11
-- 
-- Выполните этот SQL в Supabase SQL Editor:
-- https://lipolo.store (или ваш Supabase Dashboard)
-- ================================================================================

-- ============================================================================
-- 1. ВКЛЮЧЕНИЕ ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Включить RLS на таблице brand_items
ALTER TABLE brand_items ENABLE ROW LEVEL SECURITY;

-- Включить RLS на таблице brands (если есть)
-- ALTER TABLE brands ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 2. ПОЛИТИКИ RLS ДЛЯ ПУБЛИЧНОГО ДОСТУПА
-- ============================================================================

-- Удалить старые политики если есть
DROP POLICY IF EXISTS "Public can read approved active items" ON brand_items;
DROP POLICY IF EXISTS "Public can read brand info" ON brands;

-- Создать политику для публичного чтения одобренных активных товаров
CREATE POLICY "Public can read approved active items"
ON brand_items
FOR SELECT
TO anon, authenticated
USING (is_approved = true AND is_active = true);

-- Создать политику для чтения информации о брендах (если таблица есть)
-- CREATE POLICY "Public can read brand info"
-- ON brands
-- FOR SELECT
-- TO anon, authenticated
-- USING (is_active = true);

-- Проверка созданных политик
SELECT schemaname, tablename, policyname, roles, cmd 
FROM pg_policies 
WHERE tablename IN ('brand_items', 'brands')
ORDER BY tablename, policyname;

-- ============================================================================
-- 3. SQL ФУНКЦИИ ДЛЯ ИНКРЕМЕНТА СЧЕТЧИКОВ
-- ============================================================================

-- Удалить старые функции если есть
DROP FUNCTION IF EXISTS increment_impressions(UUID);
DROP FUNCTION IF EXISTS increment_clicks(UUID);

-- Функция для увеличения счетчика показов (impressions)
CREATE OR REPLACE FUNCTION increment_impressions(item_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  new_count INTEGER;
BEGIN
  -- Увеличиваем счетчик только для одобренных активных товаров
  UPDATE brand_items 
  SET impressions_count = impressions_count + 1,
      updated_at = NOW()
  WHERE id = item_uuid 
    AND is_approved = true 
    AND is_active = true
  RETURNING impressions_count INTO new_count;
  
  -- Если товар не найден или не доступен - ошибка
  IF new_count IS NULL THEN
    RAISE EXCEPTION 'Item % not found or not available', item_uuid;
  END IF;
  
  RETURN new_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Функция для увеличения счетчика кликов (clicks)
CREATE OR REPLACE FUNCTION increment_clicks(item_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  new_count INTEGER;
BEGIN
  -- Увеличиваем счетчик только для одобренных активных товаров
  UPDATE brand_items 
  SET clicks_count = clicks_count + 1,
      updated_at = NOW()
  WHERE id = item_uuid 
    AND is_approved = true 
    AND is_active = true
  RETURNING clicks_count INTO new_count;
  
  -- Если товар не найден или не доступен - ошибка
  IF new_count IS NULL THEN
    RAISE EXCEPTION 'Item % not found or not available', item_uuid;
  END IF;
  
  RETURN new_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Дать доступ к функциям для анонимных и авторизованных пользователей
GRANT EXECUTE ON FUNCTION increment_impressions(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION increment_clicks(UUID) TO anon, authenticated;

-- ============================================================================
-- 4. СОЗДАНИЕ VIEW ДЛЯ СТАТИСТИКИ (CTR - Click Through Rate)
-- ============================================================================

-- Удалить старый view если есть
DROP VIEW IF EXISTS brand_items_stats;

-- Создать view для расчета CTR
CREATE VIEW brand_items_stats AS
SELECT 
  bi.id,
  bi.brand_id,
  bi.category,
  bi.season,
  bi.description,
  bi.impressions_count,
  bi.clicks_count,
  -- Рассчитываем CTR (Click Through Rate)
  CASE 
    WHEN bi.impressions_count > 0 THEN 
      ROUND((bi.clicks_count::DECIMAL / bi.impressions_count::DECIMAL * 100), 2)
    ELSE 
      0
  END AS ctr_percentage,
  bi.created_at,
  bi.updated_at
FROM brand_items bi
WHERE bi.is_approved = true 
  AND bi.is_active = true
ORDER BY bi.impressions_count DESC, bi.created_at DESC;

-- Дать доступ к view
GRANT SELECT ON brand_items_stats TO anon, authenticated;

-- ============================================================================
-- 5. ТЕСТОВЫЕ ЗАПРОСЫ ДЛЯ ПРОВЕРКИ
-- ============================================================================

-- 5.1. Проверить что политики работают (от имени анонимного пользователя)
-- Этот запрос должен вернуть только одобренные активные товары
SET ROLE anon;
SELECT COUNT(*) AS approved_items_count 
FROM brand_items 
WHERE is_approved = true AND is_active = true;
RESET ROLE;

-- 5.2. Проверить функции инкремента
-- ВАЖНО: Замените 'your-item-uuid-here' на реальный UUID товара из вашей таблицы!
-- 
-- Сначала получим реальный UUID:
SELECT id, description FROM brand_items WHERE is_approved = true LIMIT 1;
-- 
-- Потом тестируем (замените UUID):
-- SELECT increment_impressions('your-item-uuid-here'::UUID);
-- SELECT increment_clicks('your-item-uuid-here'::UUID);

-- 5.3. Проверить view статистики
SELECT * FROM brand_items_stats LIMIT 5;

-- 5.4. Проверить какие товары есть по категориям и сезонам
SELECT 
  category,
  season,
  COUNT(*) as items_count
FROM brand_items
WHERE is_approved = true AND is_active = true
GROUP BY category, season
ORDER BY category, season;

-- ============================================================================
-- 6. ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- ============================================================================

-- Создать индексы для быстрого поиска товаров
CREATE INDEX IF NOT EXISTS idx_brand_items_category_season 
ON brand_items(category, season) 
WHERE is_approved = true AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_brand_items_impressions 
ON brand_items(impressions_count) 
WHERE is_approved = true AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_brand_items_brand_id 
ON brand_items(brand_id) 
WHERE is_approved = true AND is_active = true;

-- ============================================================================
-- ГОТОВО! ✅
-- ============================================================================

-- Проверьте что все создано успешно:
\d brand_items  -- Структура таблицы и индексы
\df increment_* -- Функции
SELECT * FROM pg_policies WHERE tablename = 'brand_items';  -- Политики

-- Примечание:
-- После выполнения этого SQL, мобильное приложение сможет:
-- 1. Читать одобренные товары брендов (через Supabase SDK)
-- 2. Записывать impressions/clicks (через Flask API который вызывает эти функции)
-- 3. Быстро загружать товары с балансировкой показов

