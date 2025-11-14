class WeatherService {
  constructor() {
    this.apiKey = import.meta.env.VITE_OPENWEATHER_API_KEY || '';
    this.baseUrl = 'https://api.openweathermap.org/data/2.5';
  }

  async getWeatherByLocation(lat, lon) {
    try {
      if (!this.apiKey) {
        // OpenWeather API key не установлен
        return this.getDefaultWeatherData();
      }

      const response = await fetch(
        `${this.baseUrl}/weather?lat=${lat}&lon=${lon}&appid=${this.apiKey}&units=metric&lang=ru`
      );
      
      if (!response.ok) {
        throw new Error('Ошибка получения погоды');
      }

      const data = await response.json();
      return this.formatWeatherData(data);
    } catch (error) {
      console.error('Ошибка получения погоды:', error);
      return this.getDefaultWeatherData();
    }
  }

  async getWeatherByCity(city) {
    try {
      if (!this.apiKey) {
        // OpenWeather API key не установлен
        return this.getDefaultWeatherData();
      }

      const response = await fetch(
        `${this.baseUrl}/weather?q=${encodeURIComponent(city)}&appid=${this.apiKey}&units=metric&lang=ru`
      );
      
      if (!response.ok) {
        throw new Error('Город не найден');
      }

      const data = await response.json();
      return this.formatWeatherData(data);
    } catch (error) {
      console.error('Ошибка получения погоды:', error);
      return this.getDefaultWeatherData();
    }
  }

  formatWeatherData(data) {
    return {
      temperature: Math.round(data.main.temp),
      feelsLike: Math.round(data.main.feels_like),
      humidity: data.main.humidity,
      description: data.weather[0].description,
      icon: data.weather[0].icon,
      windSpeed: Math.round(data.wind.speed),
      city: data.name,
      country: data.sys.country,
      timestamp: new Date().toISOString()
    };
  }

  // Fallback данные погоды
  getDefaultWeatherData() {
    return {
      temperature: 20,
      feelsLike: 20,
      humidity: 60,
      description: 'ясно',
      icon: '01d',
      windSpeed: 5,
      city: 'Неизвестно',
      country: 'RU',
      timestamp: new Date().toISOString()
    };
  }

  getSeasonFromWeather(weatherData) {
    const month = new Date().getMonth();
    const temp = weatherData.temperature;

    // Определяем сезон по температуре и месяцу
    if (temp >= 20) return 'лето';
    if (temp >= 10) return 'весна';
    if (temp >= 0) return 'осень';
    return 'зима';
  }

  getClothingRecommendations(weatherData) {
    const temp = weatherData.temperature;
    const weather = weatherData.description.toLowerCase();
    
    let recommendations = {
      category: [],
      description: []
    };

    // Рекомендации по температуре
    if (temp >= 25) {
      recommendations.category.push('легкая одежда', 'шорты', 'футболки');
      recommendations.description.push('Легкая и дышащая одежда');
    } else if (temp >= 15) {
      recommendations.category.push('джинсы', 'рубашки', 'легкие куртки');
      recommendations.description.push('Легкая куртка или джемпер');
    } else if (temp >= 5) {
      recommendations.category.push('куртки', 'джинсы', 'свитера');
      recommendations.description.push('Теплая куртка и свитер');
    } else {
      recommendations.category.push('шуба', 'теплые штаны', 'шапка');
      recommendations.description.push('Теплая зимняя одежда');
    }

    // Рекомендации по погоде
    if (weather.includes('дождь')) {
      recommendations.category.push('зонт', 'дождевик');
      recommendations.description.push('Не забудьте зонт или дождевик');
    }
    if (weather.includes('снег')) {
      recommendations.category.push('зимняя обувь', 'шапка');
      recommendations.description.push('Теплая обувь и головной убор');
    }
    if (weather.includes('ветер')) {
      recommendations.description.push('Ветрозащитная одежда');
    }

    return recommendations;
  }
}

export default new WeatherService(); 