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
      setStep('select');
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
        console.error('❌ Ошибка в ответе backend:', result);
        throw new Error(result.error || 'Неизвестная ошибка при обработке изображения');
      }
    } catch (error) {
      console.error('❌ Ошибка обработки изображения:', error);
      setError(error.message || 'Ошибка при обработке изображения');
      setStep('select');
    } finally {
      setShowLoadingModal(false);
    }
  };

  // Сохранение вещи
  const saveItem = async () => {
    if (!imageFile || !formData.category || !formData.season || !formData.description) {
      setError('Пожалуйста, заполните все поля');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Генерируем уникальный ID для изображения
      const imageId = Date.now().toString();
      
      // Конвертируем base64 в Blob
      const base64Response = await fetch(`data:image/png;base64,${processedImage}`);
      const originalBlob = await base64Response.blob();
      
      // Сохраняем изображение
      await wardrobeService.uploadImage(telegramId, imageId, originalBlob);
      
      // Сохраняем вещь в базу данных
      const newItem = await wardrobeService.addItem({
        telegram_id: telegramId,
        category: formData.category,
        season: formData.season,
        description: formData.description,
        image_id: imageId
      });

      if (onItemAdded) {
        onItemAdded(newItem);
      }
      
      // Закрываем модальное окно
      handleClose();
    } catch (error) {
      console.error('Error saving item:', error);
      setError('Ошибка сохранения вещи');
    } finally {
      setLoading(false);
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