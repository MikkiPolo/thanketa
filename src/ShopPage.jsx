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

      setAllItems(brandItems);
      // Показываем первую порцию товаров
      setDisplayedItems(brandItems.slice(0, itemsPerPage));
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
    if (isLoadingMore || allItems.length === 0) return;

    setIsLoadingMore(true);

    // Небольшая задержка для плавности
    setTimeout(() => {
      if (displayedItems.length >= allItems.length) {
        // Все товары показаны - перемешиваем и начинаем заново
        const shuffled = shuffleArray(allItems);
        setDisplayedItems([...displayedItems, ...shuffled.slice(0, itemsPerPage)]);
      } else {
        // Показываем следующую порцию из перемешанного списка
        const shuffled = shuffleArray(allItems);
        // Исключаем уже показанные товары
        const remainingItems = shuffled.filter(item => 
          !displayedItems.some(displayed => displayed.id === item.id)
        );
        
        // Если осталось мало товаров, добавляем перемешанные заново
        const nextBatch = remainingItems.length >= itemsPerPage 
          ? remainingItems.slice(0, itemsPerPage)
          : [...remainingItems, ...shuffled.slice(0, itemsPerPage - remainingItems.length)];
        
        setDisplayedItems([...displayedItems, ...nextBatch]);
      }
      setIsLoadingMore(false);
    }, 300);
  }, [allItems, displayedItems, isLoadingMore, shuffleArray]);

  // Обработчик скролла для бесконечной прокрутки
  const handleScroll = useCallback(() => {
    // Ищем элемент с классом .app, который является скроллируемым контейнером
    const appContainer = document.querySelector('.app');
    if (!appContainer) return;

    const scrollTop = appContainer.scrollTop || window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = appContainer.scrollHeight || document.documentElement.scrollHeight;
    const clientHeight = appContainer.clientHeight || window.innerHeight;

    // Если доскроллили до 80% от конца
    if (scrollHeight - scrollTop - clientHeight < clientHeight * 0.2) {
      loadMoreItems();
    }
  }, [loadMoreItems]);

  // Добавляем обработчик скролла к window и .app контейнеру
  useEffect(() => {
    const appContainer = document.querySelector('.app');
    
    const handleScrollEvent = () => {
      handleScroll();
    };
    
    // Добавляем обработчик на window (для мобильных) и на .app (для десктопа)
    window.addEventListener('scroll', handleScrollEvent, { passive: true });
    if (appContainer) {
      appContainer.addEventListener('scroll', handleScrollEvent, { passive: true });
    }
    
    return () => {
      window.removeEventListener('scroll', handleScrollEvent);
      if (appContainer) {
        appContainer.removeEventListener('scroll', handleScrollEvent);
      }
    };
  }, [handleScroll]);

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
    </div>
  );
};

export default ShopPage;

