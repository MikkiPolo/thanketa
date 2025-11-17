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
    if (isLoadingMore) {
      console.error('⏸️ Подгрузка пропущена: уже идет загрузка');
      return;
    }
    
    if (allItems.length === 0) {
      console.error('⏸️ Подгрузка пропущена: нет товаров');
      return;
    }

    console.error('🚀 Начинаем подгрузку товаров');

    setIsLoadingMore(true);

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
          // Исключаем уже показанные товары
          const remainingItems = shuffled.filter(item => 
            !prev.some(displayed => displayed.id === item.id)
          );
          
          // Если осталось мало товаров, добавляем перемешанные заново
          const nextBatch = remainingItems.length >= itemsPerPage 
            ? remainingItems.slice(0, itemsPerPage)
            : [...remainingItems, ...shuffled.slice(0, itemsPerPage - remainingItems.length)];
          
          console.error('📦 Добавляем новую порцию:', nextBatch.length, 'товаров');
          const newItems = [...prev, ...nextBatch];
          console.error('✅ Всего товаров теперь:', newItems.length);
          setIsLoadingMore(false);
          return newItems;
        }
      });
    }, 300);
  }, [allItems, isLoadingMore, shuffleArray, itemsPerPage]);

  // Используем Intersection Observer для отслеживания конца списка
  const observerTargetRef = useRef(null);
  const observerRef = useRef(null);
  const lastLoadTriggerRef = useRef(0);

  // Настройка Intersection Observer для бесконечной прокрутки
  useEffect(() => {
    // Очищаем предыдущий observer
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }

    if (allItems.length === 0) {
      console.error('⏸️ Observer не настроен: нет товаров');
      return;
    }

    // Ждем, пока элемент-триггер появится в DOM
    const setupObserver = () => {
      if (!observerTargetRef.current) {
        console.error('⏸️ Элемент-триггер еще не в DOM, повторяем через 100ms');
        setTimeout(setupObserver, 100);
        return;
      }

      console.error('👁️ Настраиваем Intersection Observer:', {
        displayedItems: displayedItems.length,
        allItems: allItems.length,
        hasTarget: !!observerTargetRef.current
      });

      const observer = new IntersectionObserver(
        (entries) => {
          const entry = entries[0];
          const now = Date.now();
          
          // Защита от частых срабатываний (минимум 500ms между вызовами)
          if (now - lastLoadTriggerRef.current < 500) {
            console.error('⏸️ Слишком часто, пропускаем');
            return;
          }

          console.error('👀 Intersection Observer событие:', {
            isIntersecting: entry.isIntersecting,
            isLoadingMore,
            displayedItems: displayedItems.length,
            allItems: allItems.length,
            intersectionRatio: entry.intersectionRatio,
            boundingClientRect: entry.boundingClientRect
          });
          
          if (entry.isIntersecting && !isLoadingMore) {
            lastLoadTriggerRef.current = now;
            console.error('🔄 Триггер подгрузки: элемент виден, загружаем еще товары');
            loadMoreItems();
          }
        },
        {
          root: null, // viewport
          rootMargin: '400px', // Начинаем загрузку за 400px до конца
          threshold: [0, 0.1, 0.5, 1.0] // Несколько порогов для надежности
        }
      );

      observer.observe(observerTargetRef.current);
      observerRef.current = observer;
      console.error('✅ Observer настроен и наблюдает за элементом');
    };

    setupObserver();

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
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
        
        {/* Элемент-триггер для Intersection Observer - всегда должен быть в конце */}
        <div 
          ref={observerTargetRef}
          style={{ 
            gridColumn: '1 / -1', 
            height: '100px', 
            width: '100%',
            marginTop: '2rem',
            position: 'relative'
          }}
          data-observer-target="true"
        >
          {/* Видимый маркер для отладки (можно убрать потом) */}
          <div style={{ 
            height: '2px', 
            width: '100%',
            background: 'transparent',
            position: 'absolute',
            top: '50%'
          }} />
        </div>
        
        {/* Пустые карточки-спейсеры для предотвращения перекрытия навигацией */}
        <div className="wardrobe-spacer"></div>
      </div>
    </div>
  );
};

export default ShopPage;

