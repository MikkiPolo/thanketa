import React, { useMemo } from 'react';
import AIRecommendations from './AIRecommendations';

const WardrobeStats = ({ wardrobe, profile }) => {
  const stats = useMemo(() => {
    if (!wardrobe || wardrobe.length === 0) {
      return {
        totalItems: 0,
        categories: {},
        seasons: {},
        mostUsedCategory: null,
        leastUsedCategory: null,
        seasonalDistribution: {}
      };
    }

    const categories = {};
    const seasons = {};
    const seasonalDistribution = {};

    wardrobe.forEach(item => {
      // Подсчет по категориям
      if (item.category) {
        categories[item.category] = (categories[item.category] || 0) + 1;
      }

      // Подсчет по сезонам
      if (item.season) {
        seasons[item.season] = (seasons[item.season] || 0) + 1;
      }

      // Распределение по сезонам
      if (item.season) {
        if (!seasonalDistribution[item.season]) {
          seasonalDistribution[item.season] = [];
        }
        seasonalDistribution[item.season].push(item);
      }
    });

    // Находим самую популярную и непопулярную категории
    const categoryEntries = Object.entries(categories);
    const mostUsedCategory = categoryEntries.reduce((a, b) => 
      categories[a[0]] > categories[b[0]] ? a : b, ['', 0]);
    const leastUsedCategory = categoryEntries.reduce((a, b) => 
      categories[a[0]] < categories[b[0]] ? a : b, ['', Infinity]);

    return {
      totalItems: wardrobe.length,
      categories,
      seasons,
      mostUsedCategory: mostUsedCategory[0] || null,
      leastUsedCategory: leastUsedCategory[0] || null,
      seasonalDistribution
    };
  }, [wardrobe]);

  if (stats.totalItems === 0) {
    return (
      <div className="wardrobe-stats empty">
        <h3>Статистика гардероба</h3>
        <p>Добавьте вещи в гардероб, чтобы увидеть статистику</p>
      </div>
    );
  }

  return (
    
    <div className="wardrobe-stats">
      <h3>Статистика гардероба</h3>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{stats.totalItems}</div>
          <div className="stat-label">Всего вещей</div>
        </div>

        <div className="stat-card">
          <div className="stat-number">{Object.keys(stats.categories).length}</div>
          <div className="stat-label">Категорий</div>
        </div>


      </div>
      {/* Анализ гардероба */}
      <AIRecommendations profile={profile} wardrobe={wardrobe} />
    </div>
    );
  };

export default WardrobeStats;