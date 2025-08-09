import React, { useState, useEffect } from 'react';
import telegramWebApp from './telegramWebApp';

const TelegramIdDebugger = ({ onTelegramIdSet }) => {
  const [debugInfo, setDebugInfo] = useState({});
  const [testId, setTestId] = useState('');

  useEffect(() => {
    // Собираем информацию о доступных способах получения Telegram ID
    const info = {
      webAppAvailable: telegramWebApp.isAvailable,
      urlParams: new URLSearchParams(window.location.search).get('tg_id'),
      localStorageId: localStorage.getItem('test_telegram_id'),
      userAgent: navigator.userAgent,
      isTelegramWebView: navigator.userAgent.includes('TelegramWebApp'),
      webAppUser: telegramWebApp.getUserData(),
      webAppId: telegramWebApp.getTelegramId()
    };

    setDebugInfo(info);
  }, []);

  const handleSetTestId = () => {
    if (testId) {
      localStorage.setItem('test_telegram_id', testId);
      onTelegramIdSet(testId);
      setDebugInfo(prev => ({ ...prev, localStorageId: testId }));
    }
  };

  const handleClearTestId = () => {
    localStorage.removeItem('test_telegram_id');
    setTestId('');
    setDebugInfo(prev => ({ ...prev, localStorageId: null }));
  };

  const handleInitWebApp = () => {
    if (telegramWebApp.isAvailable) {
      telegramWebApp.init();
      const userData = telegramWebApp.getUserData();
      const id = telegramWebApp.getTelegramId();
      setDebugInfo(prev => ({ 
        ...prev, 
        webAppUser: userData,
        webAppId: id 
      }));
      if (id) {
        onTelegramIdSet(id);
      }
    }
  };

  return (
    <div style={{ 
      padding: '1rem', 
      backgroundColor: '#f5f5f5', 
      borderRadius: '8px',
      margin: '1rem 0',
      fontFamily: 'monospace',
      fontSize: '12px'
    }}>
      <h3>🔍 Telegram ID Debugger</h3>
      
      <div style={{ marginBottom: '1rem' }}>
        <strong>Web App API:</strong>
        <div>Доступен: {debugInfo.webAppAvailable ? '✅' : '❌'}</div>
        <div>Telegram ID: {debugInfo.webAppId || 'Не найден'}</div>
        <div>Пользователь: {debugInfo.webAppUser ? JSON.stringify(debugInfo.webAppUser, null, 2) : 'Не найден'}</div>
        <button 
          onClick={handleInitWebApp}
          disabled={!debugInfo.webAppAvailable}
          style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem' }}
        >
          Инициализировать Web App
        </button>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <strong>URL параметры:</strong>
        <div>tg_id: {debugInfo.urlParams || 'Не найден'}</div>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <strong>LocalStorage (тест):</strong>
        <div>test_telegram_id: {debugInfo.localStorageId || 'Не найден'}</div>
        <div style={{ marginTop: '0.5rem' }}>
          <input
            type="text"
            value={testId}
            onChange={(e) => setTestId(e.target.value)}
            placeholder="Введите Telegram ID для тестирования"
            style={{ width: '200px', marginRight: '0.5rem' }}
          />
          <button onClick={handleSetTestId} style={{ marginRight: '0.5rem' }}>
            Установить
          </button>
          <button onClick={handleClearTestId}>
            Очистить
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <strong>Информация о браузере:</strong>
        <div>User Agent: {debugInfo.userAgent}</div>
        <div>Telegram WebView: {debugInfo.isTelegramWebView ? '✅' : '❌'}</div>
      </div>

      <div>
        <strong>Рекомендации:</strong>
        <ul style={{ margin: '0.5rem 0', paddingLeft: '1rem' }}>
          <li>Для продакшена используйте Telegram Web App API</li>
          <li>Для тестирования используйте localStorage</li>
          <li>URL параметры - запасной вариант</li>
        </ul>
      </div>
    </div>
  );
};

export default TelegramIdDebugger; 