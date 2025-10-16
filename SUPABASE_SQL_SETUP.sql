-- ================================================================================
-- НАСТРОЙКА BRAND ITEMS ДЛЯ ГИБРИДНОЙ ИНТЕГРАЦИИ
-- ================================================================================
-- ИНСТРУКЦИЯ:
-- 1. Откройте Supabase Dashboard: https://lipolo.store
-- 2. Перейдите в SQL Editor (боковое меню слева)
-- 3. Скопируйте весь этот код
-- 4. Вставьте в SQL Editor
-- 5. Нажмите "RUN" (или Ctrl+Enter)
-- ================================================================================

-- ============================================================================
-- ШАГ 1: ВКЛЮЧИТЬ ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE brand_items ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ШАГ 2: СОЗДАТЬ ПОЛИТИКУ ДЛЯ ПУБЛИЧНОГО ЧТЕНИЯ
-- ============================================================================

-- Удалить старую политику если есть
DROP POLICY IF EXISTS "Public can read approved active items" ON brand_items;

-- Создать новую политику
CREATE POLICY "Public can read approved active items"
ON brand_items
FOR SELECT
TO anon, authenticated
USING (is_approved = true AND is_active = true);

-- ============================================================================
-- ШАГ 3: СОЗДАТЬ SQL ФУНКЦИИ ДЛЯ ИНКРЕМЕНТА СЧЕТЧИКОВ
-- ============================================================================

-- Удалить старые функции
DROP FUNCTION IF EXISTS increment_impressions(UUID);
DROP FUNCTION IF EXISTS increment_clicks(UUID);

-- Функция для увеличения impressions_count
CREATE OR REPLACE FUNCTION increment_impressions(item_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  new_count INTEGER;
BEGIN
  UPDATE brand_items 
  SET impressions_count = impressions_count + 1,
      updated_at = NOW()
  WHERE id = item_uuid 
    AND is_approved = true 
    AND is_active = true
  RETURNING impressions_count INTO new_count;
  
  IF new_count IS NULL THEN
    RAISE EXCEPTION 'Item % not found or not available', item_uuid;
  END IF;
  
  RETURN new_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Функция для увеличения clicks_count
CREATE OR REPLACE FUNCTION increment_clicks(item_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  new_count INTEGER;
BEGIN
  UPDATE brand_items 
  SET clicks_count = clicks_count + 1,
      updated_at = NOW()
  WHERE id = item_uuid 
    AND is_approved = true 
    AND is_active = true
  RETURNING clicks_count INTO new_count;
  
  IF new_count IS NULL THEN
    RAISE EXCEPTION 'Item % not found or not available', item_uuid;
  END IF;
  
  RETURN new_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Дать доступ к функциям
GRANT EXECUTE ON FUNCTION increment_impressions(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION increment_clicks(UUID) TO anon, authenticated;

-- ============================================================================
-- ШАГ 4: СОЗДАТЬ VIEW ДЛЯ СТАТИСТИКИ
-- ============================================================================

DROP VIEW IF EXISTS brand_items_stats;

CREATE VIEW brand_items_stats AS
SELECT 
  bi.id,
  bi.brand_id,
  bi.category,
  bi.season,
  bi.description,
  bi.impressions_count,
  bi.clicks_count,
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

GRANT SELECT ON brand_items_stats TO anon, authenticated;

-- ============================================================================
-- ШАГ 5: СОЗДАТЬ ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- ============================================================================

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
-- ШАГ 6: ПРОВЕРКА ЧТО ВСЕ СОЗДАНО УСПЕШНО
-- ============================================================================

-- Проверить политики
SELECT 
  tablename, 
  policyname, 
  roles::text, 
  cmd
FROM pg_policies 
WHERE tablename = 'brand_items';

-- Проверить функции
SELECT 
  proname as function_name,
  pg_get_function_arguments(oid) as arguments
FROM pg_proc 
WHERE proname IN ('increment_impressions', 'increment_clicks');

-- Проверить view
SELECT COUNT(*) as total_items FROM brand_items_stats;

-- Проверить индексы
SELECT 
  indexname, 
  indexdef 
FROM pg_indexes 
WHERE tablename = 'brand_items' 
  AND indexname LIKE 'idx_brand_items%';

-- Проверить что товары доступны
SELECT 
  category,
  season,
  COUNT(*) as items_count
FROM brand_items
WHERE is_approved = true AND is_active = true
GROUP BY category, season
ORDER BY category, season;

-- ============================================================================
-- ГОТОВО! ✅
-- ============================================================================
-- После выполнения этого SQL:
-- 1. Проверьте что все запросы выше вернули результаты без ошибок
-- 2. Вернитесь к приложению и протестируйте генерацию капсул
-- 3. Товары брендов должны автоматически подмешиваться в капсулы
-- ============================================================================

