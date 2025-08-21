import React, { useState, useRef } from 'react';
import { backendService } from './backendService';
import { wardrobeService } from './supabase';
import LoadingModal from './LoadingModal';
import { Image } from 'lucide-react';

const AddItemPage = ({ telegramId, onItemAdded, onClose }) => {
  // Функция для нормализации текста (первая буква заглавная, остальные строчные)
  const normalizeText = (text) => {
    if (!text) return '';
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  };

  // Функция сжатия изображения
  const compressImage = (blob, maxWidth, quality) => {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        // Вычисляем новые размеры
        let { width, height } = img;
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
        
        canvas.width = width;
        canvas.height = height;
        
        // Рисуем изображение с новыми размерами
        ctx.drawImage(img, 0, 0, width, height);
        
        // Конвертируем в blob с заданным качеством
        canvas.toBlob(resolve, 'image/jpeg', quality);
      };
      
      img.src = URL.createObjectURL(blob);
    });
  };

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
    const file = event.target.files[0];
    if (file) {
      setImageFile(file);
      setStep('processing');
      processImage(file);
    }
  };

  // Обработка изображения
  const processImage = async (file) => {
    setShowLoadingModal(true);
    setError(null);

    try {
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
        setError('Ошибка анализа изображения');
        setStep('select');
      }
    } catch (error) {
      console.error('Error processing image:', error);
      setError('Ошибка обработки изображения');
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
      
      // Конвертируем base64 в Blob и сжимаем изображение
      const base64Response = await fetch(`data:image/png;base64,${processedImage}`);
      const originalBlob = await base64Response.blob();
      
      // Сжимаем изображение до разумного размера
      const compressedBlob = await compressImage(originalBlob, 600, 0.6);
      
      // Проверяем размер сжатого файла
      if (compressedBlob.size > 5 * 1024 * 1024) { // 5MB
        console.warn('Compressed image is still too large:', compressedBlob.size);
        // Дополнительное сжатие
        const furtherCompressedBlob = await compressImage(compressedBlob, 400, 0.4);
        await wardrobeService.uploadImage(telegramId, imageId, furtherCompressedBlob);
      } else {
        // Сохраняем изображение
        await wardrobeService.uploadImage(telegramId, imageId, compressedBlob);
      }
      
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

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleClose = () => {
    setStep('select');
    setImageFile(null);
    setProcessedImage(null);
    setAnalysis(null);
    setFormData({ category: '', season: '', description: '' });
    setError(null);
    if (onClose) {
      onClose();
    }
  };

  // Рендер шага выбора
  if (step === 'select') {
    return (
      <>
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
          
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </div>
        
        {/* Модальное окно загрузки */}
        <LoadingModal 
          isVisible={showLoadingModal}
          title="Анализируем изображение"
          subtitle="AI определяет категорию, сезон и описание вещи"
        />
      </>
    );
  }

  // Рендер шага редактирования
  if (step === 'edit') {
    return (
      <>
        <div className="add-item-content">
          <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--color-text-primary)' }}>
            Редактировать информацию
          </h2>
          
          <div className="image-preview" style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
            <img 
              src={`data:image/png;base64,${processedImage}`} 
              alt="Preview" 
              style={{ 
                maxWidth: '200px', 
                maxHeight: '200px', 
                borderRadius: '8px',
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
              <label>Сезон:</label>
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
        
        {/* Модальное окно загрузки */}
        <LoadingModal 
          isVisible={showLoadingModal}
          title="Анализируем изображение"
          subtitle="AI определяет категорию, сезон и описание вещи"
        />
      </>
    );
  }

  return null;
};

export default AddItemPage; 