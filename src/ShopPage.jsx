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
    // Используем функциональное обновление для проверки состояния
    setIsLoadingMore(current => {
      // Защита от повторных вызовов
      if (current) {
        return current;
      }
      
      if (allItems.length === 0) {
        return current;
      }

      // Устанавливаем флаг загрузки
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
      
      return true; // Устанавливаем isLoadingMore в true
    });
  }, [allItems, shuffleArray, itemsPerPage]);

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
    // Не настраиваем, если нет товаров
    if (allItems.length === 0 || displayedItems.length === 0) {
      return;
    }

    // Очищаем предыдущий observer
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }

    const setupObserver = () => {
      const target = observerTargetRef.current;
      if (!target) {
        // Повторяем попытку максимум 20 раз
        const retryCount = setupObserver.retryCount || 0;
        if (retryCount < 20) {
          setupObserver.retryCount = retryCount + 1;
          setTimeout(setupObserver, 100);
        }
        return;
      }

      // Определяем root для IntersectionObserver - это элемент, который скроллится
      const appContainer = document.querySelector('.app');
      const html = document.documentElement;
      const body = document.body;
      
      // Проверяем, какой элемент скроллится
      const appScrollHeight = appContainer ? appContainer.scrollHeight : 0;
      const appClientHeight = appContainer ? appContainer.clientHeight : 0;
      const htmlScrollHeight = html.scrollHeight || 0;
      const htmlClientHeight = html.clientHeight || window.innerHeight || 0;
      
      let scrollRoot = null;
      if (appContainer && appScrollHeight > appClientHeight) {
        scrollRoot = appContainer;
      } else if (htmlScrollHeight > htmlClientHeight) {
        scrollRoot = null; // viewport
      }

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const now = Date.now();
              // Защита от частых вызовов
              if (now - lastLoadTriggerRef.current > 500) {
                lastLoadTriggerRef.current = now;
                // Вызываем loadMoreItems напрямую - он сам проверит isLoadingMore
                loadMoreItems();
              }
            }
          });
        },
        {
          root: scrollRoot, // Используем .app как root, если он скроллится
          rootMargin: '500px', // Увеличиваем для более раннего срабатывания
          threshold: 0
        }
      );

      try {
        observer.observe(target);
        observerRef.current = observer;
      } catch (error) {
        console.error('Ошибка настройки IntersectionObserver:', error);
      }
      
      // Тестовая проверка - вызываем loadMoreItems вручную через 3 секунды для теста
      setTimeout(() => {
        console.error('🧪 ТЕСТ: Проверка состояния через 3 сек:', {
          displayedItems: displayedItems.length,
          allItems: allItems.length,
          isLoadingMore: isLoadingMore,
          targetExists: !!observerTargetRef.current,
          targetVisible: observerTargetRef.current ? observerTargetRef.current.offsetHeight > 0 : false
        });
        if (displayedItems.length < allItems.length) {
          console.error('🧪 ТЕСТ: Принудительный вызов loadMoreItems');
          loadMoreItems();
        } else if (allItems.length > 0) {
          console.error('🧪 ТЕСТ: Все товары показаны, но вызываем loadMoreItems для перемешивания');
          loadMoreItems(); // Вызываем даже если все показаны - для перемешивания
        } else {
          console.error('🧪 ТЕСТ: Нет товаров для загрузки');
        }
      }, 3000);
    };
    setupObserver.retryCount = 0;

    // Настраиваем observer после рендера
    const timeoutId = setTimeout(setupObserver, 500);

    // Запасной вариант: обработчик скролла
    let scrollTimeout;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        // Определяем, какой элемент скроллится
        const appContainer = document.querySelector('.app');
        let scrollTop = 0;
        let scrollHeight = 0;
        let clientHeight = 0;
        
        if (appContainer && appContainer.scrollHeight > appContainer.clientHeight) {
          // Скролл на .app
          scrollTop = appContainer.scrollTop;
          scrollHeight = appContainer.scrollHeight;
          clientHeight = appContainer.clientHeight;
        } else {
          // Скролл на window
          const html = document.documentElement;
          scrollTop = window.pageYOffset || html.scrollTop || 0;
          scrollHeight = Math.max(
            html.scrollHeight || 0,
            document.body.scrollHeight || 0
          );
          clientHeight = window.innerHeight || html.clientHeight || 0;
        }
        
        const distanceToBottom = scrollHeight - scrollTop - clientHeight;

        // Если до конца меньше 500px, загружаем
        if (distanceToBottom < 500) {
          const now = Date.now();
          if (now - lastLoadTriggerRef.current > 500) {
            lastLoadTriggerRef.current = now;
            loadMoreItems();
          }
        }
      }, 100);
    };

    // Добавляем обработчики на все возможные элементы
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('wheel', handleScroll, { passive: true });
    
    const appContainer = document.querySelector('.app');
    if (appContainer) {
      appContainer.addEventListener('scroll', handleScroll, { passive: true });
    }

    return () => {
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
  }, [displayedItems.length, allItems.length, loadMoreItems]);

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
  console.error('🎨 ShopPage РЕНДЕР:', {
    allItems: allItems.length,
    displayedItems: displayedItems.length,
    loading,
    error
  });
  
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
      {/* Рендерим всегда, если есть товары, даже если все уже показаны */}
      {allItems.length > 0 && (
        <div 
          ref={observerTargetRef}
          style={{ 
            width: '100%',
            minHeight: '200px',
            height: '200px',
            marginTop: '3rem',
            marginBottom: '3rem',
            position: 'relative',
            backgroundColor: 'rgba(255, 0, 0, 0.15)', // Более яркий красный фон
            pointerEvents: 'none',
            border: '4px solid red', // Толстая красная рамка
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000, // Максимальный z-index
            boxSizing: 'border-box'
          }}
          data-observer-target="true"
        >
          {/* Временный маркер для отладки */}
          <div style={{
            fontSize: '20px',
            color: 'red',
            fontWeight: 'bold',
            textAlign: 'center',
            padding: '1.5rem',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(255,0,0,0.5)',
            border: '2px solid red'
          }}>
            🔴 ТРИГГЕР ЗАГРУЗКИ 🔴
            <br />
            <span style={{ fontSize: '14px', color: '#666', display: 'block', marginTop: '0.5rem' }}>
              Показано: {displayedItems.length} / Всего: {allItems.length}
            </span>
            {displayedItems.length >= allItems.length && (
              <span style={{ fontSize: '12px', color: 'orange', display: 'block', marginTop: '0.5rem' }}>
                Все товары показаны - будет перемешивание
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ShopPage;

