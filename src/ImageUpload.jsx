import React, { useState, useRef, useCallback } from 'react';

const ImageUpload = ({ onImageUpload, multiple = false, maxSize = 5 * 1024 * 1024 }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, []);

  const handleFileSelect = useCallback((e) => {
    const files = Array.from(e.target.files);
    handleFiles(files);
  }, []);

  const handleFiles = useCallback(async (files) => {
    const validFiles = files.filter(file => {
      if (!file.type.startsWith('image/')) {
        alert('Пожалуйста, загружайте только изображения');
        return false;
      }
      if (file.size > maxSize) {
        alert(`Файл слишком большой. Максимальный размер: ${maxSize / 1024 / 1024}MB`);
        return false;
      }
      return true;
    });

    if (validFiles.length === 0) return;

    setUploading(true);
    try {
      const results = await Promise.all(
        validFiles.map(file => {
          return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
              resolve({
                file,
                preview: e.target.result,
                name: file.name,
                size: file.size
              });
            };
            reader.readAsDataURL(file);
          });
        })
      );

      if (onImageUpload) {
        onImageUpload(multiple ? results : results[0]);
      }
    } catch (error) {
      console.error('Ошибка при обработке файлов:', error);
      alert('Ошибка при загрузке изображений');
    } finally {
      setUploading(false);
    }
  }, [maxSize, multiple, onImageUpload]);

  return (
    <div
      className={`image-upload ${isDragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple={multiple}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
      
      <div className="upload-content">
        {uploading ? (
          <div className="upload-loading">
            <div className="spinner"></div>
            <p>Загрузка...</p>
          </div>
        ) : (
          <>
            <div className="upload-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7,10 12,15 17,10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </div>
            <p className="upload-text">
              {isDragOver ? 'Отпустите файлы здесь' : 'Перетащите изображения сюда или нажмите для выбора'}
            </p>
            <p className="upload-hint">
              Поддерживаются: JPG, PNG, GIF (макс. {maxSize / 1024 / 1024}MB)
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default ImageUpload; 