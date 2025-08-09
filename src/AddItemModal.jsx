import React from 'react';
import { Camera, Image, X } from 'lucide-react';

const AddItemModal = ({ isOpen, onClose, onSelectCamera, onSelectGallery }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Добавить вещь</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        <div className="add-item-options">
          <button 
            className="add-option-btn camera-option"
            onClick={onSelectCamera}
          >
            <Camera size={32} />
            <span>Сделать фото</span>
          </button>
          
          <button 
            className="add-option-btn gallery-option"
            onClick={onSelectGallery}
          >
            <Image size={32} />
            <span>Выбрать из галереи</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddItemModal; 