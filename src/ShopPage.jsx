import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { ShoppingBag, Search, X } from 'lucide-react';
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
  const [searchQuery, setSearchQuery] = useState(''); // Поисковый запрос
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
      // Показываем первую порцию товаров (если нет поиска)
      if (!searchQuery.trim()) {
        const firstBatch = brandItems.slice(0, itemsPerPage);
        console.error('👁️ ShopPage: Показываем первую порцию:', firstBatch.length, 'товаров из', brandItems.length);
        setDisplayedItems(firstBatch);
      } else {
        // Если есть поиск, фильтруем товары
        filterAndDisplayItems(brandItems, searchQuery);
      }
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

  // Фильтрация товаров по поисковому запросу
  const filterItems = useCallback((items, query) => {
    if (!query || !query.trim()) {
      return items;
    }
    
    const searchLower = query.toLowerCase().trim();
    return items.filter(item => {
      // Ищем в описании товара
      const description = (item.description || '').toLowerCase();
      // Также можно искать в категории и названии бренда
      const category = (item.category || '').toLowerCase();
      const brandName = (item.brand_name || '').toLowerCase();
      
      return description.includes(searchLower) || 
             category.includes(searchLower) || 
             brandName.includes(searchLower);
    });
  }, []);

  // Фильтрация и отображение товаров при поиске
  const filterAndDisplayItems = useCallback((items, query) => {
    const filtered = filterItems(items, query);
    setDisplayedItems(filtered);
  }, [filterItems]);

  // Мемоизация отфильтрованных товаров
  const filteredItems = useMemo(() => {
    return filterItems(allItems, searchQuery);
  }, [allItems, searchQuery, filterItems]);

  // Эффект для обновления отображаемых товаров при изменении поиска
  useEffect(() => {
    if (searchQuery.trim()) {
      // Режим поиска - показываем все отфильтрованные товары
      filterAndDisplayItems(allItems, searchQuery);
    } else {
      // Обычный режим - показываем первую порцию
      if (allItems.length > 0) {
        const firstBatch = allItems.slice(0, itemsPerPage);
        setDisplayedItems(firstBatch);
      }
    }
  }, [searchQuery, allItems, filterAndDisplayItems, itemsPerPage]);

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
  const hasScrolledRef = useRef(false); // Флаг, что пользователь хотя бы раз скроллил

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
    // Не настраиваем, если нет товаров или активен поиск
    if (allItems.length === 0 || displayedItems.length === 0 || searchQuery.trim()) {
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
              // Загружаем только если пользователь уже скроллил
              // Это предотвращает автоматическую загрузку при первой загрузке страницы
              if (!hasScrolledRef.current) {
                return;
              }
              
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
          rootMargin: '300px', // Уменьшаем для более точного срабатывания только при скроллинге
          threshold: 0
        }
      );

      try {
        observer.observe(target);
        observerRef.current = observer;
      } catch (error) {
        console.error('Ошибка настройки IntersectionObserver:', error);
      }
    };
    setupObserver.retryCount = 0;

    // Настраиваем observer после рендера
    const timeoutId = setTimeout(setupObserver, 500);

    // Запасной вариант: обработчик скролла
    let scrollTimeout;
    const handleScroll = () => {
      // Отмечаем, что пользователь скроллит
      hasScrolledRef.current = true;
      
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
  
  return (
    <div className="card" ref={scrollContainerRef} style={{ position: 'relative' }}>
      <div className="wardrobe-header" style={{ marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600' }}>Магазин</h2>
      </div>

      {/* Поле поиска */}
      <div className="search-container" style={{ marginBottom: '1.5rem' }}>
        <div style={{ position: 'relative' }}>
          <Search 
            size={20} 
            style={{ 
              position: 'absolute', 
              left: '1rem', 
              top: '50%', 
              transform: 'translateY(-50%)',
              color: 'var(--color-text-light)',
              pointerEvents: 'none'
            }} 
          />
          <input
            type="text"
            className="search-input"
            placeholder="Поиск товаров (например: белая рубашка)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              paddingLeft: '3rem',
              paddingRight: searchQuery ? '3rem' : '1rem'
            }}
          />
          {searchQuery && (
            <button
              className="clear-search-btn"
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute',
                right: '0.5rem',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: 'var(--color-text-light)',
                cursor: 'pointer',
                padding: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              aria-label="Очистить поиск"
            >
              <X size={18} />
            </button>
          )}
        </div>
        {searchQuery.trim() && (
          <div style={{ 
            marginTop: '0.5rem', 
            fontSize: '0.875rem', 
            color: 'var(--color-text-light)',
            textAlign: 'center'
          }}>
            Найдено: {filteredItems.length} {filteredItems.length === 1 ? 'товар' : filteredItems.length < 5 ? 'товара' : 'товаров'}
          </div>
        )}
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
      {/* Показываем только если нет активного поиска */}
      {allItems.length > 0 && !searchQuery.trim() && (
        <div 
          ref={observerTargetRef}
          style={{ 
            width: '100%',
            height: '1px',
            marginTop: '2rem',
            marginBottom: '2rem',
            pointerEvents: 'none'
          }}
          data-observer-target="true"
        />
      )}
      
      {/* Сообщение, если поиск не дал результатов */}
      {searchQuery.trim() && displayedItems.length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          color: 'var(--color-text-light)', 
          padding: '3rem 1rem',
          fontSize: '1rem'
        }}>
          По запросу "{searchQuery}" ничего не найдено
          <br />
          <span style={{ fontSize: '0.875rem', marginTop: '0.5rem', display: 'block' }}>
            Попробуйте изменить поисковый запрос
          </span>
        </div>
      )}
    </div>
  );
};

export default ShopPage;

