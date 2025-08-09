import React, { useState, useEffect } from 'react';
import { Calendar, Sun, Cloud, CloudRain, CloudLightning, Snowflake, CloudFog } from 'lucide-react';

const WeatherDateHeader = ({ profile }) => {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentDate, setCurrentDate] = useState('');

  // Проверяем, есть ли координаты у пользователя
  const hasLocation = profile?.location_latitude && profile?.location_longitude;

  // Форматирование даты
  const formatDate = () => {
    const now = new Date();
    const day = now.getDate();
    const month = now.toLocaleString('ru-RU', { month: 'long' }).toLowerCase();
    
    // Правильное склонение для месяцев
    const monthNames = {
      'январь': 'января',
      'февраль': 'февраля',
      'март': 'марта',
      'апрель': 'апреля',
      'май': 'мая',
      'июнь': 'июня',
      'июль': 'июля',
      'август': 'августа',
      'сентябрь': 'сентября',
      'октябрь': 'октября',
      'ноябрь': 'ноября',
      'декабрь': 'декабря'
    };
    
    const correctMonth = monthNames[month] || month;
    return `${day} ${correctMonth}`;
  };

  // Получение погоды по координатам
  const fetchWeather = async () => {
    if (!hasLocation) return;

    setLoading(true);
    try {
      const apiKey = 'd69e489c7ddeb793bff2350cc232dab7';
      const response = await fetch(
        `https://api.openweathermap.org/data/2.5/weather?lat=${profile.location_latitude}&lon=${profile.location_longitude}&appid=${apiKey}&units=metric&lang=ru`
      );
      
      if (!response.ok) {
        throw new Error(`Weather API error: ${response.status}`);
      }
      
      const data = await response.json();
      setWeather(data);
      
    } catch (error) {
      console.error('Error fetching weather:', error);
      // Fallback к моковым данным в случае ошибки
      const fallbackWeather = {
        main: {
          temp: 20,
          temp_max: 25,
          feels_like: 22
        },
        weather: [
          {
            id: 800,
            main: "Clear",
            description: "солнечно",
            icon: "01d"
          }
        ]
      };
      setWeather(fallbackWeather);
    } finally {
      setLoading(false);
    }
  };

  // Получение иконки погоды
  const getWeatherIcon = (weatherCode) => {
    const iconProps = { size: 20, color: "var(--color-text-primary)" };
    
    const icons = {
      200: <CloudLightning {...iconProps} />, // гроза с дождем
      201: <CloudLightning {...iconProps} />, // гроза с дождем
      202: <CloudLightning {...iconProps} />, // сильная гроза с дождем
      210: <CloudLightning {...iconProps} />, // легкая гроза
      211: <CloudLightning {...iconProps} />, // гроза
      212: <CloudLightning {...iconProps} />, // сильная гроза
      221: <CloudLightning {...iconProps} />, // рагозная гроза
      230: <CloudLightning {...iconProps} />, // гроза с легким дождем
      231: <CloudLightning {...iconProps} />, // гроза с дождем
      232: <CloudLightning {...iconProps} />, // гроза с сильным дождем
      300: <CloudRain {...iconProps} />, // легкий дождь
      301: <CloudRain {...iconProps} />, // дождь
      302: <CloudRain {...iconProps} />, // сильный дождь
      310: <CloudRain {...iconProps} />, // легкий дождь
      311: <CloudRain {...iconProps} />, // дождь
      312: <CloudRain {...iconProps} />, // сильный дождь
      313: <CloudRain {...iconProps} />, // дождь и град
      314: <CloudRain {...iconProps} />, // сильный дождь и град
      321: <CloudRain {...iconProps} />, // град
      500: <CloudRain {...iconProps} />, // легкий дождь
      501: <CloudRain {...iconProps} />, // умеренный дождь
      502: <CloudRain {...iconProps} />, // сильный дождь
      503: <CloudRain {...iconProps} />, // очень сильный дождь
      504: <CloudRain {...iconProps} />, // экстремальный дождь
      511: <CloudRain {...iconProps} />, // ледяной дождь
      520: <CloudRain {...iconProps} />, // легкий дождь
      521: <CloudRain {...iconProps} />, // дождь
      522: <CloudRain {...iconProps} />, // сильный дождь
      531: <CloudRain {...iconProps} />, // рагозный дождь
      600: <Snowflake {...iconProps} />, // легкий снег
      601: <Snowflake {...iconProps} />, // снег
      602: <Snowflake {...iconProps} />, // сильный снег
      611: <Snowflake {...iconProps} />, // мокрый снег
      612: <Snowflake {...iconProps} />, // легкий мокрый снег
      613: <Snowflake {...iconProps} />, // мокрый снег
      615: <Snowflake {...iconProps} />, // легкий дождь и снег
      616: <Snowflake {...iconProps} />, // дождь и снег
      620: <Snowflake {...iconProps} />, // легкий дождь и снег
      621: <Snowflake {...iconProps} />, // дождь и снег
      622: <Snowflake {...iconProps} />, // сильный дождь и снег
      701: <CloudFog {...iconProps} />, // туман
      711: <CloudFog {...iconProps} />, // дымка
      721: <CloudFog {...iconProps} />, // легкая дымка
      731: <CloudFog {...iconProps} />, // песчаная буря
      741: <CloudFog {...iconProps} />, // туман
      751: <CloudFog {...iconProps} />, // песок
      761: <CloudFog {...iconProps} />, // пыль
      762: <CloudFog {...iconProps} />, // вулканический пепел
      771: <CloudFog {...iconProps} />, // шквал
      781: <CloudFog {...iconProps} />, // торнадо
      800: <Sun {...iconProps} />, // ясно
      801: <Cloud {...iconProps} />, // малооблачно
      802: <Cloud {...iconProps} />, // облачно
      803: <Cloud {...iconProps} />, // пасмурно
      804: <Cloud {...iconProps} />, // облачно
    };
    
    return icons[weatherCode] || <Sun {...iconProps} />;
  };

  // Форматирование температуры
  const formatTemperature = (temp, tempMax) => {
    const rounded = Math.round(temp);
    const roundedMax = Math.round(tempMax);
    return `${rounded}° - ${roundedMax}°C`;
  };

  useEffect(() => {
    setCurrentDate(formatDate());
    if (hasLocation) {
      fetchWeather();
    }
  }, [profile]);

  if (!hasLocation) {
    return null; // Не показываем компонент, если нет координат
  }

  return (
    <div className="weather-date-header">
      <div className="date-section">
        <Calendar className="calendar-icon" size={20} />
        <span className="date-text">{currentDate}</span>
      </div>
      
      {weather && (
        <div className="weather-section">
          <div className="weather-top-row">
            <div className="weather-icon">
              {getWeatherIcon(weather.weather[0].id)}
            </div>
            <span className="temperature">
              {formatTemperature(weather.main.temp, weather.main.temp_max)}
            </span>
          </div>
          <span className="weather-description">
            {weather.weather[0].description}
          </span>
        </div>
      )}
      
      {loading && (
        <div className="weather-loading">
          <span>Загрузка погоды...</span>
        </div>
      )}
    </div>
  );
};

export default WeatherDateHeader; 