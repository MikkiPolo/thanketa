import React from 'react';
import { ArrowLeft, ExternalLink } from 'lucide-react';

const ShopItemDetail = ({ item, telegramId, onBack }) => {
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

        {/* Кнопка перехода в магазин */}
        {item.shop_link && (
          <button
            className="btn-primary"
            onClick={handleShopLinkClick}
            style={{
              width: '100%',
              padding: '16px',
              fontSize: '1.1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              marginBottom: 'calc(80px + 2rem)'  // Увеличили отступ для навигационного меню
            }}
          >
            <ExternalLink size={22} />
            Перейти в магазин
          </button>
        )}
      </div>
    </div>
  );
};

export default ShopItemDetail;

