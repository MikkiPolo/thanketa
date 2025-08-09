import json
import ollama
import hashlib
from typing import List, Dict, Any
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalCapsuleGenerator:
    def __init__(self, model_name="llama2:7b", temperature=0.7, max_tokens=4000, host="http://localhost:11434", timeout=30):
        """
        Инициализация генератора капсул с локальной моделью
        
        Args:
            model_name: Название модели Ollama (llama2:7b, mistral:7b, codellama:7b)
            temperature: Температура генерации (0.0-2.0)
            max_tokens: Максимальное количество токенов
            host: Хост Ollama
            timeout: Таймаут запроса
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.host = host
        self.timeout = timeout
        self.client = ollama.Client(host=host)
        self._cache = {}  # Инициализируем кэш сразу
        
    def generate_capsules(self, wardrobe: List[Dict], profile: Dict, weather: Dict = None) -> Dict:
        """
        Генерирует капсулы гардероба с помощью локальной ИИ модели
        
        Args:
            wardrobe: Список вещей в гардеробе
            profile: Профиль пользователя
            weather: Данные о погоде
            
        Returns:
            Словарь с сгенерированными капсулами
        """
        try:
            # Временно отключаем кэш для тестирования
            # cache_key = self._generate_cache_key(wardrobe, profile, weather)
            # logger.info(f"Генерируем ключ кэша: {cache_key[:8]}...")
            # cached_result = self._get_cached_capsules(cache_key)
            # if cached_result:
            #     logger.info("✅ Используем кэшированный результат")
            #     return cached_result
            # else:
            #     logger.info("❌ Кэш не найден, генерируем новые капсулы")
            logger.info("🔄 Генерируем новые капсулы (кэш отключен)")
            
            # Формируем промпт для ИИ
            prompt = self._create_prompt(wardrobe, profile, weather)
            
            # Генерируем ответ с помощью ИИ
            response = self._generate_with_ai(prompt)
            
            # Парсим ответ
            capsules = self._parse_ai_response(response)
            
            # Проверяем и исправляем несовместимые капсулы
            logger.info("=== ПРОВЕРКА СОВМЕСТИМОСТИ КАПСУЛ ===")
            self._fix_incompatible_capsules_simple(capsules, wardrobe)
            logger.info("=== КОНЕЦ ПРОВЕРКИ ===")
            
            # Временно отключаем кэширование
            # self._cache_capsules(cache_key, capsules)
            
            return capsules
            
        except Exception as e:
            logger.error(f"Ошибка генерации капсул: {e}")
            return self._generate_fallback_capsules(wardrobe, profile, weather)
    
    def _create_prompt(self, wardrobe: List[Dict], profile: Dict, weather: Dict) -> str:
        """Создает промпт для ИИ модели"""
        
        # Логируем входные данные
        logger.info("=== ВХОДНЫЕ ДАННЫЕ ===")
        logger.info(f"Гардероб: {len(wardrobe)} вещей")
        logger.info(f"Профиль: {profile}")
        logger.info(f"Погода: {weather}")
        logger.info("=== КОНЕЦ ВХОДНЫХ ДАННЫХ ===")
        
        # Форматируем гардероб
        wardrobe_text = "\n".join([
            f"- {item.get('category', 'Неизвестно')}: {item.get('description', '')} (сезон: {item.get('season', 'Круглогодично')})"
            for item in wardrobe
        ])
        
        # Форматируем профиль
        profile_text = f"""
        Имя: {profile.get('name', 'Не указано')}
        Возраст: {profile.get('age', 'Не указан')}
        Тип фигуры: {profile.get('figura', 'Не указан')}
        Цветотип: {profile.get('cvetotip', 'Не указан')}
        Любимая зона: {profile.get('like_zone', 'Не указана')}
        Проблемная зона: {profile.get('dislike_zone', 'Не указана')}
        """
        
        # Форматируем погоду
        weather_text = ""
        if weather and 'main' in weather:
            temp = weather['main'].get('temp', 'Неизвестно')
            description = weather.get('weather', [{}])[0].get('description', 'Неизвестно')
            weather_text = f"Текущая погода: {temp}°C, {description}"
        
        prompt = f"""
        Создай капсулы из гардероба:

        ГАРДЕРОБ: {wardrobe_text}
        ПРОФИЛЬ: {profile_text}
        ПОГОДА: {weather_text}

        ПРАВИЛА: платье + юбка/джинсы = НЕЛЬЗЯ

        Создай 3 категории по 3 капсулы (3-4 вещи каждая):
        1. Повседневный (casual)
        2. Деловой (business)  
        3. Вечерний (evening)

        JSON: {{"categories": [{{"id": "casual", "name": "Повседневный", "fullCapsules": [{{"id": "casual_1", "name": "Образ 1", "items": [1,2,3], "description": "Описание"}}]}}]}}
        """
        
        # Логируем промпт для отладки
        logger.info("=== ПРОМПТ ДЛЯ ИИ МОДЕЛИ ===")
        logger.info(f"Длина промпта: {len(prompt)} символов")
        logger.info(f"Промпт:\n{prompt}")
        logger.info("=== КОНЕЦ ПРОМПТА ===")
        
        return prompt
    
    def _generate_with_ai(self, prompt: str) -> str:
        """Генерирует ответ с помощью локальной ИИ модели"""
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': self.temperature,
                    'top_p': 0.9,
                    'max_tokens': 2000
                }
            )
            
            ai_response = response['message']['content']
            
            # Логируем ответ от ИИ
            logger.info("=== ОТВЕТ ОТ ИИ МОДЕЛИ ===")
            logger.info(f"Длина ответа: {len(ai_response)} символов")
            logger.info(f"Ответ:\n{ai_response}")
            logger.info("=== КОНЕЦ ОТВЕТА ===")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Ошибка при обращении к ИИ модели: {e}")
            raise
    
    def _validate_capsule_compatibility(self, items: List[int], wardrobe: List[Dict]) -> bool:
        """Проверяет совместимость вещей в капсуле"""
        try:
            # Создаем словарь вещей по ID
            wardrobe_dict = {item['id']: item for item in wardrobe}
            
            # Проверяем наличие платья
            has_dress = any(wardrobe_dict.get(item_id, {}).get('category', '').lower() in ['платье', 'dress'] 
                           for item_id in items)
            
            # Если есть платье, не должно быть юбок/джинсов/брюк
            if has_dress:
                bottom_items = ['юбка', 'джинсы', 'брюки', 'skirt', 'jeans', 'pants']
                has_bottom = any(wardrobe_dict.get(item_id, {}).get('category', '').lower() in bottom_items 
                                for item_id in items)
                if has_bottom:
                    logger.warning(f"Несовместимая капсула: платье + нижняя часть - {items}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки совместимости: {e}")
            return True  # В случае ошибки пропускаем проверку

    def _validate_and_fix_capsules(self, capsules: Dict, wardrobe: List[Dict]) -> None:
        """Проверяет и исправляет несовместимые капсулы"""
        try:
            for category in capsules.get('categories', []):
                # Проверяем полные капсулы
                for capsule in category.get('fullCapsules', []):
                    items = capsule.get('items', [])
                    if not self._validate_capsule_compatibility(items, wardrobe):
                        # Исправляем капсулу - убираем несовместимые вещи
                        self._fix_incompatible_capsule(capsule, wardrobe)
                
                # Проверяем примеры
                for example in category.get('examples', []):
                    items = example.get('items', [])
                    if not self._validate_capsule_compatibility(items, wardrobe):
                        # Исправляем пример
                        self._fix_incompatible_capsule(example, wardrobe)
                        
        except Exception as e:
            logger.error(f"Ошибка валидации капсул: {e}")

    def _fix_incompatible_capsule(self, capsule: Dict, wardrobe: List[Dict]) -> None:
        """Исправляет несовместимую капсулу"""
        try:
            items = capsule.get('items', [])
            wardrobe_dict = {item['id']: item for item in wardrobe}
            
            # Если есть платье, убираем юбки/джинсы/брюки
            dress_items = [item_id for item_id in items 
                          if wardrobe_dict.get(item_id, {}).get('category', '').lower() in ['платье', 'dress']]
            
            if dress_items:
                # Оставляем только платье и аксессуары
                bottom_items = ['юбка', 'джинсы', 'брюки', 'skirt', 'jeans', 'pants']
                compatible_items = [item_id for item_id in items 
                                  if wardrobe_dict.get(item_id, {}).get('category', '').lower() not in bottom_items]
                
                capsule['items'] = compatible_items
                capsule['description'] += " (исправлено: убраны несовместимые вещи)"
                logger.info(f"Исправлена капсула {capsule.get('id', 'unknown')}: {items} -> {compatible_items}")
                
        except Exception as e:
            logger.error(f"Ошибка исправления капсулы: {e}")

    def _fix_incompatible_capsules_simple(self, capsules: Dict, wardrobe: List[Dict]) -> None:
        """Простая функция исправления несовместимых капсул"""
        try:
            # Создаем словарь вещей по ID
            wardrobe_dict = {item['id']: item for item in wardrobe}
            
            for category in capsules.get('categories', []):
                # Исправляем полные капсулы
                for capsule in category.get('fullCapsules', []):
                    items = capsule.get('items', [])
                    fixed_items = self._fix_capsule_items(items, wardrobe_dict)
                    if fixed_items != items:
                        logger.info(f"Исправлена капсула {capsule.get('id', 'unknown')}: {items} -> {fixed_items}")
                        capsule['items'] = fixed_items
                        capsule['description'] += " (исправлено)"
                
                # Исправляем примеры
                for example in category.get('examples', []):
                    items = example.get('items', [])
                    fixed_items = self._fix_capsule_items(items, wardrobe_dict)
                    if fixed_items != items:
                        logger.info(f"Исправлен пример {example.get('id', 'unknown')}: {items} -> {fixed_items}")
                        example['items'] = fixed_items
                        example['description'] += " (исправлено)"
                        
        except Exception as e:
            logger.error(f"Ошибка исправления капсул: {e}")

    def _fix_capsule_items(self, items: List[int], wardrobe_dict: Dict) -> List[int]:
        """Исправляет список вещей в капсуле"""
        try:
            # Проверяем наличие платья
            has_dress = any(wardrobe_dict.get(item_id, {}).get('category', '').lower() in ['платье', 'dress'] 
                           for item_id in items)
            
            if has_dress:
                # Если есть платье, убираем юбки/джинсы/брюки
                bottom_items = ['юбка', 'джинсы', 'брюки', 'skirt', 'jeans', 'pants']
                compatible_items = [item_id for item_id in items 
                                  if wardrobe_dict.get(item_id, {}).get('category', '').lower() not in bottom_items]
                
                logger.info(f"Найдено платье, убираем нижние части: {items} -> {compatible_items}")
                return compatible_items
            
            return items
            
        except Exception as e:
            logger.error(f"Ошибка исправления вещей: {e}")
            return items

    def _generate_cache_key(self, wardrobe: List[Dict], profile: Dict, weather: Dict) -> str:
        """Генерирует ключ кэша для входных данных"""
        try:
            import time
            # Добавляем временную метку (обновляем каждую минуту)
            current_time = int(time.time() / 60)  # 1 минута = 60 секунд
            
            # Создаем строку для хеширования
            import random
            data_str = json.dumps({
                'wardrobe': sorted(wardrobe, key=lambda x: x.get('id', 0)),
                'profile': profile,
                'weather': weather,
                'time_bucket': current_time,  # Добавляем временную метку
                'random': random.randint(1, 100)  # Добавляем случайный компонент
            }, sort_keys=True)
            
            # Создаем MD5 хеш
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Ошибка генерации ключа кэша: {e}")
            return ""

    def _get_cached_capsules(self, cache_key: str) -> Dict:
        """Получает кэшированные капсулы"""
        # Простая реализация кэша в памяти
        if cache_key in self._cache:
            logger.info(f"Найден кэш для ключа: {cache_key[:8]}...")
            return self._cache[cache_key]
        return None

    def _cache_capsules(self, cache_key: str, capsules: Dict) -> None:
        """Кэширует капсулы"""
        try:
            # Ограничиваем размер кэша
            if len(self._cache) > 1000:
                # Удаляем старые записи
                old_keys = list(self._cache.keys())[:100]
                for key in old_keys:
                    del self._cache[key]
            
            self._cache[cache_key] = capsules
            logger.info(f"Кэширован результат для ключа: {cache_key[:8]}...")
        except Exception as e:
            logger.error(f"Ошибка кэширования: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Возвращает статистику кэша"""
        return {
            "size": len(self._cache),
            "keys": list(self._cache.keys())[:10]  # Первые 10 ключей для отладки
        }
    
    def clear_cache(self) -> None:
        """Очищает кэш"""
        self._cache.clear()
        logger.info("Кэш очищен")

    def _parse_ai_response(self, response: str) -> Dict:
        """Парсит ответ ИИ в структурированный формат"""
        try:
            # Ищем JSON в ответе
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("JSON не найден в ответе")
            
            json_str = response[start_idx:end_idx]
            capsules = json.loads(json_str)
            
            # Валидируем структуру
            if 'categories' not in capsules:
                raise ValueError("Неверная структура ответа")
            
            return capsules
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            raise ValueError(f"Неверный формат JSON: {e}")
    
    def _generate_fallback_capsules(self, wardrobe: List[Dict], profile: Dict, weather: Dict) -> Dict:
        """Генерирует базовые капсулы при ошибке ИИ"""
        logger.info("Используем fallback генерацию капсул")
        
        # Простая логика без ИИ
        categories = [
            {"id": "casual", "name": "Повседневный стиль", "description": "Уютные образы для ежедневных дел"},
            {"id": "business", "name": "Деловой образ", "description": "Элегантные решения для работы"},
            {"id": "evening", "name": "Вечерний выход", "description": "Стильные образы для особых случаев"},
            {"id": "romantic", "name": "Романтическое свидание", "description": "Нежные и привлекательные образы"},
            {"id": "weekend", "name": "Выходные", "description": "Расслабленные образы для отдыха"},
            {"id": "travel", "name": "Путешествия", "description": "Практичные образы для поездок"}
        ]
        
        result = {"categories": []}
        
        for category in categories:
            # Создаем простые примеры
            examples = []
            for i in range(2):
                items = wardrobe[i*3:(i+1)*3] if len(wardrobe) >= (i+1)*3 else wardrobe
                if items:
                    examples.append({
                        "id": f"{category['id']}_{i+1}",
                        "name": f"{category['name']} - Образ {i+1}",
                        "items": [str(item.get('id', '')) for item in items],
                        "description": f"Базовый образ для {category['description'].lower()}",
                        "reasoning": f"Образ создан с учетом вашего гардероба"
                    })
            
            # Создаем полные капсулы
            full_capsules = []
            for i in range(8):
                items = wardrobe[i*2:(i+1)*2+4] if len(wardrobe) >= (i+1)*2+4 else wardrobe
                if items:
                    full_capsules.append({
                        "id": f"{category['id']}_full_{i+1}",
                        "name": f"{category['name']} - Капсула {i+1}",
                        "items": [str(item.get('id', '')) for item in items],
                        "description": f"Полная капсула для {category['description'].lower()}",
                        "reasoning": f"Капсула создана на основе вашего гардероба"
                    })
            
            result["categories"].append({
                **category,
                "examples": examples,
                "fullCapsules": full_capsules
            })
        
        return result


# Альтернативные генераторы
class HuggingFaceCapsuleGenerator:
    """Генератор капсул с использованием Hugging Face моделей"""
    
    def __init__(self, model_name="microsoft/DialoGPT-medium"):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
    
    def generate_capsules(self, wardrobe, profile, weather=None):
        # Реализация с Hugging Face
        pass


class SentenceTransformerCapsuleGenerator:
    """Генератор капсул с использованием sentence transformers для семантического поиска"""
    
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_capsules(self, wardrobe, profile, weather=None):
        # Реализация с семантическим поиском
        pass 