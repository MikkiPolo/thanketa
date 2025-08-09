import React from 'react';

const LoadingSpinner = ({ size = 'medium', color = 'currentColor' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  };

  return (
    <div className="flex justify-center items-center">
      <div 
        className={`${sizeClasses[size]} animate-spin rounded-full border-2 border-transparent border-t-current`}
        style={{ color }}
        role="status"
        aria-label="Загрузка"
      >
        <span className="sr-only">Загрузка...</span>
      </div>
    </div>
  );
};

export default LoadingSpinner; 