import React, { useState, useEffect } from 'react';
import { User, Save, X } from 'lucide-react';
import { supabase } from './supabase';
import telegramWebApp from './telegramWebApp';

const ProfilePage = ({ telegramId }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    loadProfile();
    applyWebModeStyles();
  }, [telegramId]);

  const applyWebModeStyles = () => {
    // Определяем, запущено ли приложение в Telegram WebApp
    const isTelegramWebApp = telegramWebApp.isAvailable;
    
    if (!isTelegramWebApp) {
      // Если это обычный веб-режим, добавляем специальные стили
      const profileContent = document.querySelector('.profile-content');
      if (profileContent) {
        profileContent.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 25rem)';
        profileContent.style.maxHeight = 'calc(100vh - 120px)';
      }
      
      const card = document.querySelector('.card');
      if (card) {
        card.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 4rem)';
      }
      
      // Добавляем обработчик для клавиатуры
      const handleResize = () => {
        const bottomNav = document.querySelector(".bottom-navigation");
        const app = document.querySelector(".app");
        const isKeyboardOpen = window.innerHeight < window.outerHeight * 0.8 || window.innerHeight < 600 || window.innerHeight < window.screen.height * 0.7;
        
        console.log('Window height:', window.innerHeight, 'Outer height:', window.outerHeight, 'Keyboard open:', isKeyboardOpen);
        
        if (isKeyboardOpen) {
          console.log('Hiding navigation and adjusting padding');
          if (bottomNav) {
            bottomNav.style.display = "none";
            console.log('Navigation hidden');
          }
          if (app) app.style.paddingBottom = "0";
          if (profileContent) {
            profileContent.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 35rem)';
            profileContent.style.maxHeight = 'calc(100vh - 60px)';
          }
          if (card) {
            card.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 8rem)';
          }
        } else {
          console.log('Showing navigation and normal padding');
          if (bottomNav) {
            bottomNav.style.display = "flex";
            console.log('Navigation shown');
          }
          if (app) app.style.paddingBottom = "";
          if (profileContent) {
            profileContent.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 25rem)';
            profileContent.style.maxHeight = 'calc(100vh - 120px)';
          }
          if (card) {
            card.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 4rem)';
          }
        }
      };
      
      window.addEventListener('resize', handleResize);
      
      // Добавляем обработчики для input полей
      const inputs = document.querySelectorAll("input, select, textarea");
      inputs.forEach(input => {
        input.addEventListener("focus", () => {
          console.log('Input focused, hiding navigation');
          const bottomNav = document.querySelector(".bottom-navigation");
          if (bottomNav) {
            bottomNav.style.display = "none";
            console.log('Navigation hidden on focus');
          }
          // Автоматическая прокрутка к полю
          setTimeout(() => {
            input.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center',
              inline: 'nearest'
            });
          }, 300);
          // Принудительно вызываем handleResize
          setTimeout(() => handleResize(), 100);
        });
        input.addEventListener("blur", () => {
          console.log('Input blurred, showing navigation');
          const bottomNav = document.querySelector(".bottom-navigation");
          if (bottomNav) {
            bottomNav.style.display = "flex";
            console.log('Navigation shown on blur');
          }
          // Принудительно вызываем handleResize
          setTimeout(() => handleResize(), 100);
        });
      });
      
      // Вызываем сразу для определения текущего состояния
      handleResize();
      
      // Очистка при размонтировании
      return () => window.removeEventListener('resize', handleResize);
    }
  };

  const loadProfile = async () => {
    if (!telegramId || telegramId === 'default') {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('user_profile')
        .select('*')
        .eq('telegram_id', telegramId)
        .single();

      if (error && error.code !== 'PGRST116') {
        console.error('Error loading profile:', error);
      }

      if (data) {
        setProfile(data);
        setFormData(data);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error loading profile:', error);
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!telegramId || telegramId === 'default') {
      console.error('No valid telegram ID for saving profile');
      return;
    }
    
    try {
      const { error } = await supabase
        .from('user_profile')
        .upsert({
          telegram_id: telegramId,
          ...formData
        });

      if (error) {
        console.error('Error saving profile:', error);
        return;
      }

      setProfile(formData);
      setEditing(false);
      // Показываем навигацию при сохранении
      const bottomNav = document.querySelector(".bottom-navigation");
      if (bottomNav && !telegramWebApp.isAvailable) {
        bottomNav.style.display = "flex";
        console.log('Navigation shown on save');
      }
    } catch (error) {
      console.error('Error saving profile:', error);
    }
  };

  const handleCancel = () => {
    setFormData(profile || {});
    setEditing(false);
    // Показываем навигацию при выходе из режима редактирования
    const bottomNav = document.querySelector(".bottom-navigation");
    if (bottomNav && !telegramWebApp.isAvailable) {
      bottomNav.style.display = "flex";
      console.log('Navigation shown on cancel edit');
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="app">
        <div className="card" style={{ paddingTop: "calc(env(safe-area-inset-top) + 4rem)" }}>
          <div className="loading-text">Загрузка профиля...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="card" style={{ paddingTop: "calc(env(safe-area-inset-top) + 4rem)" }}>
        <div className="profile-header">
          <h2>Профиль</h2>
          <User size={24} className="profile-icon" />
        </div>

        <div className="profile-content">
          <div className="profile-actions">
            {!editing ? (
              <div className="flex space-x-2">
                <button 
                  className="btn-primary"
                  onClick={() => {
                    setEditing(true);
                    // Скрываем навигацию при входе в режим редактирования
                    const bottomNav = document.querySelector(".bottom-navigation");
                    if (bottomNav && !telegramWebApp.isAvailable) {
                      bottomNav.style.display = "none";
                      console.log('Navigation hidden on edit mode');
                    }
                  }}
                >
                  Редактировать
                </button>
              </div>
            ) : (
              <div className="edit-actions">
                <button 
                  className="save-profile-btn"
                  onClick={handleSave}
                >
                  <Save size={16} />
                  Сохранить
                </button>
                <button 
                  className="cancel-edit-btn"
                  onClick={handleCancel}
                >
                  <X size={16} />
                  Отмена
                </button>
              </div>
            )}
          </div>

          <div className="profile-fields">
            <div className="profile-field">
              <label>Имя:</label>
              {editing ? (
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Введите ваше имя"
                />
              ) : (
                <span className="profile-value">{profile?.name || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Возраст:</label>
              {editing ? (
                <input
                  type="number"
                  value={formData.age || ''}
                  onChange={(e) => handleInputChange('age', e.target.value)}
                  placeholder="Введите ваш возраст"
                  min="1"
                  max="120"
                />
              ) : (
                <span className="profile-value">{profile?.age || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Цветотип:</label>
              {editing ? (
                <select
                  value={formData.cvetotip || ''}
                  onChange={(e) => handleInputChange('cvetotip', e.target.value)}
                >
                  <option value="">Выберите цветотип</option>
                  <option value="весна">Весна</option>
                  <option value="лето">Лето</option>
                  <option value="осень">Осень</option>
                  <option value="зима">Зима</option>
                </select>
              ) : (
                <span className="profile-value">{profile?.cvetotip || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Тип фигуры:</label>
              {editing ? (
                <select
                  value={formData.figura || ''}
                  onChange={(e) => handleInputChange('figura', e.target.value)}
                >
                  <option value="">Выберите тип фигуры</option>
                  <option value="песочные часы">Песочные часы</option>
                  <option value="прямоугольник">Прямоугольник</option>
                  <option value="треугольник">Треугольник</option>
                  <option value="перевернутый треугольник">Перевернутый треугольник</option>
                  <option value="овал">Овал</option>
                </select>
              ) : (
                <span className="profile-value">{profile?.figura || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Род занятий:</label>
              {editing ? (
                <input
                  type="text"
                  value={formData.rod_zanyatii || ''}
                  onChange={(e) => handleInputChange('rod_zanyatii', e.target.value)}
                  placeholder="Например: офис, творчество"
                />
              ) : (
                <span className="profile-value">{profile?.rod_zanyatii || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Предпочтения в стиле:</label>
              {editing ? (
                <input
                  type="text"
                  value={formData.predpochtenia || ''}
                  onChange={(e) => handleInputChange('predpochtenia', e.target.value)}
                  placeholder="Ваши стилистические предпочтения"
                />
              ) : (
                <span className="profile-value">{profile?.predpochtenia || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Что хотите изменить:</label>
              {editing ? (
                <input
                  type="text"
                  value={formData.change || ''}
                  onChange={(e) => handleInputChange('change', e.target.value)}
                  placeholder="Что хотите изменить в стиле"
                />
              ) : (
                <span className="profile-value">{profile?.change || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Любимая зона:</label>
              {editing ? (
                <input
                  type="text"
                  value={formData.like_zone || ''}
                  onChange={(e) => handleInputChange('like_zone', e.target.value)}
                  placeholder="Например: талия, плечи"
                />
              ) : (
                <span className="profile-value">{profile?.like_zone || 'Не указано'}</span>
              )}
            </div>

            <div className="profile-field">
              <label>Зона для скрытия:</label>
              {editing ? (
                <input
                  type="text"
                  value={formData.dislike_zone || ''}
                  onChange={(e) => handleInputChange('dislike_zone', e.target.value)}
                  placeholder="Например: бедра, живот"
                />
              ) : (
                <span className="profile-value">{profile?.dislike_zone || 'Не указано'}</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage; 