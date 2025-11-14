/**
 * Сервис для работы с товарами брендов
 * 
 * Гибридный подход:
 * - Чтение товаров: Supabase напрямую (быстро ~150ms)
 * - Запись метрик: Flask API (асинхронно)
 */

import { supabase, API_BASE_URL, STORAGE_URL } from '../config/supabaseConfig';

class BrandItemsService {
  
  /**
   * Получить товары бренда для определенной категории
   * 
   * @param {string} category - Категория товара (Верх, Низ, Обувь, Сумка, Аксессуары)
   * @param {string} season - Сезон (Лето, Зима, Весна, Осень, Демисезон, Всесезонный)
   * @param {number} limit - Количество товаров
   * @returns {Promise<Array>} Массив товаров
   */
  async getItemsForCategory(category, season, limit = 5) {
    try {
      // Запрос к Supabase с балансировкой показов
      const { data, error } = await supabase
        .from('brand_items')
        .select('id, brand_id, category, season, description, image_id, shop_link, price, currency, impressions_count, clicks_count')
        .eq('is_approved', true)
        .eq('is_active', true)
        .eq('category', category)
        .or(`season.eq.${season},season.eq.Всесезонный`)  // Точный сезон ИЛИ всесезонный
        .order('impressions_count', { ascending: true })  // Балансировка: сначала с меньшими показами
        .limit(limit * 2);  // Берем больше для разнообразия
      
      if (error) {
        console.error('Ошибка загрузки товаров брендов:', error);
        return [];
      }
      
      if (!data || data.length === 0) {
        return [];
      }
      
      // Обогащаем данные: добавляем URL изображения и название бренда
      const enrichedItems = data.map(item => ({
        ...item,
        image_url: this._getImageUrl(item.brand_id, item.image_id),
        brand_name: 'LiMango', // Пока захардкожено, можно улучшить с JOIN к brands
        is_brand_item: true
      }));
      
      // Обеспечить разнообразие брендов (макс 1-2 товара от бренда)
      const result = this._ensureBrandDiversity(enrichedItems, limit);
      
      return result;
      
    } catch (error) {
      console.error('Ошибка в getItemsForCategory:', error);
      return [];
    }
  }
  
  /**
   * Получить товары для добавления в капсулу
   * 
   * @param {Object} capsuleParams - Параметры капсулы (season, temperature)
   * @param {Array} userWardrobe - Гардероб пользователя
   * @param {number} itemsPerCategory - Количество товаров на категорию
   * @returns {Promise<Array>} Массив товаров брендов для всех недостающих категорий
   */
  async getItemsForCapsule(capsuleParams = {}, userWardrobe = [], itemsPerCategory = 2) {
    const { season = 'Всесезонный', temperature = 20 } = capsuleParams;
    
    // Группируем гардероб пользователя по категориям
    const userByCategory = this._groupByCategory(userWardrobe);
    
    // Определяем какие категории нужно добавить
    const categoriesToLoad = ['Верх', 'Низ', 'Обувь', 'Сумка', 'Аксессуары'];
    
    // Если холодно - добавляем верхнюю одежду
    if (temperature < 18) {
      categoriesToLoad.push('Верхняя одежда');
    }
    
    // Загружаем товары для каждой категории параллельно
    const loadPromises = categoriesToLoad.map(async (category) => {
      const userHas = (userByCategory[category] || []).length;
      const toLoad = userHas > 0 ? 1 : itemsPerCategory; // Если у пользователя есть - берем меньше
      
      const items = await this.getItemsForCategory(category, season, toLoad);
      
      return {
        category,
        items
      };
    });
    
    // Ждем все запросы
    const results = await Promise.all(loadPromises);
    
    // Собираем все товары
    const allBrandItems = results.flatMap(r => r.items);
    
    return allBrandItems;
  }
  
  /**
   * Зафиксировать показ товара (impression)
   * Fire-and-forget - не ждем ответа
   * 
   * @param {string} itemId - ID товара
   * @param {string} userId - ID пользователя (Telegram ID)
   * @param {string} capsuleId - ID капсулы (опционально)
   */
  trackImpression(itemId, userId = null, capsuleId = null) {
    if (!itemId) return;
    
    // Асинхронный запрос к Flask API (не блокирует UI)
    fetch(`${API_BASE_URL}/items/${itemId}/impression`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        user_id: userId,
        capsule_id: capsuleId 
      })
    })
    .then(() => {
      // Impression tracked (логирование отключено)
    })
    .catch(() => {
      // Failed to track impression (не критично)
    });
  }
  
  /**
   * Зафиксировать клик по товару (click)
   * Fire-and-forget - не ждем ответа
   * 
   * @param {string} itemId - ID товара
   * @param {string} userId - ID пользователя (Telegram ID)
   * @param {string} capsuleId - ID капсулы (опционально)
   */
  trackClick(itemId, userId = null, capsuleId = null) {
    if (!itemId) return;
    
    // Асинхронный запрос к Flask API (не блокирует UI)
    fetch(`${API_BASE_URL}/items/${itemId}/click`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        user_id: userId,
        capsule_id: capsuleId,
        action: 'visit_shop'
      })
    })
    .then(() => {
      // Click tracked (логирование отключено)
    })
    .catch(() => {
      // Failed to track click (не критично)
    });
  }
  
  /**
   * Обработать клик по товару: записать метрику и открыть магазин
   * 
   * @param {Object} item - Объект товара
   * @param {string} userId - ID пользователя (Telegram ID)
   * @param {string} capsuleId - ID капсулы (опционально)
   */
  handleItemClick(item, userId = null, capsuleId = null) {
    if (!item) return;
    
    // Записываем клик (асинхронно)
    this.trackClick(item.id, userId, capsuleId);
    
    // Открываем ссылку на магазин в новой вкладке
    if (item.shop_link) {
      try {
        window.open(item.shop_link, '_blank', 'noopener,noreferrer');
        // Shop link opened (логирование отключено)
      } catch (error) {
        console.error('❌ Error opening shop link:', error);
      }
    } else {
      // No shop_link for item (не критично)
    }
  }
  
  // ========== Helper Methods ==========
  
  /**
   * Получить URL изображения товара
   * 
   * @param {string} brandId - ID бренда
   * @param {string} imageId - ID изображения
   * @returns {string} Полный URL изображения
   */
  _getImageUrl(brandId, imageId) {
    if (!brandId || !imageId) {
      return null;
    }
    return `${STORAGE_URL}/${brandId}/${imageId}.jpg`;
  }
  
  /**
   * Сгруппировать вещи по категориям
   * 
   * @param {Array} items - Массив вещей
   * @returns {Object} Объект с группами по категориям
   */
  _groupByCategory(items) {
    return (items || []).reduce((acc, item) => {
      const category = item.category || 'Другое';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(item);
      return acc;
    }, {});
  }
  
  /**
   * Обеспечить разнообразие брендов
   * Максимум 1-2 товара от одного бренда
   * 
   * @param {Array} items - Массив товаров
   * @param {number} limit - Лимит товаров
   * @returns {Array} Отфильтрованный массив
   */
  _ensureBrandDiversity(items, limit) {
    if (!items || items.length === 0) return [];
    
    const byBrand = new Map();
    const otherItems = [];
    
    items.forEach(item => {
      const brandId = item.brand_id;
      
      if (!byBrand.has(brandId)) {
        // Первый товар от этого бренда
        byBrand.set(brandId, [item]);
      } else {
        const brandItems = byBrand.get(brandId);
        if (brandItems.length < 2) {
          // Второй товар от этого бренда
          brandItems.push(item);
        } else {
          // Третий и далее - в резерв
          otherItems.push(item);
        }
      }
    });
    
    // Собираем результат: сначала уникальные бренды, потом остальные
    const result = [
      ...Array.from(byBrand.values()).flat(),
      ...otherItems
    ].slice(0, limit);
    
    return result;
  }
  
  /**
   * Тестовая функция для проверки подключения
   */
  async testConnection() {
    try {
      // Testing Supabase connection
      
      const { data, error } = await supabase
        .from('brand_items')
        .select('id, description, category')
        .eq('is_approved', true)
        .eq('is_active', true)
        .limit(1);
      
      if (error) {
        console.error('❌ Supabase connection error:', error);
        return false;
      }
      
      // Supabase connected
      return true;
      
    } catch (error) {
      console.error('❌ Exception testing connection:', error);
      return false;
    }
  }
}

// Экспортируем singleton
export default new BrandItemsService();

