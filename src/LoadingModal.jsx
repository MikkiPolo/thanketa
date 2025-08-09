import React, { useState, useEffect } from 'react';

const LoadingModal = ({ isVisible, title = "Анализируем изображение...", subtitle = "ИИ изучает вашу вещь и определяет её характеристики" }) => {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  
  const analysisMessages = [
    "Анализируем изображение...",
    "Определяем тип одежды...",
    "Анализируем цветовую гамму...",
    "Определяем сезонность...",
    "Генерируем описание...",
    "Проверяем стилистику...",
    "Формируем рекомендации..."
  ];

  const savingMessages = [
    "Сохраняем вещь...",
    "Загружаем изображение...",
    "Обновляем гардероб...",
    "Проверяем данные..."
  ];

  const messages = title.includes("Анализируем") ? analysisMessages : savingMessages;

  useEffect(() => {
    if (!isVisible) {
      setCurrentMessageIndex(0);
      return;
    }

    const interval = setInterval(() => {
      setCurrentMessageIndex((prevIndex) => 
        prevIndex === messages.length - 1 ? 0 : prevIndex + 1
      );
    }, 2500); // Меняем каждые 2.5 секунды

    return () => clearInterval(interval);
  }, [isVisible, messages.length]);

  if (!isVisible) return null;

  return (
    <div className="loading-modal-overlay">
      <div className="loading-modal-content">
        <div className="siri-animation">
          <div className="siri-dot"></div>
          <div className="siri-dot"></div>
          <div className="siri-dot"></div>
        </div>
        <div className="loading-text">{messages[currentMessageIndex]}</div>
        <div className="loading-subtext">{subtitle}</div>
      </div>
    </div>
  );
};

export default LoadingModal; 