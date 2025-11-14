import React, { useState, useRef } from 'react';
import { backendService } from './backendService';
import { wardrobeService } from './supabase';
import LoadingModal from './LoadingModal';
import { Image } from 'lucide-react';
import { normalizeText } from './utils/textUtils';

const AddWardrobeItem = ({ telegramId, onItemAdded, onClose }) => {

  const [step, setStep] = useState('select'); // select, processing, edit, saving
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

  // Выбрать файл из галереи
  const selectFromGallery = (event) => {
    try {
      const file = event.target.files[0];
      if (file) {
        setImageFile(file);
        setStep('processing');
        processImage(file);
      } else {
        setError('Файл не выбран');
      }
    } catch (error) {
      console.error('Gallery selection error:', error);
      setError('Ошибка при выборе файла из галереи');
      setStep('select');
    }
  };

  // Обработка изображения
  const processImage = async (file) => {
    try {
      // Проверяем размер файла перед обработкой
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        throw new Error('Файл слишком большой. Максимальный размер: 10MB');
      }
      
      // Проверяем тип файла
      if (!file.type.startsWith('image/')) {
        throw new Error('Выбранный файл не является изображением');
      }
      
      setShowLoadingModal(true);
      setError(null);
      
      // Анализируем изображение с AI
      const result = await backendService.analyzeWardrobeItem(file);
      
      if (result.success) {
        setProcessedImage(result.image_base64);
        setAnalysis(result.analysis);
        
        // Заполняем форму данными из AI анализа
        setFormData({
          category: normalizeText(result.analysis.category || ''),
          season: normalizeText(result.analysis.season || ''),
          description: normalizeText(result.analysis.description || '')
        });
        
        setStep('edit');
      } else {
        throw new Error(result.error || 'Неизвестная ошибка при обработке изображения');
      }
    } catch (error) {
      console.error('Ошибка обработки изображения:', error.message);
      
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
      
      setError(errorMessage);
      setStep('select');
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
      let compressedBlob;
      try {
        compressedBlob = await backendService.aggressiveCompressImage(imageBlob);
      } catch (compressionError) {
        console.error('Ошибка сжатия изображения:', compressionError);
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
      
      if (onItemAdded) {
        onItemAdded(newItem);
      }
      
      // Закрываем модальное окно
      handleClose();
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
    setStep('select');
    setImageFile(null);
    setProcessedImage(null);
    setAnalysis(null);
    setFormData({ category: '', season: '', description: '' });
    setError(null);
    onClose();
  };

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

        {step === 'select' && (
          <div className="add-item-content" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button 
              className="btn-primary"
              onClick={() => fileInputRef.current?.click()}
            >
              Добавить фото
            </button>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={selectFromGallery}
              style={{ display: 'none' }}
            />
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
                  placeholder="Например: Лето, Зима, Всесезонное"
                />
              </div>
              
              <div className="form-group">
                <label>Описание:</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Например: Черное платье миди длины"
                  rows={3}
                />
              </div>
            </div>
            
            <div className="form-actions">
              <button className="btn-secondary" onClick={handleClose}>
                Отмена
              </button>
              <button 
                className="btn-primary" 
                onClick={saveItem}
                disabled={loading}
              >
                {loading ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          </div>
        )}

        {/* Модальное окно загрузки */}
        <LoadingModal 
          isVisible={showLoadingModal}
          title="Анализируем изображение"
          subtitle="AI определяет категорию, сезон и описание вещи"
        />
      </div>
    </div>
  );
};

export default AddWardrobeItem; 