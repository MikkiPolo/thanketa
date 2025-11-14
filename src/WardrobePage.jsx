import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Camera, Plus } from 'lucide-react';
import { wardrobeService } from './supabase';
import WardrobeStats from './WardrobeStats';
import AddWardrobeItem from './AddWardrobeItem';
import WardrobeItemDetail from './WardrobeItemDetail';
import LoadingSpinner from './LoadingSpinner';
import NotificationModal from './NotificationModal';



const WardrobePage = ({ telegramId, access, onBack, profile }) => {
  const [wardrobe, setWardrobe] = useState([]);
  const [filteredWardrobe, setFilteredWardrobe] = useState([]);
  const [editingRow, setEditingRow] = useState(null);
  const [editedData, setEditedData] = useState({});
  const [loading, setLoading] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [notification, setNotification] = useState({ isVisible: false, type: 'success', title: '', message: '' });

  const cardRef = useRef(null);
  const hasFetched = useRef(false);

  const fetchWardrobe = useCallback(async () => {
    // Защита от повторных запросов
    if (loading) return;
    
    setLoading(true);
    setWardrobe([]);
    try {
      const data = await wardrobeService.getWardrobe(telegramId);
      const cleaned = data.filter(item => item && item.id);
      setWardrobe(cleaned);
      setFilteredWardrobe(cleaned);
      setTimeout(() => {
        if (cardRef.current) {
          cardRef.current.scrollTop = 0;
        }
      }, 100);
    } catch (error) {
      console.error('Error fetching wardrobe:', error);
      setWardrobe([]);
      setFilteredWardrobe([]);
    } finally {
      setLoading(false);
    }
  }, [telegramId, loading]);

// Удалён бесполезный useEffect со скроллом

useEffect(() => {
  if (!hasFetched.current && telegramId && (access === 'full' || access === 'demo')) {
    hasFetched.current = true;
    fetchWardrobe();
  }
}, [telegramId, access, fetchWardrobe]); // Добавляем fetchWardrobe в зависимости

// Слушаем событие для открытия модального окна добавления
useEffect(() => {
  const handleOpenAddModal = () => {
    setShowAddModal(true);
  };

  window.addEventListener('openAddModal', handleOpenAddModal);

  return () => {
    window.removeEventListener('openAddModal', handleOpenAddModal);
  };
}, []);


  const handleEdit = (id, item) => {
    setEditingRow(id);
    setEditedData(item);
  };

  const handleChange = (field, value) => {
    setEditedData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async (row) => {
    try {
      await wardrobeService.updateItem(row.id, {
        ...editedData,
        telegram_id: row.telegram_id,
      });
      setWardrobe(prev =>
        prev.map(item => item.id === row.id ? { ...item, ...editedData } : item)
      );
      setFilteredWardrobe(prev =>
        prev.map(item => item.id === row.id ? { ...item, ...editedData } : item)
      );
      setEditingRow(null);
      setEditedData({});
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  const handleDelete = async (id) => {
  const confirmed = window.confirm("Точно хотите удалить эту вещь?");
  if (!confirmed) return;

  try {
    await wardrobeService.deleteItem(id);
    fetchWardrobe();
    if (editingRow === id) {
      setEditingRow(null);
      setEditedData({});
    }
  } catch (err) {
    console.error("Ошибка при удалении:", err);
  }
};

  const handleCategoryFilter = (category) => {
    if (!category) {
      setFilteredWardrobe(wardrobe);
    } else {
      const filtered = wardrobe.filter(item => item.category === category);
      setFilteredWardrobe(filtered);
    }
  };

  const handleImageUpload = async (images) => {
    // Здесь можно добавить логику для сохранения изображений
    
    // Пока что просто показываем уведомление
    alert('Функция загрузки изображений в разработке');
  };

  const handleAddItem = () => {
    // Ограничение для demo: максимум 20 вещей
    if (access === 'demo' && wardrobe.length >= 20) {
      showNotification('error', '', 'В демо-режиме можно добавить не более 20 вещей');
      return;
    }
    setShowAddModal(true);
  };

  const showNotification = (type, title, message) => {
    setNotification({ isVisible: true, type, title, message });
    // Авто-скрытие через 2 секунды
    window.clearTimeout(showNotification._t);
    showNotification._t = window.setTimeout(() => {
      setNotification({ isVisible: false, type: 'success', title: '', message: '' });
    }, 2000);
  };

  const hideNotification = () => {
    setNotification({ isVisible: false, type: 'success', title: '', message: '' });
  };

  const handleItemAdded = (newItem) => {
    setWardrobe(prev => [newItem, ...prev]);
    setFilteredWardrobe(prev => [newItem, ...prev]);
    showNotification('success', '', 'Вещь успешно добавлена в гардероб!');
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
  };

  const handleItemClick = (item) => {
    setSelectedItem(item);
  };

  const handleItemDetailBack = () => {
    setSelectedItem(null);
  };

  const handleItemUpdated = (updatedItem) => {
    setWardrobe(prev => prev.map(item => item.id === updatedItem.id ? updatedItem : item));
    setFilteredWardrobe(prev => prev.map(item => item.id === updatedItem.id ? updatedItem : item));
    setSelectedItem(updatedItem);
  };

  const handleItemDeleted = (itemId) => {
    setWardrobe(prev => prev.filter(item => item.id !== itemId));
    setFilteredWardrobe(prev => prev.filter(item => item.id !== itemId));
    setSelectedItem(null);
  };

  // Если выбрана детальная страница, показываем только её
  if (selectedItem) {
    return (
      <WardrobeItemDetail
        item={selectedItem}
        telegramId={telegramId}
        onBack={handleItemDetailBack}
        onItemUpdated={handleItemUpdated}
        onItemDeleted={handleItemDeleted}
      />
    );
  }

  // Иначе показываем список гардероба
  return (
    <div className="app">
      <div className="card" style={{ paddingTop: "calc(env(safe-area-inset-top) + 4rem)" }}>
        <div className="wardrobe-header" style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
          <h2 style={{ margin: 0, color: 'var(--color-text-primary)', marginBottom: '1rem' }}>Гардероб</h2>
        </div>
        <div className="wardrobe-buttons">
          <button 
            className="btn-primary wardrobe-add-btn" 
            onClick={handleAddItem}
            aria-label="Добавить"
          >
            +
          </button>
          <button 
            className="btn-secondary" 
            onClick={() => setShowStats(!showStats)}
          >
            Статистика
          </button>
          <button className="btn-secondary" onClick={onBack}>Назад</button>
        </div>

        {showStats && (
          <WardrobeStats 
            wardrobe={wardrobe}
            profile={profile}
          />
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <LoadingSpinner size="large" color="var(--color-accent)" />
            <p style={{ marginTop: '1rem', color: 'var(--color-text-primary)' }}>
              Загрузка гардероба...
            </p>
          </div>
        ) : (
          <div className="wardrobe-grid" ref={cardRef}>
            {filteredWardrobe.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--input-text)', padding: '1rem' }}>
                {wardrobe.length === 0 ? 'Гардероб пуст' : 'Ничего не найдено'}
              </div>
            ) : (
              <>
                {filteredWardrobe
                .filter(item => item && item.id && item.category)
                .map(item => (
                  <div 
                    key={item.id} 
                    className="wardrobe-grid-item"
                    onClick={() => handleItemClick(item)}
                  >
                    <div className="wardrobe-item-icon">
                      {item.image_id ? (
                        <img 
                          src={wardrobeService.getImageUrl(telegramId, item.image_id)}
                          alt={item.description}
                          onError={(e) => {
                            if (e.target.src.includes('.png')) {
                              const jpgUrl = e.target.src.replace('.png', '.jpg');
                              e.target.src = jpgUrl;
                            } else {
                              e.target.style.display = 'none';
                            }
                          }}
                        />
                      ) : (
                        <div className="wardrobe-item-placeholder" aria-label="no image">
                          <Camera size={20} />
                        </div>
                      )}
                    </div>
                    <div className="wardrobe-item-category">
                      {item.category}
                    </div>
                  </div>
                ))}
                {/* Пустые карточки-спейсеры для предотвращения перекрытия навигацией */}
                <div className="wardrobe-spacer"></div>
                <div className="wardrobe-spacer"></div>
              </>
            )}
          </div>
        )}

        {showAddModal && (
          <AddWardrobeItem
            telegramId={telegramId}
            onItemAdded={handleItemAdded}
            onClose={handleCloseAddModal}
          />
        )}

        {/* Уведомления */}
        <NotificationModal
          isVisible={notification.isVisible}
          type={notification.type}
          title={notification.title}
          message={notification.message}
          onClose={hideNotification}
        />
      </div>
    </div>
  );
}
export default WardrobePage;