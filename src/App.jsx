import { useState, useEffect, useRef, useCallback, useMemo} from "react";
import { Camera, Image } from 'lucide-react';
import "./App.css";
import WardrobePage from './WardrobePage';
import CapsulePage from './CapsulePage';
import FavoritesPage from './FavoritesPage';
import ProfilePage from './ProfilePage';
import ShopPage from './ShopPage';
import ChatPage from './ChatPage';
import ProfileMenuModal from './ProfileMenuModal';

import BottomNavigation from './BottomNavigation';
import AddItemPage from './AddItemPage';
import AddWardrobeItem from './AddWardrobeItem';
import ThemeToggle from './ThemeToggle';
import LoadingSpinner from './LoadingSpinner';
import ProgressBar from './ProgressBar';
import ErrorBoundary from './ErrorBoundary';
import WeatherDateHeader from './WeatherDateHeader';

import NotificationModal from './NotificationModal';
import { useCache } from './cache';
import { profileService } from './supabase';
import telegramWebApp from './telegramWebApp';
import brandItemsService from './services/brandItemsService';
import TelegramIdDebugger from './TelegramIdDebugger';
import { normalizeText, validateAge, cleanAge } from './utils/textUtils';


// удален дублирующийся массив questions вне компонента

export default function App() {
  console.log('🚀 App компонент начал рендеринг');
  
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({});
  const [currentPage, setCurrentPage] = useState('home');
  const [animate, setAnimate] = useState(true);
  const [tgId, setTgId] = useState(null);
  const [existingProfile, setExistingProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  
  console.log('📊 App состояние инициализировано:', { tgId, loading, step });
  const [started, setStarted] = useState(false);
  const [viewing, setViewing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [viewingWardrobe, setViewingWardrobe] = useState(false);
  const [viewingCapsules, setViewingCapsules] = useState(false);
  const [theme, setTheme] = useState('light');
  const [showStats, setShowStats] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAddWardrobeItem, setShowAddWardrobeItem] = useState(false);
  const [notification, setNotification] = useState({ isVisible: false, type: 'success', title: '', message: '' });
  const [showDebugger, setShowDebugger] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const wardrobeRef = useRef(null);
  
  // Инициализация кэша
  const cache = useCache();
  
  // Делаем brandItemsService доступным глобально для ShopPage
  useEffect(() => {
    window.brandItemsService = brandItemsService;
  }, []);

  // Мемоизируем вопросы
  const questions = useMemo(() => [
    { title: "Как тебя зовут?", field: "name" },
    { 
      title: "Сколько тебе лет?", 
      field: "age",
      hint: (
        <>
          <strong>Введите только цифры:</strong> например, 25
        </>
      ),
    },
    {
      title: "Как бы ты описала свой тип фигуры?",
      field: "figura",
      hint: (
        <>
        <strong>Например:</strong> Яблоко (O), Треугольник (A), Перевернутый треугольник (V),<br />
        Прямоугольник (H), «Песочные часы» (X)<br /><br />
        Если не уверена — ничего страшного!<br /><br />
        Этот бот поможет:{" "}
        <a href="https://t.me/figuralnabot" target="_blank" rel="noopener noreferrer">@figuralnabot</a>
      </>
      ),
    },
    {
      title: "Какой у тебя цветотип?",
      field: "cvetotip",
      hint: (
        <>
          <strong>Например:</strong> тёплая весна, холодное лето
          <br /><br />
          Если не уверена — ничего страшного!
          <br /><br />
          Этот бот поможет:{" "}
          <a href="https://t.me/chrommabot" target="_blank" rel="noopener noreferrer">
            @chrommabot
          </a>
        </>
      ),
    },
    { title: "Чем ты занимаешься? Есть ли дресс-код?", field: "rod_zanyatii" },
    {
      title: "Какой стиль одежды тебе ближе всего?",
      field: "predpochtenia",
      hint: (
        <>
          <strong>Например:</strong>
          <br />• повседневный (casual)<br />• классика или офисный стиль<br />• спорт-шик<br />• бохо<br />• минимализм<br />• романтичный<br />• пока не знаю, хочу понять
        </>
      ),
    },
    {
      title: "Хочешь что-то изменить в стиле или ищешь вдохновение?",
      field: "change",
      hint: (
        <>
          <strong>Например:</strong>
          <br />• Хочу выглядеть более женственно<br />• Хочется обновить гардероб<br />• Не уверена, но чувствую, что нужно что-то новое<br />• Просто хочется понять, что мне подходит
        </>
      ),
    },
    {
      title: "Какие части тела тебе хочется подчеркнуть?",
      field: "like_zone",
      hint:(
        <>
        <strong>Например:</strong> Талия и ключицы.<br />
        Если не знаешь — так и напиши: не знаю.
        </>
      ),
    },
    {
      title: "Какие зоны ты предпочла бы скрыть?",
      field: "dislike_zone",
      hint:(
        <>
        <strong>Например:</strong> живот и бёдра. <br/>
        Если не знаешь — так и напиши: не знаю.
        </>
      ),
    },
  ], []);



  // Слушаем событие для открытия AddWardrobeItem
  useEffect(() => {
    const handleOpenAddModal = () => {
      setShowAddWardrobeItem(true);
    };

    window.addEventListener('openAddModal', handleOpenAddModal);

    return () => {
      window.removeEventListener('openAddModal', handleOpenAddModal);
    };
  }, []);



  // Управление темой
  const toggleTheme = useCallback(() => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  }, [theme]);

  // Загрузка темы из localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
  }, []);

  const handleEditProfile = useCallback(() => {
    setEditForm(existingProfile || {});
    setEditing(true);
  }, [existingProfile]);

  const handleSaveEditedProfile = useCallback(async () => {
    try {
      await profileService.saveProfile({ 
        telegram_id: tgId, 
        ...editForm 
      });
      alert("Анкета обновлена!");
      setExistingProfile(editForm);
      setEditing(false);
    } catch (error) {
      console.error('Error saving profile:', error);
      alert("Ошибка при сохранении изменений");
    }
  }, [tgId, editForm]);

  // Функция для получения геолокации
  const requestGeolocation = useCallback(async () => {
    if (!navigator.geolocation) {
      console.warn('Геолокация не поддерживается вашим браузером');
      return null;
    }

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          console.log('📍 Геолокация получена:', latitude, longitude);
          
          try {
            // Сохраняем координаты в профиль
            await profileService.saveProfile({
              telegram_id: tgId,
              location_latitude: latitude,
              location_longitude: longitude
            });
            console.log('✅ Координаты сохранены в профиль');
            resolve({ latitude, longitude });
          } catch (error) {
            console.error('❌ Ошибка сохранения координат:', error);
            resolve(null);
          }
        },
        (error) => {
          console.warn('⚠️ Пользователь не предоставил доступ к геолокации:', error.message);
          resolve(null);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    });
  }, [tgId]);



  useEffect(() => {
    const fetchProfile = async () => {
      let tg_id = null;
      
      // 1. Пробуем получить из Telegram Web App API
      if (telegramWebApp.isAvailable) {
        console.log('Telegram Web App доступен, инициализируем...');
        telegramWebApp.init();
        telegramWebApp.setupFullScreen(); // Настраиваем полный экран
        tg_id = telegramWebApp.getTelegramId();
        console.log('Telegram ID из Web App:', tg_id);
      }
      
      // 2. Если не получилось, пробуем из URL параметра
      if (!tg_id) {
        const urlParams = new URLSearchParams(window.location.search);
        tg_id = urlParams.get("tg_id");
        console.log('Telegram ID из URL:', tg_id);
      }
      
      // 3. Если все еще нет, пробуем из localStorage (для тестирования)
      if (!tg_id) {
        tg_id = localStorage.getItem('test_telegram_id');
        console.log('Telegram ID из localStorage:', tg_id);
      }
      
      console.log('Final tg_id:', tg_id);
      console.log('Current tgId state:', tgId);
      
      if (tg_id) {
        console.log('Setting tgId to:', tg_id);
        setTgId(tg_id);
        
        // Проверяем кэш
        const cachedProfile = cache.get(`profile_${tg_id}`);
        if (cachedProfile) {
          console.log('Found cached profile:', cachedProfile);
          setExistingProfile(cachedProfile);
          setLoading(false);
          return; // Выходим, если данные есть в кэше
        }
        
        console.log('Fetching profile from Supabase...');
        try {
          const profile = await profileService.getProfile(tg_id);
          console.log('Supabase response:', profile);
          setExistingProfile(profile);
          
          // Сохраняем в кэш
          if (profile) {
            cache.set(`profile_${tg_id}`, profile, 5 * 60 * 1000); // 5 минут
          }
          
          setLoading(false);
        } catch (error) {
          console.error('Supabase error:', error);
          setLoading(false);
        }
      } else {
        console.log('No tg_id found from any source');
        // Устанавливаем loading в false, чтобы показать форму входа
        setLoading(false);
        setTgId(null); // Явно устанавливаем null, чтобы форма входа показалась
      }
    };

    fetchProfile();
  }, []); // Убираем cache из зависимостей

  // Отладочный useEffect для проверки состояния
  useEffect(() => {
    console.log('Current state:', {
      tgId,
      existingProfile,
      loading,
      viewingWardrobe
    });
  }, [tgId, existingProfile, loading, viewingWardrobe]);
  
  useEffect(() => {
  if (viewingWardrobe) {
    window.scrollTo({ top: 0, behavior: "auto" });
  }
}, [viewingWardrobe]);



  // Функция для нормализации текста (первая буква заглавная, остальные строчные)
  const handleChange = (e) => {
    // Защита от ошибок, если questions или step не определены
    if (!questions || !questions[step]) {
      console.error('questions or step not defined in handleChange');
      return;
    }
    const field = questions[step].field;
    let value = e.target.value;
    
    // Специальная обработка для поля age - только цифры
    if (field === 'age') {
      value = cleanAge(value);
    } else {
      // Для остальных полей применяем нормализацию
      value = normalizeText(value);
    }
    
    setForm({ ...form, [field]: value });
  };

  const handleNext = () => {
    setAnimate(false);
    setTimeout(async () => {
      setAnimate(true);
      if (step < questions.length - 1) {
        setStep(step + 1);
      } else {
        try {
          // Валидация данных перед сохранением
          const dataToSave = { 
            telegram_id: tgId, 
            ...form, 
            step: 'completed' 
          };
          
          // Проверяем, что возраст является числом
          if (dataToSave.age && !validateAge(dataToSave.age)) {
            alert("Пожалуйста, введите корректный возраст (только цифры от 1 до 120)");
            return;
          }
          
          // Преобразуем возраст в число, если он есть
          if (dataToSave.age) {
            dataToSave.age = parseInt(dataToSave.age);
          }
          
          await profileService.saveProfile(dataToSave);

          // Запрашиваем геолокацию после сохранения профиля (не блокируем, если пользователь откажет)
          requestGeolocation().catch(err => {
            console.warn('Геолокация не получена:', err);
          });

          setStarted(false);
          setExistingProfile({ name: form.name });
        } catch (error) {
          console.error('Error saving profile:', error);
          alert("Ошибка при сохранении анкеты");
        }
      }
    }, 120);
  };

  const handleBack = () => {
    setAnimate(false);
    setTimeout(() => {
      setAnimate(true);
      if (step > 0) setStep(step - 1);
    }, 120);
  };

  const handleCancel = () => {
    if (confirm("Вы точно хотите отменить заполнение анкеты?")) {
      setForm({});
      setStep(0);
      setStarted(false);
    }
  };

  const handleStart = () => {
    setForm({});
    setStep(0);
    setStarted(true);
  };

  const handlePageChange = (page) => {
    if (page === 'add') {
      setShowAddModal(true);
    } else if (page === 'profile') {
      // Откроем меню профиля (action sheet)
      setShowProfileMenu(true);
    } else {
      setCurrentPage(page);
    }
  };



  const handleAddItemClose = () => {
    setShowAddModal(false);
  };

  const handleAddItemAdded = (newItem) => {
    // Вещь добавлена, показываем уведомление
    console.log('Item added:', newItem);
    showNotification('success', '', 'Вещь успешно добавлена в гардероб!');
    setShowAddModal(false);
  };

  const handleAddWardrobeItemClose = () => {
    setShowAddWardrobeItem(false);
  };

  const showNotification = (type, title, message) => {
    setNotification({ isVisible: true, type, title, message });
  };

  const hideNotification = () => {
    setNotification({ isVisible: false, type: 'success', title: '', message: '' });
  };

  const handleAddWardrobeItemAdded = (newItem) => {
    console.log('Wardrobe item added:', newItem);
    showNotification('success', '', 'Вещь успешно добавлена в гардероб!');
    setShowAddWardrobeItem(false);
  };

  const handleViewProfile = () => {
    setViewing(true);
  };

  const handleTelegramIdSet = (newTgId) => {
    console.log('Setting Telegram ID from debugger:', newTgId);
    setTgId(newTgId);
    // Перезагружаем профиль с новым ID
    const fetchProfile = async () => {
      try {
        const profile = await profileService.getProfile(newTgId);
        setExistingProfile(profile);
        if (profile) {
          cache.set(`profile_${newTgId}`, profile, 5 * 60 * 1000);
        }
      } catch (error) {
        console.error('Error fetching profile with new ID:', error);
      }
    };
    fetchProfile();
  };

  // Состояние для ввода Telegram ID на десктопе
  const [inputTelegramId, setInputTelegramId] = useState('');

  const handleTelegramIdSubmit = (e) => {
    e.preventDefault();
    if (inputTelegramId.trim()) {
      const tgId = inputTelegramId.trim();
      localStorage.setItem('test_telegram_id', tgId);
      setTgId(tgId);
      // Перезагружаем профиль
      window.location.reload();
    }
  };

  // Показываем форму входа если нет tgId И загрузка завершена
  // ВАЖНО: эта проверка должна быть ПЕРВОЙ, до любых обращений к questions или другим данным
  console.log('🔍 Проверка условий:', { 
    tgId, 
    loading, 
    shouldShowLogin: !tgId && !loading, 
    started, 
    viewing, 
    editing,
    questionsDefined: !!questions,
    stepValue: step
  });
  
  // КРИТИЧЕСКИ ВАЖНО: эта проверка должна быть ПЕРВОЙ
  if (!tgId && !loading) {
    console.log('✅ Показываем форму входа - условие выполнено!');
    return (
      <ErrorBoundary>
        <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
          <div className="card login-card">
            <div className="login-content">
              <div className="login-header">
                <h1>GLAMORA</h1>
                <p className="login-subtitle">Вход в приложение</p>
              </div>
              
              <form onSubmit={handleTelegramIdSubmit} className="login-form">
                <div className="login-input-group">
                  <label htmlFor="telegram-id" className="login-label">
                    Telegram ID
                  </label>
                  <input
                    id="telegram-id"
                    type="text"
                    value={inputTelegramId}
                    onChange={(e) => setInputTelegramId(e.target.value)}
                    placeholder="Введите ваш Telegram ID"
                    className="login-input"
                    autoFocus
                    required
                  />
                  <p className="login-hint">
                    {telegramWebApp.isAvailable 
                      ? 'Не удалось получить данные из Telegram автоматически' 
                      : 'Введите ваш Telegram ID для доступа к приложению'}
                  </p>
                </div>
                
                <button
                  type="submit"
                  className="btn-primary login-button"
                  disabled={!inputTelegramId.trim()}
                >
                  Войти
                </button>
              </form>

              <div className="login-footer">
                <p className="login-footer-text">
                  Или добавьте <code>?tg_id=ваш_id</code> к URL
                </p>
              </div>
              
              {/* Debugger для разработки */}
              {import.meta.env.DEV && (
                <div className="login-debugger">
                  <button 
                    onClick={() => setShowDebugger(!showDebugger)}
                    className="debugger-toggle"
                  >
                    {showDebugger ? 'Скрыть' : 'Показать'} Debugger
                  </button>
                  
                  {showDebugger && (
                    <div style={{ marginTop: '1rem' }}>
                      <TelegramIdDebugger onTelegramIdSet={handleTelegramIdSet} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  if (loading) {
    return (
      <ErrorBoundary>
        <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
          <div className="card">
            <LoadingSpinner size="large" color="var(--color-accent)" />
            <p style={{ textAlign: 'center', marginTop: '1rem', color: 'var(--color-text-primary)' }}>
              Загрузка...
            </p>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  // Теперь безопасно можем обращаться к questions, так как проверки на вход и загрузку пройдены
  // НО! Проверяем, что questions определен, иначе будет ошибка
  if (!questions || !questions[step]) {
    console.error('❌ КРИТИЧЕСКАЯ ОШИБКА: questions не определен!', { questions, step });
    return (
      <ErrorBoundary>
        <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
          <div className="card">
            <h2>Ошибка инициализации</h2>
            <p>Пожалуйста, обновите страницу</p>
            <button onClick={() => window.location.reload()}>Обновить</button>
          </div>
        </div>
      </ErrorBoundary>
    );
  }
  
  const { title, hint, field } = questions[step];
  const progress = ((step + 1) / questions.length) * 100;

  if (viewingCapsules && existingProfile?.telegram_id) {
    return (
      <ErrorBoundary>
        <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
          <CapsulePage
            profile={existingProfile}
            onBack={() => {
              setViewingCapsules(false);
            }}
          />
        </div>
      </ErrorBoundary>
    );
  }

  if (viewingWardrobe && existingProfile?.telegram_id) {
    return (
      <ErrorBoundary>
        <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
          <WardrobePage
            telegramId={existingProfile.telegram_id}
            access={existingProfile.access}
            profile={existingProfile}
            scrollRef={wardrobeRef}
            onBack={() => {
              setViewingWardrobe(false);
            }}
          />
        </div>
      </ErrorBoundary>
    );
  }

  // Основной рендер с навигацией
  if (!started && !viewing) {
    return (
      <ErrorBoundary>
        <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
          
          {/* Основной контент */}
          {currentPage === 'home' && (
            <div className="card" style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: "calc(env(safe-area-inset-top) + 4rem)", minHeight: "100vh" }}>
              {/* Компонент погоды и даты */}
              <WeatherDateHeader profile={existingProfile} />
              
              <div className="logo" style={{ marginTop: "2rem", marginBottom: "0.7rem" }}>
                <img src={theme === 'dark' ? "/vite1.svg" : "/vite.svg"} alt="logo" className="logo-img" />
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
                <ProgressBar progress={0} showPercentage={false} />
              </div>

              <div style={{ fontSize: "1.4rem", marginBottom: "1rem", textAlign: "center", color: "var(--color-text-primary)" }}>
                {existingProfile?.name ? `Привет, ${existingProfile.name}` : "Добро пожаловать!"}
              </div>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                  justifyContent: "center",
                  alignItems: "stretch",
                  width: "100%",
                  maxWidth: 320,
                  margin: "0 auto",
                }}
              >
                {/* Кнопки профиля на главной странице */}
                {existingProfile && existingProfile.name && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '3rem' }}>
                    <button 
                      className="btn-primary" 
                      onClick={() => setCurrentPage('profile')}
                      style={{ padding: '12px 20px', fontSize: '1rem' }}
                    >
                      Просмотреть профиль
                    </button>

                    <button 
                      className="btn-secondary" 
                      onClick={() => {
                        const supportUrl = `https://t.me/glamorasupportbot${existingProfile?.telegram_id ? `?start=uid_${existingProfile.telegram_id}` : ''}`;
                        try {
                          if (window?.Telegram?.WebApp?.openTelegramLink) {
                            window.Telegram.WebApp.openTelegramLink(supportUrl);
                          } else {
                            window.open(supportUrl, '_blank');
                          }
                        } catch (e) {
                          window.open(supportUrl, '_blank');
                        }
                      }}
                      style={{ padding: '12px 20px', fontSize: '1rem' }}
                    >
                      Обратиться в поддержку
                    </button>

                    <button 
                      className="btn-secondary" 
                      onClick={() => {
                        const feedbackUrl = `https://t.me/glamorafeedbackbot${existingProfile?.telegram_id ? `?start=uid_${existingProfile.telegram_id}` : ''}`;
                        try {
                          if (window?.Telegram?.WebApp?.openTelegramLink) {
                            window.Telegram.WebApp.openTelegramLink(feedbackUrl);
                          } else {
                            window.open(feedbackUrl, '_blank');
                          }
                        } catch (e) {
                          window.open(feedbackUrl, '_blank');
                        }
                      }}
                      style={{ padding: '12px 20px', fontSize: '1rem' }}
                    >
                      Оставить отзыв
                    </button>
                  </div>
                )}

                <div className="buttons" style={{ marginTop: "1.5rem" }}>
                  {!existingProfile || !existingProfile.name ? (
                    <button onClick={handleStart} className="next">
                      Заполнить анкету
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          )}

          {currentPage === 'wardrobe' && (existingProfile?.access === "full" || existingProfile?.access === "demo") && (
            <WardrobePage
              telegramId={existingProfile.telegram_id}
              access={existingProfile.access}
              profile={existingProfile}
              scrollRef={wardrobeRef}
              onBack={() => setCurrentPage('home')}
            />
          )}

          {currentPage === 'wardrobe' && !(existingProfile?.access === "full" || existingProfile?.access === "demo") && (
            <div className="card">
              <div className="error-content">
                <h2>Доступ ограничен</h2>
                <p>Для доступа к гардеробу необходим полный доступ</p>
              </div>
            </div>
          )}

          {/* Модальное окно добавления вещи */}
          {showAddModal && (existingProfile?.access === "full" || existingProfile?.access === "demo") && (
            <div className="modal-overlay">
              <div className="modal-content">
                <div className="modal-header">
                  <h3>Добавить вещь в гардероб</h3>
                  <button className="close-btn" onClick={handleAddItemClose}>×</button>
                </div>
                <div className="camera-controls">
                  <button className="btn-primary" onClick={() => {
                    setShowAddModal(false);
                    // Открываем AddWardrobeItem напрямую
                    const event = new CustomEvent('openAddModal');
                    window.dispatchEvent(event);
                  }}>
                    <Camera size={20} />
                    Запустить камеру
                  </button>
                  <button className="btn-secondary" onClick={() => {
                    setShowAddModal(false);
                    // Открываем AddWardrobeItem напрямую
                    const event = new CustomEvent('openAddModal');
                    window.dispatchEvent(event);
                  }}>
                    <Image size={20} />
                    Добавить фото
                  </button>
                </div>
              </div>
            </div>
          )}

          {showAddModal && !(existingProfile?.access === "full" || existingProfile?.access === "demo") && (
            <div className="modal-overlay">
              <div className="modal-content">
                <div className="modal-header">
                  <h3>Доступ ограничен</h3>
                  <button className="close-btn" onClick={handleAddItemClose}>×</button>
                </div>
                <div className="error-content">
                  <p>Для добавления вещей необходим полный доступ</p>
                </div>
              </div>
            </div>
          )}

          {/* AddWardrobeItem модальное окно */}
          {showAddWardrobeItem && (
            <AddWardrobeItem
              telegramId={existingProfile?.telegram_id}
              onItemAdded={handleAddWardrobeItemAdded}
              onClose={handleAddWardrobeItemClose}
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



                  {currentPage === 'favorites' && (
            <FavoritesPage 
              telegramId={existingProfile?.telegram_id || tgId}
              showNotification={showNotification}
            />
          )}

          {currentPage === 'capsules' && (existingProfile?.access === "full" || existingProfile?.access === "demo") && (
            <CapsulePage 
              profile={existingProfile}
              onBack={() => handlePageChange('wardrobe')}
            />
          )}

          {currentPage === 'capsules' && !(existingProfile?.access === "full" || existingProfile?.access === "demo") && (
            <div className="card">
              <div className="error-content">
                <h2>Доступ ограничен</h2>
                <p>Для доступа к капсулам необходим полный доступ</p>
              </div>
            </div>
          )}

          {currentPage === 'profile' && (
            <ProfilePage telegramId={existingProfile?.telegram_id || 'default'} />
          )}

          {currentPage === 'shop' && (
            <ShopPage 
              telegramId={existingProfile?.telegram_id || 'default'}
              season={existingProfile?.season || 'Осень'}
              temperature={15.0}
              onBack={() => setCurrentPage('home')}
            />
          )}

          {currentPage === 'chat' && (
            <ChatPage 
              telegramId={existingProfile?.telegram_id || tgId || 'default'}
            />
          )}

          {/* Нижняя навигация */}
          {existingProfile && (
            <BottomNavigation 
              activePage={currentPage} 
              onPageChange={handlePageChange} 
            />
          )}
          {/* Меню профиля */}
          <ProfileMenuModal 
            isOpen={showProfileMenu}
            telegramId={existingProfile?.telegram_id}
            onViewProfile={() => setCurrentPage('profile')}
            onClose={() => setShowProfileMenu(false)}
          />


        </div>
      </ErrorBoundary>
    );
  }
  if (editing && existingProfile) {
    return (
      <ErrorBoundary>
        <div className="app">
          <div className="card">
            <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
              <img src={theme === 'dark' ? "/vite1.svg" : "/vite.svg"} alt="logo" className="logo-img" />
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
              <ProgressBar progress={100} showPercentage={false} />
            </div>
            <h2 style={{ marginBottom: '1rem', textAlign: "center", color: "var(--color-text-primary)" }}>Редактировать профиль</h2>
            <form
              onSubmit={e => {
                e.preventDefault();
                handleSaveEditedProfile();
              }}
              style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem', marginBottom: '1.5rem' }}
            >
              {questions.map(q => (
                <div
                  key={q.field}
                  style={{
                    background: "var(--input-bg)",
                    borderRadius: "10px",
                    padding: "12px 14px",
                    boxShadow: "0 1px 2px var(--shadow)",
                    border: "1px solid var(--color-accent)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.3rem"
                  }}
                >
                  <label style={{ fontWeight: 600, fontSize: "1.04rem", color: "var(--color-text-primary)" }}>
                    {q.title}
                  </label>
                  <input
                    type="text"
                    value={editForm[q.field] || ""}
                    onChange={e => setEditForm({ ...editForm, [q.field]: e.target.value })}
                    placeholder="Введите значение..."
                    style={{
                      width: "100%",
                      padding: "8px",
                      fontSize: "1rem",
                      borderRadius: "6px",
                      border: "1px solid var(--color-accent)",
                      background: "var(--input-bg)",
                      color: "var(--input-text)"
                    }}
                  />
                </div>
              ))}
              <div className="buttons" style={{ marginTop: "1.5rem" }}>
                <button type="button" className="cancel" onClick={() => setEditing(false)}>
                  Назад
                </button>
                <button type="submit" className="next">
                  Сохранить изменения
                </button>
              </div>
            </form>
          </div>
        </div>
      </ErrorBoundary>
    );
  }
  if (viewing && existingProfile && existingProfile.name) {
    return (
      <ErrorBoundary>
        <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
          <div className="card scrollable-card">
            <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
              <img src={theme === 'dark' ? "/vite1.svg" : "/vite.svg"} alt="logo" className="logo-img" />
            </div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
              <ProgressBar progress={100} showPercentage={false} />
            </div>
            <h2 style={{ marginBottom: '1rem', textAlign: "center", color: "var(--color-text-primary)" }}>Твой профиль</h2>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              marginBottom: '1.5rem'
            }}>
              {questions.map(q => (
                <div className="profile-block" key={q.field}>
                  <div style={{
                    fontWeight: 700,
                    fontSize: "1.08rem",
                    color: "#000000",
                    marginBottom: 2
                  }}>
                    {q.title}
                  </div>
                  <div className="answer-from-db">
                    {existingProfile[q.field] || <span style={{ color: '#bbb' }}>—</span>}
                  </div>
                </div>
              ))}
            </div>
            <div className="buttons" style={{ marginTop: '1.5rem' }}>
              <button className="cancel" onClick={() => setViewing(false)}>Назад</button>
              <button className="next" onClick={handleEditProfile}>Изменить</button>
            </div>
          </div>
        </div>
      </ErrorBoundary>
    );
  }
  return (
    <ErrorBoundary>
      <div className={`app ${telegramWebApp.isAvailable ? 'telegram-webapp' : ''}`}>
        <div className={`card ${animate ? "fade-in" : "fade-out"}`}>
          <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
            <img src={theme === 'dark' ? "/vite1.svg" : "/vite.svg"} alt="logo" className="logo-img" />
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
            <ProgressBar progress={progress} showPercentage={true} />
          </div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-start" }}>
            <p className="question">{title}</p>
            {hint && (
              <div className="hint" style={{ marginBottom: "1rem", fontSize: "0.95rem", color: "var(--input-text)" }}>
                {hint}
              </div>
            )}
            <div className="input-wrap">
              <input
                type="text"
                value={form[field] || ""}
                onChange={handleChange}
                placeholder="Введите ответ..."
                autoFocus
              />
            </div>
          </div>
          <div className="buttons">
            {step > 0 && (
              <button className="back" onClick={handleBack}>
                Назад
              </button>
            )}
            <button className="cancel" onClick={handleCancel}>
              Отменить
            </button>
            <button className="next" onClick={handleNext} disabled={!form[field] || !form[field].trim()}>
              {step === questions.length - 1 ? "Сохранить" : "Далее"}
            </button>
          </div>
        </div>

        <style>{`
          .fade-in {
            animation: fadeInCard 0.35s cubic-bezier(.4,0,.2,1);
          }
          .fade-out {
            animation: fadeOutCard 0.15s cubic-bezier(.4,0,.2,1);
          }
          @keyframes fadeInCard {
            from { opacity: 0; transform: translateY(16px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
          }
          @keyframes fadeOutCard {
            from { opacity: 1; transform: translateY(0) scale(1); }
            to { opacity: 0; transform: translateY(16px) scale(0.98); }
          }
        `}</style>
      </div>
    </ErrorBoundary>
  );
}
