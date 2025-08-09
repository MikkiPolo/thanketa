import React from 'react';

const ProgressBar = ({ progress, animated = true, showPercentage = false }) => {
  return (
    <div className="progress-container">
      <div className="progress-bar">
        <div 
          className={`progress ${animated ? 'animated' : ''}`}
          style={{ width: `${progress}%` }}
        />
      </div>
      {showPercentage && (
        <div className="progress-text">
          {Math.round(progress)}%
        </div>
      )}
    </div>
  );
};

export default ProgressBar; 