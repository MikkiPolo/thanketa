import React, { useState } from 'react';
import { backendService } from './backendService';

const AIRecommendations = ({ profile, wardrobe }) => {
  const [recommendations, setRecommendations] = useState('');
  const [unsuitable, setUnsuitable] = useState([]);
  const [loading, setLoading] = useState(false);

  const generateRecommendations = async () => {
    if (!profile || !wardrobe || wardrobe.length === 0) {
      setRecommendations('Недостаточно данных для анализа. Заполните анкету и добавьте вещи в гардероб.');
      setUnsuitable([]);
      return;
    }

    setLoading(true);
    
    try {
      // Пробуем умные рекомендации с бэкенда
      const data = await backendService.getWardrobeRecommendations(profile, wardrobe);
      const smartText = data.recommendations;
      const unsuitableItems = data.unsuitableItems || [];
      if (smartText && smartText.trim().length > 0) {
        setRecommendations(smartText);
        setUnsuitable(unsuitableItems);
        // Помечаем неподходящие вещи в БД (Supabase)
        try {
          if (Array.isArray(unsuitableItems) && unsuitableItems.length > 0) {
            const mod = await import('./supabase');
            for (const u of unsuitableItems) {
              if (u && u.id) {
                mod.wardrobeService.setItemSuitability(u.id, false);
              }
            }
          }
        } catch (e) { /* ignore */ }
        // Кешируем в localStorage
        try {
          const cache = {
            recommendations: smartText,
            unsuitable: unsuitableItems,
            savedAt: Date.now(),
            profileHash: JSON.stringify(profile),
            wardrobeHash: JSON.stringify(wardrobe.map(i => ({ id: i.id, category: i.category, season: i.season, description: i.description })))
          };
          localStorage.setItem('ai_reco_cache', JSON.stringify(cache));
        } catch (e) {
          // ignore storage errors
        }
      } else {
        // Fallback к локальной логике
        const analysis = analyzeWardrobe(profile, wardrobe);
        setRecommendations(analysis);
        setUnsuitable([]);
      }
    } catch (error) {
      // Fallback при ошибке сети/сервера
      const analysis = analyzeWardrobe(profile, wardrobe);
      setRecommendations(analysis);
      setUnsuitable([]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeWardrobe = (profile, wardrobe) => {
    // Анализ гардероба на основе профиля
    const categories = {};
    const seasons = {};
    const colors = {};
    
    wardrobe.forEach(item => {
      // Подсчет категорий
      categories[item.category] = (categories[item.category] || 0) + 1;
      
      // Подсчет сезонов
      seasons[item.season] = (seasons[item.season] || 0) + 1;
    });

    return generateGeneralRecommendations(profile, wardrobe);
  };



  const generateGeneralRecommendations = (profile, wardrobe) => {
    const recommendations = [];
    
    // Анализ по типу фигуры
    if (profile.figura) {
      const figuraLower = profile.figura.toLowerCase();
      if (figuraLower.includes('яблоко') || figuraLower.includes('o')) {
        recommendations.push('• Для вашего типа фигуры выбирайте платья с завышенной талией и джинсы с высокой посадкой');
      } else if (figuraLower.includes('треугольник') || figuraLower.includes('a')) {
        recommendations.push('• Носите пиджаки и блузки с интересными деталями в верхней части');
      } else if (figuraLower.includes('песочные часы') || figuraLower.includes('x')) {
        recommendations.push('• Подчеркивайте талию поясами и заправляйте блузки в юбки/брюки');
      }
    }
    
    // Анализ по цветотипу
    if (profile.cvetotip) {
      const cvetotipLower = profile.cvetotip.toLowerCase();
      if (cvetotipLower.includes('весна') || cvetotipLower.includes('тепл')) {
        recommendations.push('• Выбирайте теплые оттенки: бежевый, персиковый, коралловый');
      } else if (cvetotipLower.includes('лето') || cvetotipLower.includes('холодн')) {
        recommendations.push('• Идеальны холодные оттенки: голубой, серый, розовый');
      }
    }
    
    // Рекомендации по количеству
    if (wardrobe.length < 20) {
      recommendations.push('• Расширьте базовый гардероб - добавьте больше базовых вещей');
    }
    
    if (wardrobe.length > 100) {
      recommendations.push('• Проведите ревизию - возможно, есть вещи, которые вы не носите');
    }
    
    // Рекомендации по аксессуарам
    const accessories = wardrobe.filter(item => 
      ['Сумка', 'Серьги', 'Бусы', 'Пояс', 'Шарф'].includes(item.category)
    ).length;
    
    if (accessories < 5) {
      recommendations.push('• Добавьте аксессуары - они оживляют любой образ');
    }
    
    // Анализ проблемных зон
    if (profile.like_zone) {
      recommendations.push(`• Подчеркивайте ${profile.like_zone} - используйте акценты и интересные детали`);
    }
    
    if (profile.dislike_zone) {
      recommendations.push(`• Для ${profile.dislike_zone} выбирайте свободный крой и вертикальные линии`);
    }
    
    return recommendations.length > 0 ? recommendations.join('\n') : '• Ваш гардероб хорошо сбалансирован!';
  };

  // Автозапрос отключён — используем только ручную кнопку
  // Но при маунте пытаемся прочитать кеш и показать последнюю версию
  React.useEffect(() => {
    try {
      const raw = localStorage.getItem('ai_reco_cache');
      if (!raw) return;
      const cached = JSON.parse(raw);
      if (cached && cached.recommendations) {
        setRecommendations(cached.recommendations);
        setUnsuitable(Array.isArray(cached.unsuitable) ? cached.unsuitable : []);
      }
    } catch (e) {
      // ignore
    }
  }, []);

  return (
    <div className="ai-recommendations">
      <h3>Анализ гардероба</h3>
      
      {loading ? (
        <div className="recommendations-loading">
          <div className="spinner"></div>
          <p>Анализируем ваш гардероб...</p>
        </div>
      ) : (
        <div className="recommendations-content">
          {recommendations ? (
            <div className="recommendations-text">
              {recommendations.split('\n').map((line, index) => (
                <p key={index} style={{ 
                  margin: line.startsWith('•') ? '0.5rem 0 0.5rem 1rem' : '0.5rem 0',
                  fontWeight: line.includes('**') ? 'bold' : 'normal'
                }}>
                  {line}
                </p>
              ))}
              {unsuitable && unsuitable.length > 0 && (
                <div className="unsuitable-block" style={{ marginTop: '1rem' }}>
                  <h4 style={{ margin: '0.5rem 0' }}>Неподходящие вещи</h4>
                  <ul style={{ paddingLeft: '1.25rem' }}>
                    {unsuitable.map((u) => (
                      <li key={u.id} style={{ marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 600 }}>{u.category || 'Вещь'}</span>
                        {u.description ? ` — ${u.description}` : ''}
                        {u.reason ? `: ${u.reason}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p>Нажмите кнопку для анализа гардероба</p>
          )}
        </div>
      )}
      
      <button 
        className="refresh-recommendations-btn"
        onClick={generateRecommendations}
        disabled={loading}
      >
        Обновить анализ
      </button>
    </div>
  );
};

export default AIRecommendations; 