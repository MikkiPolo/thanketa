class CacheManager {
  constructor() {
    this.prefix = 'wardrobe_';
    this.defaultTTL = 30 * 60 * 1000; // 30 минут
  }

  // Сохранение данных в кэш
  set(key, data, ttl = this.defaultTTL) {
    try {
      const cacheData = {
        data,
        timestamp: Date.now(),
        ttl
      };
      
      localStorage.setItem(
        this.prefix + key, 
        JSON.stringify(cacheData)
      );
      
      return true;
    } catch (error) {
      console.error('Ошибка сохранения в кэш:', error);
      return false;
    }
  }

  // Получение данных из кэша
  get(key) {
    try {
      const cached = localStorage.getItem(this.prefix + key);
      
      if (!cached) {
        return null;
      }

      const cacheData = JSON.parse(cached);
      const now = Date.now();
      
      // Проверяем, не истек ли срок действия кэша
      if (now - cacheData.timestamp > cacheData.ttl) {
        this.remove(key);
        return null;
      }

      return cacheData.data;
    } catch (error) {
      console.error('Ошибка чтения из кэша:', error);
      return null;
    }
  }

  // Удаление данных из кэша
  remove(key) {
    try {
      localStorage.removeItem(this.prefix + key);
      return true;
    } catch (error) {
      console.error('Ошибка удаления из кэша:', error);
      return false;
    }
  }

  // Очистка всего кэша
  clear() {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(this.prefix)) {
          localStorage.removeItem(key);
        }
      });
      return true;
    } catch (error) {
      console.error('Ошибка очистки кэша:', error);
      return false;
    }
  }

  // Получение размера кэша
  getSize() {
    try {
      const keys = Object.keys(localStorage);
      const cacheKeys = keys.filter(key => key.startsWith(this.prefix));
      
      let totalSize = 0;
      cacheKeys.forEach(key => {
        totalSize += localStorage.getItem(key).length;
      });
      
      return {
        items: cacheKeys.length,
        size: totalSize,
        sizeKB: Math.round(totalSize / 1024 * 100) / 100
      };
    } catch (error) {
      console.error('Ошибка получения размера кэша:', error);
      return { items: 0, size: 0, sizeKB: 0 };
    }
  }

  // Проверка наличия данных в кэше
  has(key) {
    return this.get(key) !== null;
  }

  // Получение времени создания кэша
  getTimestamp(key) {
    try {
      const cached = localStorage.getItem(this.prefix + key);
      if (!cached) return null;
      
      const cacheData = JSON.parse(cached);
      return cacheData.timestamp;
    } catch (error) {
      return null;
    }
  }

  // Получение времени жизни кэша
  getTTL(key) {
    try {
      const cached = localStorage.getItem(this.prefix + key);
      if (!cached) return null;
      
      const cacheData = JSON.parse(cached);
      return cacheData.ttl;
    } catch (error) {
      return null;
    }
  }

  // Получение оставшегося времени жизни
  getRemainingTTL(key) {
    try {
      const timestamp = this.getTimestamp(key);
      const ttl = this.getTTL(key);
      
      if (timestamp === null || ttl === null) {
        return 0;
      }

      const elapsed = Date.now() - timestamp;
      const remaining = ttl - elapsed;
      
      return Math.max(0, remaining);
    } catch (error) {
      return 0;
    }
  }
}

// Создаем экземпляр для использования
const cache = new CacheManager();

// Хуки для React
export const useCache = () => {
  const setCachedData = (key, data, ttl) => {
    return cache.set(key, data, ttl);
  };

  const getCachedData = (key) => {
    return cache.get(key);
  };

  const removeCachedData = (key) => {
    return cache.remove(key);
  };

  const clearCache = () => {
    return cache.clear();
  };

  const getCacheInfo = () => {
    return cache.getSize();
  };

  return {
    set: setCachedData,
    get: getCachedData,
    remove: removeCachedData,
    clear: clearCache,
    info: getCacheInfo,
    has: cache.has.bind(cache),
    getRemainingTTL: cache.getRemainingTTL.bind(cache)
  };
};

export default cache; 