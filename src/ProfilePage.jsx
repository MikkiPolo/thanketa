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
    const profileContent = document.querySelector('.profile-content');
    const card = document.querySelector('.card');

    const applyKeyboardLayout = () => {
      const vv = window.visualViewport;
      const viewportHeight = vv ? vv.height : window.innerHeight;
      const fullHeight = window.innerHeight;
      const keyboardPx = Math.max(0, fullHeight - viewportHeight);
      const isKeyboardOpen = keyboardPx > 120; // эвристика

      const bottomNav = document.querySelector('.bottom-navigation');
      if (isKeyboardOpen) {
        if (bottomNav) bottomNav.style.display = 'none';
        if (profileContent) {
          const extra = Math.min(320, keyboardPx + 80);
          profileContent.style.paddingBottom = `${extra}px`;
          profileContent.style.maxHeight = 'unset';
        }
        if (card) {
          const extra = Math.min(240, keyboardPx + 40);
          card.style.paddingBottom = `${extra}px`;
        }
      } else {
        if (bottomNav) bottomNav.style.display = 'flex';
        if (profileContent) {
          profileContent.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 4rem)';
          profileContent.style.maxHeight = '';
        }
        if (card) {
          card.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 4rem)';
        }
      }
    };

    // Начальные значения
    if (profileContent) profileContent.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 4rem)';
    if (card) card.style.paddingBottom = 'calc(env(safe-area-inset-bottom) + 4rem)';

    // Слушатели для visualViewport и resize
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', applyKeyboardLayout);
      window.visualViewport.addEventListener('scroll', applyKeyboardLayout);
    }
    window.addEventListener('resize', applyKeyboardLayout);

    // Скрытие/показ навигации при фокусе
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach((input) => {
      input.addEventListener('focus', applyKeyboardLayout);
      input.addEventListener('blur', applyKeyboardLayout);
    });

    // Первичный расчет
    applyKeyboardLayout();

    // Очистка
    return () => {
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', applyKeyboardLayout);
        window.visualViewport.removeEventListener('scroll', applyKeyboardLayout);
      }
      window.removeEventListener('resize', applyKeyboardLayout);
      inputs.forEach((input) => {
        input.removeEventListener('focus', applyKeyboardLayout);
        input.removeEventListener('blur', applyKeyboardLayout);
      });
    };
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
      const bottomNav = document.querySelector('.bottom-navigation');
      if (bottomNav) bottomNav.style.display = 'flex';
    } catch (error) {
      console.error('Error saving profile:', error);
    }
  };

  const handleCancel = () => {
    setFormData(profile || {});
    setEditing(false);
    const bottomNav = document.querySelector('.bottom-navigation');
    if (bottomNav) bottomNav.style.display = 'flex';
  };

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="app">
        <div className="card" style={{ paddingTop: 'calc(env(safe-area-inset-top) + 4rem)' }}>
          <div className="loading-text">Загрузка профиля...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="card" style={{ paddingTop: 'calc(env(safe-area-inset-top) + 4rem)' }}>
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
                    const bottomNav = document.querySelector('.bottom-navigation');
                    if (bottomNav) bottomNav.style.display = 'none';
                  }}
                >
                  Редактировать
                </button>
              </div>
            ) : (
              <div className="edit-actions">
                <button className="btn-primary" onClick={handleSave}>
                  <Save size={16} />
                  Сохранить
                </button>
                <button className="btn-secondary" onClick={handleCancel}>
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
                <input
                  type="text"
                  value={formData.cvetotip || ''}
                  onChange={(e) => handleInputChange('cvetotip', e.target.value)}
                  placeholder="Например: тёплая осень, холодное лето"
                  list="cvetotip-hints"
                />
              ) : (
                <span className="profile-value">{profile?.cvetotip || 'Не указано'}</span>
              )}
              <datalist id="cvetotip-hints">
                <option value="тёплая осень" />
                <option value="светлая весна" />
                <option value="холодное лето" />
                <option value="яркая зима" />
              </datalist>
            </div>

            <div className="profile-field">
              <label>Тип фигуры:</label>
              {editing ? (
                <input
                  type="text"
                  value={formData.figura || ''}
                  onChange={(e) => handleInputChange('figura', e.target.value)}
                  placeholder="Например: песочные часы, прямоугольник"
                  list="figura-hints"
                />
              ) : (
                <span className="profile-value">{profile?.figura || 'Не указано'}</span>
              )}
              <datalist id="figura-hints">
                <option value="песочные часы" />
                <option value="прямоугольник" />
                <option value="треугольник" />
                <option value="перевернутый треугольник" />
                <option value="овал" />
              </datalist>
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