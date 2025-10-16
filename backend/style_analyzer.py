"""
Анализатор стиля и цвета для улучшенной генерации капсул

Без использования GPT - только rule-based логика
"""

import re
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import Counter


# ============================================================================
# ЦВЕТОВОЙ АНАЛИЗ
# ============================================================================

# Основные цвета с вариациями написания
COLOR_KEYWORDS = {
    'черный': ['черн', 'black'],
    'белый': ['бел', 'white', 'молочн', 'ivory', 'слоновая кость'],
    'серый': ['сер', 'grey', 'gray', 'пепельн', 'графит'],
    'бежевый': ['беж', 'beige', 'песочн', 'кремов', 'camel', 'верблюж'],
    'коричневый': ['коричнев', 'brown', 'шоколад', 'кофе', 'каштан'],
    'синий': ['син', 'blue', 'голуб', 'лазур', 'небесн'],
    'красный': ['красн', 'red', 'бордо', 'вишнев', 'алый', 'багров', 'винн'],
    'зеленый': ['зелен', 'green', 'хаки', 'оливк', 'изумруд', 'мятн'],
    'желтый': ['желт', 'yellow', 'лимон', 'горчич', 'gold', 'золот'],
    'оранжевый': ['оранж', 'orange', 'терракот', 'рыжий'],
    'розовый': ['розов', 'pink', 'пудр', 'фуксия', 'коралл'],
    'фиолетовый': ['фиолет', 'purple', 'сирен', 'лаванд', 'баклажан'],
    'бордовый': ['бордо', 'burgundy', 'марсала', 'вишнев'],
    'хаки': ['хаки', 'khaki', 'оливк']
}

# Нейтральные цвета (сочетаются со всем)
NEUTRAL_COLORS = {'черный', 'белый', 'серый', 'бежевый', 'коричневый'}

# Яркие цвета (акцентные)
BRIGHT_COLORS = {'красный', 'желтый', 'оранжевый', 'розовый', 'фиолетовый', 'синий', 'зеленый'}

# Цветовая гармония (какие цвета сочетаются)
COLOR_HARMONY = {
    'черный': {'белый', 'серый', 'красный', 'желтый', 'розовый', 'синий', 'зеленый', 'оранжевый', 'фиолетовый'},  # Сочетается со всем
    'белый': {'черный', 'серый', 'синий', 'красный', 'зеленый', 'коричневый', 'бежевый'},  # Сочетается почти со всем
    'серый': {'белый', 'черный', 'розовый', 'синий', 'желтый', 'фиолетовый'},
    'бежевый': {'белый', 'коричневый', 'синий', 'зеленый', 'розовый'},
    'коричневый': {'бежевый', 'белый', 'зеленый', 'оранжевый', 'желтый'},
    'синий': {'белый', 'черный', 'серый', 'бежевый', 'желтый', 'оранжевый'},
    'красный': {'черный', 'белый', 'бежевый', 'серый'},
    'зеленый': {'бежевый', 'коричневый', 'белый', 'черный'},
    'желтый': {'серый', 'синий', 'черный', 'белый'},
    'оранжевый': {'синий', 'коричневый', 'белый', 'черный'},
    'розовый': {'серый', 'белый', 'бежевый', 'черный'},
    'фиолетовый': {'серый', 'белый', 'желтый', 'черный'},
}


def extract_colors(description: str) -> List[str]:
    """
    Извлекает цвета из описания вещи
    
    Returns:
        Список найденных цветов (например: ['черный', 'белый'])
    """
    if not description:
        return []
    
    desc_lower = description.lower()
    found_colors = []
    
    for color, keywords in COLOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                if color not in found_colors:
                    found_colors.append(color)
                break
    
    return found_colors


def are_colors_harmonious(colors: List[str]) -> bool:
    """
    Проверяет гармоничность цветовой комбинации
    
    Правила:
    - Если все нейтральные → ОК
    - Если нейтральные + 1 яркий → ОК
    - Если нейтральные + 2 ярких (сочетаемых) → ОК
    - Если 3+ ярких → НЕТ
    """
    if not colors:
        return True
    
    # Разделяем на нейтральные и яркие
    neutral_count = sum(1 for c in colors if c in NEUTRAL_COLORS)
    bright = [c for c in colors if c in BRIGHT_COLORS]
    
    # Все нейтральные - отлично
    if len(bright) == 0:
        return True
    
    # Нейтральные + 1 яркий - отлично
    if len(bright) == 1:
        return True
    
    # Нейтральные + 2 ярких - проверяем сочетаемость
    if len(bright) == 2:
        c1, c2 = bright[0], bright[1]
        return c2 in COLOR_HARMONY.get(c1, set()) or c1 in COLOR_HARMONY.get(c2, set())
    
    # 3+ ярких цвета - перебор
    return False


def get_color_palette(colors: List[str]) -> str:
    """
    Определяет цветовую палитру капсулы
    
    Returns:
        Название палитры: 'monochrome', 'neutral', 'accent', 'colorful'
    """
    if not colors:
        return 'neutral'
    
    neutral_count = sum(1 for c in colors if c in NEUTRAL_COLORS)
    bright_count = sum(1 for c in colors if c in BRIGHT_COLORS)
    
    # Монохром (1 цвет)
    if len(set(colors)) == 1:
        return 'monochrome'
    
    # Нейтральная палитра (только нейтральные)
    if bright_count == 0:
        return 'neutral'
    
    # Акцентная (нейтральные + 1 яркий)
    if bright_count == 1 and neutral_count > 0:
        return 'accent'
    
    # Яркая (2+ ярких)
    return 'colorful'


# ============================================================================
# АНАЛИЗ СТИЛЯ
# ============================================================================

STYLE_KEYWORDS = {
    'деловой': {
        'keywords': ['пиджак', 'костюм', 'классическ', 'офис', 'деловой', 'строг', 'formal'],
        'compatible': ['casual', 'минималистичный']
    },
    'casual': {
        'keywords': ['casual', 'повседневн', 'базов', 'джинс', 'футболк', 'свитшот'],
        'compatible': ['деловой', 'спортивный', 'минималистичный']
    },
    'спортивный': {
        'keywords': ['спорт', 'sports', 'лосины', 'худи', 'толстовк', 'кроссовк', 'снекер'],
        'compatible': ['casual']
    },
    'романтичный': {
        'keywords': ['романтичн', 'цветочн', 'рюши', 'кружев', 'воздушн', 'нежн', 'feminine'],
        'compatible': ['casual']
    },
    'уличный': {
        'keywords': ['оверсайз', 'oversize', 'street', 'urban', 'грубый', 'винтаж'],
        'compatible': ['casual', 'спортивный']
    },
    'минималистичный': {
        'keywords': ['минимал', 'minimal', 'лаконичн', 'простой', 'чист'],
        'compatible': ['деловой', 'casual']
    },
    'вечерний': {
        'keywords': ['вечерн', 'коктейльн', 'нарядн', 'праздничн', 'блеск', 'sequin', 'пайетк'],
        'compatible': []
    }
}


def detect_style(description: str) -> str:
    """
    Определяет стиль вещи из описания
    
    Returns:
        Название стиля или 'casual' по умолчанию
    """
    if not description:
        return 'casual'
    
    desc_lower = description.lower()
    
    # Подсчитываем совпадения для каждого стиля
    style_scores = {}
    for style, data in STYLE_KEYWORDS.items():
        score = sum(1 for keyword in data['keywords'] if keyword in desc_lower)
        if score > 0:
            style_scores[style] = score
    
    # Возвращаем стиль с максимальным совпадением
    if style_scores:
        return max(style_scores, key=style_scores.get)
    
    return 'casual'


def are_styles_compatible(styles: List[str]) -> bool:
    """
    Проверяет совместимость стилей в капсуле
    
    Правила:
    - Все вещи одного стиля → ОК
    - Совместимые стили → ОК
    - Несовместимые (деловой + спортивный) → НЕТ
    """
    if not styles or len(set(styles)) == 1:
        return True  # Все одного стиля
    
    unique_styles = set(styles)
    
    # Проверяем каждую пару
    for style1 in unique_styles:
        for style2 in unique_styles:
            if style1 != style2:
                compatible = STYLE_KEYWORDS.get(style1, {}).get('compatible', [])
                if style2 not in compatible:
                    return False
    
    return True


# ============================================================================
# АНАЛИЗ ПРИНТОВ И ПАТТЕРНОВ
# ============================================================================

PATTERN_KEYWORDS = {
    'полоска': ['полоск', 'stripe', 'в полоск'],
    'клетка': ['клетк', 'plaid', 'check', 'в клетк'],
    'горошек': ['горошек', 'горох', 'dot', 'polka'],
    'цветочный': ['цветочн', 'floral', 'цветы', 'flowers', 'botanical'],
    'леопардовый': ['леопард', 'leopard', 'анималистичн', 'animal'],
    'абстрактный': ['абстракт', 'abstract', 'геометр'],
    'однотонный': ['однотон', 'solid', 'гладк']
}


def detect_pattern(description: str) -> Optional[str]:
    """
    Определяет наличие принта/паттерна
    
    Returns:
        Название паттерна или None если однотонная
    """
    if not description:
        return None
    
    desc_lower = description.lower()
    
    for pattern, keywords in PATTERN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return pattern
    
    return None  # Однотонная


def check_pattern_compatibility(patterns: List[Optional[str]]) -> bool:
    """
    Проверяет совместимость паттернов
    
    Правило: максимум 1 принт на капсулу (или все однотонное)
    """
    # Убираем None (однотонные вещи)
    actual_patterns = [p for p in patterns if p is not None]
    
    # Если 0-1 принт - ОК
    return len(actual_patterns) <= 1


# ============================================================================
# АНАЛИЗ СИЛУЭТА
# ============================================================================

SILHOUETTE_KEYWORDS = {
    'оверсайз': ['оверсайз', 'oversize', 'свободн', 'широк', 'мешковат', 'объемн'],
    'облегающий': ['облегающ', 'fitted', 'tight', 'узк', 'приталенн', 'slim'],
    'прямой': ['прямой', 'straight', 'классическ'],
    'А-силуэт': ['а-силуэт', 'трапеци', 'расклешенн']
}


def detect_silhouette(description: str, category: str) -> str:
    """
    Определяет силуэт вещи
    
    Returns:
        'oversize', 'fitted', 'straight', 'A-line', или 'straight' по умолчанию
    """
    if not description:
        return 'straight'
    
    desc_lower = description.lower()
    
    for silhouette, keywords in SILHOUETTE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                if silhouette == 'оверсайз':
                    return 'oversize'
                elif silhouette == 'облегающий':
                    return 'fitted'
                elif silhouette == 'А-силуэт':
                    return 'A-line'
    
    return 'straight'


def check_silhouette_balance(top_silhouette: str, bottom_silhouette: str) -> bool:
    """
    Проверяет баланс силуэтов верха и низа
    
    Правило: широкий верх = узкий низ (и наоборот)
    """
    # Оверсайз верх + оверсайз низ = плохо
    if top_silhouette == 'oversize' and bottom_silhouette == 'oversize':
        return False
    
    # Облегающий верх + облегающий низ = может быть слишком тесно
    # Но допустимо для некоторых образов
    if top_silhouette == 'fitted' and bottom_silhouette == 'fitted':
        return True  # Разрешаем
    
    # Оверсайз верх + узкий низ = идеально
    if top_silhouette == 'oversize' and bottom_silhouette == 'fitted':
        return True
    
    # Все остальные комбинации - ОК
    return True


# ============================================================================
# АНАЛИЗ МАТЕРИАЛОВ
# ============================================================================

MATERIAL_KEYWORDS = {
    'хлопок': {
        'keywords': ['хлопок', 'cotton', 'коттон'],
        'seasons': ['Весна', 'Лето', 'Осень', 'Всесезонный']
    },
    'лен': {
        'keywords': ['лен', 'linen'],
        'seasons': ['Весна', 'Лето']
    },
    'шелк': {
        'keywords': ['шелк', 'silk'],
        'seasons': ['Весна', 'Лето', 'Осень']
    },
    'шерсть': {
        'keywords': ['шерст', 'wool', 'кашемир', 'cashmere'],
        'seasons': ['Осень', 'Зима']
    },
    'кожа': {
        'keywords': ['кож', 'leather', 'замш', 'suede', 'нубук'],
        'seasons': ['Весна', 'Осень', 'Зима', 'Всесезонный']
    },
    'деним': {
        'keywords': ['джинс', 'denim', 'деним'],
        'seasons': ['Весна', 'Осень', 'Всесезонный']
    },
    'трикотаж': {
        'keywords': ['трикотаж', 'knit', 'вязан'],
        'seasons': ['Осень', 'Зима', 'Весна']
    },
    'синтетика': {
        'keywords': ['полиэстер', 'polyester', 'нейлон', 'nylon', 'эластан'],
        'seasons': ['Весна', 'Лето', 'Осень', 'Зима', 'Всесезонный']
    }
}


def detect_material(description: str) -> Optional[str]:
    """
    Определяет основной материал вещи
    """
    if not description:
        return None
    
    desc_lower = description.lower()
    
    for material, data in MATERIAL_KEYWORDS.items():
        for keyword in data['keywords']:
            if keyword in desc_lower:
                return material
    
    return None


def is_material_seasonal(material: Optional[str], season: str) -> bool:
    """
    Проверяет соответствие материала сезону
    """
    if not material:
        return True  # Неизвестный материал - разрешаем
    
    material_data = MATERIAL_KEYWORDS.get(material, {})
    allowed_seasons = material_data.get('seasons', [])
    
    return season in allowed_seasons or 'Всесезонный' in allowed_seasons


# ============================================================================
# ОПРЕДЕЛЕНИЕ ПОВОДА
# ============================================================================

OCCASION_RULES = {
    'офис': {
        'required_styles': ['деловой', 'минималистичный', 'casual'],
        'forbidden_styles': ['спортивный', 'вечерний'],
        'preferred_colors': NEUTRAL_COLORS,
        'max_bright_colors': 1,
        'icon': '🏢'
    },
    'прогулка': {
        'required_styles': ['casual', 'уличный', 'спортивный'],
        'forbidden_styles': ['деловой', 'вечерний'],
        'preferred_colors': NEUTRAL_COLORS | BRIGHT_COLORS,
        'max_bright_colors': 2,
        'icon': '☕'
    },
    'вечер': {
        'required_styles': ['вечерний', 'деловой', 'романтичный'],
        'forbidden_styles': ['спортивный'],
        'preferred_colors': {'черный', 'белый', 'красный', 'синий', 'серый'},
        'max_bright_colors': 2,
        'icon': '🍷'
    },
    'спорт': {
        'required_styles': ['спортивный', 'casual'],
        'forbidden_styles': ['деловой', 'вечерний', 'романтичный'],
        'preferred_colors': BRIGHT_COLORS | NEUTRAL_COLORS,
        'max_bright_colors': 3,
        'icon': '🏃'
    }
}


def detect_occasion(items: List[Dict[str, Any]]) -> str:
    """
    Определяет повод для капсулы на основе стилей вещей
    
    Returns:
        'офис', 'прогулка', 'вечер', 'спорт' или 'повседневный'
    """
    if not items:
        return 'повседневный'
    
    # Определяем стили всех вещей
    styles = [detect_style(item.get('description', '')) for item in items]
    style_counts = Counter(styles)
    
    # Проверяем каждый повод
    occasion_scores = {}
    
    for occasion, rules in OCCASION_RULES.items():
        score = 0
        
        # Проверяем required styles
        for req_style in rules['required_styles']:
            if req_style in style_counts:
                score += style_counts[req_style] * 2  # Удвоенный вес для required
        
        # Штраф за forbidden styles
        for forbidden_style in rules['forbidden_styles']:
            if forbidden_style in style_counts:
                score -= style_counts[forbidden_style] * 3  # Тройной штраф
        
        occasion_scores[occasion] = score
    
    # Выбираем повод с максимальным score
    if occasion_scores:
        best_occasion = max(occasion_scores, key=occasion_scores.get)
        if occasion_scores[best_occasion] > 0:
            return best_occasion
    
    return 'прогулка'  # Default


# ============================================================================
# АНАЛИЗ АКСЕССУАРОВ
# ============================================================================

def detect_metal_tone(description: str) -> Optional[str]:
    """
    Определяет тон металла в украшениях
    
    Returns:
        'золото', 'серебро' или None
    """
    if not description:
        return None
    
    desc_lower = description.lower()
    
    gold_keywords = ['золот', 'gold', 'желтый металл', 'розовое золото']
    silver_keywords = ['серебр', 'silver', 'белый металл', 'платин']
    
    has_gold = any(k in desc_lower for k in gold_keywords)
    has_silver = any(k in desc_lower for k in silver_keywords)
    
    if has_gold and not has_silver:
        return 'золото'
    elif has_silver and not has_gold:
        return 'серебро'
    
    return None


def check_metal_consistency(accessories: List[Dict[str, Any]]) -> bool:
    """
    Проверяет единство тона металла в аксессуарах
    
    Правило: все украшения должны быть одного тона (золото ИЛИ серебро)
    """
    metals = [detect_metal_tone(acc.get('description', '')) for acc in accessories]
    actual_metals = [m for m in metals if m is not None]
    
    # Если нет определенных металлов - ОК
    if len(actual_metals) == 0:
        return True
    
    # Все одного тона - ОК
    return len(set(actual_metals)) <= 1


# ============================================================================
# SCORING CAPSULE (ОЦЕНКА КАПСУЛЫ)
# ============================================================================

def score_capsule(items: List[Dict[str, Any]], season: str, temperature: float) -> Dict[str, Any]:
    """
    Оценивает качество капсулы по множеству критериев
    
    Returns:
        {
            'total_score': int (0-100),
            'color_score': int,
            'style_score': int,
            'pattern_score': int,
            'balance_score': int,
            'occasion': str,
            'palette': str,
            'issues': List[str]
        }
    """
    scores = {
        'total_score': 0,
        'color_score': 0,
        'style_score': 0,
        'pattern_score': 0,
        'balance_score': 0,
        'accessory_score': 0,
        'occasion': 'повседневный',
        'palette': 'neutral',
        'issues': []
    }
    
    if not items:
        return scores
    
    # 1. ЦВЕТОВАЯ ГАРМОНИЯ (30 баллов)
    all_colors = []
    for item in items:
        colors = extract_colors(item.get('description', ''))
        all_colors.extend(colors)
    
    if are_colors_harmonious(all_colors):
        scores['color_score'] = 30
    else:
        scores['color_score'] = 10
        scores['issues'].append('Несочетаемые цвета')
    
    scores['palette'] = get_color_palette(all_colors)
    
    # 2. СТИЛЕВАЯ СОВМЕСТИМОСТЬ (25 баллов)
    styles = [detect_style(item.get('description', '')) for item in items]
    if are_styles_compatible(styles):
        scores['style_score'] = 25
    else:
        scores['style_score'] = 10
        scores['issues'].append('Несовместимые стили')
    
    scores['occasion'] = detect_occasion(items)
    
    # 3. ПАТТЕРНЫ (15 баллов)
    patterns = [detect_pattern(item.get('description', '')) for item in items]
    if check_pattern_compatibility(patterns):
        scores['pattern_score'] = 15
    else:
        scores['pattern_score'] = 5
        scores['issues'].append('Слишком много принтов')
    
    # 4. БАЛАНС СИЛУЭТОВ (15 баллов)
    tops = [item for item in items if item.get('category', '').lower() in ['верх', 'блузка', 'футболка', 'рубашка']]
    bottoms = [item for item in items if item.get('category', '').lower() in ['низ', 'брюки', 'юбка']]
    
    if tops and bottoms:
        top_sil = detect_silhouette(tops[0].get('description', ''), tops[0].get('category', ''))
        bottom_sil = detect_silhouette(bottoms[0].get('description', ''), bottoms[0].get('category', ''))
        
        if check_silhouette_balance(top_sil, bottom_sil):
            scores['balance_score'] = 15
        else:
            scores['balance_score'] = 5
            scores['issues'].append('Несбалансированный силуэт')
    else:
        scores['balance_score'] = 10  # Нейтральная оценка если нет пары верх+низ
    
    # 5. АКСЕССУАРЫ (15 баллов)
    accessories = [item for item in items if 'аксессуар' in item.get('category', '').lower() or 'сумка' in item.get('category', '').lower()]
    
    if check_metal_consistency(accessories):
        scores['accessory_score'] = 15
    else:
        scores['accessory_score'] = 5
        scores['issues'].append('Смешаны золото и серебро')
    
    # Штраф за слишком много аксессуаров (>4)
    if len(accessories) > 4:
        scores['accessory_score'] -= 5
        scores['issues'].append('Перегруз аксессуарами')
    
    # ИТОГОВЫЙ СЧЕТ
    scores['total_score'] = (
        scores['color_score'] + 
        scores['style_score'] + 
        scores['pattern_score'] + 
        scores['balance_score'] + 
        scores['accessory_score']
    )
    
    return scores


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_dominant_color(items: List[Dict[str, Any]]) -> Optional[str]:
    """
    Определяет доминирующий цвет в капсуле
    """
    all_colors = []
    for item in items:
        colors = extract_colors(item.get('description', ''))
        all_colors.extend(colors)
    
    if not all_colors:
        return None
    
    # Подсчитываем частоту цветов
    color_counts = Counter(all_colors)
    return color_counts.most_common(1)[0][0]


def analyze_capsule_richness(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует насыщенность и емкость капсулы
    
    Returns:
        {
            'item_count': int,
            'layer_count': int,  # Количество слоев (верх)
            'accessory_count': int,
            'color_variety': int,  # Количество уникальных цветов
            'has_statement_piece': bool  # Есть ли акцентная вещь
        }
    """
    # Подсчитываем слои одежды
    layers = sum(1 for item in items if item.get('category', '').lower() in [
        'верх', 'блузка', 'футболка', 'рубашка', 'свитер', 'пиджак', 'куртка', 'верхняя одежда'
    ])
    
    # Подсчитываем аксессуары
    accs = sum(1 for item in items if 'аксессуар' in item.get('category', '').lower() or 'сумка' in item.get('category', '').lower())
    
    # Уникальные цвета
    all_colors = []
    for item in items:
        all_colors.extend(extract_colors(item.get('description', '')))
    color_variety = len(set(all_colors))
    
    # Акцентная вещь (яркий цвет или необычный паттерн)
    has_statement = any(
        any(c in BRIGHT_COLORS for c in extract_colors(item.get('description', ''))) or
        detect_pattern(item.get('description', '')) in ['леопардовый', 'цветочный', 'абстрактный']
        for item in items
    )
    
    return {
        'item_count': len(items),
        'layer_count': layers,
        'accessory_count': accs,
        'color_variety': color_variety,
        'has_statement_piece': has_statement
    }

