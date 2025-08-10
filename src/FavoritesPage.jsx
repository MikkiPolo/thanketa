import React, { useState, useEffect } from 'react';
import { Heart, Trash2, ArrowLeft } from 'lucide-react';
import { favoritesService } from './supabase';
import CapsulePage from './CapsulePage';
import NotificationModal from './NotificationModal';

const FavoritesPage = ({ telegramId, showNotification }) => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCapsule, setSelectedCapsule] = useState(null);
  const [notification, setNotification] = useState({ isVisible: false, type: 'success', title: '', message: '' });

  useEffect(() => {
    if (telegramId) {
      loadFavorites();
    }
  }, [telegramId]);

  const loadFavorites = async () => {
    try {
      setLoading(true);
      const favoritesData = await favoritesService.getFavorites(telegramId);
      
      // Форматируем данные для отображения
      const formattedFavorites = favoritesData.map(fav => ({
        id: fav.capsule_id,
        name: fav.capsule_name,
        description: fav.capsule_description,
        items: (fav.capsule_data?.items || []).map(item => ({
          ...item,
          imageUrl: item.image_id ? `https://lipolo.store/storage/v1/object/public/wardrobe-images/${telegramId}/${item.image_id}.png` : null
        })),
        category: fav.capsule_category,
        addedAt: fav.created_at
      }));
      
      setFavorites(formattedFavorites);
    } catch (error) {
      console.error('Ошибка загрузки избранного:', error);
    } finally {
      setLoading(false);
    }
  };

  const showLocalNotification = (type, title, message) => {
    setNotification({ isVisible: true, type, title, message });
  };

  const hideNotification = () => {
    setNotification({ isVisible: false, type: 'success', title: '', message: '' });
  };



  // Если выбрана капсула для детального просмотра, показываем CapsulePage
  if (selectedCapsule) {
    return (
      <CapsulePage 
        profile={{ telegram_id: telegramId }}
        onBack={() => setSelectedCapsule(null)}
        initialCapsule={selectedCapsule}
        isFavoritesView={true}
      />
    );
  }

  if (loading) {
    return (
      <div className="app favorites-page">
        <div className="card">
          <div className="loading-content">
            <h2>Загрузка избранного...</h2>
          </div>
        </div>
      </div>
    );
  }

  // Фильтруем только капсулы с предметами
  const validFavorites = favorites.filter(favorite => 
    favorite.items && favorite.items.length > 0
  );

  if (validFavorites.length === 0) {
    return (
      <div className="app favorites-page">
        <div className="card">
          <div className="empty-favorites">
            <h2>Избранное пусто</h2>
            <p>Добавьте капсулы в избранное, чтобы они появились здесь</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app favorites-page">
      <div className="card">
        <div className="item-detail-header">
          <h2>Избранное</h2>
        </div>
        
        <div className="capsules-grid">
          {validFavorites.map((favorite) => {
            // Приоритезированный выбор предметов как в CapsulePage
            const toLower = (s) => (s || '').toLowerCase();
            const topSet = new Set(['блузка','футболка','рубашка','свитер','топ','джемпер','кофта','водолазка']);
            const bottomSet = new Set(['юбка','брюки','джинсы','шорты','легинсы','леггинсы']);
            const dressSet = new Set(['платье','сарафан']);
            const shoesSet = new Set(['обувь','туфли','ботинки','кроссовки','сапоги','сандалии','мокасины','балетки']);
            const accSet = new Set(['сумка','аксессуары','украшения','пояс','шарф','часы','очки','серьги','колье','браслет','рюкзак']);
            const outerSet = new Set(['пиджак','куртка','пальто','кардиган','жакет','жилет']);

            const items = (favorite.items || []).filter(Boolean);
            const capacity = items.length >= 5 ? 9 : 4;
            const dresses = [], tops = [], bottoms = [], shoes = [], accessories = [], outerwear = [], rest = [];
            items.forEach(it => {
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
            if (dresses.length) { tryPush(dresses); } else { tryPush(tops); tryPush(bottoms); }
            tryPush(shoes); tryPush(accessories); tryPush(outerwear);
            const pools = [dresses, tops, bottoms, shoes, accessories, outerwear, rest];
            for (const p of pools) { while (picked.length < capacity && p.length) picked.push(p.shift()); if (picked.length>=capacity) break; }
            const moreCount = items.length - picked.length;
            const grid3 = picked.length > 4;

            return (
              <div 
                key={favorite.id} 
                className="capsule-card"
                onClick={() => setSelectedCapsule(favorite)}
              >
                <div className={`capsule-canvas-preview grid ${picked.length > 6 ? 'grid-3' : ''}`}>
                  {picked.map((item, index) => (
                    <div key={index} className="capsule-canvas-item">
                      {item.imageUrl && item.imageUrl !== 'null' && (
                        <img 
                          src={item.imageUrl} 
                          alt={item.description}
                          onError={(e) => { if (e.target.src.includes('.png')) { e.target.src = e.target.src.replace('.png', '.jpg'); } }}
                        />
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
        </div>
      </div>
      
      {/* Уведомления */}
      <NotificationModal
        isVisible={notification.isVisible}
        type={notification.type}
        title={notification.title}
        message={notification.message}
        onClose={hideNotification}
      />
    </div>
  );
};

export default FavoritesPage; 