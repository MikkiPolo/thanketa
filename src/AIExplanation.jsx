import React, { useState, useEffect } from 'react';
import { Info, Lightbulb, Clock, Brain } from 'lucide-react';

const AIExplanation = ({ analysisResult, onClose }) => {
  const [explanation, setExplanation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (analysisResult) {
      generateExplanation();
    }
  }, [analysisResult]);

  const generateExplanation = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/ai-explanation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_result: analysisResult
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setExplanation(data.explanation);
      } else {
        setError('Не удалось получить объяснение');
      }
    } catch (error) {
      console.error('Error generating explanation:', error);
      setError('Ошибка при получении объяснения');
    } finally {
      setIsLoading(false);
    }
  };

  const getAITypeIcon = (aiType) => {
    switch (aiType) {
      case 'gpt':
        return <Brain className="w-4 h-4" />;
      case 'huggingface':
        return <Brain className="w-4 h-4" />;
      case 'rule_based':
        return <Lightbulb className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getAITypeText = (aiType) => {
    switch (aiType) {
      case 'gpt':
        return 'GPT AI';
      case 'huggingface':
        return 'HuggingFace AI';
      case 'rule_based':
        return 'Правила';
      default:
        return 'AI';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.7) return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
    if (confidence > 0.4) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300';
    return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300';
  };

  const getConfidenceText = (confidence) => {
    if (confidence > 0.7) return 'Высокая';
    if (confidence > 0.4) return 'Средняя';
    return 'Низкая';
  };

  if (!analysisResult) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-lg w-full mx-4 shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
            <Info className="w-5 h-5" />
            <span>Объяснение анализа</span>
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        {/* Информация об анализе */}
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Категория:</span>
              <div className="font-medium text-gray-900 dark:text-white">
                {analysisResult.category}
              </div>
            </div>
            
            {analysisResult.season && (
              <div>
                <span className="text-gray-600 dark:text-gray-400">Сезон:</span>
                <div className="font-medium text-gray-900 dark:text-white">
                  {analysisResult.season}
                </div>
              </div>
            )}
            
            {analysisResult.style && (
              <div>
                <span className="text-gray-600 dark:text-gray-400">Стиль:</span>
                <div className="font-medium text-gray-900 dark:text-white">
                  {analysisResult.style}
                </div>
              </div>
            )}
            
            {analysisResult.colors && analysisResult.colors.length > 0 && (
              <div>
                <span className="text-gray-600 dark:text-gray-400">Цвета:</span>
                <div className="font-medium text-gray-900 dark:text-white">
                  {analysisResult.colors.join(', ')}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Метаданные AI */}
        <div className="mb-6 flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-center space-x-2">
            {getAITypeIcon(analysisResult.ai_type)}
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Анализ выполнен: {getAITypeText(analysisResult.ai_type)}
            </span>
          </div>
          
          {analysisResult.confidence && (
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(analysisResult.confidence)}`}>
              {getConfidenceText(analysisResult.confidence)} ({Math.round(analysisResult.confidence * 100)}%)
            </div>
          )}
        </div>

        {/* Объяснение */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
            <Lightbulb className="w-4 h-4" />
            <span>Почему AI так решил?</span>
          </h4>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600 dark:text-gray-400">Генерируем объяснение...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
            </div>
          ) : (
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-gray-800 dark:text-gray-200 text-sm leading-relaxed">
                {explanation || 'Объяснение недоступно'}
              </p>
            </div>
          )}
        </div>

        {/* Временная метка */}
        {analysisResult.timestamp && (
          <div className="flex items-center justify-center text-xs text-gray-500 dark:text-gray-400 space-x-1">
            <Clock className="w-3 h-3" />
            <span>
              Анализ выполнен: {new Date(analysisResult.timestamp).toLocaleString('ru-RU')}
            </span>
          </div>
        )}

        {/* Кнопка закрытия */}
        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIExplanation; 