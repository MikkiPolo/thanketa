import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Brain, Lightbulb } from 'lucide-react';

const AIStats = ({ onClose }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAIStats();
  }, []);

  const fetchAIStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('/ai-performance');
      
      if (response.ok) {
        const data = await response.json();
        setStats(data.performance_stats);
      } else {
        setError('Не удалось загрузить статистику');
      }
    } catch (error) {
      console.error('Error fetching AI stats:', error);
      setError('Ошибка при загрузке статистики');
    } finally {
      setLoading(false);
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
        return <Brain className="w-4 h-4" />;
    }
  };

  const getAITypeName = (aiType) => {
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

  const getAccuracyColor = (accuracy) => {
    if (accuracy > 0.8) return 'text-green-600';
    if (accuracy > 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getAccuracyText = (accuracy) => {
    if (accuracy > 0.8) return 'Отличная';
    if (accuracy > 0.6) return 'Хорошая';
    return 'Требует улучшения';
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">Загружаем статистику...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
          <div className="text-center">
            <div className="text-red-600 dark:text-red-400 mb-4">
              <BarChart3 className="w-12 h-12 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Ошибка загрузки
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
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
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-lg w-full mx-4 shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
            <BarChart3 className="w-5 h-5" />
            <span>Статистика AI</span>
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        {stats && Object.keys(stats).length > 0 ? (
          <div className="space-y-4">
            {Object.entries(stats).map(([aiType, data]) => (
              <div key={aiType} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getAITypeIcon(aiType)}
                    <span className="font-medium text-gray-900 dark:text-white">
                      {getAITypeName(aiType)}
                    </span>
                  </div>
                  <div className={`text-sm font-medium ${getAccuracyColor(data.average_accuracy)}`}>
                    {getAccuracyText(data.average_accuracy)}
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Точность:</span>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {Math.round(data.average_accuracy * 100)}%
                    </div>
                  </div>
                  
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Анализов:</span>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {data.total_predictions}
                    </div>
                  </div>
                  
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Дней:</span>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {data.days_analyzed}
                    </div>
                  </div>
                  
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Среднее в день:</span>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {Math.round(data.total_predictions / data.days_analyzed)}
                    </div>
                  </div>
                </div>
                
                {/* Прогресс бар точности */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <span>Точность</span>
                    <span>{Math.round(data.average_accuracy * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        data.average_accuracy > 0.8
                          ? 'bg-green-500'
                          : data.average_accuracy > 0.6
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${data.average_accuracy * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              Статистика пока недоступна. Попробуйте позже.
            </p>
          </div>
        )}

        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <p>• Статистика обновляется в реальном времени</p>
            <p>• Точность рассчитывается на основе обратной связи пользователей</p>
            <p>• Данные хранятся за последние 30 дней</p>
          </div>
        </div>

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

export default AIStats; 