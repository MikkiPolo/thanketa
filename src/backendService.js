// Сервис для работы с backend API
import { BACKEND_URL, BACKEND_URL_WITH_VERSION, API_ENDPOINTS } from './config.js';

// Функция для retry запросов
const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      // Ждем перед повторной попыткой
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
};

export const backendService = {
  // Проверка здоровья сервера
  async healthCheck() {
    try {
      const response = await retryRequest(async () => {
        const res = await fetch(`${BACKEND_URL}${API_ENDPOINTS.HEALTH}?v=${Date.now()}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res;
      });
      return await response.json();
    } catch (error) {
      console.error('Backend health check failed:', error);
      throw error;
    }
  },

  // Удаление фона с изображения
  async removeBackground(imageFile) {
    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.REMOVE_BACKGROUND}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Background removal failed:', error);
      throw error;
    }
  },

  // Анализ гардероба с AI - UPDATED 2024-08-06 23:35
  async analyzeWardrobeItem(imageFile, userId = 'anonymous') {
    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('user_id', userId);

      const url = `${BACKEND_URL}${API_ENDPOINTS.ANALYZE_WARDROBE}?v=${Date.now()}`;
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Ошибка анализа гардероба:', response.status);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Ошибка анализа гардероба:', error.message);
      throw error;
    }
  },

    // Конвертация base64 в Blob
  base64ToBlob(base64String) {
    const byteCharacters = atob(base64String);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: 'image/png' });
  },

  // Сжатие изображения с автоматическим подбором параметров
  async compressImage(imageFile, maxWidth = 800, quality = 0.8) {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      const handleLoad = () => {
        try {
          // Вычисляем новые размеры
          let { width, height } = img;
          
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
          
          // Устанавливаем размер canvas
          canvas.width = width;
          canvas.height = height;
          
          // Очищаем canvas с прозрачностью
          ctx.clearRect(0, 0, width, height);
          
          // Рисуем изображение с новыми размерами
          ctx.drawImage(img, 0, 0, width, height);
          
          // Конвертируем в Blob с прозрачностью (PNG)
          canvas.toBlob((compressedBlob) => {
            if (compressedBlob) {
              // Создаем новый File объект с оригинальным именем
              const compressedFile = new File([compressedBlob], imageFile.name, {
                type: 'image/png',
                lastModified: Date.now()
              });
              resolve(compressedFile);
            } else {
              reject(new Error('Failed to create compressed blob'));
            }
          }, 'image/png', quality);
        } catch (error) {
          reject(new Error('Failed to process image: ' + error.message));
        }
      };
      
      img.onload = handleLoad;
      img.onerror = (error) => {
        console.error('Image load error:', error);
        reject(new Error('Load failed'));
      };
      
      // Создаем URL для изображения с обработкой ошибок
      try {
        const url = URL.createObjectURL(imageFile);
        img.src = url;
        
        // Очищаем URL после обработки
        img.onload = () => {
          URL.revokeObjectURL(url);
          handleLoad();
        };
      } catch (error) {
        reject(new Error('Failed to create object URL: ' + error.message));
      }
    });
  },

  // Агрессивное сжатие для больших файлов
  async aggressiveCompressImage(imageFile) {
    console.log('Original file size:', imageFile.size, 'bytes');
    
    // Первое сжатие: 600px, качество 0.7
    let compressed = await this.compressImage(imageFile, 600, 0.7);
    console.log('First compression:', compressed.size, 'bytes');
    
    // Если файл все еще больше 2MB, сжимаем еще больше
    if (compressed.size > 2 * 1024 * 1024) {
      compressed = await this.compressImage(compressed, 400, 0.5);
      console.log('Second compression:', compressed.size, 'bytes');
    }
    
    // Если файл все еще больше 1MB, сжимаем до минимума
    if (compressed.size > 1 * 1024 * 1024) {
      compressed = await this.compressImage(compressed, 300, 0.3);
      console.log('Final compression:', compressed.size, 'bytes');
    }
    
    return compressed;
  },

  // Отправка обратной связи по AI анализу
  async submitAIFeedback(feedbackData) {
    try {
      const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.AI_FEEDBACK}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('AI feedback submission failed:', error);
      throw error;
    }
  },

  // Получение статистики AI производительности
  async getAIPerformance() {
    try {
      const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.AI_PERFORMANCE}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('AI performance fetch failed:', error);
      throw error;
    }
  },

  // Получение объяснения AI анализа
  async getAIExplanation(analysisResult) {
    try {
      const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.AI_EXPLANATION}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ analysis_result: analysisResult }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('AI explanation fetch failed:', error);
      throw error;
    }
  },

  // Умные рекомендации гардероба
  async getWardrobeRecommendations(profile, wardrobe) {
    try {
      const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.WARDROBE_RECOMMENDATIONS}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile, wardrobe })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return {
        recommendations: data?.recommendations || '',
        unsuitableItems: Array.isArray(data?.unsuitable_items) ? data.unsuitable_items : []
      };
    } catch (error) {
      console.error('Wardrobe recommendations fetch failed:', error);
      throw error;
    }
  }
  ,
  async getLooks(looksRequest) {
    try {
      const url = `${BACKEND_URL}${API_ENDPOINTS.GET_LOOKS || '/looks'}`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(looksRequest || {})
      });
      if (!resp.ok) throw new Error(`HTTP error! status: ${resp.status}`);
      return await resp.json();
    } catch (e) {
      console.error('Looks fetch failed:', e);
      throw e;
    }
  }
}; 