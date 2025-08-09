import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, MessageCircle, X } from 'lucide-react';

const AIFeedback = ({ analysisResult, onFeedback, onClose }) => {
  const [rating, setRating] = useState(null);
  const [correction, setCorrection] = useState('');
  const [showCorrection, setShowCorrection] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRating = (newRating) => {
    setRating(newRating);
    if (newRating === 'negative') {
      setShowCorrection(true);
    } else {
      setShowCorrection(false);
    }
  };

  const handleSubmit = async () => {
    if (!rating) return;

    setIsSubmitting(true);
    try {
      const feedbackData = {
        user_id: 'anonymous', // TODO: получить из контекста пользователя
        item_id: analysisResult.id || Date.now().toString(),
        rating: rating,
        correction: showCorrection ? correction : null
      };

      const response = await fetch('/ai-feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData),
      });

      if (response.ok) {
        onFeedback && onFeedback(feedbackData);
        onClose && onClose();
      } else {
        console.error('Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.7) return 'text-green-600';
    if (confidence > 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceText = (confidence) => {
    if (confidence > 0.7) return 'Высокая';
    if (confidence > 0.4) return 'Средняя';
    return 'Низкая';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Оцените анализ AI
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X size={20} />
          </button>
        </div>

        {/* Результат анализа */}
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Категория:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {analysisResult.category}
              </span>
            </div>
            
            {analysisResult.season && (
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Сезон:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {analysisResult.season}
                </span>
              </div>
            )}
            
            {analysisResult.style && (
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Стиль:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {analysisResult.style}
                </span>
              </div>
            )}
            
            {analysisResult.colors && analysisResult.colors.length > 0 && (
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Цвета:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {analysisResult.colors.join(', ')}
                </span>
              </div>
            )}
            
            {analysisResult.confidence && (
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Уверенность:</span>
                <span className={`text-sm font-medium ${getConfidenceColor(analysisResult.confidence)}`}>
                  {getConfidenceText(analysisResult.confidence)} ({Math.round(analysisResult.confidence * 100)}%)
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Кнопки оценки */}
        <div className="flex justify-center space-x-4 mb-4">
          <button
            onClick={() => handleRating('positive')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
              rating === 'positive'
                ? 'bg-green-100 border-green-500 text-green-700 dark:bg-green-900 dark:border-green-400 dark:text-green-300'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <ThumbsUp size={16} />
            <span>Правильно</span>
          </button>
          
          <button
            onClick={() => handleRating('negative')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
              rating === 'negative'
                ? 'bg-red-100 border-red-500 text-red-700 dark:bg-red-900 dark:border-red-400 dark:text-red-300'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <ThumbsDown size={16} />
            <span>Неправильно</span>
          </button>
        </div>

        {/* Поле для исправления */}
        {showCorrection && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Что не так? (опционально)
            </label>
            <textarea
              value={correction}
              onChange={(e) => setCorrection(e.target.value)}
              placeholder="Опишите, что AI определил неправильно..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              rows="3"
            />
          </div>
        )}

        {/* Кнопки действий */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Отмена
          </button>
          
          <button
            onClick={handleSubmit}
            disabled={!rating || isSubmitting}
            className={`px-4 py-2 rounded-lg text-white transition-colors ${
              rating && !isSubmitting
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? 'Отправка...' : 'Отправить'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIFeedback; 