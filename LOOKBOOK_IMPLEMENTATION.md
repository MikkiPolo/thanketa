# 📸 Реализация Lookbook (как в Alta)

## Анализ UI из Alta

### Что видно на скриншотах:
1. **Masonry grid** - изображения разной высоты в колонках
2. **Full-screen просмотр** - при клике изображение на весь экран
3. **UI overlay элементы:**
   - Внизу слева: карточка с иконкой обуви + число (количество похожих вещей)
   - Иконка закладки + число (количество сохранений)
   - Внизу справа: кнопка "Avatar" (теги/профили)
4. **Интерактивность** - можно кликать на элементы образа

---

## Реализация для GLAMORA

### 1. Установка библиотеки

```bash
npm install react-masonry-css
```

### 2. Структура базы данных (Supabase)

```sql
-- Таблица для lookbook образов
CREATE TABLE lookbook_images (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  image_url TEXT NOT NULL,
  title TEXT,
  description TEXT,
  style_tags TEXT[], -- ['casual', 'business', 'evening', 'street']
  season TEXT, -- 'Осень', 'Зима', 'Весна', 'Лето'
  temperature_range TEXT, -- '15-25'
  items JSONB, -- [{category: 'top', color: 'black', brand: '...', item_id: '...'}]
  brand_id UUID,
  is_approved BOOLEAN DEFAULT false,
  likes_count INTEGER DEFAULT 0,
  saves_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица для сохраненных образов пользователями
CREATE TABLE lookbook_favorites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  telegram_id TEXT NOT NULL,
  lookbook_image_id UUID REFERENCES lookbook_images(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(telegram_id, lookbook_image_id)
);

-- Индексы
CREATE INDEX idx_lookbook_style_tags ON lookbook_images USING GIN(style_tags);
CREATE INDEX idx_lookbook_season ON lookbook_images(season);
CREATE INDEX idx_lookbook_approved ON lookbook_images(is_approved);
CREATE INDEX idx_lookbook_favorites_user ON lookbook_favorites(telegram_id);
```

### 3. Компонент LookbookPage.jsx

```jsx
import React, { useState, useEffect } from 'react';
import Masonry from 'react-masonry-css';
import { Bookmark, Heart, X, Search, Filter } from 'lucide-react';
import './LookbookPage.css';

const LookbookPage = ({ telegramId, onBack }) => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(null);
  const [favorites, setFavorites] = useState(new Set());
  const [filter, setFilter] = useState({ style: null, season: null });

  // Breakpoints для masonry grid (как в Alta - 2 колонки на мобильных)
  const breakpointColumnsObj = {
    default: 2,
    768: 2,
    480: 1
  };

  useEffect(() => {
    loadLookbookImages();
    loadFavorites();
  }, [telegramId, filter]);

  const loadLookbookImages = async () => {
    try {
      setLoading(true);
      // Запрос к вашему API или Supabase
      const response = await fetch(`/api/lookbook?style=${filter.style || ''}&season=${filter.season || ''}`);
      const data = await response.json();
      setImages(data.images || []);
    } catch (error) {
      console.error('Ошибка загрузки lookbook:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    if (!telegramId) return;
    try {
      const response = await fetch(`/api/lookbook/favorites?telegram_id=${telegramId}`);
      const data = await response.json();
      setFavorites(new Set(data.favorite_ids || []));
    } catch (error) {
      console.error('Ошибка загрузки избранного:', error);
    }
  };

  const handleImageClick = (image) => {
    setSelectedImage(image);
  };

  const handleFavorite = async (imageId) => {
    if (!telegramId) return;
    
    const isFavorite = favorites.has(imageId);
    try {
      if (isFavorite) {
        await fetch(`/api/lookbook/favorites`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ telegram_id: telegramId, lookbook_image_id: imageId })
        });
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(imageId);
          return newSet;
        });
      } else {
        await fetch(`/api/lookbook/favorites`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ telegram_id: telegramId, lookbook_image_id: imageId })
        });
        setFavorites(prev => new Set([...prev, imageId]));
      }
    } catch (error) {
      console.error('Ошибка сохранения:', error);
    }
  };

  const handleFindSimilar = async (image) => {
    // Интеграция с AI для поиска похожих вещей в гардеробе
    // Открыть модальное окно с результатами
    console.log('Поиск похожих вещей для образа:', image.id);
  };

  if (loading) {
    return <div className="loading-spinner">Загрузка...</div>;
  }

  return (
    <div className="lookbook-page">
      {/* Header */}
      <div className="lookbook-header">
        <h1>Вдохновение</h1>
        <button className="close-btn" onClick={onBack}>
          <X size={24} />
        </button>
      </div>

      {/* Filters */}
      <div className="lookbook-filters">
        <button 
          className={`filter-btn ${filter.style === 'casual' ? 'active' : ''}`}
          onClick={() => setFilter({...filter, style: filter.style === 'casual' ? null : 'casual'})}
        >
          Casual
        </button>
        <button 
          className={`filter-btn ${filter.style === 'business' ? 'active' : ''}`}
          onClick={() => setFilter({...filter, style: filter.style === 'business' ? null : 'business'})}
        >
          Business
        </button>
        <button 
          className={`filter-btn ${filter.season === 'Осень' ? 'active' : ''}`}
          onClick={() => setFilter({...filter, season: filter.season === 'Осень' ? null : 'Осень'})}
        >
          Осень
        </button>
      </div>

      {/* Masonry Grid */}
      <Masonry
        breakpointCols={breakpointColumnsObj}
        className="lookbook-masonry-grid"
        columnClassName="lookbook-masonry-column"
      >
        {images.map((image) => (
          <div 
            key={image.id} 
            className="lookbook-item"
            onClick={() => handleImageClick(image)}
          >
            <img src={image.image_url} alt={image.title || 'Look'} />
            
            {/* Overlay при наведении */}
            <div className="lookbook-overlay">
              <div className="lookbook-stats">
                <div className="lookbook-stat-item">
                  <Heart size={16} />
                  <span>{image.likes_count || 0}</span>
                </div>
                <div className="lookbook-stat-item">
                  <Bookmark size={16} />
                  <span>{image.saves_count || 0}</span>
                </div>
              </div>
            </div>

            {/* Bottom overlay (как в Alta) */}
            <div className="lookbook-bottom-overlay">
              {/* Карточка с похожими вещами */}
              <div className="lookbook-similar-card" onClick={(e) => {
                e.stopPropagation();
                handleFindSimilar(image);
              }}>
                <div className="lookbook-similar-icon">👢</div>
                <span className="lookbook-similar-count">{image.similar_items_count || 0}</span>
              </div>

              {/* Иконка сохранения */}
              <button 
                className={`lookbook-favorite-btn ${favorites.has(image.id) ? 'active' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  handleFavorite(image.id);
                }}
              >
                <Bookmark size={20} fill={favorites.has(image.id) ? 'currentColor' : 'none'} />
                <span>{image.saves_count || 0}</span>
              </button>
            </div>
          </div>
        ))}
      </Masonry>

      {/* Full-screen modal (как в Alta) */}
      {selectedImage && (
        <div className="lookbook-modal" onClick={() => setSelectedImage(null)}>
          <div className="lookbook-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="lookbook-modal-close" onClick={() => setSelectedImage(null)}>
              <X size={24} />
            </button>
            
            <img src={selectedImage.image_url} alt={selectedImage.title} />
            
            {/* UI элементы поверх изображения (как в Alta) */}
            <div className="lookbook-modal-overlay">
              <div className="lookbook-modal-similar">
                <div className="lookbook-modal-similar-icon">👢</div>
                <span>{selectedImage.similar_items_count || 0}</span>
                <button onClick={() => handleFindSimilar(selectedImage)}>
                  Найти похожее
                </button>
              </div>
              
              <div className="lookbook-modal-actions">
                <button 
                  className={`lookbook-modal-favorite ${favorites.has(selectedImage.id) ? 'active' : ''}`}
                  onClick={() => handleFavorite(selectedImage.id)}
                >
                  <Bookmark size={24} fill={favorites.has(selectedImage.id) ? 'currentColor' : 'none'} />
                  <span>{selectedImage.saves_count || 0}</span>
                </button>
              </div>
            </div>

            {/* Информация об образе */}
            <div className="lookbook-modal-info">
              <h3>{selectedImage.title}</h3>
              <p>{selectedImage.description}</p>
              <div className="lookbook-modal-tags">
                {selectedImage.style_tags?.map(tag => (
                  <span key={tag} className="lookbook-tag">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LookbookPage;
```

### 4. Стили LookbookPage.css

```css
/* Lookbook Page */
.lookbook-page {
  padding: 1rem;
  padding-bottom: calc(var(--bottom-gap) + 1rem);
  background: var(--background-main);
  min-height: 100vh;
}

.lookbook-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
}

.lookbook-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-primary);
  padding: 0.5rem;
}

/* Filters */
.lookbook-filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  color: var(--color-text-primary);
  border-radius: 20px;
  cursor: pointer;
  white-space: nowrap;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.filter-btn.active {
  background: var(--button-bg);
  color: var(--button-text);
  border-color: var(--button-bg);
}

/* Masonry Grid */
.lookbook-masonry-grid {
  display: flex;
  width: 100%;
  gap: 0.5rem;
}

.lookbook-masonry-column {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Lookbook Item */
.lookbook-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: var(--card-bg);
  box-shadow: 0 2px 8px var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s;
}

.lookbook-item:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px var(--shadow);
}

.lookbook-item img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: cover;
}

/* Overlay при наведении */
.lookbook-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, transparent 30%);
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.lookbook-item:hover .lookbook-overlay {
  opacity: 1;
}

.lookbook-stats {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  display: flex;
  gap: 0.5rem;
}

.lookbook-stat-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: rgba(255, 255, 255, 0.9);
  padding: 0.25rem 0.5rem;
  border-radius: 20px;
  font-size: 0.75rem;
  color: var(--color-text-primary);
}

/* Bottom Overlay (как в Alta) */
.lookbook-bottom-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0.75rem;
  background: linear-gradient(to top, rgba(0,0,0,0.5) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.2s;
}

.lookbook-item:hover .lookbook-bottom-overlay {
  opacity: 1;
}

/* Карточка с похожими вещами (как в Alta - внизу слева) */
.lookbook-similar-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.lookbook-similar-card:hover {
  transform: scale(1.05);
}

.lookbook-similar-icon {
  font-size: 1.25rem;
}

.lookbook-similar-count {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 0.875rem;
}

/* Кнопка сохранения (как в Alta - внизу справа) */
.lookbook-favorite-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  color: var(--color-text-primary);
  transition: all 0.2s;
}

.lookbook-favorite-btn.active {
  color: #FF6B6B;
}

.lookbook-favorite-btn span {
  font-size: 0.875rem;
  font-weight: 600;
}

/* Full-screen Modal (как в Alta) */
.lookbook-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.95);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
}

.lookbook-modal-content {
  position: relative;
  width: 100%;
  max-width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.lookbook-modal-content img {
  width: 100%;
  height: auto;
  object-fit: contain;
  flex: 1;
}

.lookbook-modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1001;
  color: var(--color-text-primary);
}

/* UI элементы поверх модального изображения (как в Alta) */
.lookbook-modal-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 1rem;
  background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 100%);
}

.lookbook-modal-similar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.95);
  padding: 0.75rem 1rem;
  border-radius: 12px;
  cursor: pointer;
}

.lookbook-modal-similar-icon {
  font-size: 1.5rem;
}

.lookbook-modal-similar span {
  font-weight: 600;
  font-size: 1rem;
}

.lookbook-modal-similar button {
  margin-left: 0.5rem;
  padding: 0.25rem 0.75rem;
  background: var(--button-bg);
  color: var(--button-text);
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
}

.lookbook-modal-actions {
  display: flex;
  gap: 0.5rem;
}

.lookbook-modal-favorite {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  cursor: pointer;
  color: var(--color-text-primary);
  font-size: 1rem;
  font-weight: 600;
}

.lookbook-modal-favorite.active {
  color: #FF6B6B;
}

/* Информация об образе */
.lookbook-modal-info {
  background: var(--card-bg);
  padding: 1.5rem;
  color: var(--color-text-primary);
}

.lookbook-modal-info h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.lookbook-modal-info p {
  color: var(--color-text-light);
  margin-bottom: 1rem;
  line-height: 1.5;
}

.lookbook-modal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.lookbook-tag {
  padding: 0.25rem 0.75rem;
  background: var(--hint-bg);
  color: var(--color-text-primary);
  border-radius: 12px;
  font-size: 0.875rem;
}

/* Loading */
.loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  color: var(--color-text-light);
}
```

### 5. Backend API endpoints (backend/app.py)

```python
@app.route('/api/lookbook', methods=['GET'])
def get_lookbook_images():
    """Получение lookbook образов с фильтрами"""
    try:
        style = request.args.get('style')
        season = request.args.get('season')
        
        # Запрос к Supabase
        query = supabase.table('lookbook_images').select('*').eq('is_approved', True)
        
        if style:
            query = query.contains('style_tags', [style])
        if season:
            query = query.eq('season', season)
        
        response = query.order('created_at', desc=True).limit(50).execute()
        
        return jsonify({
            'images': response.data,
            'count': len(response.data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lookbook/favorites', methods=['POST', 'DELETE'])
def manage_lookbook_favorites():
    """Добавление/удаление избранного"""
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        lookbook_image_id = data.get('lookbook_image_id')
        
        if request.method == 'POST':
            # Добавить в избранное
            supabase.table('lookbook_favorites').insert({
                'telegram_id': telegram_id,
                'lookbook_image_id': lookbook_image_id
            }).execute()
            
            # Увеличить счетчик
            supabase.table('lookbook_images').update({
                'saves_count': supabase.rpc('increment', {'x': 1})
            }).eq('id', lookbook_image_id).execute()
            
        elif request.method == 'DELETE':
            # Удалить из избранного
            supabase.table('lookbook_favorites').delete().eq(
                'telegram_id', telegram_id
            ).eq('lookbook_image_id', lookbook_image_id).execute()
            
            # Уменьшить счетчик
            supabase.table('lookbook_images').update({
                'saves_count': supabase.rpc('decrement', {'x': 1})
            }).eq('id', lookbook_image_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lookbook/<image_id>/similar', methods=['GET'])
def find_similar_items(image_id):
    """Поиск похожих вещей в гардеробе пользователя"""
    try:
        telegram_id = request.args.get('telegram_id')
        
        # Получить образ
        image = supabase.table('lookbook_images').select('*').eq('id', image_id).single().execute()
        
        # AI анализ образа и поиск похожих вещей
        # (интеграция с вашим AI)
        
        return jsonify({
            'similar_items': [],
            'missing_items': []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Интеграция в навигацию

Добавить в `BottomNavigation.jsx`:

```jsx
const navItems = [
  // ... существующие
  {
    id: 'lookbook',
    label: 'Вдохновение',
    icon: Sparkles, // или другая иконка
    isSpecial: false
  }
];
```

И в `App.jsx`:

```jsx
{currentPage === 'lookbook' && (
  <LookbookPage 
    telegramId={existingProfile?.telegram_id}
    onBack={() => setCurrentPage('home')}
  />
)}
```

---

## Источники контента

### Вариант 1: Автогенерация из товаров брендов
- Использовать товары из `brand_items`
- Создавать коллажи автоматически
- Показывать как "Готовые образы"

### Вариант 2: Партнерские lookbook
- Бренды предоставляют фото
- Загружаются в Supabase
- Модерация через админ-панель

### Вариант 3: Пользовательский контент
- Пользователи загружают свои образы
- AI модерация или ручная
- Сообщество вдохновляющих образов

---

## Следующие шаги

1. ✅ Установить `react-masonry-css`
2. ✅ Создать таблицы в Supabase
3. ✅ Создать компонент `LookbookPage.jsx`
4. ✅ Добавить стили
5. ✅ Реализовать API endpoints
6. ✅ Интегрировать в навигацию
7. ✅ Добавить источник контента (автогенерация или партнеры)

Готово! Теперь у вас будет lookbook как в Alta! 🎨

