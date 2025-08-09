import json
import hashlib
import redis
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from functools import lru_cache
import openai
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIError(Exception):
    """Исключение для ошибок AI"""
    pass

class AIType(Enum):
    """Типы AI анализаторов"""
    GPT = "gpt"
    HUGGINGFACE = "huggingface"
    RULE_BASED = "rule_based"
    CACHED = "cached"

@dataclass
class AnalysisResult:
    """Результат анализа гардероба"""
    category: str
    season: str
    style: str
    colors: List[str]
    confidence: float
    ai_type: AIType
    explanation: str
    timestamp: datetime

@dataclass
class UserFeedback:
    """Обратная связь пользователя"""
    user_id: str
    item_id: str
    rating: str  # 'positive', 'negative', 'neutral'
    correction: Optional[Dict] = None
    timestamp: datetime = None

class RuleBasedAnalyzer:
    """Правило-основанный анализатор как fallback"""
    
    def __init__(self):
        self.category_keywords = {
            'верх': ['блузка', 'футболка', 'рубашка', 'свитер', 'кофта', 'топ', 'джемпер'],
            'низ': ['джинсы', 'брюки', 'юбка', 'шорты', 'легинсы', 'штаны'],
            'обувь': ['туфли', 'ботинки', 'кроссовки', 'сапоги', 'сандалии', 'мокасины'],
            'сумка': ['сумка', 'кошелек', 'рюкзак'],
            'аксессуары': ['шарф', 'шапка', 'пояс', 'украшения', 'часы']
        }
        
        self.season_keywords = {
            'весна': ['весенний', 'весна', 'март', 'апрель', 'май'],
            'лето': ['летний', 'лето', 'июнь', 'июль', 'август'],
            'осень': ['осенний', 'осень', 'сентябрь', 'октябрь', 'ноябрь'],
            'зима': ['зимний', 'зима', 'декабрь', 'январь', 'февраль']
        }
        
        self.style_keywords = {
            'casual': ['повседневный', 'casual', 'комфортный', 'расслабленный'],
            'классический': ['классический', 'офисный', 'деловой', 'элегантный'],
            'спорт': ['спортивный', 'спорт', 'активный', 'тренировочный'],
            'романтический': ['романтический', 'женственный', 'нежный', 'воздушный']
        }
        
        self.color_keywords = {
            'черный': ['черный', 'черная', 'черное'],
            'белый': ['белый', 'белая', 'белое'],
            'синий': ['синий', 'синяя', 'синее', 'голубой', 'голубая'],
            'красный': ['красный', 'красная', 'красное'],
            'зеленый': ['зеленый', 'зеленая', 'зеленое'],
            'желтый': ['желтый', 'желтая', 'желтое'],
            'розовый': ['розовый', 'розовая', 'розовое'],
            'серый': ['серый', 'серая', 'серое']
        }
    
    def analyze(self, image_description: str) -> AnalysisResult:
        """Анализирует описание изображения по правилам"""
        try:
            # Определяем категорию
            category = self._determine_category(image_description.lower())
            
            # Определяем сезон
            season = self._determine_season(image_description.lower())
            
            # Определяем стиль
            style = self._determine_style(image_description.lower())
            
            # Определяем цвета
            colors = self._determine_colors(image_description.lower())
            
            # Создаем объяснение
            explanation = self._create_explanation(category, season, style, colors)
            
            return AnalysisResult(
                category=category,
                season=season,
                style=style,
                colors=colors,
                confidence=0.6,  # Средняя уверенность для rule-based
                ai_type=AIType.RULE_BASED,
                explanation=explanation,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка в rule-based анализе: {e}")
            return self._get_default_result()
    
    def _determine_category(self, text: str) -> str:
        """Определяет категорию по ключевым словам"""
        for category, keywords in self.category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        return 'другое'
    
    def _determine_season(self, text: str) -> str:
        """Определяет сезон по ключевым словам"""
        for season, keywords in self.season_keywords.items():
            if any(keyword in text for keyword in keywords):
                return season
        return 'всесезонный'
    
    def _determine_style(self, text: str) -> str:
        """Определяет стиль по ключевым словам"""
        for style, keywords in self.style_keywords.items():
            if any(keyword in text for keyword in keywords):
                return style
        return 'повседневный'
    
    def _determine_colors(self, text: str) -> List[str]:
        """Определяет цвета по ключевым словам"""
        colors = []
        for color, keywords in self.color_keywords.items():
            if any(keyword in text for keyword in keywords):
                colors.append(color)
        return colors if colors else ['неопределенный']
    
    def _create_explanation(self, category: str, season: str, style: str, colors: List[str]) -> str:
        """Создает объяснение анализа"""
        explanation_parts = []
        
        if category != 'другое':
            explanation_parts.append(f"Категория: {category}")
        
        if season != 'всесезонный':
            explanation_parts.append(f"Сезон: {season}")
        
        if style != 'повседневный':
            explanation_parts.append(f"Стиль: {style}")
        
        if colors and colors[0] != 'неопределенный':
            explanation_parts.append(f"Цвета: {', '.join(colors)}")
        
        return " • ".join(explanation_parts) if explanation_parts else "Базовый анализ по описанию"
    
    def _get_default_result(self) -> AnalysisResult:
        """Возвращает результат по умолчанию"""
        return AnalysisResult(
            category='другое',
            season='всесезонный',
            style='повседневный',
            colors=['неопределенный'],
            confidence=0.3,
            ai_type=AIType.RULE_BASED,
            explanation='Базовый анализ - не удалось определить детали',
            timestamp=datetime.now()
        )

class GPTAnalyzer:
    """GPT анализатор для анализа гардероба"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не установлен")
        
        # Глобальный таймаут на уровне клиента, чтобы SDK гарантированно применял его
        self.client = openai.OpenAI(api_key=self.api_key, timeout=60)
    
    def analyze(self, image_description: str, image_base64: str = None) -> AnalysisResult:
        """Анализирует изображение с помощью GPT (Vision)"""
        try:
            print(f"🔍 Начинаем GPT анализ. image_base64: {'есть' if image_base64 else 'нет'}")
            if image_base64:
                print(f"📏 Размер base64: {len(image_base64)} символов")
            
            # Полный системный промпт (правила) – из сообщения пользователя
            system_prompt = (
                "Ты — эксперт по распознаванию одежды на фотографиях.\n"
                "Твоя задача — по изображению определить конкретный тип вещи, её сезонность и составить информативное краткое описание, которое будет использоваться стилистом для создания капсул и стилистических рекомендаций.\n\n"
                "Верни результат в формате строго валидного JSON:\n"
                "{\n"
                "\"type\": \"\",          // Название конкретной вещи\n"
                "\"season\": \"\",        // Сезонность\n"
                "\"description\": \"\"    // Краткое, точное описание\n"
                "}\n\n"
                "Пояснение к каждому полю:\n\n"
                "1. \"type\"\n   Укажи конкретный тип вещи, используя профессиональные названия. Например:\n\n"
                "* \"водолазка\"\n* \"свитер\"\n* \"джемпер\"\n* \"футболка\"\n* \"рубашка\"\n* \"брюки\"\n* \"джинсы\"\n* \"юбка\"\n* \"пальто\"\n* \"платье\"\n* \"босоножки\"\n* \"ботинки\"\n* \"сумка\"\n* \"шарф\"\n\n"
                "Не упрощай до категорий вроде \"верх\", \"низ\", \"аксессуар\", \"обувь\" — это делает другой ассистент.\n\n"
                "2. \"season\"\n   Укажи один из сезонов, в который вещь уместна:\n\n"
                "* \"лето\" — лёгкие, открытые вещи\n* \"осень-весна\" — средняя плотность, базовые вещи\n* \"зима\" — утеплённые, тёплые вещи\n* \"всесезон\" — можно носить круглый год (например, футболки, рубашки, джинсы)\n\n"
                "3. \"description\"\n   Кратко, но по делу. Укажи:\n\n"
                "* фасон (прямой, oversize, приталенный и т.д.)\n* цвет\n* материал (если можно определить)\n* особенности (воротник, рукава, застёжки, длина, декор и т.д.)\n\n"
                "Примеры:\n\n"
                "* \"Водолазка приталенного кроя, бежевого цвета, вязаная, с высоким воротом\"\n"
                "* \"Свитер oversize, серый, крупной вязки, с круглым вырезом\"\n"
                "* \"Юбка миди, чёрная, прямого кроя, с разрезом спереди\"\n\n"
                "Важно:\n\n"
                "* Не придумывай — анализируй только то, что видно на фото\n"
                "* Не добавляй никакой текст кроме JSON\n"
                "* Всегда указывай \"type\", даже если он не очевиден — выбери наиболее вероятный\n"
                "* Не сокращай и не упрощай описание\n"
                "* Не используй markdown или дополнительные пояснения — только JSON"
            )
            
            # Короткий пользовательский текст без дублирования правил
            user_text = "Проанализируй изображение и верни строго валидный JSON по правилам выше."
            
            # Попытка использовать загрузку файла для очень больших изображений, чтобы избежать огромных data URL
            use_file_upload = False
            file_id: Optional[str] = None
            try:
                if image_base64 and len(image_base64) > 4_000_000:  # ~4М символов
                    import base64
                    image_bytes = base64.b64decode(image_base64)
                    file = self.client.files.create(
                        file=("image.jpg", image_bytes, "image/jpeg"),
                        purpose="vision"
                    )
                    file_id = file.id
                    use_file_upload = True
                    print(f"📄 Загружен файл в OpenAI Files, id={file_id}")
            except Exception as upload_err:
                print(f"⚠️ Не удалось загрузить файл в OpenAI Files: {upload_err}. Переходим к data URL.")
                use_file_upload = False
            
            raw_output = None
            # Если удалось загрузить файл — используем Chat Completions с image_url=file id не поддерживается, поэтому откатываемся к data URL ниже
            if use_file_upload and file_id:
                pass
            
            # Если не использовали файл, отправляем через Chat Completions с data URL
            if not use_file_upload:
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                user_content: List[Dict[str, Any]] = [{"type": "text", "text": user_text}]
                if image_base64:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    })
                messages.append({"role": "user", "content": user_content})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=200
                )
                # Безопасный разбор контента
                if getattr(response, "choices", None):
                    raw_output = response.choices[0].message.content
                else:
                    print(f"⚠️ Пустой список choices. Полный ответ: {response}")
                    raise AIError("Пустой ответ от модели")
            
            if raw_output is None:
                raise AIError("Не удалось получить текстовый вывод от модели")
            
            content = raw_output.strip()
            # Убираем возможные markdown блоки
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            print(f"🧾 Сырой ответ модели: {content[:500]}")
            result_json = json.loads(content)
            
            return AnalysisResult(
                category=result_json.get('type', 'неопределено'),
                season=result_json.get('season', 'всесезон'),
                style='повседневный',
                colors=['неопределенный'],
                confidence=0.9,
                ai_type=AIType.GPT,
                explanation=result_json.get('description', 'Предмет гардероба'),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Ошибка GPT анализа: {e}")
            # Возврат минимального результата без догадок
            return AnalysisResult(
                category='не распознано',
                season='не распознано',
                style='не распознано',
                colors=['не распознано'],
                confidence=0.0,
                ai_type=AIType.GPT,
                explanation='GPT не смог распознать предмет',
                timestamp=datetime.now()
            )

class RedisCache:
    """Кэш для AI результатов"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()  # Проверяем соединение
            logger.info("Redis кэш подключен успешно")
        except Exception as e:
            logger.warning(f"Redis недоступен: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Dict]:
        """Получает данные из кэша"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {e}")
            return None
    
    def set(self, key: str, value: Dict, ttl: int = 86400) -> bool:
        """Сохраняет данные в кэш"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Удаляет данные из кэша"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False

class AIMetrics:
    """Метрики для отслеживания качества AI"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.cache = RedisCache(redis_url)
    
    def track_accuracy(self, prediction: AnalysisResult, user_feedback: UserFeedback):
        """Отслеживает точность предсказаний"""
        try:
            accuracy = self._calculate_accuracy(prediction, user_feedback)
            
            metric_data = {
                'ai_model': prediction.ai_type.value,
                'accuracy': accuracy,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_feedback.user_id,
                'category': prediction.category,
                'confidence': prediction.confidence
            }
            
            # Сохраняем метрику
            key = f"ai_metrics:{prediction.ai_type.value}:{datetime.now().strftime('%Y-%m-%d')}"
            self.cache.set(key, metric_data, ttl=2592000)  # 30 дней
            
            logger.info(f"Метрика сохранена: {accuracy}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения метрики: {e}")
    
    def _calculate_accuracy(self, prediction: AnalysisResult, feedback: UserFeedback) -> float:
        """Вычисляет точность предсказания"""
        if feedback.rating == 'positive':
            return prediction.confidence
        elif feedback.rating == 'negative':
            return 1.0 - prediction.confidence
        else:
            return 0.5
    
    def get_model_performance(self, ai_type: AIType, days: int = 30) -> Dict:
        """Получает производительность модели"""
        try:
            # Получаем метрики за последние дни
            metrics = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                key = f"ai_metrics:{ai_type.value}:{date}"
                metric = self.cache.get(key)
                if metric:
                    metrics.append(metric)
            
            if not metrics:
                return {'average_accuracy': 0.0, 'total_predictions': 0}
            
            # Вычисляем среднюю точность
            total_accuracy = sum(m['accuracy'] for m in metrics)
            average_accuracy = total_accuracy / len(metrics)
            
            return {
                'average_accuracy': average_accuracy,
                'total_predictions': len(metrics),
                'days_analyzed': days
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения метрик: {e}")
            return {'average_accuracy': 0.0, 'total_predictions': 0}

class AIWardrobeAnalyzer:
    """Основной класс для анализа гардероба с fallback и кэшированием"""
    
    def __init__(self, primary_ai=None, fallback_ai=None, cache_url: str = "redis://localhost:6379"):
        self.primary_ai = primary_ai
        self.fallback_ai = fallback_ai or RuleBasedAnalyzer()
        self.cache = RedisCache(cache_url)
        self.metrics = AIMetrics(cache_url)
        self.circuit_breaker = CircuitBreaker()
    
    def analyze_item(self, image_description: str, user_id: str = None, image_base64: str = None) -> AnalysisResult:
        """Анализирует предмет гардероба с fallback"""
        
        # Создаем хеш для кэширования
        image_hash = self._create_image_hash(image_description)
        
        # Отключаем кэш для анализа изображений
        # cached_result = self.cache.get(image_hash)
        # if cached_result:
        #     logger.info("Используем кэшированный результат")
        #     return AnalysisResult(**cached_result)
        
        try:
            # Используем только GPT AI
            if self.primary_ai:
                result = self.primary_ai.analyze(image_description, image_base64)
                return result
            else:
                raise AIError("GPT AI не инициализирован")
                
        except Exception as e:
            logger.error(f"Ошибка GPT AI: {e}")
            
            # Возвращаем "не распознано" вместо fallback
            return AnalysisResult(
                category='не распознано',
                season='не распознано',
                style='не распознано',
                colors=['не распознано'],
                confidence=0.0,
                ai_type=AIType.GPT,
                explanation='GPT не смог распознать предмет',
                timestamp=datetime.now()
            )
    
    def _analyze_with_fallback(self, image_description: str) -> AnalysisResult:
        """Анализирует с помощью fallback AI"""
        try:
            result = self.fallback_ai.analyze(image_description)
            logger.info("Использован fallback анализатор")
            return result
        except Exception as e:
            logger.error(f"Ошибка fallback AI: {e}")
            return self.fallback_ai._get_default_result()
    
    def _create_image_hash(self, description: str) -> str:
        """Создает хеш для изображения"""
        return hashlib.md5(description.encode()).hexdigest()
    
    def record_feedback(self, analysis_result: AnalysisResult, feedback: UserFeedback):
        """Записывает обратную связь пользователя"""
        try:
            self.metrics.track_accuracy(analysis_result, feedback)
            logger.info(f"Обратная связь записана: {feedback.rating}")
        except Exception as e:
            logger.error(f"Ошибка записи обратной связи: {e}")
    
    def get_performance_stats(self) -> Dict:
        """Получает статистику производительности"""
        stats = {}
        
        for ai_type in AIType:
            if ai_type != AIType.CACHED:
                performance = self.metrics.get_model_performance(ai_type)
                stats[ai_type.value] = performance
        
        return stats

class CircuitBreaker:
    """Circuit breaker для защиты от сбоев AI"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """Проверяет, открыт ли circuit breaker"""
        if self.state == "OPEN":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        """Записывает успешный запрос"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Записывает неудачный запрос"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker открыт после {self.failure_count} неудач")

# Фабрика для создания анализаторов
class AIAnalyzerFactory:
    """Фабрика для создания AI анализаторов"""
    
    @staticmethod
    def create_analyzer(ai_type: str, **kwargs) -> AIWardrobeAnalyzer:
        """Создает анализатор нужного типа"""
        
        if ai_type == "gpt":
            try:
                primary_ai = GPTAnalyzer()
                logger.info("✅ GPT анализатор инициализирован")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации GPT анализатора: {e}")
                primary_ai = None
        elif ai_type == "huggingface":
            # Здесь будет инициализация HuggingFace анализатора
            primary_ai = None  # Пока не реализован
        else:
            primary_ai = None
        
        # Fallback анализатор всегда доступен
        fallback_ai = RuleBasedAnalyzer()
        
        return AIWardrobeAnalyzer(primary_ai=primary_ai, fallback_ai=fallback_ai, **kwargs) 