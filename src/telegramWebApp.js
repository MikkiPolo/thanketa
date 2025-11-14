// Telegram Web App API интеграция
class TelegramWebApp {
  constructor() {
    this.isAvailable = window.Telegram && window.Telegram.WebApp;
    this.webApp = this.isAvailable ? window.Telegram.WebApp : null;
  }

  // Инициализация Web App
  init() {
    if (!this.isAvailable) {
      return false;
    }

    try {
      this.webApp.ready();
      this.webApp.expand();
      // применяем VisualViewport offsets для iOS клавиатуры
      try {
        const root = document.documentElement;
        const tabbar = document.getElementById('tabbar');

        const updateTabbarHeight = () => {
          const h = tabbar ? Math.round(tabbar.getBoundingClientRect().height) : 0;
          root.style.setProperty('--tabbar-h', `${h}px`);
          recomputeBottomGap();
        };

        const updateVisualViewport = () => {
          const vv = window.visualViewport;
          if (!vv) return;
          const occludedBottom = Math.max(0, window.innerHeight - (vv.height + vv.offsetTop));
          root.style.setProperty('--vv-bottom', `${occludedBottom}px`);
          recomputeBottomGap();
        };

        const recomputeBottomGap = () => {
          const styles = getComputedStyle(root);
          const safe = parseFloat(styles.getPropertyValue('--safe')) || 0;
          const tab = parseFloat(styles.getPropertyValue('--tabbar-h')) || 0;
          const vvBot = parseFloat(styles.getPropertyValue('--vv-bottom')) || 0;
          const gap = Math.max(tab + safe, vvBot);
          root.style.setProperty('--bottom-gap', `${gap}px`);
        };

        // Инициализация наблюдателей
        try { new ResizeObserver(updateTabbarHeight).observe(tabbar); } catch (e) {}
        updateTabbarHeight();

        if (window.visualViewport) {
          window.visualViewport.addEventListener('resize', updateVisualViewport);
          window.visualViewport.addEventListener('scroll', updateVisualViewport);
          updateVisualViewport();
        }
      } catch (e) { /* ignore */ }
      return true;
    } catch (error) {
      console.error('Ошибка инициализации Telegram Web App:', error);
      return false;
    }
  }

  // Получение данных пользователя
  getUserData() {
    if (!this.isAvailable) {
      return null;
    }

    const initData = this.webApp.initData;
    const user = this.webApp.initDataUnsafe?.user;

    if (user) {
      return {
        id: user.id,
        first_name: user.first_name,
        last_name: user.last_name,
        username: user.username,
        language_code: user.language_code,
        is_premium: user.is_premium,
        photo_url: user.photo_url
      };
    }

    return null;
  }

  // Получение Telegram ID
  getTelegramId() {
    const userData = this.getUserData();
    return userData ? userData.id : null;
  }

  // Получение имени пользователя
  getUserName() {
    const userData = this.getUserData();
    if (!userData) return null;
    
    if (userData.first_name && userData.last_name) {
      return `${userData.first_name} ${userData.last_name}`;
    }
    return userData.first_name || userData.username || 'Пользователь';
  }

  // Проверка валидности initData
  validateInitData() {
    if (!this.isAvailable) return false;
    
    try {
      const initData = this.webApp.initData;
      if (!initData) {
        return false;
      }
      
      // Проверяем наличие обязательных полей
      const user = this.webApp.initDataUnsafe?.user;
      if (!user || !user.id) {
        return false;
      }
      
      // В продакшене здесь должна быть проверка HMAC-SHA256 подписи
      // Для безопасности нужно проверять подпись от Telegram
      if (import.meta.env.PROD) {
        // TODO: Реализовать проверку подписи
        // const isValid = this.validateSignature(initData, this.webApp.initDataUnsafe);
        // return isValid;
      }
      
      return true;
    } catch (error) {
      console.error('Ошибка валидации initData:', error);
      return false;
    }
  }

  // Отправка данных в Telegram
  sendData(data) {
    if (!this.isAvailable) return false;
    
    try {
      this.webApp.sendData(JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Ошибка отправки данных в Telegram:', error);
      return false;
    }
  }

  // Показать главную кнопку
  showMainButton(text, callback) {
    if (!this.isAvailable) return;
    
    this.webApp.MainButton.setText(text);
    this.webApp.MainButton.onClick(callback);
    this.webApp.MainButton.show();
  }

  // Скрыть главную кнопку
  hideMainButton() {
    if (!this.isAvailable) return;
    this.webApp.MainButton.hide();
  }

  // Показать всплывающее окно
  showPopup(title, message, buttons = []) {
    if (!this.isAvailable) return;
    
    this.webApp.showPopup({
      title,
      message,
      buttons
    });
  }

  // Показать алерт
  showAlert(message) {
    if (!this.isAvailable) return;
    this.webApp.showAlert(message);
  }

  // Показать подтверждение
  showConfirm(message) {
    if (!this.isAvailable) return false;
    return this.webApp.showConfirm(message);
  }

  // Получить тему
  getTheme() {
    if (!this.isAvailable) return 'light';
    return this.webApp.colorScheme || 'light';
  }

  // Получить цветовую схему
  getColorScheme() {
    if (!this.isAvailable) return { bg_color: '#ffffff', text_color: '#000000' };
    return {
      bg_color: this.webApp.themeParams?.bg_color || '#ffffff',
      text_color: this.webApp.themeParams?.text_color || '#000000',
      hint_color: this.webApp.themeParams?.hint_color || '#999999',
      link_color: this.webApp.themeParams?.link_color || '#2481cc',
      button_color: this.webApp.themeParams?.button_color || '#2481cc',
      button_text_color: this.webApp.themeParams?.button_text_color || '#ffffff'
    };
  }

  // Закрыть Web App
  close() {
    if (!this.isAvailable) return;
    this.webApp.close();
  }

  // Настроить интерфейс для полного экрана
  setupFullScreen() {
    if (!this.isAvailable) return;
    
    try {
      // Раскрываем на полный экран
      this.webApp.expand();
      
      // Устанавливаем цвета интерфейса
      this.webApp.setHeaderColor('#ffffff');
      this.webApp.setBackgroundColor('#ffffff');
      
      // Скрываем стандартные кнопки Telegram
      this.webApp.MainButton.hide();
      this.webApp.BackButton.hide();
      
      // Устанавливаем viewport height для корректного отображения
      const viewportHeight = this.webApp.viewportHeight;
      if (viewportHeight) {
        document.documentElement.style.setProperty('--tg-viewport-height', `${viewportHeight}px`);
      }
      
      console.log('Telegram Web App настроен для полного экрана');
    } catch (error) {
      console.error('Ошибка настройки полного экрана:', error);
    }
  }

  // Получить безопасные отступы для интерфейса
  getSafeInsets() {
    if (!this.isAvailable) {
      return { top: 0, bottom: 0, left: 0, right: 0 };
    }
    
    return {
      top: this.webApp.viewportStableHeight ? 
        (this.webApp.viewportHeight - this.webApp.viewportStableHeight) : 0,
      bottom: 0,
      left: 0,
      right: 0
    };
  }

  // Применить безопасные отступы к элементу
  applySafeInsets(element) {
    if (!this.isAvailable) return;
    
    const insets = this.getSafeInsets();
    if (element) {
      element.style.paddingTop = `${insets.top}px`;
      element.style.paddingBottom = `${insets.bottom}px`;
    }
  }
}

// Создаем глобальный экземпляр
const telegramWebApp = new TelegramWebApp();

export default telegramWebApp; 