import React, { useState } from 'react';
import { wardrobeService } from './supabase';
import { ArrowLeft, Trash2 } from 'lucide-react';

const WardrobeItemDetail = ({ item, telegramId, onBack, onItemUpdated, onItemDeleted }) => {
  // Функция для нормализации текста (первая буква заглавная, остальные строчные)
  const normalizeText = (text) => {
    if (!text) return '';
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  };
  
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState({
    category: normalizeText(item.category || ''),
    season: normalizeText(item.season || ''),
    description: normalizeText(item.description || '')
  });
  const [isSuitable, setIsSuitable] = useState(item.is_suitable !== false);
  const [banProtected, setBanProtected] = useState(item.ban_protected === true);

  const handleChange = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    try {
      // Нормализуем текст перед сохранением
      const normalizedData = {
        category: normalizeText(editedData.category),
        season: normalizeText(editedData.season),
        description: normalizeText(editedData.description),
        telegram_id: telegramId,
      };

      await wardrobeService.updateItem(item.id, normalizedData);
      
      const updatedItem = { ...item, ...normalizedData };
      onItemUpdated(updatedItem);
      setIsEditing(false);
    } catch (error) {
      console.error('Save failed:', error);
      alert('Ошибка при сохранении');
    }
  };

  const handleDelete = async () => {
    const confirmed = window.confirm("Точно хотите удалить эту вещь?");
    if (!confirmed) return;

    try {
      await wardrobeService.deleteItem(item.id);
      onItemDeleted(item.id);
    } catch (err) {
      console.error("Ошибка при удалении:", err);
      alert('Ошибка при удалении');
    }
  };

  return (
    <div className="app">
      <div className="card">
        <div className="item-detail-header">
          <button className="btn-icon back-btn" onClick={onBack}>
            <ArrowLeft size={20} />
          </button>
        </div>

        <div className="item-detail-content">
          {/* Изображение */}
          {item.image_id && (
            <div className="item-detail-image">
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
            </div>
          )}

          {/* Характеристики */}
          <div className="item-detail-info">
            {isEditing ? (
              <>
                <div className="form-group">
                  <label>Категория:</label>
                  <input
                    type="text"
                    value={editedData.category}
                    onChange={e => handleChange('category', e.target.value)}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Сезонность:</label>
                  <input
                    type="text"
                    value={editedData.season}
                    onChange={e => handleChange('season', e.target.value)}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Описание:</label>
                  <textarea
                    value={editedData.description}
                    onChange={e => handleChange('description', e.target.value)}
                    className="form-textarea"
                    rows="4"
                  />
                </div>
              </>
            ) : (
              <>
                <div className="info-row">
                  <span className="info-label">Категория:</span>
                  <span className="info-value">{item.category || 'Не указано'}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Сезонность:</span>
                  <span className="info-value">{item.season || 'Не указано'}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Описание:</span>
                  <span className="info-value">{item.description || 'Не указано'}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Статус:</span>
                  <span className="info-value">{isSuitable ? 'Используется в капсулах' : 'Не используется в капсулах'}</span>
                </div>
                {!isSuitable && item.ban_reason && (
                  <div className="info-row">
                    <span className="info-label">Причина:</span>
                    <span className="info-value">{item.ban_reason}</span>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Кнопки */}
          <div className="item-detail-actions">
            {isEditing ? (
              <>
                <button
                  className="btn-primary"
                  onClick={handleSave}
                  disabled={!editedData.category || !editedData.season || !editedData.description}
                >
                  Сохранить
                </button>
                                            <button
                              className="btn-secondary"
                              onClick={() => {
                                setIsEditing(false);
                                setEditedData({
                                  category: normalizeText(item.category || ''),
                                  season: normalizeText(item.season || ''),
                                  description: normalizeText(item.description || '')
                                });
                              }}
                            >
                              Отмена
                            </button>
              </>
            ) : (
              <>
                {!isSuitable && (
                  <button
                    className="btn-secondary"
                    onClick={async () => {
                      try {
                        // Вернуть вещь из бана: включаем и защищаем от авто-бана
                        await wardrobeService.updateItem(item.id, { is_suitable: true, ban_protected: true });
                        setIsSuitable(true);
                        setBanProtected(true);
                        onItemUpdated({ ...item, is_suitable: true, ban_protected: true });
                      } catch (e) {
                        alert('Не удалось обновить статус вещи');
                      }
                    }}
                    title={'Вернуть'}
                  >
                    Вернуть
                  </button>
                )}
                <button
                  className="btn-primary"
                  onClick={() => setIsEditing(true)}
                >
                  Изменить
                </button>
                <button
                  className="btn-icon delete-btn"
                  onClick={handleDelete}
                  title="Удалить"
                >
                  <Trash2 size={20} />
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WardrobeItemDetail; 