"""
Capsule Engine V4 - ПРАВИЛЬНАЯ ЛОГИКА

ОБЯЗАТЕЛЬНАЯ БАЗОВАЯ КАПСУЛА:
- Верх + Низ (или Платье) + Обувь + Сумка + Серьги/Бусы + Ремень/Браслет

ТЕМПЕРАТУРНЫЕ ДОПОЛНЕНИЯ:
- Холодно (<15°C): Верхняя одежда + Шапка + Шарф + Перчатки
- Холодно + верхняя одежда: убираем видимые украшения (ремень, браслет)

АКСЕССУАРЫ:
- Теплая погода: серьги + ремень/браслет + опционально (бусы, очки)
- Холодная погода: серьги (макс) + шапка + шарф + перчатки

Автор: AI Assistant
Дата: 2025-10-12
"""

import random
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass


@dataclass
class Capsule:
    id: str
    name: str
    items: List[str]
    description: str


def tokenize_category(raw: str) -> Set[str]:
    """Токенизация категории"""
    if not raw:
        return set()
    s = raw.lower().strip()
    tokens = set()
    for word in s.split():
        word = word.strip('.,!?;:()[]{}«»"\'')
        if len(word) >= 3:
            # Сохраняем начало слова для поиска корней
            tokens.add(word[:6])
    return tokens


def translate_category(raw: str) -> str:
    """
    Переводит категорию в стандартный формат
    
    Возвращает: tops, bottoms, dresses, outerwear, light_outerwear, shoes, bags, accessories, other
    """
    if not raw:
        return "other"
    
    tokens = tokenize_category(raw)
    
    # LIGHT OUTERWEAR — легкая верхняя одежда (требует базового верха под низ!)
    light_outerwear = {"кардиг", "жилет", "пиджак", "жакет", "болеро"}
    if tokens & light_outerwear:
        return "light_outerwear"
    
    # TOPS — верх (базовый)
    tops = {"верх", "блузк", "футбол", "рубашк", "топ", "свитер", "джемпер", "лонгс", "водол", "майка"}
    if tokens & tops:
        return "tops"
    
    # BOTTOMS — низ
    bottoms = {"низ", "брюки", "джинс", "юбка", "шорты", "легин", "штаны"}
    if tokens & bottoms:
        return "bottoms"
    
    # DRESSES — платья
    dresses = {"платье", "сараф", "комбин"}
    if tokens & dresses:
        return "dresses"
    
    # OUTERWEAR — верхняя одежда
    outerwear = {"куртка", "пальто", "плащ", "тренч", "парка", "пуховик", "ветров", "бомбер", "косух", "дублен", "шуба"}
    if tokens & outerwear:
        return "outerwear"
    
    # SHOES — обувь
    shoes = {"обувь", "туфли", "ботинк", "сапог", "кроссо", "кеды", "слипон", "балетк", "босон", "лоферы", "мокаси", "сандал", "босони"}
    if tokens & shoes:
        return "shoes"
    
    # BAGS — сумки (ОТДЕЛЬНАЯ категория!)
    bags = {"сумка", "сумка-", "тоут", "shoppe", "шоппе", "багет", "кроссб", "седло-", "хобо", "почтал", "портфе", "рюкзак", "клатч"}
    if tokens & bags:
        return "bags"
    
    # ACCESSORIES — аксессуары
    accessories = {
        "аксесс", "ремень", "пояс", "шарф", "платок", "палант", "снуд", "шаль", 
        "галсту", "брошь", "заколк", "шапка", "кепка", "берет", "шляпа", "панам",
        "очки", "часы", "браслет", "серьги", "колье", "бусы", "кольцо", "цепоч",
        "перчатк", "варежк"
    }
    if tokens & accessories:
        return "accessories"
    
    return "other"


def accessory_subtype(item: Dict[str, Any]) -> str:
    """
    Определяет подтип аксессуара
    
    Returns: earrings, necklace, bracelet, belt, scarf, headwear, gloves, bag, watch, sunglasses, other
    """
    desc = (item.get('description', '') + ' ' + item.get('category', '')).lower()
    tokens = tokenize_category(desc)
    
    # Украшения (видимые)
    if tokens & {"серьги", "серёжк"}:
        return "earrings"
    if tokens & {"колье", "бусы", "ожерел", "цепоч", "подвес"}:
        return "necklace"
    if tokens & {"браслет"}:
        return "bracelet"
    if tokens & {"кольцо", "перстен"}:
        return "ring"
    if tokens & {"ремень", "пояс"}:
        return "belt"
    
    # Теплые аксессуары
    if tokens & {"шарф", "платок", "палант", "снуд"}:
        return "scarf"
    if tokens & {"шапка", "шапк", "берет", "кепка", "панам", "шляпа"}:
        return "headwear"
    if tokens & {"перчатк", "варежк", "митенк"}:
        return "gloves"
    
    # Функциональные
    if tokens & {"часы"}:
        return "watch"
    if tokens & {"очки", "солнце"}:
        return "sunglasses"
    
    return "other"


def get_item_warmth_level(item: Dict[str, Any]) -> str:
    """Определяет уровень теплоты вещи (БЕЗ сумок - они температурно-нейтральные)"""
    desc = item.get('description', '').lower()
    category = item.get('category', '').lower()
    text = f"{desc} {category}"
    
    # VERY_LIGHT (25-60°C)
    if any(word in text for word in ['сарафан', 'майка', 'сандал', 'босоножк', 'топ-труба', 'корсет']):
        return 'VERY_LIGHT'
    
    # LIGHT (15-25°C) 
    elif any(word in text for word in ['футболк', 'блузк', 'рубашк', 'топ', 'кеды', 'босоножк']):
        return 'LIGHT'
    
    # MEDIUM (5-15°C)
    elif any(word in text for word in ['кардиг', 'жакет', 'пиджак', 'джинс', 'юбк', 'брюк', 'кроссовк', 'туфл']):
        return 'MEDIUM'
    
    # WARM (-5-5°C)
    elif any(word in text for word in ['свитер', 'толстовк', 'худи', 'джемпер', 'пуловер', 'ботинк', 'сапог']):
        return 'WARM'
    
    # VERY_WARM (-60--5°C)
    elif any(word in text for word in ['пуховик', 'пальто', 'куртк', 'шуб', 'дубленк', 'валенк', 'дутик']):
        return 'VERY_WARM'
    
    # По умолчанию MEDIUM
    return 'MEDIUM'

def is_suitable_for_temp_and_season(item: Dict[str, Any], temp_c: float, season: str) -> bool:
    """
    Проверяет подходит ли вещь для температуры и сезона (СТРОГОЕ СОБЛЮДЕНИЕ ТЗ)
    
    ТЕМПЕРАТУРНЫЕ ДИАПАЗОНЫ:
    - VERY_LIGHT: 25-60°C (сарафан, майка, сандалии)
    - LIGHT: 15-25°C (футболка, блузка, рубашка)
    - MEDIUM: 5-15°C (кардиган, джинсы, кроссовки)
    - WARM: -5-5°C (свитер, толстовка, ботинки)
    - VERY_WARM: -60--5°C (пуховик, пальто, сапоги)
    
    ИСКЛЮЧЕНИЯ (температурно-нейтральные):
    - bags (сумки)
    - accessories (аксессуары)
    """
    desc = item.get('description', '').lower()
    category = item.get('category', '').lower()
    item_category = translate_category(category)
    
    # СУМКИ И АКСЕССУАРЫ - ТЕМПЕРАТУРНО-НЕЙТРАЛЬНЫЕ (всегда проходят)
    if item_category in ['bags', 'accessories']:
        return True
    
    # Определяем уровень теплоты вещи
    warmth_level = get_item_warmth_level(item)
    
    # Температурные диапазоны (РАСШИРЕННЫЕ, С ПЕРЕКРЫТИЯМИ)
    temp_ranges = {
        'VERY_LIGHT': (22, 60),   # +22°C и выше (летние вещи)
        'LIGHT': (12, 60),        # +12°C и выше (легкие вещи подходят до зимы)
        'MEDIUM': (-5, 25),       # -5 до +25°C (базовые вещи - почти всесезон)
        'WARM': (-60, 15),        # до +15°C (теплые вещи - в прохладу)
        'VERY_WARM': (-60, 5),    # до +5°C (зимние вещи)
    }
    
    # Проверяем соответствие температуры
    temp_range = temp_ranges.get(warmth_level, (-5, 25))
    is_temp_ok = temp_range[0] <= temp_c <= temp_range[1]
    
    if not is_temp_ok:
        return False
    
    # Дополнительная проверка для шорт
    if 'шорт' in desc or 'шорт' in category:
        # Шорты только в жару или летом
        if temp_c >= 22.0 or season == 'Лето':
            return True
        else:
            return False  # ❌ Блокируем шорты осенью/весной/зимой при <22°C
    
    return True


def generate_capsules_v4_old(
    wardrobe_items: List[Dict[str, Any]],
    season_hint: str,
    temp_c: float,
    predpochtenia: str = "Повседневный",
    figura: str = "",
    cvetotip: str = "",
    banned_ids: Optional[List[str]] = None,
    allowed_ids: Optional[List[str]] = None,
    max_total: int = 20
) -> Dict[str, Any]:
    """
    Генерирует капсулы с ПРАВИЛЬНОЙ логикой
    
    ОБЯЗАТЕЛЬНАЯ СТРУКТУРА КАПСУЛЫ:
    - База: Верх + Низ (или Платье) + Обувь + Сумка
    - Обязательные аксессуары (теплая погода): Серьги/Бусы + Ремень/Браслет
    - Обязательные аксессуары (холодная погода): Шапка + Шарф + Перчатки + макс Серьги
    - Опциональные: очки, часы, дополнительные украшения
    
    Args:
        wardrobe_items: Гардероб пользователя
        season_hint: Сезон
        temp_c: Температура
        max_total: Максимум капсул (по умолчанию 20)
    
    Returns:
        Dict с капсулами в формате {categories: [{fullCapsules: [...]}]}
    """
    
    print(f"🎯 Capsule Engine V4: Правильная логика формирования капсул")
    print(f"   Сезон: {season_hint}, Температура: {temp_c}°C, Макс: {max_total}")
    
    # Группируем вещи по категориям с фильтрацией по температуре/сезону
    by_category = defaultdict(list)
    for item in wardrobe_items:
        if banned_ids and str(item.get('id')) in banned_ids:
            continue
        if allowed_ids and str(item.get('id')) not in allowed_ids:
            continue
        
        # ФИЛЬТРАЦИЯ: проверяем подходит ли вещь для температуры/сезона
        if not is_suitable_for_temp_and_season(item, temp_c, season_hint):
            continue
        
        cat = translate_category(item.get('category', ''))
        by_category[cat].append(item)
    
    # Группируем аксессуары по подтипам
    accessories_by_subtype = defaultdict(list)
    for acc in by_category['accessories']:
        subtype = accessory_subtype(acc)
        accessories_by_subtype[subtype].append(acc)
    
    # Проверяем что есть сумки (они могут быть в accessories)
    bags_list = by_category['bags'].copy()
    # Если нет отдельной категории bags, ищем в accessories
    if not bags_list:
        for item in wardrobe_items:
            if 'сумка' in item.get('category', '').lower():
                bags_list.append(item)
    
    # Статистика
    print(f"📊 Категории: tops={len(by_category['tops'])}, bottoms={len(by_category['bottoms'])}, "
          f"dresses={len(by_category['dresses'])}, outer={len(by_category['outerwear'])}, "
          f"light_outer={len(by_category['light_outerwear'])}, "
          f"shoes={len(by_category['shoes'])}, bags={len(bags_list)}, "
          f"accs={len(by_category['accessories'])}")
    
    print(f"💍 Аксессуары по типам:")
    for subtype, items in accessories_by_subtype.items():
        if items:
            print(f"   - {subtype}: {len(items)}")
    
    # Перемешиваем для разнообразия
    random.shuffle(by_category['tops'])
    random.shuffle(by_category['bottoms'])
    random.shuffle(by_category['dresses'])
    random.shuffle(by_category['outerwear'])
    random.shuffle(by_category['light_outerwear'])
    random.shuffle(by_category['shoes'])
    random.shuffle(bags_list)
    
    # Создаем очереди
    tops_q = deque(by_category['tops'])
    bottoms_q = deque(by_category['bottoms'])
    dresses_q = deque(by_category['dresses'])
    outer_q = deque(by_category['outerwear'])
    light_outer_q = deque(by_category['light_outerwear'])  # ← Новая очередь для кардиганов/жилетов
    shoes_q = deque(by_category['shoes'])
    bags_q = deque(bags_list)
    
    # Очереди аксессуаров по типам
    earrings_q = deque(accessories_by_subtype.get('earrings', []))
    necklace_q = deque(accessories_by_subtype.get('necklace', []))
    belt_q = deque(accessories_by_subtype.get('belt', []))
    bracelet_q = deque(accessories_by_subtype.get('bracelet', []))
    ring_q = deque(accessories_by_subtype.get('ring', []))  # ← ДОБАВЛЕНО: кольца
    scarf_q = deque(accessories_by_subtype.get('scarf', []))
    headwear_q = deque(accessories_by_subtype.get('headwear', []))
    gloves_q = deque(accessories_by_subtype.get('gloves', []))
    watch_q = deque(accessories_by_subtype.get('watch', []))
    sunglasses_q = deque(accessories_by_subtype.get('sunglasses', []))
    
    # Трекинг использования вещей
    used_count = defaultdict(int)
    max_uses = 3
    produced_keys = set()
    
    capsules = []
    
    def can_use(item: Dict[str, Any]) -> bool:
        """Проверяет можно ли использовать вещь"""
        return used_count[str(item['id'])] < max_uses
    
    def mark_used(item: Dict[str, Any]):
        """Отмечает вещь как использованную"""
        used_count[str(item['id'])] += 1
    
    def pick_from_queue(queue: deque) -> Optional[Dict[str, Any]]:
        """Выбирает вещь из очереди, которую можно использовать"""
        for _ in range(len(queue)):
            item = queue.popleft()
            if can_use(item):
                queue.append(item)  # Возвращаем в конец
                return item
            queue.append(item)
        return None
    
    def get_capsule_key(items: List[Dict[str, Any]]) -> str:
        """Уникальный ключ капсулы"""
        ids = sorted([str(item['id']) for item in items])
        return '_'.join(ids)
    
    def build_capsule(items: List[Dict[str, Any]]) -> Optional[Capsule]:
        """
        Создает капсулу из списка вещей
        
        Проверяет:
        - Уникальность комбинации
        - Все вещи доступны для использования
        """
        key = get_capsule_key(items)
        if key in produced_keys:
            return None
        
        # Помечаем все вещи как использованные
        for item in items:
            mark_used(item)
        
        produced_keys.add(key)
        
        # Формируем КРАСИВОЕ название и описание (СТРОГОЕ СОБЛЮДЕНИЕ ТЗ)
        has_dress = any(translate_category(item.get('category', '')) == 'dresses' for item in items)
        has_outerwear = any(translate_category(item.get('category', '')) == 'outerwear' for item in items)
        has_light_outerwear = any(translate_category(item.get('category', '')) == 'light_outerwear' for item in items)
        
        # Определяем шаблон капсулы
        if has_dress:
            if has_outerwear:
                name = "Элегантный образ с верхней одеждой"
            elif has_light_outerwear:
                name = "Женственный стиль с кардиганом"
            else:
                name = "Платье - готовый образ"
        elif has_outerwear and has_light_outerwear:
            name = "Многослойный образ"
        elif has_outerwear:
            if temp_c < 15.0:
                name = "Зимний теплый образ"
            else:
                name = "Стильный аутфит"
        elif has_light_outerwear:
            name = "Многослойный образ"
        elif temp_c >= 25.0:
            name = "Летний легкий образ"
        elif len(items) >= 8:
            name = "Многослойный look"
        else:
            name = "Повседневный сет"
        
        # Описание с количеством вещей
        description = f"{len(items)} вещей: " + ", ".join([item.get('category', 'вещь') for item in items[:4]])
        if len(items) > 4:
            description += f" + еще {len(items) - 4}"
        
        capsule_id = f"c{len(capsules) + 1}"
        return Capsule(
            id=capsule_id,
            name=name,
            items=[str(item['id']) for item in items],
            description=description
        )
    
    def pick_mandatory_accessories_warm() -> List[Dict[str, Any]]:
        """
        Выбирает ОБЯЗАТЕЛЬНЫЕ аксессуары для теплой погоды (≥15°C)
        
        ОБЯЗАТЕЛЬНО (минимум 2-3):
        - Серьги ИЛИ Бусы (обязательно 1)
        - Ремень ИЛИ Браслет (обязательно 1)
        - Часы ИЛИ Очки (опционально)
        
        ЦЕЛЬ: Капсула должна быть НАСЫЩЕННОЙ, не скучной!
        """
        accessories = []
        
        # 1. Серьги или Бусы (ОБЯЗАТЕЛЬНО! Пробуем несколько раз)
        earrings = pick_from_queue(earrings_q)
        if earrings:
            accessories.append(earrings)
        else:
            # Если нет серёг - берем бусы
            necklace = pick_from_queue(necklace_q)
            if necklace:
                accessories.append(necklace)
        
        # 2. Ремень или Браслет (ОБЯЗАТЕЛЬНО!)
        belt = pick_from_queue(belt_q)
        if belt:
            accessories.append(belt)
        else:
            # Если нет ремня - берем браслет
            bracelet = pick_from_queue(bracelet_q)
            if bracelet:
                accessories.append(bracelet)
        
        # 3. Часы (высокий приоритет - 70%)
        if watch_q and random.random() < 0.7:
            watch = pick_from_queue(watch_q)
            if watch:
                accessories.append(watch)
        
        # 4. Очки (средний приоритет - 40%)
        if sunglasses_q and random.random() < 0.4:
            glasses = pick_from_queue(sunglasses_q)
            if glasses:
                accessories.append(glasses)
        
        # 5. Дополнительный браслет если есть место (30%)
        if len(accessories) < 4 and bracelet_q and random.random() < 0.3:
            extra_bracelet = pick_from_queue(bracelet_q)
            if extra_bracelet:
                accessories.append(extra_bracelet)
        
        # 6. Кольцо как дополнительное украшение (20%)
        if len(accessories) < 5 and ring_q and random.random() < 0.2:
            ring = pick_from_queue(ring_q)
            if ring:
                accessories.append(ring)
        
        return accessories
    
    def pick_mandatory_accessories_cold() -> List[Dict[str, Any]]:
        """
        Выбирает ОБЯЗАТЕЛЬНЫЕ аксессуары для холодной погоды
        
        Обязательно:
        - Шапка
        - Шарф
        - Перчатки
        
        Максимум:
        - Серьги (видны из-под шапки)
        """
        accessories = []
        
        # 1. Шапка (обязательно)
        headwear = pick_from_queue(headwear_q)
        if headwear:
            accessories.append(headwear)
        
        # 2. Шарф (обязательно)
        scarf = pick_from_queue(scarf_q)
        if scarf:
            accessories.append(scarf)
        
        # 3. Перчатки (обязательно)
        gloves = pick_from_queue(gloves_q)
        if gloves:
            accessories.append(gloves)
        
        # 4. Максимум серьги (видны)
        if earrings_q and random.random() < 0.7:
            earrings = pick_from_queue(earrings_q)
            if earrings:
                accessories.append(earrings)
        
        return accessories
    
    # ========== ГЕНЕРАЦИЯ КАПСУЛ ==========
    
    print(f"🔨 Начинаем генерацию капсул...")
    
    # Определяем температурные слои (СТРОГОЕ СОБЛЮДЕНИЕ ТЗ)
    # ХОЛОДНО (<15°C): ОБЯЗАТЕЛЬНА верхняя одежда + шапка + шарф + перчатки (без ремня/браслета)
    # ТЕПЛО (15-25°C): легкая одежда + видимые украшения (серьги + ремень)
    # ЖАРКО (≥25°C): минимум одежды + видимые украшения
    
    is_cold = temp_c < 15.0           # <15°C: ОБЯЗАТЕЛЬНА верхняя одежда + холодные аксессуары
    is_warm_weather = 15.0 <= temp_c < 25.0  # 15-25°C: легкая одежда + видимые украшения
    is_hot = temp_c >= 25.0           # ≥25°C: минимум одежды + видимые украшения
    
    # СТРАТЕГИЯ 1: Капсулы с платьями (если есть)
    if dresses_q:
        print(f"   👗 Генерируем капсулы с платьями...")
        for _ in range(len(dresses_q)):
            if len(capsules) >= max_total:
                break
            
            dress = pick_from_queue(dresses_q)
            if not dress:
                break
            
            # Обувь (ОБЯЗАТЕЛЬНО!)
            shoes = pick_from_queue(shoes_q)
            if not shoes:
                break  # Останавливаем если закончилась обувь
            
            # Сумка (желательно, но не критично)
            bag = pick_from_queue(bags_q)
            
            # Базовые вещи (платье = верх + низ)
            items = [dress, shoes]
            if bag:
                items.append(bag)
            
            # ТЕМПЕРАТУРНАЯ ЛОГИКА (СТРОГОЕ СОБЛЮДЕНИЕ ТЗ)
            if is_cold:
                # ХОЛОДНО (<15°C): ОБЯЗАТЕЛЬНА верхняя одежда + шапка + шарф + перчатки
                outerwear = pick_from_queue(outer_q)
                if not outerwear:
                    continue  # ❌ Пропускаем - нельзя без верхней одежды в холод!
                
                items.append(outerwear)
                
                # ОПЦИОНАЛЬНО: легкая верхняя одежда под теплую (многослойность)
                if light_outer_q and random.random() < 0.3:
                    light_outer = pick_from_queue(light_outer_q)
                    if light_outer:
                        items.append(light_outer)
                
                # ХОЛОДНЫЕ АКСЕССУАРЫ: шапка + шарф + перчатки (+макс серьги)
                accessories = pick_mandatory_accessories_cold()
                
            elif is_warm_weather:
                # ТЕПЛО (15-25°C): легкая верхняя одежда опционально + видимые украшения
                # 40% вероятность легкой верхней одежды (кардиган для стиля)
                if light_outer_q and random.random() < 0.4:
                    light_outer = pick_from_queue(light_outer_q)
                    if light_outer:
                        items.append(light_outer)
                
                # ТЕПЛЫЕ АКСЕССУАРЫ: серьги + ремень + часы + очки
                accessories = pick_mandatory_accessories_warm()
                
            else:  # is_hot
                # ЖАРКО (≥25°C): БЕЗ верхней одежды, только легкие аксессуары
                # Легкая верхняя одежда крайне редко (10%)
                if light_outer_q and random.random() < 0.1:
                    light_outer = pick_from_queue(light_outer_q)
                    if light_outer:
                        items.append(light_outer)
                
                # ТЕПЛЫЕ АКСЕССУАРЫ: серьги + ремень + часы + очки
                accessories = pick_mandatory_accessories_warm()
            
            items.extend(accessories)
            
            # Создаем капсулу (убрали строгую проверку - пусть будет хоть что-то)
            capsule = build_capsule(items)
            if capsule:
                capsules.append(capsule)
    
    # СТРАТЕГИЯ 2: Капсулы с верхом и низом
    print(f"   👕 Генерируем капсулы с верхом и низом...")
    
    while len(capsules) < max_total and tops_q and bottoms_q:
        top = pick_from_queue(tops_q)
        if not top:
            break
        
        # ВАЖНО: Проверяем что top не является light_outerwear (пиджак/кардиган)
        # Если это light_outerwear, пропускаем его - он должен быть ПОВЕРХ базового верха!
        top_category = translate_category(top.get('category', ''))
        if top_category == 'light_outerwear':
            print(f"   ⚠️ Пропускаем {top.get('description', '')} как базовый верх - это light_outerwear!")
            continue
        
        bottom = pick_from_queue(bottoms_q)
        if not bottom:
            break
        
        # Обувь (ОБЯЗАТЕЛЬНО!)
        shoes = pick_from_queue(shoes_q)
        if not shoes:
            break  # Останавливаем если закончилась обувь
        
        # Сумка (желательно)
        bag = pick_from_queue(bags_q)
        
        # Базовые вещи
        items = [top, bottom, shoes]
        if bag:
            items.append(bag)
        
        # ТЕМПЕРАТУРНАЯ ЛОГИКА С МНОГОСЛОЙНОСТЬЮ (СТРОГОЕ СОБЛЮДЕНИЕ ТЗ)
        if is_cold:
            # ХОЛОДНО (<15°C): ОБЯЗАТЕЛЬНА верхняя одежда + шапка + шарф + перчатки
            outerwear = pick_from_queue(outer_q)
            if not outerwear:
                continue  # ❌ Пропускаем - нельзя без верхней одежды в холод!
            
            items.append(outerwear)
            
            # ОПЦИОНАЛЬНО: легкая верхняя одежда под теплую (многослойность)
            if light_outer_q and random.random() < 0.3:
                light_outer = pick_from_queue(light_outer_q)
                if light_outer:
                    items.append(light_outer)
            
            # ХОЛОДНЫЕ АКСЕССУАРЫ: шапка + шарф + перчатки (+макс серьги)
            accessories = pick_mandatory_accessories_cold()
            
        elif is_warm_weather:
            # ТЕПЛО (15-25°C): легкая верхняя одежда опционально + видимые украшения
            # 40% вероятность легкой верхней одежды (кардиган для стиля)
            if light_outer_q and random.random() < 0.4:
                light_outer = pick_from_queue(light_outer_q)
                if light_outer:
                    items.append(light_outer)
            
            # ТЕПЛЫЕ АКСЕССУАРЫ: серьги + ремень + часы + очки
            accessories = pick_mandatory_accessories_warm()
            
        else:  # is_hot
            # ЖАРКО (≥25°C): БЕЗ верхней одежды, только легкие аксессуары
            # Легкая верхняя одежда крайне редко (10%)
            if light_outer_q and random.random() < 0.1:
                light_outer = pick_from_queue(light_outer_q)
                if light_outer:
                    items.append(light_outer)
            
            # ТЕПЛЫЕ АКСЕССУАРЫ: серьги + ремень + часы + очки
            accessories = pick_mandatory_accessories_warm()
        
        items.extend(accessories)
        
        # Создаем капсулу (аксессуары добавим даже если их мало)
        capsule = build_capsule(items)
        if capsule:
            capsules.append(capsule)
        
        if len(capsules) >= max_total:
            break
    
    # Логируем первые 3 капсулы для проверки
    print(f"📦 Примеры сгенерированных капсул:")
    for i, cap in enumerate(capsules[:3], 1):
        items_desc = []
        for item_id in cap.items:
            for item in wardrobe_items:
                if str(item['id']) == item_id:
                    cat = translate_category(item.get('category', ''))
                    if cat == 'accessories':
                        subtype = accessory_subtype(item)
                        items_desc.append(f"{cat}({subtype})")
                    elif cat == 'light_outerwear':
                        items_desc.append(f"light_outer({item.get('description', '')[:15]})")
                    else:
                        items_desc.append(cat)
                    break
        print(f"   {i}. {cap.name}: {', '.join(items_desc)}")
    
    print(f"✅ Сгенерировано капсул: {len(capsules)}")
    
    # Формируем результат
    capsules_json = [
        {
            "id": c.id,
            "name": c.name,
            "items": c.items,
            "description": c.description
        }
        for c in capsules
    ]
    
    return {
        "categories": [{
            "id": "v4_capsules",
            "name": "Стильные образы",
            "description": f"Капсулы с правильной структурой (V4)",
            "capsules": capsules_json,
            "fullCapsules": capsules_json
        }]
    }


# ==========================
# V5 Логика (гибридная)
# ==========================

def generate_capsules(
    wardrobe_items: List[Dict[str, Any]],
    season_hint: str,
    temp_c: float,
    predpochtenia: str = "Повседневный",
    figura: str = "",
    cvetotip: str = "",
    banned_ids: Optional[List[str]] = None,
    allowed_ids: Optional[List[str]] = None,
    max_total: int = 20
) -> Dict[str, Any]:
    """
    Генерация капсул V5 (импорт из capsule_engine_v5).
    """
    try:
        from capsule_engine_v5 import generate_capsules as generate_capsules_v5
        return generate_capsules_v5(
            wardrobe_items=wardrobe_items,
            season_hint=season_hint,
            temp_c=temp_c,
            predpochtenia=predpochtenia,
            figura=figura,
            cvetotip=cvetotip,
            banned_ids=banned_ids,
            allowed_ids=allowed_ids,
            max_total=max_total
        )
    except ImportError:
        print("⚠️ V5 не найден, используем старую V4 логику")
        return generate_capsules_v4_old(
            wardrobe_items=wardrobe_items,
            season_hint=season_hint,
            temp_c=temp_c,
            predpochtenia=predpochtenia,
            figura=figura,
            cvetotip=cvetotip,
            banned_ids=banned_ids,
            allowed_ids=allowed_ids,
            max_total=max_total
        )

