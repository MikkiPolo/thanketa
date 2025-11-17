import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ShoppingBag } from 'lucide-react';
import ShopItemDetail from './ShopItemDetail';
import LoadingSpinner from './LoadingSpinner';

const ShopPage = ({ telegramId, season = 'Осень', temperature = 15.0, onBack }) => {
  console.error('🛍️ ShopPage компонент рендерится:', { telegramId, season });
  
  const [allItems, setAllItems] = useState([]); // Все загруженные товары
  const [displayedItems, setDisplayedItems] = useState([]); // Товары для отображения
  const [loading, setLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [error, setError] = useState(null);
  const scrollContainerRef = useRef(null);
  const itemsPerPage = 20;

  // Загрузка товаров брендов
  useEffect(() => {
    console.error('🔄 ShopPage: начинаем загрузку товаров для сезона:', season);
    loadBrandItems();
  }, [season]);

  const loadBrandItems = async () => {
    try {
      setLoading(true);
      setError(null);

      // Запрос к публичному API
      const apiUrl = `https://linapolo.ru/api/public/items/capsule?season=${season}`;

      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const brandItems = data.items || [];

      console.error('📦 ShopPage: Загружено товаров:', brandItems.length);
      console.error('📦 ShopPage: Первые 3 товара:', brandItems.slice(0, 3).map(i => ({ id: i.id, description: i.description?.substring(0, 30) })));
      
      setAllItems(brandItems);
      // Показываем первую порцию товаров
      const firstBatch = brandItems.slice(0, itemsPerPage);
      console.error('👁️ ShopPage: Показываем первую порцию:', firstBatch.length, 'товаров из', brandItems.length);
      setDisplayedItems(firstBatch);
    } catch (err) {
      console.error('Ошибка загрузки товаров брендов:', err);
      setError('Не удалось загрузить товары. Попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  // Перемешивание массива (Fisher-Yates shuffle)
  const shuffleArray = useCallback((array) => {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }, []);

  // Загрузка следующей порции товаров
  const loadMoreItems = useCallback(() => {
    // Защита от повторных вызовов
    if (isLoadingMore) {
      return;
    }
    
    if (allItems.length === 0) {
      return;
    }

    setIsLoadingMore(true);

    // Небольшая задержка для плавности
    setTimeout(() => {
      setDisplayedItems(prev => {
        // Получаем ID уже показанных товаров
        const shownIds = new Set(prev.map(item => item.id));
        
        // Перемешиваем все товары
        const shuffled = shuffleArray(allItems);
        
        // Исключаем уже показанные
        const remainingItems = shuffled.filter(item => !shownIds.has(item.id));
        
        // Берем следующую порцию
        let nextBatch;
        if (remainingItems.length >= itemsPerPage) {
          nextBatch = remainingItems.slice(0, itemsPerPage);
        } else if (remainingItems.length > 0) {
          // Если осталось мало, добавляем перемешанные из всех
          const additionalNeeded = itemsPerPage - remainingItems.length;
          const additional = shuffleArray(allItems).slice(0, additionalNeeded);
          nextBatch = [...remainingItems, ...additional];
        } else {
          // Все товары показаны - перемешиваем заново
          nextBatch = shuffled.slice(0, itemsPerPage);
        }
        
        setIsLoadingMore(false);
        return [...prev, ...nextBatch];
      });
    }, 200);
  }, [allItems, isLoadingMore, shuffleArray, itemsPerPage]);

  // Используем Intersection Observer для отслеживания конца списка
  const observerTargetRef = useRef(null);
  const observerRef = useRef(null);
  const lastLoadTriggerRef = useRef(0);

  // Функция проверки необходимости подгрузки
  const checkShouldLoadMore = useCallback(() => {
    // Проверяем состояние через ref, чтобы избежать проблем с замыканиями
    if (allItems.length === 0) return false;

    // Проверяем все возможные скроллируемые элементы
    const appContainer = document.querySelector('.app');
    const body = document.body;
    const html = document.documentElement;
    
    // Определяем, какой элемент скроллится
    let scrollTop = 0;
    let scrollHeight = 0;
    let clientHeight = 0;
    
    if (appContainer && appContainer.scrollHeight > appContainer.clientHeight) {
      scrollTop = appContainer.scrollTop;
      scrollHeight = appContainer.scrollHeight;
      clientHeight = appContainer.clientHeight;
    } else {
      scrollTop = window.pageYOffset || html.scrollTop || body.scrollTop || 0;
      scrollHeight = Math.max(html.scrollHeight, body.scrollHeight, html.offsetHeight, body.offsetHeight);
      clientHeight = window.innerHeight || html.clientHeight || body.clientHeight;
    }

    // Проверяем, доскроллили ли до конца (более агрессивно - 50% от высоты экрана)
    const distanceToBottom = scrollHeight - scrollTop - clientHeight;
    const threshold = clientHeight * 0.5; // 50% от высоты экрана

    const shouldLoad = distanceToBottom < threshold;

    console.error('📏 Проверка скролла:', {
      scrollTop,
      scrollHeight,
      clientHeight,
      distanceToBottom,
      threshold,
      shouldLoad,
      displayedItems: displayedItems.length,
      allItems: allItems.length
    });

    return shouldLoad;
  }, [allItems.length, displayedItems.length]);

  // Настройка Intersection Observer для бесконечной прокрутки
  useEffect(() => {
    // Не настраиваем, если нет товаров или все уже показаны
    if (allItems.length === 0 || displayedItems.length === 0) {
      return;
    }

    // Если все товары уже показаны и их меньше чем itemsPerPage * 2, не нужен observer
    if (displayedItems.length >= allItems.length && allItems.length < itemsPerPage * 2) {
      return;
    }

    // Очищаем предыдущий observer
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }

    let isSetup = false;

    const setupObserver = () => {
      if (isSetup) return;
      
      const target = observerTargetRef.current;
      if (!target) {
        // Повторяем попытку
        setTimeout(setupObserver, 200);
        return;
      }

      isSetup = true;

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const now = Date.now();
              // Защита от частых вызовов
              if (now - lastLoadTriggerRef.current > 1000 && !isLoadingMore) {
                lastLoadTriggerRef.current = now;
                loadMoreItems();
              }
            }
          });
        },
        {
          root: null, // viewport
          rootMargin: '0px', // Без отступа - срабатывает когда элемент появляется
          threshold: 0.1 // Срабатывает когда 10% элемента видно
        }
      );

      try {
        observer.observe(target);
        observerRef.current = observer;
      } catch (error) {
        console.error('Ошибка настройки IntersectionObserver:', error);
      }
    };

    // Настраиваем observer после рендера
    const timeoutId = setTimeout(setupObserver, 500);

    // Запасной вариант: обработчик скролла
    let scrollTimeout;
    const handleScroll = () => {
      if (isLoadingMore) return;
      
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        const html = document.documentElement;
        const scrollTop = window.pageYOffset || html.scrollTop || 0;
        const scrollHeight = Math.max(
          html.scrollHeight || 0,
          document.body.scrollHeight || 0
        );
        const clientHeight = window.innerHeight || html.clientHeight || 0;
        const distanceToBottom = scrollHeight - scrollTop - clientHeight;

        // Если до конца меньше 200px, загружаем
        if (distanceToBottom < 200) {
          const now = Date.now();
          if (now - lastLoadTriggerRef.current > 1000) {
            lastLoadTriggerRef.current = now;
            loadMoreItems();
          }
        }
      }, 150);
    };

    // Добавляем обработчики
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('wheel', handleScroll, { passive: true });
    
    const appContainer = document.querySelector('.app');
    if (appContainer) {
      appContainer.addEventListener('scroll', handleScroll, { passive: true });
    }

    return () => {
      isSetup = false;
      clearTimeout(timeoutId);
      clearTimeout(scrollTimeout);
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('wheel', handleScroll);
      if (appContainer) {
        appContainer.removeEventListener('scroll', handleScroll);
      }
    };
  }, [displayedItems.length, allItems.length, isLoadingMore, loadMoreItems]);

  const handleItemClick = (item) => {
    setSelectedItem(item);
    
    // Отправляем impression ТОЛЬКО при открытии детального просмотра
    if (window.brandItemsService) {
      window.brandItemsService.trackImpression(item.id, telegramId);
    }
  };

  const handleItemDetailBack = () => {
    setSelectedItem(null);
  };

  if (loading) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="loading-spinner"></div>
          <p>Загружаем товары...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="error-content">
          <h2>Ошибка</h2>
          <p>{error}</p>
          <button className="btn-secondary" onClick={loadBrandItems}>
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  // Если выбран товар - показываем детальный просмотр (как в гардеробе)
  if (selectedItem) {
    return (
      <ShopItemDetail
        item={selectedItem}
        telegramId={telegramId}
        onBack={handleItemDetailBack}
      />
    );
  }

  // Иначе показываем список товаров
  return (
    <div className="card" ref={scrollContainerRef}>
      <div className="wardrobe-header" style={{ marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600' }}>Магазин</h2>
      </div>

      {/* Сетка товаров (точно как в гардеробе) */}
      <div className="wardrobe-grid">
        {displayedItems.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--input-text)', padding: '1rem' }}>
            Нет товаров для отображения
          </div>
        ) : (
          displayedItems.map((item, index) => (
            <div 
              key={`${item.id}-${index}`} 
              className="wardrobe-grid-item"
              onClick={() => handleItemClick(item)}
            >
              <div className="wardrobe-item-icon">
                {item.image_url ? (
                  <img 
                    src={item.image_url}
                    alt={item.description}
                    onError={(e) => {
                      if (e.target.src.includes('.png')) {
                        e.target.src = e.target.src.replace('.png', '.jpg');
                      } else {
                        e.target.style.display = 'none';
                      }
                    }}
                  />
                ) : (
                  <div className="wardrobe-item-placeholder" aria-label="no image">
                    <ShoppingBag size={20} />
                  </div>
                )}
              </div>
              {/* Убрали подпись категории в превью */}
            </div>
          ))
        )}
        
        {/* Индикатор загрузки */}
        {isLoadingMore && (
          <div style={{ 
            gridColumn: '1 / -1', 
            textAlign: 'center', 
            padding: '2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <LoadingSpinner size="small" />
            <p style={{ 
              margin: 0, 
              color: 'var(--color-text-light)', 
              fontSize: '0.875rem' 
            }}>
              Загружаем еще товары...
            </p>
          </div>
        )}
        
        {/* Пустые карточки-спейсеры для предотвращения перекрытия навигацией */}
        <div className="wardrobe-spacer"></div>
      </div>
      
      {/* Элемент-триггер для Intersection Observer - ВНЕ grid для надежности */}
      {displayedItems.length > 0 && displayedItems.length < allItems.length && (
        <div 
          ref={observerTargetRef}
          style={{ 
            width: '100%',
            height: '50px',
            marginTop: '2rem',
            marginBottom: '2rem',
            position: 'relative',
            backgroundColor: 'transparent',
            pointerEvents: 'none'
          }}
          data-observer-target="true"
          aria-hidden="true"
        />
      )}
    </div>
  );
};

export default ShopPage;

