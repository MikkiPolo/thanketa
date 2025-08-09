import React, { useState, useRef } from 'react';
import { backendService } from './backendService';
import { wardrobeService } from './supabase';
import LoadingModal from './LoadingModal';
import { Camera, Image } from 'lucide-react';
import { normalizeText } from './utils/textUtils';

const AddWardrobeItem = ({ telegramId, onItemAdded, onClose }) => {


  const [step, setStep] = useState('camera'); // camera, processing, edit, saving
  const [imageFile, setImageFile] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [formData, setFormData] = useState({
    category: '',
    season: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [showLoadingModal, setShowLoadingModal] = useState(false);
  const [error, setError] = useState(null);

  
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Запуск камеры
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Camera access denied:', error);
      setError('Не удалось получить доступ к камере');
    }
  };

  // Остановка камеры
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  // Сделать снимок
  const takePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      const context = canvas.getContext('2d');
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0);
      
      canvas.toBlob((blob) => {
        const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
        setImageFile(file);
        setStep('processing');
        processImage(file);
      }, 'image/jpeg');
    }
  };

  // Выбрать файл из галереи
  const selectFromGallery = (event) => {
    try {
      const file = event.target.files[0];
      if (file) {
        console.log('Selected file:', {
          name: file.name,
          type: file.type,
          size: file.size
        });
        
        setImageFile(file);
        setStep('processing');
        processImage(file);
      } else {
        setError('Файл не выбран');
      }
    } catch (error) {
      console.error('Gallery selection error:', error);
      setError('Ошибка при выборе файла из галереи');
      setStep('camera');
    }
  };

  // Обработка изображения
  const processImage = async (file) => {
    try {
      console.log('🚀 Начинаем обработку изображения:', {
        name: file.name,
        type: file.type,
        size: file.size,
        lastModified: file.lastModified
      });
      
      // Проверяем размер файла перед обработкой
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        throw new Error('Файл слишком большой. Максимальный размер: 10MB');
      }
      
      // Проверяем тип файла
      if (!file.type.startsWith('image/')) {
        throw new Error('Выбранный файл не является изображением');
      }
      
      console.log('✅ Валидация файла прошла успешно');
      
      setShowLoadingModal(true);
      setError(null);
      
      console.log('📡 Отправляем запрос к backend...');
      
      // Анализируем изображение с AI
      const result = await backendService.analyzeWardrobeItem(file);
      
      console.log('📥 Получен ответ от backend:', {
        success: result.success,
        hasImage: !!result.image_base64,
        hasAnalysis: !!result.analysis
      });
      
      if (result.success) {
        setProcessedImage(result.image_base64);
        setAnalysis(result.analysis);
        
        // Заполняем форму данными из AI анализа
        setFormData({
          category: normalizeText(result.analysis.category || ''),
          season: normalizeText(result.analysis.season || ''),
          description: normalizeText(result.analysis.description || '')
        });
        
        console.log('✅ Обработка завершена успешно, переходим к редактированию');
        setStep('edit');
      } else {
        throw new Error(result.error || 'Ошибка анализа изображения');
      }
    } catch (error) {
      console.error('❌ Image processing failed:', error);
      console.error('❌ Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      
      let errorMessage = 'Ошибка обработки изображения';
      
      if (error.message?.includes('Файл слишком большой')) {
        errorMessage = 'Файл слишком большой. Максимальный размер: 10MB';
      } else if (error.message?.includes('HTTP error! status: 413')) {
        errorMessage = 'Файл слишком большой для обработки. Попробуйте уменьшить изображение.';
      } else if (error.message?.includes('Load failed')) {
        errorMessage = 'Не удалось загрузить изображение. Попробуйте другое изображение или перезагрузите страницу.';
      } else if (error.message?.includes('не является изображением')) {
        errorMessage = 'Выбранный файл не является изображением. Выберите файл с расширением .jpg, .png, .jpeg или .webp';
      } else if (error.message?.includes('Failed to fetch')) {
        errorMessage = 'Ошибка сети. Проверьте подключение к интернету и попробуйте снова.';
      } else if (error.message?.includes('NetworkError')) {
        errorMessage = 'Ошибка сети. Проверьте подключение к интернету и попробуйте снова.';
      } else {
        errorMessage = 'Ошибка обработки изображения: ' + error.message;
      }
      
      console.log('💬 Показываем пользователю ошибку:', errorMessage);
      setError(errorMessage);
      setStep('camera');
    } finally {
      setShowLoadingModal(false);
    }
  };

  // Сохранение вещи
  const saveItem = async () => {
    if (!formData.category || !formData.season || !formData.description) {
      setError('Заполните все поля');
      return;
    }

    setShowLoadingModal(true);
    setError(null);

    try {
      // Генерируем правильный UUID для изображения
      const imageId = crypto.randomUUID();
      
      // Конвертируем base64 в Blob
      const imageBlob = backendService.base64ToBlob(processedImage);
      
      // Агрессивно сжимаем изображение перед загрузкой
      console.log('Compressing image...');
      let compressedBlob;
      try {
        compressedBlob = await backendService.aggressiveCompressImage(imageBlob);
        console.log('Image compressed:', compressedBlob.size, 'bytes');
      } catch (compressionError) {
        console.error('Compression failed:', compressionError);
        throw new Error('Не удалось сжать изображение. Попробуйте другое изображение.');
      }
      
      // Проверяем размер файла
      if (compressedBlob.size > 5 * 1024 * 1024) {
        throw new Error('Файл слишком большой даже после сжатия. Попробуйте другое изображение.');
      }
      
      // Сохраняем изображение в Supabase Storage
      await wardrobeService.uploadImage(telegramId, imageId, compressedBlob);
      
      // Нормализуем текст перед сохранением
      const normalizedData = {
        telegram_id: telegramId,
        category: normalizeText(formData.category),
        season: normalizeText(formData.season),
        description: normalizeText(formData.description),
        image_id: imageId,
        ai_generated: true
      };
      
      // Сохраняем данные вещи в базу
      const newItem = await wardrobeService.addItem(normalizedData);
      
      onItemAdded(newItem);
      onClose();
    } catch (error) {
      console.error('Save failed:', error);
      
      // Показываем понятное сообщение об ошибке
      let errorMessage = 'Ошибка сохранения';
      
      if (error.message?.includes('Файл слишком большой')) {
        errorMessage = 'Файл слишком большой. Попробуйте другое изображение или уменьшите его размер.';
      } else if (error.message?.includes('Не удалось сжать изображение')) {
        errorMessage = 'Не удалось обработать изображение. Попробуйте другое изображение.';
      } else if (error.message?.includes('Ошибка сети')) {
        errorMessage = 'Ошибка сети. Проверьте подключение к интернету и попробуйте снова.';
      } else if (error.message?.includes('CORS')) {
        errorMessage = 'Ошибка доступа к серверу. Попробуйте обновить страницу.';
      } else if (error.message?.includes('Load failed')) {
        errorMessage = 'Не удалось загрузить изображение. Попробуйте другое изображение.';
      } else {
        errorMessage = 'Ошибка сохранения: ' + error.message;
      }
      
      setError(errorMessage);
    } finally {
      setShowLoadingModal(false);
    }
  };

  // Обработка изменений в форме
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Закрытие модального окна
  const handleClose = () => {
    stopCamera();
    onClose();
  };

  // Очистка камеры при закрытии модального окна
  React.useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Добавить вещь в гардероб</h3>
          <button className="close-btn" onClick={handleClose}>×</button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {step === 'camera' && (
          <div className="camera-step">
            <div className="camera-container" style={{ display: 'none' }}>
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted
                style={{ width: '100%', maxWidth: '400px' }}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
            </div>
            
            <div className="camera-controls" id="camera-controls">
              <button className="btn-primary" onClick={async () => {
                await startCamera();
                document.querySelector('.camera-container').style.display = 'block';
                document.querySelector('.camera-shoot-controls').style.display = 'block';
                document.getElementById('camera-controls').style.display = 'none';
              }}>
                <Camera size={20} />
                Запустить камеру
              </button>
              <button className="btn-secondary" onClick={() => fileInputRef.current?.click()}>
                <Image size={20} />
                Выбрать из галереи
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={selectFromGallery}
                style={{ display: 'none' }}
              />
            </div>
            
            <div className="camera-shoot-controls" style={{ display: 'none' }}>
              <button className="btn-primary" onClick={takePhoto}>
                <Camera size={20} />
                Сделать снимок
              </button>
              <button className="btn-secondary" onClick={() => {
                stopCamera();
                document.querySelector('.camera-container').style.display = 'none';
                document.querySelector('.camera-shoot-controls').style.display = 'none';
                document.getElementById('camera-controls').style.display = 'block';
              }}>
                Отменить
              </button>
            </div>
          </div>
        )}



        {step === 'edit' && (
          <div className="edit-step">
            <div className="image-preview">
              <img 
                src={`data:image/png;base64,${processedImage}`}
                alt="Обработанное изображение"
                style={{ 
                  maxWidth: '200px', 
                  maxHeight: '200px',
                  backgroundColor: 'transparent'
                }}
              />
            </div>
            

            
            <div className="form-fields">
              <div className="form-group">
                <label>Категория:</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  placeholder="Например: Платье, Брюки, Блузка"
                />
              </div>
              
              <div className="form-group">
                <label>Сезонность:</label>
                <input
                  type="text"
                  value={formData.season}
                  onChange={(e) => handleInputChange('season', e.target.value)}
                  placeholder="Например: Лето, Зима, Демисезон"
                />
              </div>
              
              <div className="form-group">
                <label>Описание:</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Описание вещи"
                  rows="3"
                />
              </div>
            </div>
            
            <div className="form-actions">
              <button 
                className="btn-primary" 
                onClick={saveItem}
                disabled={showLoadingModal}
              >
                Сохранить
              </button>
              <button className="btn-secondary" onClick={handleClose}>
                Отменить
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Модальное окно загрузки */}
      <LoadingModal 
        isVisible={showLoadingModal}
        title={step === 'processing' ? "Анализируем изображение..." : "Сохраняем вещь..."}
        subtitle={step === 'processing' 
          ? "ИИ изучает вашу вещь и определяет её характеристики" 
          : "Загружаем изображение и сохраняем данные"
        }
      />
    </div>
  );
};

export default AddWardrobeItem; 