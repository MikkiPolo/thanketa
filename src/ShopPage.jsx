import React, { useState, useEffect } from 'react';
import { ShoppingBag } from 'lucide-react';
import ShopItemDetail from './ShopItemDetail';

const ShopPage = ({ telegramId, season = 'Осень', temperature = 15.0, onBack }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [error, setError] = useState(null);

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

      setItems(brandItems);
    } catch (err) {
      console.error('Ошибка загрузки товаров брендов:', err);
      setError('Не удалось загрузить товары. Попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

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
    <div className="card">
      <div className="wardrobe-header" style={{ marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600' }}>Магазин</h2>
      </div>

      {/* Сетка товаров (точно как в гардеробе) */}
      <div className="wardrobe-grid">
        {items.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--input-text)', padding: '1rem' }}>
            Нет товаров для отображения
          </div>
        ) : (
          items.map((item) => (
            <div 
              key={item.id} 
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
        {/* Пустые карточки-спейсеры для предотвращения перекрытия навигацией */}
        <div className="wardrobe-spacer"></div>
      </div>
    </div>
  );
};

export default ShopPage;

