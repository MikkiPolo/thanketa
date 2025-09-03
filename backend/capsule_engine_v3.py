"""
Новый алгоритм генерации капсул v3
Реализует поэтапный подход: фильтрация -> шаблоны -> совместимость -> скоринг -> генерация
"""

import random
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# КОНСТАНТЫ И СЛОВАРИ
# ============================================================================

class LayerType(Enum):
    BASE = "base"           # База (майки, футболки)
    MIDDLE = "middle"       # Средний слой (рубашки, блузы)
    OUTER = "outer"         # Внешний слой (кардиганы, жакеты)
    BOTTOM = "bottom"       # Низ (брюки, юбки)
    DRESS = "dress"         # Платья
    SHOES = "shoes"         # Обувь
    ACCESSORY = "accessory" # Аксессуары

class WarmthLevel(Enum):
    VERY_LIGHT = "very_light"  # +25°C и выше
    LIGHT = "light"            # +15°C до +25°C
    MEDIUM = "medium"          # +5°C до +15°C
    WARM = "warm"              # -5°C до +5°C
    VERY_WARM = "very_warm"    # -5°C и ниже

class FormalityLevel(Enum):
    SPORT = 0      # Спорт
    CASUAL = 1     # Повседневный
    SMART_CASUAL = 2  # Умный повседневный
    BUSINESS = 3   # Деловой
    EVENING = 4    # Вечерний

# Словарь категорий с их свойствами
CATEGORY_PROPERTIES = {
    # Верх
    "Футболка": {"layer": LayerType.BASE, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Майка": {"layer": LayerType.BASE, "warmth": WarmthLevel.VERY_LIGHT, "formality": FormalityLevel.CASUAL},
    "Рубашка": {"layer": LayerType.MIDDLE, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.SMART_CASUAL},
    "Блуза": {"layer": LayerType.MIDDLE, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.SMART_CASUAL},
    "Кардиган": {"layer": LayerType.OUTER, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.CASUAL},
    "Жакет": {"layer": LayerType.OUTER, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.BUSINESS},
    "Пиджак": {"layer": LayerType.OUTER, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.BUSINESS},
    "Свитер": {"layer": LayerType.MIDDLE, "warmth": WarmthLevel.WARM, "formality": FormalityLevel.CASUAL},
    "Толстовка": {"layer": LayerType.MIDDLE, "warmth": WarmthLevel.WARM, "formality": FormalityLevel.CASUAL},
    "Худи": {"layer": LayerType.MIDDLE, "warmth": WarmthLevel.WARM, "formality": FormalityLevel.CASUAL},
    
    # Низ
    "Джинсы": {"layer": LayerType.BOTTOM, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.CASUAL},
    "Брюки": {"layer": LayerType.BOTTOM, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.SMART_CASUAL},
    "Юбка": {"layer": LayerType.BOTTOM, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.SMART_CASUAL},
    "Шорты": {"layer": LayerType.BOTTOM, "warmth": WarmthLevel.VERY_LIGHT, "formality": FormalityLevel.CASUAL},
    "Легинсы": {"layer": LayerType.BOTTOM, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.CASUAL},
    
    # Платья
    "Платье": {"layer": LayerType.DRESS, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.SMART_CASUAL},
    "Сарафан": {"layer": LayerType.DRESS, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Комбинезон": {"layer": LayerType.DRESS, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.CASUAL},
    
    # Обувь
    "Кроссовки": {"layer": LayerType.SHOES, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.SPORT},
    "Кеды": {"layer": LayerType.SHOES, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.CASUAL},
    "Ботинки": {"layer": LayerType.SHOES, "warmth": WarmthLevel.WARM, "formality": FormalityLevel.CASUAL},
    "Туфли": {"layer": LayerType.SHOES, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.BUSINESS},
    "Сапоги": {"layer": LayerType.SHOES, "warmth": WarmthLevel.WARM, "formality": FormalityLevel.CASUAL},
    "Сандалии": {"layer": LayerType.SHOES, "warmth": WarmthLevel.VERY_LIGHT, "formality": FormalityLevel.CASUAL},
    "Босоножки": {"layer": LayerType.SHOES, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.SMART_CASUAL},
    
    # Аксессуары
    "Сумка": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Рюкзак": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Клатч": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.EVENING},
    "Шарф": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.CASUAL},
    "Перчатки": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.MEDIUM, "formality": FormalityLevel.CASUAL},
    "Серьги": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Ожерелье": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Браслет": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Кольцо": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Часы": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Ремень": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Галстук": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.BUSINESS},
    "Бейсболка": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
    "Шляпа": {"layer": LayerType.ACCESSORY, "warmth": WarmthLevel.LIGHT, "formality": FormalityLevel.CASUAL},
}

# Температурные диапазоны для каждого уровня теплоты
WARMTH_TEMPERATURE_RANGES = {
    WarmthLevel.VERY_LIGHT: (15, 50),  # +15°C и выше
    WarmthLevel.LIGHT: (5, 35),        # +5°C до +35°C
    WarmthLevel.MEDIUM: (-5, 30),      # -5°C до +30°C
    WarmthLevel.WARM: (-15, 20),       # -15°C до +20°C
    WarmthLevel.VERY_WARM: (-50, 10),  # -50°C до +10°C
}

# ============================================================================
# ДАТАКЛАССЫ
# ============================================================================

@dataclass
class ItemProperties:
    """Свойства вещи после нормализации"""
    layer: LayerType
    warmth: WarmthLevel
    formality: FormalityLevel
    color_temperature: str  # "warm" или "cool"
    color_lightness: str    # "light" или "dark"
    color_saturation: str   # "bright" или "muted"
    has_pattern: bool
    pattern_size: str       # "large" или "small"
    material: str
    texture: str

@dataclass
class CapsuleTemplate:
    """Шаблон капсулы"""
    name: str
    required_slots: List[str]  # ["top", "bottom", "shoes", "bag"]
    optional_slots: List[str]  # ["outer", "accessory"]
    min_formality: int
    max_formality: int
    description: str

@dataclass
class CapsuleCandidate:
    """Кандидат на капсулу"""
    items: Dict[str, Any]
    score: float
    template: CapsuleTemplate
    missing_slots: List[str]
    explanation: str

# ============================================================================
# ОСНОВНЫЕ ФУНКЦИИ
# ============================================================================

def normalize_item(item: Dict[str, Any]) -> ItemProperties:
    """Нормализация вещи - присвоение свойств по категории"""
    category = item.get('category', '')
    
    # Получаем базовые свойства из словаря
    props = CATEGORY_PROPERTIES.get(category, {
        "layer": LayerType.MIDDLE,
        "warmth": WarmthLevel.MEDIUM,
        "formality": FormalityLevel.CASUAL
    })
    
    # Анализируем цвет
    color_temperature, color_lightness, color_saturation = analyze_color(item.get('description', ''))
    
    # Анализируем принт
    has_pattern, pattern_size = analyze_pattern(item.get('description', ''))
    
    return ItemProperties(
        layer=props["layer"],
        warmth=props["warmth"],
        formality=props["formality"],
        color_temperature=color_temperature,
        color_lightness=color_lightness,
        color_saturation=color_saturation,
        has_pattern=has_pattern,
        pattern_size=pattern_size,
        material=extract_material(item.get('description', '')),
        texture=extract_texture(item.get('description', ''))
    )

def analyze_color(description: str) -> Tuple[str, str, str]:
    """Анализ цвета вещи"""
    desc_lower = description.lower()
    
    # Температура цвета
    warm_colors = ['красный', 'оранжевый', 'желтый', 'золотой', 'медный', 'бордовый', 'терракотовый']
    cool_colors = ['синий', 'голубой', 'фиолетовый', 'серебряный', 'серый', 'бирюзовый', 'мятный']
    
    color_temperature = "neutral"
    for color in warm_colors:
        if color in desc_lower:
            color_temperature = "warm"
            break
    for color in cool_colors:
        if color in desc_lower:
            color_temperature = "cool"
            break
    
    # Светлота
    light_words = ['светлый', 'пастельный', 'нежный', 'бледный']
    dark_words = ['темный', 'глубокий', 'насыщенный', 'яркий']
    
    color_lightness = "medium"
    for word in light_words:
        if word in desc_lower:
            color_lightness = "light"
            break
    for word in dark_words:
        if word in desc_lower:
            color_lightness = "dark"
            break
    
    # Насыщенность
    bright_words = ['яркий', 'насыщенный', 'кричащий']
    muted_words = ['приглушенный', 'пастельный', 'нежный']
    
    color_saturation = "medium"
    for word in bright_words:
        if word in desc_lower:
            color_saturation = "bright"
            break
    for word in muted_words:
        if word in desc_lower:
            color_saturation = "muted"
            break
    
    return color_temperature, color_lightness, color_saturation

def analyze_pattern(description: str) -> Tuple[bool, str]:
    """Анализ принта на вещи"""
    desc_lower = description.lower()
    
    pattern_words = ['принт', 'рисунок', 'узор', 'полоска', 'клетка', 'горошек', 'цветок', 'геометрия']
    large_pattern_words = ['крупный', 'большой', 'яркий']
    small_pattern_words = ['мелкий', 'нежный', 'тонкий']
    
    has_pattern = any(word in desc_lower for word in pattern_words)
    pattern_size = "small"
    
    if has_pattern:
        if any(word in desc_lower for word in large_pattern_words):
            pattern_size = "large"
        elif any(word in desc_lower for word in small_pattern_words):
            pattern_size = "small"
    
    return has_pattern, pattern_size

def extract_material(description: str) -> str:
    """Извлечение материала из описания"""
    desc_lower = description.lower()
    
    materials = {
        'хлопок': 'cotton',
        'лен': 'linen',
        'шелк': 'silk',
        'шерсть': 'wool',
        'деним': 'denim',
        'кожа': 'leather',
        'замша': 'suede',
        'трикотаж': 'knit',
        'полиэстер': 'polyester'
    }
    
    for ru_material, en_material in materials.items():
        if ru_material in desc_lower:
            return en_material
    
    return 'unknown'

def extract_texture(description: str) -> str:
    """Извлечение фактуры из описания"""
    desc_lower = description.lower()
    
    textures = {
        'гладкий': 'smooth',
        'шероховатый': 'rough',
        'мягкий': 'soft',
        'жесткий': 'stiff',
        'эластичный': 'stretchy',
        'плотный': 'dense',
        'тонкий': 'thin',
        'толстый': 'thick'
    }
    
    for ru_texture, en_texture in textures.items():
        if ru_texture in desc_lower:
            return en_texture
    
    return 'unknown'

# ============================================================================
# STAGE A: ЖЕСТКИЕ ФИЛЬТРЫ
# ============================================================================

def apply_hard_filters(wardrobe_items: List[Dict[str, Any]], 
                      temperature: Optional[float] = None, 
                      weather: Optional[Dict[str, Any]] = None,
                      body_type: Optional[str] = None,
                      color_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Применение жестких фильтров к гардеробу"""
    if temperature is not None:
        print(f"🔍 Stage A: Применяем жесткие фильтры для температуры {temperature}°C")
    else:
        print(f"🔍 Stage A: Применяем жесткие фильтры (температура не указана)")
    
    filtered_items = []
    
    for item in wardrobe_items:
        category = item.get('category', '')
        print(f"   Проверяем: {category}")
        
        # Фильтр по температуре (только если температура указана)
        if temperature is not None and not is_temperature_suitable(item, temperature):
            print(f"     ❌ Не подходит по температуре")
            continue
            
        # Фильтр по погоде
        if weather and not is_weather_suitable(item, weather):
            print(f"     ❌ Не подходит по погоде")
            continue
            
        # Фильтр по фигуре
        if body_type and not is_body_type_suitable(item, body_type):
            print(f"     ❌ Не подходит по фигуре")
            continue
            
        # Фильтр по цветотипу
        if color_type and not is_color_type_suitable(item, color_type):
            print(f"     ❌ Не подходит по цветотипу")
            continue
        
        print(f"     ✅ Прошло все фильтры")
        filtered_items.append(item)
    
    print(f"✅ После жестких фильтров: {len(filtered_items)} из {len(wardrobe_items)} вещей")
    return filtered_items

def is_temperature_suitable(item: Dict[str, Any], temperature: float) -> bool:
    """Проверка соответствия вещи температуре"""
    category = item.get('category', '')
    props = CATEGORY_PROPERTIES.get(category, {})
    warmth = props.get('warmth', WarmthLevel.MEDIUM)
    
    temp_range = WARMTH_TEMPERATURE_RANGES.get(warmth, (5, 15))
    is_suitable = temp_range[0] <= temperature <= temp_range[1]
    print(f"       Температура: {temperature}°C, диапазон: {temp_range}, подходит: {is_suitable}")
    return is_suitable

def is_weather_suitable(item: Dict[str, Any], weather: Dict[str, Any]) -> bool:
    """Проверка соответствия вещи погоде"""
    # Пока базовая реализация
    return True

def is_body_type_suitable(item: Dict[str, Any], body_type: str) -> bool:
    """Проверка соответствия вещи типу фигуры"""
    # Пока базовая реализация
    return True

def is_color_type_suitable(item: Dict[str, Any], color_type: str) -> bool:
    """Проверка соответствия вещи цветотипу"""
    # Пока базовая реализация
    return True

# ============================================================================
# STAGE B: ШАБЛОНЫ ОБРАЗОВ
# ============================================================================

def get_capsule_templates() -> List[CapsuleTemplate]:
    """Получение шаблонов капсул"""
    return [
        CapsuleTemplate(
            name="Повседневный сет",
            required_slots=["top", "bottom"],
            optional_slots=["shoes", "bag", "outer", "accessory"],
            min_formality=0,
            max_formality=2,
            description="Базовый повседневный образ"
        ),
        CapsuleTemplate(
            name="Платье - готовый образ",
            required_slots=["dress"],
            optional_slots=["shoes", "bag", "outer", "accessory"],
            min_formality=1,
            max_formality=3,
            description="Готовый образ с платьем"
        ),
        CapsuleTemplate(
            name="Многослойный образ",
            required_slots=["top", "middle", "bottom"],
            optional_slots=["shoes", "bag", "outer", "accessory"],
            min_formality=1,
            max_formality=3,
            description="Образ с несколькими слоями"
        ),
        CapsuleTemplate(
            name="Летний легкий образ",
            required_slots=["top", "bottom"],
            optional_slots=["shoes", "bag", "accessory"],
            min_formality=0,
            max_formality=1,
            description="Легкий летний образ"
        ),
        CapsuleTemplate(
            name="Зимний теплый образ",
            required_slots=["top", "middle", "outer", "bottom"],
            optional_slots=["shoes", "bag", "accessory"],
            min_formality=1,
            max_formality=3,
            description="Теплый зимний образ"
        )
    ]

# ============================================================================
# STAGE C: СОВМЕСТИМОСТЬ И ПРАВИЛА
# ============================================================================

def check_silhouette_compatibility(items: Dict[str, Any]) -> bool:
    """Проверка совместимости силуэта"""
    # Базовая реализация
    return True

def check_color_compatibility(items: Dict[str, Any]) -> bool:
    """Проверка совместимости цветов"""
    # Базовая реализация
    return True

def check_texture_compatibility(items: Dict[str, Any]) -> bool:
    """Проверка совместимости фактур"""
    # Базовая реализация
    return True

def check_formality_compatibility(items: Dict[str, Any]) -> bool:
    """Проверка совместимости формальности"""
    # Базовая реализация
    return True

# ============================================================================
# STAGE D: СКОРИНГ
# ============================================================================

def score_capsule(capsule: Dict[str, Any]) -> float:
    """Оценка капсулы по системе скоринга (0-100)"""
    score = 0
    
    # Силуэт и фигура: 0-30
    silhouette_score = score_silhouette(capsule)
    score += silhouette_score * 0.3
    
    # Цвет и палитра: 0-25
    color_score = score_colors(capsule)
    score += color_score * 0.25
    
    # Погода и сезонность: 0-15
    weather_score = score_weather(capsule)
    score += weather_score * 0.15
    
    # Формальность: 0-15
    formality_score = score_formality(capsule)
    score += formality_score * 0.15
    
    # Стиль и фактура: 0-10
    style_score = score_style(capsule)
    score += style_score * 0.1
    
    # Диверсификация: 0-5
    diversity_score = score_diversity(capsule)
    score += diversity_score * 0.05
    
    return min(100, max(0, score))

def score_silhouette(capsule: Dict[str, Any]) -> float:
    """Оценка силуэта (0-100)"""
    # Базовая реализация
    return 70

def score_colors(capsule: Dict[str, Any]) -> float:
    """Оценка цветов (0-100)"""
    # Базовая реализация
    return 75

def score_weather(capsule: Dict[str, Any]) -> float:
    """Оценка соответствия погоде (0-100)"""
    # Базовая реализация
    return 80

def score_formality(capsule: Dict[str, Any]) -> float:
    """Оценка формальности (0-100)"""
    # Базовая реализация
    return 70

def score_style(capsule: Dict[str, Any]) -> float:
    """Оценка стиля (0-100)"""
    # Базовая реализация
    return 65

def score_diversity(capsule: Dict[str, Any]) -> float:
    """Оценка диверсификации (0-100)"""
    # Базовая реализация
    return 60

# ============================================================================
# STAGE E: ГЕНЕРАЦИЯ
# ============================================================================

def generate_capsules_v3(wardrobe_items: List[Dict[str, Any]], 
                        temperature: Optional[float] = None,
                        max_total: int = 20,
                        weather: Optional[Dict[str, Any]] = None,
                        body_type: Optional[str] = None,
                        color_type: Optional[str] = None,
                        history: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Основная функция генерации капсул по новому алгоритму
    """
    print(f"🚀 Начало генерации капсул v3")
    if temperature is not None:
        print(f"📦 Входные данные: {len(wardrobe_items)} вещей, температура {temperature}°C")
    else:
        print(f"📦 Входные данные: {len(wardrobe_items)} вещей, температура не указана")
    print(f"🌡️ Погода: {weather}")
    print(f"👤 Фигура: {body_type}, Цветотип: {color_type}")
    
    try:
        # Stage A: Жесткие фильтры
        filtered_items = apply_hard_filters(wardrobe_items, temperature, weather, body_type, color_type)
    except Exception as e:
        print(f"❌ Ошибка в фильтрации: {e}")
        return []
    
    if not filtered_items:
        print("❌ Нет подходящих вещей после фильтрации")
        return []
    
    print(f"✅ После фильтрации: {len(filtered_items)} вещей")
    for item in filtered_items:
        print(f"   - {item.get('category', 'Неизвестно')}: {item.get('description', 'Нет описания')[:50]}...")
    
    # Проверяем минимальные требования
    if not has_minimum_requirements(filtered_items):
        print("❌ Недостаточно вещей для создания капсул")
        return []
    
    # Stage B: Получаем шаблоны
    templates = get_capsule_templates()
    
    # Stage C-E: Генерируем капсулы
    capsules = []
    used_combinations = set(history or [])
    
    used_items = set()  # Отслеживаем использованные вещи
    item_usage_count = {}  # Отслеживаем количество использований для обуви и аксессуаров
    
    for template in templates:
        # Ограничиваем количество капсул для каждого шаблона
        remaining_slots = max_total - len(capsules)
        template_max = min(20, remaining_slots)  # Максимум 20 капсул на шаблон
        
        if template_max <= 0:
            break
            
        template_capsules = generate_capsules_for_template(
            filtered_items, template, template_max, used_combinations, used_items, item_usage_count
        )
        capsules.extend(template_capsules)
        
        if len(capsules) >= max_total:
            break
    
    # Сортируем по скорингу
    capsules.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Ограничиваем количество
    final_capsules = capsules[:max_total]
    
    # Преобразуем капсулы в формат, ожидаемый фронтендом
    formatted_capsules = []
    for i, capsule in enumerate(final_capsules):
        # Извлекаем ID вещей из капсулы
        item_ids = []
        for slot, item in capsule.items():
            if isinstance(item, dict) and 'id' in item:
                item_ids.append(item['id'])
        
        formatted_capsule = {
            'id': f'v3_capsule_{i+1}',
            'name': capsule.get('template', f'Образ {i+1}'),
            'items': item_ids,
            'description': capsule.get('explanation', 'Сбалансированный образ'),
            'score': capsule.get('score', 0),
            'missingShoes': 'shoes' not in capsule
        }
        formatted_capsules.append(formatted_capsule)
    
    print(f"✅ Сгенерировано капсул: {len(formatted_capsules)}")
    return formatted_capsules

def has_minimum_requirements(items: List[Dict[str, Any]]) -> bool:
    """Проверка минимальных требований для генерации"""
    categories = [item.get('category', '') for item in items]
    
    # Нужны либо низы, либо платья
    has_bottoms = any(cat in ['Джинсы', 'Брюки', 'Юбка', 'Шорты', 'Легинсы'] for cat in categories)
    has_dresses = any(cat in ['Платье', 'Сарафан', 'Комбинезон'] for cat in categories)
    
    return has_bottoms or has_dresses

def generate_capsules_for_template(items: List[Dict[str, Any]], 
                                 template: CapsuleTemplate,
                                 max_count: int,
                                 used_combinations: Set[str],
                                 used_items: Set[str],
                                 item_usage_count: Dict[str, int]) -> List[Dict[str, Any]]:
    """Генерация капсул для конкретного шаблона"""
    print(f"🎯 Генерируем капсулы для шаблона: {template.name}")
    
    # Группируем вещи по слотам
    items_by_slot = group_items_by_slots(items)
    
    capsules = []
    attempts = 0
    max_attempts = 100  # Уменьшаем количество попыток
    
    while len(capsules) < max_count and attempts < max_attempts:
        attempts += 1
        
        # Пробуем создать капсулу
        capsule = try_create_capsule(items_by_slot, template, used_combinations, used_items, item_usage_count)
        
        if capsule:
            # Проверяем совместимость
            if check_capsule_compatibility(capsule):
                # Скоринг
                score = score_capsule(capsule)
                if score >= 70:  # Порог качества
                    capsule['score'] = score
                    capsule['template'] = template.name
                    capsule['explanation'] = generate_explanation(capsule)
                    capsules.append(capsule)
                    
                    # Добавляем в использованные комбинации
                    combination_key = create_combination_key(capsule)
                    used_combinations.add(combination_key)
    
    print(f"✅ Для шаблона {template.name}: {len(capsules)} капсул")
    return capsules

def group_items_by_slots(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Группировка вещей по слотам"""
    slots = {
        'top': [],
        'middle': [],
        'outer': [],
        'bottom': [],
        'dress': [],
        'shoes': [],
        'bag': [],
        'accessory': []
    }
    
    for item in items:
        category = item.get('category', '')
        props = CATEGORY_PROPERTIES.get(category, {})
        layer = props.get('layer', LayerType.MIDDLE)
        
        print(f"   Группируем {category}: layer={layer}")
        
        if layer == LayerType.BASE:
            slots['top'].append(item)
        elif layer == LayerType.MIDDLE:
            slots['middle'].append(item)
        elif layer == LayerType.OUTER:
            slots['outer'].append(item)
        elif layer == LayerType.BOTTOM:
            slots['bottom'].append(item)
        elif layer == LayerType.DRESS:
            slots['dress'].append(item)
        elif layer == LayerType.SHOES:
            slots['shoes'].append(item)
        elif layer == LayerType.ACCESSORY:
            if 'сумка' in category.lower() or 'рюкзак' in category.lower() or 'клатч' in category.lower():
                slots['bag'].append(item)
            else:
                slots['accessory'].append(item)
    
    print(f"   Результат группировки:")
    for slot_name, slot_items in slots.items():
        if slot_items:
            print(f"     {slot_name}: {len(slot_items)} вещей")
    
    return slots

def try_create_capsule(items_by_slot: Dict[str, List[Dict[str, Any]]], 
                      template: CapsuleTemplate,
                      used_combinations: Set[str],
                      used_items: Set[str],
                      item_usage_count: Dict[str, int]) -> Optional[Dict[str, Any]]:
    """Попытка создания капсулы по шаблону"""
    capsule = {}
    
    # Заполняем обязательные слоты
    for slot in template.required_slots:
        if slot in items_by_slot and items_by_slot[slot]:
            # Умные ограничения для обуви и аксессуаров
            if slot == 'shoes':
                # Обувь: максимум 3 использования, но если нет обуви - игнорируем ограничение
                available_items = []
                for item in items_by_slot[slot]:
                    item_id = item['id']
                    if isinstance(item_id, list):
                        item_id = item_id[0] if item_id else 'unknown'
                    usage_count = item_usage_count.get(item_id, 0)
                    if usage_count < 3:
                        available_items.append(item)
                
                if not available_items:
                    # Если вся обувь использована 3+ раз, но есть обувь - берем подходящую (игнорируем ограничения)
                    available_items = items_by_slot[slot]
                    print(f"     ⚠️ Вся обувь использована 3+ раз, игнорируем ограничения и берем подходящую")
                
                if available_items:
                    item = random.choice(available_items)
                    capsule[slot] = item
                    item_id = item['id']
                    if isinstance(item_id, list):
                        item_id = item_id[0] if item_id else 'unknown'
                    item_usage_count[item_id] = item_usage_count.get(item_id, 0) + 1
                    print(f"     👟 Выбрана обувь: {item.get('name', 'Unknown')} (использований: {item_usage_count[item_id]})")
                else:
                    print(f"     ⚠️ Нет обуви для слота {slot}, создаем капсулу без обуви")
                    continue
            else:
                # Обычные вещи: максимум 1 использование
                available_items = []
                for item in items_by_slot[slot]:
                    item_id = item['id']
                    if isinstance(item_id, list):
                        item_id = item_id[0] if item_id else 'unknown'
                    if item_id not in used_items:
                        available_items.append(item)
                
                if not available_items:
                    # Если все вещи использованы, берем подходящую (игнорируем ограничения)
                    available_items = items_by_slot[slot]
                    print(f"     ⚠️ Все {slot} использованы, игнорируем ограничения и берем подходящую")
                
                item = random.choice(available_items)
                capsule[slot] = item
                item_id = item['id']
                if isinstance(item_id, list):
                    item_id = item_id[0] if item_id else 'unknown'
                used_items.add(item_id)
        else:
            # Если нет обуви, но есть другие обязательные элементы, создаем капсулу без обуви
            if slot == 'shoes':
                print(f"     ⚠️ Нет обуви для слота {slot}, создаем капсулу без обуви")
                continue
            else:
                return None  # Не можем создать капсулу без других обязательных элементов
    
    # Заполняем опциональные слоты
    for slot in template.optional_slots:
        if slot in items_by_slot and items_by_slot[slot]:
            if random.random() < 0.7:  # 70% вероятность добавить опциональный элемент
                # Умные ограничения для аксессуаров
                if slot == 'accessory':
                    # Аксессуары: максимум 2 использования, но если нет аксессуаров - игнорируем ограничение
                    available_items = []
                    for item in items_by_slot[slot]:
                        item_id = item['id']
                        if isinstance(item_id, list):
                            item_id = item_id[0] if item_id else 'unknown'
                        usage_count = item_usage_count.get(item_id, 0)
                        if usage_count < 2:
                            available_items.append(item)
                    
                    if not available_items:
                        # Если все аксессуары использованы 2+ раз, но есть аксессуары - берем подходящую (игнорируем ограничения)
                        available_items = items_by_slot[slot]
                        print(f"     ⚠️ Все аксессуары использованы 2+ раз, игнорируем ограничения и берем подходящую")
                    
                    if available_items:
                        item = random.choice(available_items)
                        capsule[slot] = item
                        item_id = item['id']
                        if isinstance(item_id, list):
                            item_id = item_id[0] if item_id else 'unknown'
                        item_usage_count[item_id] = item_usage_count.get(item_id, 0) + 1
                        print(f"     💍 Выбран аксессуар: {item.get('name', 'Unknown')} (использований: {item_usage_count[item_id]})")
                else:
                    # Обычные опциональные вещи: максимум 1 использование
                    available_items = []
                    for item in items_by_slot[slot]:
                        item_id = item['id']
                        if isinstance(item_id, list):
                            item_id = item_id[0] if item_id else 'unknown'
                        if item_id not in used_items:
                            available_items.append(item)
                    
                    if available_items:
                        item = random.choice(available_items)
                        capsule[slot] = item
                        item_id = item['id']
                        if isinstance(item_id, list):
                            item_id = item_id[0] if item_id else 'unknown'
                        used_items.add(item_id)
                    else:
                        # Если все вещи использованы, берем подходящую (игнорируем ограничения)
                        available_items = items_by_slot[slot]
                        if available_items:
                            item = random.choice(available_items)
                            capsule[slot] = item
                            print(f"     ⚠️ Все {slot} использованы, игнорируем ограничения и берем подходящую")
    
    # Проверяем, что комбинация не использовалась
    combination_key = create_combination_key(capsule)
    if combination_key in used_combinations:
        return None
    
    return capsule

def check_capsule_compatibility(capsule: Dict[str, Any]) -> bool:
    """Проверка совместимости элементов капсулы"""
    return (check_silhouette_compatibility(capsule) and
            check_color_compatibility(capsule) and
            check_texture_compatibility(capsule) and
            check_formality_compatibility(capsule))

def create_combination_key(capsule: Dict[str, Any]) -> str:
    """Создание ключа для комбинации вещей"""
    item_ids = []
    for slot, item in capsule.items():
        if isinstance(item, dict) and 'id' in item:
            item_id = item['id']
            # Если id это список, берем первый элемент
            if isinstance(item_id, list):
                item_id = item_id[0] if item_id else 'unknown'
            item_ids.append(str(item_id))
    
    return '|'.join(sorted(item_ids))

def generate_explanation(capsule: Dict[str, Any]) -> str:
    """Генерация объяснения для капсулы"""
    # Базовая реализация
    return "Сбалансированный образ с хорошим сочетанием цветов и фактур"

# ============================================================================
# ЭКСПОРТИРУЕМАЯ ФУНКЦИЯ
# ============================================================================

def generate_capsules(wardrobe_items: List[Dict[str, Any]], 
                     temperature: Optional[float] = None,
                     max_total: int = 20,
                     weather: Optional[Dict[str, Any]] = None,
                     body_type: Optional[str] = None,
                     color_type: Optional[str] = None,
                     history: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Главная функция для генерации капсул
    Совместима с существующим API
    """
    capsules = generate_capsules_v3(
        wardrobe_items=wardrobe_items,
        temperature=temperature,
        max_total=max_total,
        weather=weather,
        body_type=body_type,
        color_type=color_type,
        history=history
    )
    
    # Преобразуем в формат, ожидаемый app.py
    return {
        'categories': [
            {
                'id': 'v3_generated',
                'name': 'Сгенерированные образы',
                'description': 'Образы, созданные новым алгоритмом v3',
                'fullCapsules': capsules,
                'examples': capsules[:3] if capsules else []
            }
        ],
        'total_capsules': len(capsules)
    }
