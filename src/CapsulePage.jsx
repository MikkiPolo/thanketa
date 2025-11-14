import React, { useState, useEffect } from 'react';
import { ArrowLeft, Star, Shirt, Briefcase, Sparkles, Sun, Plane, Heart, ShoppingBag } from 'lucide-react';
import { wardrobeService, favoritesService } from './supabase';
import brandItemsService from './services/brandItemsService';
import { BACKEND_URL, API_ENDPOINTS } from './config.js';
import LoadingModal from './LoadingModal';


const CapsulePage = ({ profile, onBack, initialCapsule = null, isFavoritesView = false }) => {
  const [capsules, setCapsules] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedCapsule, setSelectedCapsule] = useState(initialCapsule);
  const [favorites, setFavorites] = useState([]);



  // Категории капсул
  const capsuleCategories = [
    {
      id: 'casual',
      name: 'Повседневный стиль',
      description: 'Уютные образы для ежедневных дел',
      icon: 'shirt'
    },
    {
      id: 'business',
      name: 'Деловой образ',
      description: 'Элегантные решения для работы',
      icon: 'briefcase'
    },
    {
      id: 'evening',
      name: 'Вечерний выход',
      description: 'Стильные образы для особых случаев',
      icon: 'sparkles'
    },
    {
      id: 'romantic',
      name: 'Романтическое свидание',
      description: 'Нежные и привлекательные образы',
      icon: 'heart'
    },
    {
      id: 'weekend',
      name: 'Выходные',
      description: 'Расслабленные образы для отдыха',
      icon: 'sun'
    },
    {
      id: 'travel',
      name: 'Путешествия',
      description: 'Практичные образы для поездок',
      icon: 'plane'
    }
  ];

  useEffect(() => {
    loadFavorites();
    loadCachedCapsules();
  }, []);

  // 🛍️ АВТОМАТИЧЕСКАЯ ОТПРАВКА IMPRESSIONS ДЛЯ ВСЕХ ВИДИМЫХ ТОВАРОВ БРЕНДОВ
  useEffect(() => {
    if (!capsules || !Array.isArray(capsules) || capsules.length === 0) {
      return;
    }

    // Отправляем impressions для всех товаров брендов во всех капсулах
    const impressionsSent = new Set(); // Чтобы не отправлять дубликаты

    capsules.forEach(capsule => {
      (capsule.items || []).forEach(item => {
        if (item.is_brand_item && item.id) {
          const uniqueKey = `${item.id}_${capsule.id}`;
          if (!impressionsSent.has(uniqueKey)) {
            brandItemsService.trackImpression(item.id, profile.telegram_id, capsule.id);
            impressionsSent.add(uniqueKey);
          }
        }
      });
    });

    if (impressionsSent.size > 0) {
      // Impressions отправлены
    }
  }, [capsules, profile.telegram_id]); // Запускается при смене капсул



  const loadFavorites = async () => {
    try {
      // Загружаем избранное
      
      if (!profile.telegram_id || profile.telegram_id === 'default') {
        setFavorites([]);
        return;
      }

      const favoritesData = await favoritesService.getFavorites(profile.telegram_id);
      
      // Преобразуем данные из Supabase в нужный формат
      const formattedFavorites = favoritesData.map(fav => ({
        id: fav.capsule_id,
        name: fav.capsule_name,
        description: fav.capsule_description,
        items: (fav.capsule_data?.items || []).map(item => ({
          ...item,
          imageUrl: item.image_id ? wardrobeService.getImageUrl(profile.telegram_id, item.image_id) : null
        })),
        category: fav.capsule_category,
        addedAt: fav.created_at
      }));
      
      setFavorites(formattedFavorites);
    } catch (error) {
      console.error('Ошибка загрузки избранного:', error);
      // Fallback к localStorage если Supabase недоступен
      try {
        const savedFavorites = localStorage.getItem(`favorites_${profile.telegram_id}`);
        if (savedFavorites) {
          setFavorites(JSON.parse(savedFavorites));
        }
      } catch (localError) {
        console.error('Ошибка загрузки из localStorage:', localError);
      }
    }
  };

  const loadCachedCapsules = () => {
    try {
      const cachedCapsules = localStorage.getItem(`cached_capsules_${profile.telegram_id}`);
      if (cachedCapsules) {
        let parsedCapsules = JSON.parse(cachedCapsules);
        // Миграция: если в кэше лежит объект с categories → разворачиваем в плоский список
        try {
          if (parsedCapsules && parsedCapsules.categories) {
            const flat = [];
            (parsedCapsules.categories || []).forEach(category => {
              (category.fullCapsules || []).forEach(capsule => {
                flat.push({
                  id: capsule.id,
                  name: capsule.name || category.name || 'Капсула',
                  description: capsule.description || category.description || '',
                  items: capsule.items || [],
                  category: category.id
                });
              });
            });
            parsedCapsules = flat;
            localStorage.setItem(`cached_capsules_${profile.telegram_id}`, JSON.stringify(flat));
          }
        } catch (_) {}
        // Проверяем, что кэш не устарел (24 часа)
        const cacheTime = localStorage.getItem(`cached_capsules_time_${profile.telegram_id}`);
        if (cacheTime && (Date.now() - parseInt(cacheTime)) < 24 * 60 * 60 * 1000) {
          setCapsules(parsedCapsules);
          setLoading(false);
          return;
        }
      }
      // Если кэша нет или он устарел, показываем пустую страницу
      setCapsules(null);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки кэша:', error);
      setCapsules(null);
      setLoading(false);
    }
  };

  const generateCapsules = async () => {
    try {
      setLoading(true);
      // При обновлении скрываем текущие капсулы, чтобы не мигало и пользователь не видел старые
      setCapsules(null);
      
      // Получаем гардероб пользователя
      const wardrobe = await wardrobeService.getWardrobe(profile.telegram_id);
      // Фильтруем сразу неподходящие вещи на клиенте для жёсткой гарантии
      const eligibleWardrobe = (wardrobe || []).filter(it => it && it.is_suitable !== false);
      
      // Получаем погоду (используем существующий компонент)
      const weather = await fetchWeather();
      
      // Генерируем капсулы на основе гардероба, анкеты и погоды
      const generatedCapsules = await generateCapsulesFromWardrobe(eligibleWardrobe, profile, weather, { forceRefresh: true });
      
      setCapsules(generatedCapsules);
      
      // Сохраняем в кэш
      localStorage.setItem(`cached_capsules_${profile.telegram_id}`, JSON.stringify(generatedCapsules));
      localStorage.setItem(`cached_capsules_time_${profile.telegram_id}`, Date.now().toString());
    } catch (error) {
      console.error('Ошибка при генерации капсул:', error);
      
      // Показываем ошибку пользователю
      if (error.message.includes('Превышено время ожидания')) {
        alert('Генерация капсул заняла слишком много времени. Попробуйте еще раз.');
      } else {
        alert(`Ошибка при генерации капсул: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchWeather = async () => {
    // Используем логику из WeatherDateHeader
    if (!profile.location_latitude || !profile.location_longitude) {
      return null;
    }

    try {
      const response = await fetch(
        `https://api.openweathermap.org/data/2.5/weather?lat=${profile.location_latitude}&lon=${profile.location_longitude}&appid=d69e489c7ddeb793bff2350cc232dab7&units=metric&lang=ru`
      );
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Ошибка получения погоды:', error);
    }
    return null;
  };

  // Функция для сортировки предметов по логическому порядку
  const sortItemsByCategory = (items) => {
    const categoryOrder = {
      // Одежда (приоритет 1-3)
      'платье': 1,
      'блузка': 2,
      'футболка': 2,
      'рубашка': 2,
      'свитер': 2,
      'топ': 2,
      'джемпер': 2,
      'кардиган': 2,
      'жилет': 2,
      'пиджак': 2,
      'куртка': 2,
      'пальто': 2,
      'брюки': 3,
      'джинсы': 3,
      'юбка': 3,
      'шорты': 3,
      'легинсы': 3,
      // Обувь (приоритет 4)
      'обувь': 4,
      'туфли': 4,
      'ботинки': 4,
      'кроссовки': 4,
      'сапоги': 4,
      'сандалии': 4,
      'мокасины': 4,
      'шлепки': 4,
      'балетки': 4,
      // Аксессуары (приоритет 5)
      'сумка': 5,
      'аксессуары': 5,
      'украшения': 5,
      'пояс': 5,
      'шарф': 5,
      'шапка': 5,
      'очки': 5,
      'серьги': 5,
      'колье': 5,
      'браслет': 5
    };

    return items.sort((a, b) => {
      const orderA = categoryOrder[a.category?.toLowerCase()] || 999;
      const orderB = categoryOrder[b.category?.toLowerCase()] || 999;
      return orderA - orderB;
    });
  };

  const generateCapsulesFromWardrobe = async (wardrobe, profile, weather, options = {}) => {
    try {
      // Отправляем запрос на бэкенд для генерации капсул с таймаутом 120 секунд
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 секунд
      
      try {
        const fullUrl = `${BACKEND_URL}${API_ENDPOINTS.GENERATE_CAPSULES}`;
        
        const slimWardrobe = (wardrobe || []).map(it => ({
          id: it.id,
          category: it.category,
          season: it.season,
          description: it.description,
          is_suitable: it.is_suitable
        }));

        // Передаём на бэкенд уже показанные комбинации, чтобы новые не повторяли старые
        const excludeCombinations = Array.isArray(capsules)
          ? capsules.map(c => (c.items || []).map(it => it.id))
          : [];

      const response = await fetch(fullUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          mode: 'cors',
          cache: 'no-store',
          body: JSON.stringify({
            wardrobe: slimWardrobe,
            profile: profile,
            weather: weather,
            // Явно обходим кэш при ручном обновлении и принудительно включаем rule-engine
            no_cache: options.forceRefresh === true,
            engine: 'rule', // Принудительно используем rule-based движок
            rule_engine: true, // Дополнительный флаг для rule-engine
            exclude_combinations: excludeCombinations
          }),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId); // Очищаем таймаут если запрос завершился

        if (response.ok) {
          const result = await response.json();
          if (result?.meta?.insufficient) {
            alert('Недостаточно подходящих вещей для создания капсул. Добавьте больше вещей в гардероб. Пока мы показываем стильные образы с товарами партнеров');
          }
          
           // Проверяем структуру ответа
           if (!result.capsules || !result.capsules.categories) {
            console.error('Неверная структура ответа от бэкенда:', result);
            throw new Error('Неверная структура ответа от бэкенда');
          }
           // Ограничиваем вывод максимум 20 капсул на клиенте (доп. гарантия)
           const maxClientCaps = 20;
          
          // Преобразуем результат бэкенда в плоский список капсул без категорий
           const flat = [];
          (result.capsules.categories || []).forEach(category => {
            (category.fullCapsules || []).forEach(capsule => {
                const itemsResolved = sortItemsByCategory((capsule.items || []).map(itemIdOrObject => {
                // Проверяем: это ID вещи пользователя или полный объект товара бренда?
                if (typeof itemIdOrObject === 'object' && itemIdOrObject !== null) {
                  // Это полный объект (брендовый товар или вещь пользователя)
                  const processedItem = {
                    ...itemIdOrObject,
                    imageUrl: itemIdOrObject.imageUrl || itemIdOrObject.image_url || null, // Поддерживаем оба формата
                    is_brand_item: itemIdOrObject.is_brand_item !== false // По умолчанию true, если не указано false
                  };
                  
                  // Для вещей пользователя добавляем правильный imageUrl
                  if (!processedItem.is_brand_item && processedItem.id) {
                    const userItem = wardrobe.find(w => w.id === processedItem.id && w.is_suitable !== false);
                    if (userItem && userItem.image_id) {
                      processedItem.imageUrl = wardrobeService.getImageUrl(profile.telegram_id, userItem.image_id);
                    }
                  }
                  
                  return processedItem;
                } else {
                  // Это ID вещи пользователя (строка/число)
                  const item = wardrobe.find(w => w.id === itemIdOrObject && w.is_suitable !== false);
                  return item ? {
                    ...item,
                    imageUrl: item.image_id ? wardrobeService.getImageUrl(profile.telegram_id, item.image_id) : null,
                    is_brand_item: false
                  } : null;
                }
              }).filter(Boolean));
              flat.push({
                id: capsule.id,
                name: capsule.name || category.name || 'Капсула',
                description: capsule.description || category.description || '',
                items: itemsResolved,
                category: category.id
              });
            });
          });
           return flat.slice(0, maxClientCaps);
        } else {
          console.error('Ошибка генерации капсул:', response.statusText);
          throw new Error(`Ошибка сервера: ${response.statusText}`);
        }
      } catch (fetchError) {
        clearTimeout(timeoutId); // Очищаем таймаут в случае ошибки
        if (fetchError.name === 'AbortError') {
          console.error('Таймаут запроса к бэкенду (90 секунд)');
          throw new Error('Превышено время ожидания ответа от сервера. Попробуйте еще раз.');
        }
        throw fetchError;
      }
    } catch (error) {
      console.error('Ошибка при генерации капсул:', error);
      throw error; // Пробрасываем ошибку дальше
    }
  };


  // Выбор предметов для превью с приоритетом (всегда максимум 8 для 2 колонок)
  const getPreviewItems = (items) => {
    if (!Array.isArray(items)) return [];
    const normalized = items.filter(Boolean);
    const total = normalized.length;
    const capacity = total >= 5 ? 8 : 4; // Всегда четное число для 2 колонок

    const toLower = (s) => (s || '').toLowerCase();

    const dresses = [];
    const tops = [];
    const bottoms = [];
    const shoes = [];
    const accessories = [];
    const outerwear = [];
    const rest = [];

    const topSet = new Set(['блузка','футболка','рубашка','свитер','топ','джемпер','кофта','водолазка']);
    const bottomSet = new Set(['юбка','брюки','джинсы','шорты','легинсы','леггинсы']);
    const dressSet = new Set(['платье','сарафан']);
    const shoesSet = new Set(['обувь','туфли','ботинки','кроссовки','сапоги','сандалии','мокасины','балетки']);
    const accSet = new Set(['сумка','аксессуары','украшения','пояс','шарф','часы','очки','серьги','колье','браслет','рюкзак']);
    const outerSet = new Set(['пиджак','куртка','пальто','кардиган','жакет','жилет']);

    normalized.forEach((it) => {
      const cat = toLower(it.category);
      if (dressSet.has(cat)) dresses.push(it);
      else if (topSet.has(cat)) tops.push(it);
      else if (bottomSet.has(cat)) bottoms.push(it);
      else if (shoesSet.has(cat)) shoes.push(it);
      else if (accSet.has(cat)) accessories.push(it);
      else if (outerSet.has(cat)) outerwear.push(it);
      else rest.push(it);
    });

    const picked = [];
    const tryPush = (arr) => { if (picked.length < capacity && arr.length) picked.push(arr.shift()); };

    if (dresses.length) {
      tryPush(dresses);
    } else {
      tryPush(tops);
      tryPush(bottoms);
    }
    tryPush(shoes);
    tryPush(accessories);
    tryPush(outerwear);

    // Заполняем остатками по группам, чтобы показать больше ассортимента
    const pools = [dresses, tops, bottoms, shoes, accessories, outerwear, rest];
    for (const pool of pools) {
      while (picked.length < capacity && pool.length) {
        picked.push(pool.shift());
      }
      if (picked.length >= capacity) break;
    }

    return picked;
  };

  // Позиционирование предметов на белом холсте по шаблонам
  const getPreviewPositions = (items) => {
    if (!Array.isArray(items)) return [];
    const toLower = (s) => (s || '').toLowerCase();

    // Классификация с учётом синонимов и описаний
    const isOneOf = (val, list) => list.includes(toLower(val));
    const classify = (it) => {
      const c = toLower(it.category);
      const d = toLower(it.description);
      if (isOneOf(c, ['платье', 'сарафан'])) return 'dress';
      if (isOneOf(c, ['пиджак', 'куртка', 'пальто', 'кардиган', 'жакет', 'жилет'])) return 'outer';
      if (isOneOf(c, ['юбка','брюки','джинсы','шорты','легинсы','леггинсы'])) return 'bottom';
      if (
        isOneOf(c, ['обувь','туфли','ботинки','кроссовки','сапоги','сандалии','мокасины','балетки','шлепки','сланцы','тапки','тапочки','мюли','сабо']) ||
        /(туфл|ботин|кросс|сапог|сандал|мокасин|балетк|шлеп|сланц|тапоч|мюл|сабо)/.test(d)
      ) return 'shoes';
      if (isOneOf(c, ['сумка','аксессуары','украшения','пояс','шарф','часы','очки','серьги','колье','браслет','рюкзак'])) return 'acc';
      if (isOneOf(c, ['блузка','футболка','рубашка','свитер','топ','джемпер','кофта','водолазка'])) return 'top';
      return 'other';
    };

    const typed = items.map((it) => ({ it, t: classify(it) }));
    const getFirst = (t) => typed.find((x) => x.t === t)?.it;
    const getMany = (t, limit = 2) => typed.filter((x) => x.t === t).map((x) => x.it).slice(0, limit);

    const dress = getFirst('dress');
    const top = getFirst('top');
    const bottom = getFirst('bottom');
    const shoes = getFirst('shoes');
    const outer = getFirst('outer');
    const accessories = getMany('acc', 2);

    const count = items.length;
    const scale = count >= 5 ? 0.9 : 1.0;

    const placements = [];

    if (dress) {
      placements.push({ item: dress, left: 50, top: 32, width: 42 * scale, z: 2 });
      if (outer) placements.push({ item: outer, left: 24, top: 32, width: 28 * scale, z: 1 });
      if (shoes) placements.push({ item: shoes, left: 50, top: 80, width: 26 * scale, z: 3 });
      if (accessories[0]) placements.push({ item: accessories[0], left: 78, top: 42, width: 20 * scale, z: 4 });
      if (accessories[1]) placements.push({ item: accessories[1], left: 22, top: 44, width: 18 * scale, z: 4 });
    } else {
      if (top) placements.push({ item: top, left: 50, top: 28, width: 34 * scale, z: 2 });
      if (bottom) placements.push({ item: bottom, left: 50, top: 56, width: 34 * scale, z: 2 });
      if (outer) placements.push({ item: outer, left: 22, top: 30, width: 26 * scale, z: 1 });
      if (shoes) placements.push({ item: shoes, left: 50, top: 80, width: 26 * scale, z: 3 });
      if (accessories[0]) placements.push({ item: accessories[0], left: 78, top: 40, width: 20 * scale, z: 4 });
      if (accessories[1]) placements.push({ item: accessories[1], left: 22, top: 42, width: 18 * scale, z: 4 });
    }

    const placedIds = new Set(placements.map((p) => p.item.id));
    const rest = items.filter((it) => !placedIds.has(it.id)).slice(0, 2);
    if (rest[0]) placements.push({ item: rest[0], left: 30, top: 50, width: 22 * scale, z: 2 });
    if (rest[1]) placements.push({ item: rest[1], left: 70, top: 50, width: 22 * scale, z: 2 });

    return placements.sort((a, b) => (a.z || 1) - (b.z || 1));
  };



  const handleAddToFavorites = async (capsule) => {
    try {
      // Проверяем, что у нас есть telegram_id
      if (!profile.telegram_id || profile.telegram_id === 'default') {
        console.error('Отсутствует telegram_id');
        alert('Ошибка: не удалось определить пользователя. Попробуйте перезагрузить страницу.');
        return;
      }

      const favoriteCapsule = {
        id: capsule.id,
        name: capsule.name,
        description: capsule.description,
        items: capsule.items,
        category: selectedCategory || 'general'
      };

      // Сохраняем в Supabase
      await favoritesService.addToFavorites(profile.telegram_id, favoriteCapsule);
      
      // Обновляем локальное состояние
      const newFavorites = [...favorites, favoriteCapsule];
      setFavorites(newFavorites);
      
      // Также сохраняем в localStorage как fallback
      localStorage.setItem(`favorites_${profile.telegram_id}`, JSON.stringify(newFavorites));
      
      // Показываем уведомление
      alert('Капсула добавлена в избранное!');
    } catch (error) {
      console.error('❌ Ошибка добавления в избранное:', error);
      console.error('Детали ошибки:', {
        message: error.message,
        stack: error.stack,
        telegramId: profile.telegram_id,
        capsuleId: capsule.id
      });
      alert('Ошибка при добавлении в избранное. Попробуйте еще раз.');
    }
  };

  const handleRemoveFromFavorites = async (capsuleId) => {
    try {
      // Удаляем из Supabase
      await favoritesService.removeFromFavorites(profile.telegram_id, capsuleId);
      
      // Обновляем локальное состояние
      const newFavorites = favorites.filter(fav => fav.id !== capsuleId);
      setFavorites(newFavorites);
      
      // Также обновляем localStorage как fallback
      localStorage.setItem(`favorites_${profile.telegram_id}`, JSON.stringify(newFavorites));
      
      // Показываем уведомление
      alert('Капсула удалена из избранного!');
      
      // Если это просмотр из избранного, возвращаемся назад
      if (isFavoritesView) {
        onBack();
      }
    } catch (error) {
      console.error('Ошибка удаления из избранного:', error);
      alert('Ошибка при удалении из избранного. Попробуйте еще раз.');
    }
  };

  const isInFavorites = (capsuleId) => {
    // Если это просмотр из избранного, всегда возвращаем true
    if (isFavoritesView) {
      return true;
    }
    
    // Находим текущую капсулу по ID
    const currentCapsule = capsules?.find(cap => cap.id === capsuleId);
    if (!currentCapsule || !currentCapsule.items) return false;
    
    // Создаем отсортированный массив ID вещей текущей капсулы
    const currentItems = currentCapsule.items.map(item => item.id).sort();
    
    // Проверяем, есть ли в избранном капсула с таким же содержимым
    return favorites.some(fav => {
      if (!fav.items) return false;
      const favItems = fav.items.map(item => item.id).sort();
      return JSON.stringify(currentItems) === JSON.stringify(favItems);
    });
  };

  // Функция для генерации изображения капсулы
  const generateCapsuleImage = async (capsule) => {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      // Устанавливаем размеры canvas (оптимально для мессенджеров)
      canvas.width = 800;
      canvas.height = 1100; // Увеличили высоту

      // Очищаем canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Фон
      ctx.fillStyle = '#F8F9FA';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Логотип вверху
      const loadLogo = () => {
        return new Promise((resolve, reject) => {
          const logoImg = new Image();
          logoImg.crossOrigin = 'anonymous';
          logoImg.onload = () => resolve(logoImg);
          logoImg.onerror = reject;
          logoImg.src = '/vite.svg';
          // Logo loaded
        });
      };

      // Отрисовываем логотип и описание
      const drawHeader = async () => {
        try {
          // Загружаем и отрисовываем логотип
          const logo = await loadLogo();
          const logoWidth = 300; // Ширина логотипа
          const logoHeight = 80; // Высота логотипа (сохраняем пропорции)
          const logoX = (canvas.width - logoWidth) / 2;
          const logoY = 30;
          
          ctx.drawImage(logo, logoX, logoY, logoWidth, logoHeight);
        } catch (error) {
          console.error('Ошибка загрузки логотипа:', error);
          // Fallback к текстовому заголовку если логотип не загрузился
          ctx.fillStyle = '#2C3E50';
          ctx.font = 'bold 32px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(capsule.name, canvas.width / 2, 60);
        }
      };

      // Сетка для предметов
      const itemsPerRow = 2;
      const itemSize = 300;
      const itemSpacing = 50;
      const startX = (canvas.width - (itemsPerRow * itemSize + (itemsPerRow - 1) * itemSpacing)) / 2;
      const startY = 180; // Уменьшили отступ, так как убрали описание

      // Загружаем и отрисовываем изображения предметов
      const loadImage = (src) => {
        return new Promise((resolve, reject) => {
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = () => resolve(img);
          img.onerror = reject;
          img.src = src;
        });
      };

      // Отрисовываем предметы
      const drawItems = async () => {
        try {
          // Сначала отрисовываем заголовок с логотипом
          await drawHeader();
          
          for (let i = 0; i < Math.min(capsule.items.length, 6); i++) {
            const item = capsule.items[i];
            const row = Math.floor(i / itemsPerRow);
            const col = i % itemsPerRow;
            const x = startX + col * (itemSize + itemSpacing);
            const y = startY + row * (itemSize + itemSpacing + 80);

            // Фон для предмета
            ctx.fillStyle = '#FFFFFF';
            ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
            ctx.shadowBlur = 10;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 2;
            ctx.fillRect(x, y, itemSize, itemSize);
            ctx.shadowColor = 'transparent';

            // Изображение предмета
            if (item.imageUrl || item.image_url) {
              try {
                const img = await loadImage(item.imageUrl || item.image_url);
                
                // Вычисляем размеры для вписывания в квадрат
                const scale = Math.min(itemSize / img.width, itemSize / img.height);
                const scaledWidth = img.width * scale;
                const scaledHeight = img.height * scale;
                const offsetX = x + (itemSize - scaledWidth) / 2;
                const offsetY = y + (itemSize - scaledHeight) / 2;

                ctx.drawImage(img, offsetX, offsetY, scaledWidth, scaledHeight);
              } catch (error) {
                console.error('Ошибка загрузки изображения:', error);
                // Плейсхолдер если изображение не загрузилось
                ctx.fillStyle = '#E9ECEF';
                ctx.fillRect(x + 50, y + 50, itemSize - 100, itemSize - 100);
                ctx.fillStyle = '#6C757D';
                ctx.font = '16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('Изображение', x + itemSize / 2, y + itemSize / 2);
              }
            }

            // Название предмета
            ctx.fillStyle = '#2C3E50';
            ctx.font = 'bold 16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(item.category, x + itemSize / 2, y + itemSize + 25);

            // Описание предмета
            ctx.fillStyle = '#6C757D';
            ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            const words = item.description.split(' ');
            let line = '';
            let lineY = y + itemSize + 45;
            
            for (let word of words) {
              const testLine = line + word + ' ';
              const metrics = ctx.measureText(testLine);
              
              if (metrics.width > itemSize - 20) {
                ctx.fillText(line, x + itemSize / 2, lineY);
                line = word + ' ';
                lineY += 20;
              } else {
                line = testLine;
              }
            }
            ctx.fillText(line, x + itemSize / 2, lineY);
          }

          // Убираем логотип приложения для чистого изображения

          // Генерируем blob из canvas
          canvas.toBlob((blob) => {
            resolve(blob);
          }, 'image/png', 0.9);
        } catch (error) {
          reject(error);
        }
      };

      drawItems();
    });
  };


  const getLucideIcon = (iconName) => {
    const iconMap = {
      'shirt': <Shirt size={24} />,
      'briefcase': <Briefcase size={24} />,
      'sparkles': <Sparkles size={24} />,
      'heart': <Heart size={24} />,
      'sun': <Sun size={24} />,
      'plane': <Plane size={24} />
    };
    return iconMap[iconName] || <Shirt size={24} />;
  };

  if (loading) {
    return (
      <>
        <div className="app">
          <div className="card">
            {/* Пустой контент во время загрузки */}
          </div>
        </div>
        <LoadingModal 
          isVisible={loading}
          title="Генерируем капсулы..."
          subtitle="Анализируем ваш гардероб и создаем стильные образы"
        />
      </>
    );
  }

  if (selectedCapsule) {
    // Если капсула пустая, показываем сообщение
    if (!selectedCapsule.items || selectedCapsule.items.length === 0) {
      return (
        <div className="app capsules-page">
          <div className="card" style={{ paddingTop: "calc(env(safe-area-inset-top) + 2rem)" }}>
            <div className="item-detail-header">
              <button className="btn-icon back-btn" onClick={() => {
                if (isFavoritesView) {
                  onBack();
                } else {
                  setSelectedCapsule(null);
                }
              }}>
                <ArrowLeft size={20} />
              </button>
            </div>
            
            <div className="capsule-detail">
              <h2>{selectedCapsule.name || 'Капсула'}</h2>
              <p className="capsule-description">Эта капсула не содержит предметов</p>
              
              <div className="capsule-actions">
                <button className="btn-primary" onClick={() => setSelectedCapsule(null)}>
                  Назад к списку
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div className="app capsules-page">
        <div className="card" style={{ paddingTop: "calc(env(safe-area-inset-top) + 2rem)" }}>
          <div className="item-detail-header">
            <button className="btn-icon back-btn" onClick={() => {
              if (isFavoritesView) {
                onBack();
              } else {
                setSelectedCapsule(null);
              }
            }}>
              <ArrowLeft size={20} />
            </button>
          </div>
          
          <div className="capsule-detail">
            <h2>{selectedCapsule.name || 'Капсула'}</h2>
            <p className="capsule-description">{selectedCapsule.description || 'Описание капсулы'}</p>
            
            <div className="capsule-visualization">
              <div className="capsule-outfit grid-layout">
                {selectedCapsule.items.map((item, index) => (
                  <div 
                    key={index} 
                    className="capsule-item-overlay"
                    data-category={item.category?.toLowerCase()}
                  >
                    {(item.imageUrl || item.image_url) && (item.imageUrl || item.image_url) !== 'null' && (
                      <img 
                        src={item.imageUrl || item.image_url} 
                        alt={item.description}
                        onError={(e) => {
                          console.error('❌ Ошибка загрузки изображения в деталях:', e.target.src);
                          if (e.target.src.includes('.png')) {
                            e.target.src = e.target.src.replace('.png', '.jpg');
                            // Trying .jpg version
                          }
                        }}
                        onLoad={() => {
                          // Image loaded
                        }}
                      />
                    )}
                  </div>
                ))}
                
              </div>
              
              <div className="capsule-items-list">
                {selectedCapsule.items.map((item, index) => (
                  <div 
                    key={index} 
                    className={`capsule-item-info ${item.is_brand_item ? 'brand-item' : ''}`}
                    onClick={() => {
                      if (item.is_brand_item) {
                        // Товар бренда - открыть магазин
                        brandItemsService.handleItemClick(item, profile.telegram_id, selectedCapsule.id);
                      }
                    }}
                    style={item.is_brand_item ? { cursor: 'pointer' } : {}}
                  >
                    <h4>
                      {item.category}
                      {item.is_brand_item && (
                        <span style={{ 
                          marginLeft: '8px', 
                          fontSize: '12px', 
                          background: '#000', 
                          color: '#fff', 
                          padding: '2px 6px', 
                          borderRadius: '4px' 
                        }}>
                          🛍️ {item.brand_name || 'Бренд'}
                        </span>
                      )}
                    </h4>
                    <p>{item.description}</p>
                    {item.is_brand_item && item.price && (
                      <p style={{ fontWeight: 'bold', color: '#000', marginTop: '4px' }}>
                        {item.price} {item.currency || 'RUB'}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="capsule-actions">
              {/* Кнопка добавления/удаления из избранного */}
              {isInFavorites(selectedCapsule.id) ? (
                <button 
                  className="btn-secondary remove-from-favorites-btn" 
                  onClick={() => handleRemoveFromFavorites(selectedCapsule.id)}
                >
                  ❤️ Убрать из избранного
                </button>
              ) : (
                <button 
                  className="btn-primary add-to-favorites-btn" 
                  onClick={() => handleAddToFavorites(selectedCapsule)}
                >
                  🤍 Добавить в избранное
                </button>
              )}
            </div>

          </div>
        </div>
        

      </div>
    );
  }

  // Плоский список капсул

  return (
    <div className="app capsules-page">
      <div className="card" style={{ paddingTop: "calc(env(safe-area-inset-top) + 1rem)" }}>
        <div className="item-detail-header">
          <button className="btn-icon back-btn" onClick={onBack}>
            <ArrowLeft size={20} />
          </button>
        </div>
        
        {Array.isArray(capsules) ? (
          <>
            <div className="capsules-header">
              <h2>Капсулы гардероба</h2>
              <p className="capsules-intro">Персональные образы, созданные специально для вас</p>
              <div className="capsules-actions">
                <button 
                  className="btn-primary refresh-btn"
                  onClick={generateCapsules}
                  disabled={loading}
                >
                  {loading ? 'Обновляем...' : 'Обновить капсулы'}
                </button>

              </div>
            </div>
            
            <div className="capsules-grid">
              {capsules.map((capsule) => {
                const preview = capsule.items || [];
                const moreCount = 0;
                return (
                  <div 
                    key={capsule.id} 
                    className="capsule-card"
                    onClick={() => {
                      setSelectedCapsule(capsule);
                      // Impressions уже отправлены при загрузке капсул (см. useEffect выше)
                    }}
                  >
                    <div className={`capsule-canvas-preview grid ${
                      preview.length >= 7 ? 'has-many-items' : ''
                    }`}>
                      {preview.map((it, index) => (
                        <div
                          key={index}
                          className="capsule-canvas-item"
                          data-category={it.category?.toLowerCase()}
                          onClick={(e) => {
                            // Если это товар бренда - открываем магазин (не открывая саму капсулу)
                            if (it.is_brand_item && it.shop_link) {
                              e.stopPropagation(); // Останавливаем всплытие события
                              brandItemsService.handleItemClick(it, profile.telegram_id, capsule.id);
                            }
                          }}
                          style={{
                            cursor: it.is_brand_item ? 'pointer' : 'default',
                            border: 'none',
                            borderRadius: it.is_brand_item ? '8px' : '0',
                            overflow: 'hidden',
                            boxShadow: it.is_brand_item ? '0 2px 6px rgba(0, 0, 0, 0.1), 0 4px 12px rgba(0, 0, 0, 0.05)' : 'none',
                            transition: it.is_brand_item ? 'all 0.3s ease' : 'none'
                          }}
                          onMouseEnter={(e) => {
                            if (it.is_brand_item) {
                              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15), 0 8px 20px rgba(0, 0, 0, 0.08)';
                              e.currentTarget.style.transform = 'translateY(-2px)';
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (it.is_brand_item) {
                              e.currentTarget.style.boxShadow = '0 2px 6px rgba(0, 0, 0, 0.1), 0 4px 12px rgba(0, 0, 0, 0.05)';
                              e.currentTarget.style.transform = 'translateY(0)';
                            }
                          }}
                        >
                          {(it.imageUrl || it.image_url) && (it.imageUrl || it.image_url) !== 'null' && (
                            <img
                              src={it.imageUrl || it.image_url}
                              alt={it.description}
                              onError={(e) => {
                                console.error('❌ Ошибка загрузки изображения:', e.target.src);
                                console.error('❌ Статус:', e.target.naturalWidth === 0 ? 'Не загружено' : 'Загружено');
                                if (e.target.src.includes('.png')) {
                                  e.target.src = e.target.src.replace('.png', '.jpg');
                                  // Trying .jpg version
                                }
                              }}
                              onLoad={() => {
                                // Image loaded
                              }}
                            />
                          )}
                          {/* Бейдж для товаров брендов */}
                          {it.is_brand_item && (
                            <div style={{
                              position: 'absolute',
                              top: '4px',
                              right: '4px',
                              background: '#000',
                              color: '#fff',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '10px',
                              fontWeight: 'bold'
                            }}>
                              🛍️
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    {moreCount > 0 && (
                      <div className="capsule-more-badge">+{moreCount}</div>
                    )}
                  </div>
                );
              })}
              
              {/* Пустая капсула-спейсер для предотвращения перекрытия навигацией */}
              <div className="capsule-spacer"></div>
            </div>
          </>
        ) : (
          // Если нет капсул - показываем пустое состояние
          <div className="empty-capsules">
            <h2>Капсулы гардероба</h2>
            <p className="capsules-intro">Персональные образы, созданные специально для вас</p>
            
            <div className="empty-icon">
              <Sparkles size={48} />
            </div>
            <h3>Капсулы не найдены</h3>
            <p>Нажмите кнопку "Получить капсулы" чтобы создать персональные образы</p>
            
            <div className="capsules-actions">
              <button 
                className="btn-primary refresh-btn"
                onClick={generateCapsules}
                disabled={loading}
              >
                {loading ? 'Генерируем...' : 'Получить капсулы'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CapsulePage; 