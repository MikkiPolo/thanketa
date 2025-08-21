import React from 'react';
import { Image, X } from 'lucide-react';

const AddItemModal = ({ isOpen, onClose, onSelectGallery }) => {
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
            className="add-option-btn gallery-option"
            onClick={onSelectGallery}
          >
            <Image size={32} />
            <span>Добавить фото</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddItemModal; 