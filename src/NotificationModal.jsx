import React from 'react';

const NotificationModal = ({ isVisible, type = 'success', title, message, onClose }) => {
  if (!isVisible) return null;

  return (
    <div className="notification-overlay">
      <div className="notification-content">
        <div className="notification-text">
          <p className="notification-message">{message}</p>
        </div>
        <button className="notification-close" onClick={onClose}>
          ×
        </button>
      </div>
    </div>
  );
};

export default NotificationModal; 