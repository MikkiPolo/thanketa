import React from 'react';

const openTelegramLink = (url) => {
  try {
    if (window?.Telegram?.WebApp?.openTelegramLink) {
      window.Telegram.WebApp.openTelegramLink(url);
    } else {
      window.open(url, '_blank');
    }
  } catch (e) {
    window.open(url, '_blank');
  }
};

const ProfileMenuModal = ({ isOpen, telegramId, onViewProfile, onClose }) => {
  if (!isOpen) return null;

  const supportUrl = `https://t.me/glamorasupportbot${telegramId ? `?start=uid_${telegramId}` : ''}`;
  const feedbackUrl = `https://t.me/glamorafeedbackbot${telegramId ? `?start=uid_${telegramId}` : ''}`;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Профиль</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button className="btn-primary" onClick={() => { onViewProfile(); onClose(); }}>
            Просмотреть профиль
          </button>

          <button className="btn-secondary" onClick={() => openTelegramLink(supportUrl)}>
            Обратиться в поддержку
          </button>

          <button className="btn-secondary" onClick={() => openTelegramLink(feedbackUrl)}>
            Оставить отзыв
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileMenuModal;


