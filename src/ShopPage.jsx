import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ShoppingBag } from 'lucide-react';
import ShopItemDetail from './ShopItemDetail';
import LoadingSpinner from './LoadingSpinner';

const ShopPage = ({ telegramId, season = 'Осень', temperature = 15.0, onBack }) => {
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

      console.error('📦 Загружено товаров:', brandItems.length);
      setAllItems(brandItems);
      // Показываем первую порцию товаров
      const firstBatch = brandItems.slice(0, itemsPerPage);
      console.error('👁️ Показываем первую порцию:', firstBatch.length, 'товаров');
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
    setIsLoadingMore(current => {
      if (current) {
        console.error('⏸️ Подгрузка пропущена: уже идет загрузка');
        return current;
      }
      
      if (allItems.length === 0) {
        console.error('⏸️ Подгрузка пропущена: нет товаров');
        return current;
      }

      console.error('🚀 Начинаем подгрузку товаров');

      // Небольшая задержка для плавности
      setTimeout(() => {
        setDisplayedItems(prev => {
          console.error('📊 Текущее состояние:', {
            displayed: prev.length,
            all: allItems.length
          });

          if (prev.length >= allItems.length) {
            // Все товары показаны - перемешиваем и начинаем заново
            console.error('🔄 Все товары показаны, перемешиваем заново');
            const shuffled = shuffleArray(allItems);
            const newItems = [...prev, ...shuffled.slice(0, itemsPerPage)];
            console.error('✅ Добавлено товаров:', newItems.length - prev.length, 'Всего:', newItems.length);
            setIsLoadingMore(false);
            return newItems;
          } else {
            // Показываем следующую порцию из перемешанного списка
            const shuffled = shuffleArray(allItems);
            
            // Получаем ID уже показанных товаров
            const shownIds = new Set(prev.map(item => item.id));
            
            // Исключаем уже показанные товары
            const remainingItems = shuffled.filter(item => !shownIds.has(item.id));
            
            // Если осталось мало товаров, перемешиваем все заново и берем любые
            let nextBatch;
            if (remainingItems.length >= itemsPerPage) {
              nextBatch = remainingItems.slice(0, itemsPerPage);
            } else if (remainingItems.length > 0) {
              // Добавляем оставшиеся + перемешанные из всех
              const additionalNeeded = itemsPerPage - remainingItems.length;
              const additional = shuffleArray(allItems).slice(0, additionalNeeded);
              nextBatch = [...remainingItems, ...additional];
            } else {
              // Все товары уже показаны - перемешиваем заново
              nextBatch = shuffled.slice(0, itemsPerPage);
            }
            
            console.error('📦 Добавляем новую порцию:', nextBatch.length, 'товаров');
            const newItems = [...prev, ...nextBatch];
            console.error('✅ Всего товаров теперь:', newItems.length);
            setIsLoadingMore(false);
            return newItems;
          }
        });
      }, 300);

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
    if (allItems.length === 0) {
      console.error('⏸️ Observer не настроен: нет товаров');
      return;
    }

    console.error('🔧 Настройка бесконечной прокрутки:', {
      displayedItems: displayedItems.length,
      allItems: allItems.length,
      isLoadingMore
    });

    // Очищаем предыдущий observer
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }

    // Ждем, пока элемент-триггер появится в DOM
    let retryCount = 0;
    const maxRetries = 20; // Максимум 2 секунды ожидания
    
    const setupObserver = () => {
      if (!observerTargetRef.current) {
        retryCount++;
        if (retryCount < maxRetries) {
          console.error(`⏸️ Элемент-триггер еще не в DOM (попытка ${retryCount}/${maxRetries}), повторяем через 100ms`);
          setTimeout(setupObserver, 100);
        } else {
          console.error('❌ Элемент-триггер не найден после всех попыток');
        }
        return;
      }

      console.error('👁️ Настраиваем Intersection Observer:', {
        displayedItems: displayedItems.length,
        allItems: allItems.length,
        hasTarget: !!observerTargetRef.current,
        targetElement: observerTargetRef.current
      });

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            const now = Date.now();
            
            // Защита от частых срабатываний (минимум 500ms между вызовами)
            if (now - lastLoadTriggerRef.current < 500) {
              return;
            }

      console.error('👀 Intersection Observer событие:', {
        isIntersecting: entry.isIntersecting,
        displayedItems: displayedItems.length,
        allItems: allItems.length,
        intersectionRatio: entry.intersectionRatio,
        boundingClientRect: {
          top: entry.boundingClientRect.top,
          bottom: entry.boundingClientRect.bottom,
          height: entry.boundingClientRect.height
        },
        rootBounds: entry.rootBounds ? {
          top: entry.rootBounds.top,
          bottom: entry.rootBounds.bottom,
          height: entry.rootBounds.height
        } : null
      });
            
            if (entry.isIntersecting) {
              // Проверяем isLoadingMore через функциональное обновление
              setIsLoadingMore(current => {
                if (current) return current; // Уже идет загрузка
                
                lastLoadTriggerRef.current = now;
                console.error('🔄 Триггер подгрузки (Observer): элемент виден, загружаем еще товары');
                loadMoreItems();
                
                return current;
              });
            }
          });
        },
        {
          root: null, // viewport
          rootMargin: '600px', // Начинаем загрузку за 600px до конца
          threshold: [0, 0.01, 0.1, 0.5, 1.0] // Несколько порогов
        }
      );

      try {
        observer.observe(observerTargetRef.current);
        observerRef.current = observer;
        console.error('✅ Observer настроен и наблюдает за элементом');
      } catch (error) {
        console.error('❌ Ошибка настройки Observer:', error);
      }
    };

    // Задержка для гарантии, что DOM обновлен
    setTimeout(setupObserver, 200);

    // Запасной вариант: обработчик скролла (более агрессивный)
    let scrollTimeout;
    const handleScroll = () => {
      // Throttle - проверяем не чаще раза в 100ms
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        // Проверяем isLoadingMore через функциональное обновление
        setIsLoadingMore(current => {
          if (current) return current; // Уже идет загрузка
          
          if (checkShouldLoadMore()) {
            const now = Date.now();
            if (now - lastLoadTriggerRef.current > 500) {
              lastLoadTriggerRef.current = now;
              console.error('🔄 Триггер подгрузки (Scroll): доскроллили до конца');
              loadMoreItems();
            }
          }
          
          return current;
        });
      }, 100);
    };

    // Добавляем обработчики на все возможные скроллируемые элементы
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('wheel', handleScroll, { passive: true });
    window.addEventListener('touchmove', handleScroll, { passive: true });
    
    const appContainer = document.querySelector('.app');
    if (appContainer) {
      appContainer.addEventListener('scroll', handleScroll, { passive: true });
    }

    // Также проверяем при изменении размера окна
    window.addEventListener('resize', handleScroll, { passive: true });

    return () => {
      clearTimeout(scrollTimeout);
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('wheel', handleScroll);
      window.removeEventListener('touchmove', handleScroll);
      window.removeEventListener('resize', handleScroll);
      if (appContainer) {
        appContainer.removeEventListener('scroll', handleScroll);
      }
    };
  }, [displayedItems.length, allItems.length, checkShouldLoadMore, loadMoreItems]);

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
        
        {/* Элемент-триггер для Intersection Observer - должен быть сразу после товаров */}
        {displayedItems.length > 0 && (
          <div 
            ref={observerTargetRef}
            style={{ 
              gridColumn: '1 / -1', 
              height: '100px', 
              width: '100%',
              marginTop: '2rem',
              marginBottom: '1rem',
              position: 'relative',
              backgroundColor: 'transparent',
              pointerEvents: 'none'
            }}
            data-observer-target="true"
          >
            {/* Невидимый маркер для отладки */}
            <div style={{ 
              height: '2px', 
              width: '100%',
              backgroundColor: 'transparent',
              position: 'absolute',
              top: '50%'
            }} />
          </div>
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
    </div>
  );
};

export default ShopPage;

