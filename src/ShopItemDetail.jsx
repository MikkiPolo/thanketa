import React, { useState } from 'react';
import { ArrowLeft, ExternalLink, Plus } from 'lucide-react';
import { wardrobeService } from './supabase';
import { backendService } from './backendService';

const ShopItemDetail = ({ item, telegramId, onBack }) => {
  const [isAddingToWardrobe, setIsAddingToWardrobe] = useState(false);
  const [addError, setAddError] = useState(null);
  const [addSuccess, setAddSuccess] = useState(false);

  if (!item) return null;

  const handleShopLinkClick = () => {
    if (!item.shop_link) return;

    // Отправляем click
    if (window.brandItemsService) {
      window.brandItemsService.trackClick(item.id, telegramId);
    }

    // Открываем ссылку
    try {
      if (window?.Telegram?.WebApp?.openLink) {
        window.Telegram.WebApp.openLink(item.shop_link);
      } else {
        window.open(item.shop_link, '_blank', 'noopener,noreferrer');
      }
    } catch (error) {
      console.error('Ошибка открытия ссылки:', error);
      window.open(item.shop_link, '_blank', 'noopener,noreferrer');
    }
  };

  // Функция для скачивания изображения по URL
  const downloadImage = async (url) => {
    try {
      // Пробуем скачать через fetch с CORS
      let response;
      try {
        response = await fetch(url, {
          mode: 'cors',
          credentials: 'omit',
          cache: 'no-cache'
        });
      } catch (corsError) {
        // Если CORS не работает, пробуем через proxy или canvas
        // CORS error, trying alternative method
        
        // Альтернативный метод через canvas (работает для изображений с того же домена или без CORS)
        return new Promise((resolve, reject) => {
          const img = new Image();
          img.crossOrigin = 'anonymous';
          
          img.onload = () => {
            try {
              const canvas = document.createElement('canvas');
              canvas.width = img.width;
              canvas.height = img.height;
              const ctx = canvas.getContext('2d');
              ctx.drawImage(img, 0, 0);
              
              canvas.toBlob((blob) => {
                if (blob) {
                  resolve(blob);
                } else {
                  reject(new Error('Не удалось конвертировать изображение'));
                }
              }, 'image/png');
            } catch (canvasError) {
              reject(new Error('Ошибка обработки изображения: ' + canvasError.message));
            }
          };
          
          img.onerror = () => {
            reject(new Error('Не удалось загрузить изображение. Возможна проблема с CORS или доступом к изображению.'));
          };
          
          img.src = url;
        });
      }
      
      if (!response || !response.ok) {
        throw new Error(`HTTP error! status: ${response?.status || 'unknown'}`);
      }
      
      const blob = await response.blob();
      return blob;
    } catch (error) {
      console.error('Ошибка скачивания изображения:', error);
      throw new Error(error.message || 'Не удалось загрузить изображение. Проверьте подключение к интернету.');
    }
  };

  // Функция добавления товара в гардероб
  const handleAddToWardrobe = async () => {
    if (!telegramId || telegramId === 'default') {
      setAddError('Не удалось определить пользователя. Попробуйте перезагрузить страницу.');
      return;
    }

    if (!item.image_url) {
      setAddError('У товара отсутствует изображение.');
      return;
    }

    setIsAddingToWardrobe(true);
    setAddError(null);
    setAddSuccess(false);

    try {
      // Начинаем добавление товара в гардероб

      // 1. Скачиваем изображение
      const imageBlob = await downloadImage(item.image_url);

      // 2. Сжимаем изображение
      console.log('🗜️ Сжимаем изображение...');
      const compressedBlob = await backendService.aggressiveCompressImage(imageBlob);
      console.log('✅ Изображение сжато, размер:', compressedBlob.size, 'bytes');

      // 3. Генерируем UUID для изображения
      const imageId = crypto.randomUUID();

      // 4. Загружаем изображение в Supabase Storage
      console.log('☁️ Загружаем изображение в Supabase Storage...');
      await wardrobeService.uploadImage(telegramId, imageId, compressedBlob);
      console.log('✅ Изображение загружено в Storage');

      // 5. Сохраняем данные вещи в базу данных
      const wardrobeItem = {
        telegram_id: telegramId,
        category: item.category || 'другое',
        season: item.season || 'Всесезонно',
        description: item.description || `${item.brand_name || 'Товар'} из магазина`,
        image_id: imageId,
        ai_generated: false // Товар из магазина, не AI-генерированный
      };

      console.log('💾 Сохраняем данные в базу:', wardrobeItem);
      const newItem = await wardrobeService.addItem(wardrobeItem);
      console.log('✅ Товар успешно добавлен в гардероб:', newItem);

      setAddSuccess(true);
      
      // Показываем уведомление
      setTimeout(() => {
        alert('Товар успешно добавлен в гардероб!');
        setAddSuccess(false);
      }, 100);

    } catch (error) {
      console.error('❌ Ошибка добавления в гардероб:', error);
      
      let errorMessage = 'Ошибка при добавлении в гардероб. Попробуйте еще раз.';
      
      if (error.message?.includes('Не удалось загрузить изображение')) {
        errorMessage = 'Не удалось загрузить изображение. Проверьте подключение к интернету.';
      } else if (error.message?.includes('Файл слишком большой')) {
        errorMessage = 'Изображение слишком большое. Попробуйте другой товар.';
      } else if (error.message?.includes('Ошибка сети')) {
        errorMessage = 'Ошибка сети. Проверьте подключение к интернету.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setAddError(errorMessage);
    } finally {
      setIsAddingToWardrobe(false);
    }
  };

  return (
    <div className="card" style={{ paddingTop: 'calc(env(safe-area-inset-top) + 1rem)' }}>
      {/* Кнопка назад */}
      <button 
        onClick={onBack}
        className="back-btn"
        style={{
          position: 'absolute',
          top: 'calc(env(safe-area-inset-top) + 1rem)',
          left: '1rem',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          color: 'var(--color-text-primary)',
          fontSize: '1rem',
          zIndex: 10
        }}
      >
        <ArrowLeft size={24} />
        <span>Назад</span>
      </button>

      <div style={{ padding: '3rem 1rem 1rem' }}>
        {/* Бренд */}
        <h2 style={{ 
          fontSize: '1.5rem', 
          fontWeight: '600', 
          marginBottom: '1rem',
          textAlign: 'center'
        }}>
          {item.brand_name || 'Магазин'}
        </h2>

        {/* Изображение */}
        {item.image_url && (
          <div style={{
            width: '100%',
            maxHeight: '400px',
            background: '#f5f5f5',
            borderRadius: '12px',
            overflow: 'hidden',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <img
              src={item.image_url}
              alt={item.description}
              style={{
                width: '100%',
                maxHeight: '400px',
                objectFit: 'contain'
              }}
              onError={(e) => {
                if (e.target.src.includes('.png')) {
                  e.target.src = e.target.src.replace('.png', '.jpg');
                }
              }}
            />
          </div>
        )}

        {/* Информация о товаре */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ 
            fontSize: '0.9rem', 
            color: '#999', 
            marginBottom: '0.5rem',
            display: 'flex',
            gap: '8px',
            flexWrap: 'wrap'
          }}>
            <span>{item.category}</span>
            {item.season && <span>• {item.season}</span>}
          </div>
          
          <div style={{ 
            fontSize: '1rem', 
            lineHeight: '1.6', 
            marginBottom: '1rem',
            color: 'var(--color-text-primary)'
          }}>
            {item.description}
          </div>

          {item.price && (
            <div style={{ 
              fontSize: '1.3rem', 
              fontWeight: '600', 
              marginBottom: '1.5rem',
              color: 'var(--color-text-primary)'
            }}>
              {item.price} {item.currency || 'RUB'}
            </div>
          )}
        </div>

        {/* Сообщения об ошибках и успехе */}
        {addError && (
          <div style={{
            padding: '12px',
            background: '#fee',
            color: '#c33',
            borderRadius: '8px',
            marginBottom: '1rem',
            fontSize: '0.9rem'
          }}>
            {addError}
          </div>
        )}

        {addSuccess && (
          <div style={{
            padding: '12px',
            background: '#efe',
            color: '#3c3',
            borderRadius: '8px',
            marginBottom: '1rem',
            fontSize: '0.9rem'
          }}>
            Товар успешно добавлен в гардероб!
          </div>
        )}

        {/* Кнопки действий */}
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '12px',
          marginBottom: 'calc(80px + 2rem)'
        }}>
          {/* Кнопка добавления в гардероб */}
          <button
            className={addSuccess ? "btn-secondary" : "btn-primary"}
            onClick={handleAddToWardrobe}
            disabled={isAddingToWardrobe || addSuccess}
            style={{
              width: '100%',
              padding: '16px',
              fontSize: '1.1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              opacity: isAddingToWardrobe ? 0.6 : 1,
              cursor: isAddingToWardrobe ? 'not-allowed' : 'pointer'
            }}
          >
            {isAddingToWardrobe ? (
              <>
                <span className="loading-spinner" style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid currentColor',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                  display: 'inline-block'
                }}></span>
                Добавляем...
              </>
            ) : addSuccess ? (
              <>
                ✓ Добавлено в гардероб
              </>
            ) : (
              <>
                <Plus size={22} />
                Добавить в гардероб
              </>
            )}
          </button>

          {/* Кнопка перехода в магазин */}
          {item.shop_link && (
            <button
              className="btn-secondary"
              onClick={handleShopLinkClick}
              style={{
                width: '100%',
                padding: '16px',
                fontSize: '1.1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px'
              }}
            >
              <ExternalLink size={22} />
              Перейти в магазин
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShopItemDetail;

