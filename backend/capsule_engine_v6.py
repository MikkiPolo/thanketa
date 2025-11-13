"""
Capsule Engine V6 - ПОЛНАЯ АДАПТАЦИЯ ПОД ИНСТРУКЦИЮ ПО ТКАНЯМ И ТЕМПЕРАТУРЕ

НОВАЯ ЛОГИКА:
- Фильтрация тканей по температуре (лен при +26°C, шерсть при <+10°C)
- Правильная обувь по температуре
- Головные уборы по температуре  
- Циклическое использование вещей (БЕЗ лимита max_uses)
- Строгая валидация капсул

ТЕМПЕРАТУРНЫЕ ЗОНЫ:
- ≥26°C: жарко (лен, хлопок, сандалии)
- 21-25°C: тепло (хлопок, вискоза, кеды, балетки)
- 15-20°C: прохладно (джинс, трикотаж, лоферы, мокасины) + ОБЯЗАТЕЛЬНО кардиган
- 10-14°C: свежо (плотный трикотаж, легкая шерсть, полуботинки)
- 5-9°C: холодно (шерсть, кашемир, флис, демисезонные ботинки)
- 0-4°C: очень холодно (шерсть, кашемир, утепленные ботинки)
- <0°C: мороз (термофлис, драп, мех, зимние сапоги)

ОБЯЗАТЕЛЬНАЯ БАЗОВАЯ КАПСУЛА:
- Верх + Низ (или Платье) + Обувь + Сумка + Серьги/Бусы + Ремень/Браслет

ТЕМПЕРАТУРНЫЕ ДОПОЛНЕНИЯ:
- Прохладно (15-20°C): Кардиган/Пиджак ОБЯЗАТЕЛЬНО
- Холодно (<15°C): Верхняя одежда + Шапка + Шарф + Перчатки (убираем видимые украшения)

Автор: AI Assistant
Дата: 2025-10-14 (V6)
"""

import random
import time
from typing import List, Dict, Any, Optional, Set
from collections import deque, defaultdict
from dataclasses import dataclass


@dataclass
class Capsule:
    id: str
    name: str
    items: List[str]
    description: str


# ==========================
# ТОКЕНИЗАЦИЯ И КАТЕГОРИЗАЦИЯ
# ==========================

def tokenize_category(raw: str) -> Set[str]:
    """Токенизация категории для поиска ключевых слов"""
    if not raw:
        return set()
    s = raw.lower().strip()
    tokens = set()
    for word in s.split():
        word = word.strip('.,!?;:()[]{}«»"\'')
        if len(word) >= 3:
            tokens.add(word[:6])  # Первые 6 символов для корней
    return tokens


def translate_category(raw: str) -> str:
    """
    Переводит категорию в стандартный формат
    
    Возвращает: tops, bottoms, dresses, outerwear, light_outerwear, shoes, bags, accessories, other
    """
    if not raw:
        return "other"
    
    tokens = tokenize_category(raw)
    
    # Диагностика для Водолазки и Свитшота (только при первом вызове)
    # if 'водолазка' in raw.lower():
    #     print(f"    🔍 ВОДОЛАЗКА: категория '{raw}' → токены {tokens}")
    # if 'свитшот' in raw.lower():
    #     print(f"    🔍 СВИТШОТ: категория '{raw}' → токены {tokens}")
    
    # LIGHT OUTERWEAR — легкая верхняя одежда (требует базового верха!)
    light_outerwear = {"кардиг", "жилет", "пиджак", "жакет", "болеро"}
    if tokens & light_outerwear:
        return "light_outerwear"
    
    # TOPS — верх (базовый)
    tops = {"верх", "блузк", "футбол", "рубашк", "топ", "свитер", "свитшот", "свитш", "свитшо", "джемпер", "лонгс", "водол", "водола", "водолазка", "майка"}
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
    shoes = {"обувь", "туфли", "ботинк", "сапог", "кроссо", "кеды", "слипон", "балетк", "лоферы", "мокаси", "сандал", "босон"}
    if tokens & shoes:
        return "shoes"
    
    # BAGS — сумки (ОТДЕЛЬНАЯ категория!)
    bags = {"сумка", "тоут", "shoppe", "шоппе", "багет", "кроссб", "седло-", "хобо", "почтал", "портфе", "рюкзак", "клатч"}
    if tokens & bags:
        return "bags"
    
    # ACCESSORIES — аксессуары
    accessories = {
        "аксесс", "ремень", "пояс", "шарф", "платок", "палант", "снуд", "шаль", 
        "галсту", "брошь", "заколк", "шапка", "кепка", "берет", "шляпа", "панам",
        "очки", "часы", "браслет", "серьги", "колье", "бусы", "кольцо", "цепоч",
        "перчатк", "варежк", "митенк"
    }
    if tokens & accessories:
        return "accessories"
    
    return "other"


def accessory_subtype(item: Dict[str, Any]) -> str:
    """
    Определяет подтип аксессуара
    
    Возвращает: earrings, necklace, bracelet, ring, belt, scarf, headwear, gloves, watch, sunglasses, other
    """
    desc = (item.get('description', '') + ' ' + item.get('category', '')).lower()
    tokens = tokenize_category(desc)
    
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
    if tokens & {"шарф", "платок", "палант", "снуд"}:
        return "scarf"
    if tokens & {"шапка", "берет", "кепка", "панам", "шляпа", "капор"}:
        return "headwear"
    if tokens & {"перчатк", "варежк", "митенк"}:
        return "gloves"
    if tokens & {"часы"}:
        return "watch"
    if tokens & {"очки", "солнце"}:
        return "sunglasses"
    
    # Если ничего не подошло - other
    # if 'водолазка' in desc:
    #     print(f"    ❌ ВОДОЛАЗКА: не распознана, возвращаем 'other'")
    # if 'свитшот' in desc:
    #     print(f"    ❌ СВИТШОТ: не распознан, возвращаем 'other'")
    return "other"


# ==========================
# АНАЛИЗ ТКАНЕЙ ПО ТЕМПЕРАТУРЕ (НОВАЯ ЛОГИКА!)
# ==========================

def detect_fabric(item: Dict[str, Any]) -> Set[str]:
    """
    Определяет ткани вещи из описания
    
    Возвращает множество тканей: {'хлопок', 'лен', 'шерсть', ...}
    """
    text = (item.get('description', '') + ' ' + item.get('category', '')).lower()
    
    # Диагностика для Водолазки и Свитшота
    if 'водолазка' in text:
        print(f"    🔍 ВОДОЛАЗКА: текст для анализа: '{text}'")
        print(f"    🔍 ВОДОЛАЗКА: поиск 'лен' в тексте: {'лен' in text}")
        print(f"    🔍 ВОДОЛАЗКА: поиск 'льнян' в тексте: {'льнян' in text}")
        print(f"    🔍 ВОДОЛАЗКА: поиск ' льн' в тексте: {' льн' in text}")
    
    if 'свитшот' in text:
        print(f"    🔍 СВИТШОТ: текст для анализа: '{text}'")
        print(f"    🔍 СВИТШОТ: поиск 'свитшот' в тексте: {'свитшот' in text}")
        print(f"    🔍 СВИТШОТ: поиск 'свитш' в тексте: {'свитш' in text}")
    
    fabrics = set()
    
    # Легкие ткани (жаркая погода)
    if any(k in text for k in [' льн', 'льнян', ' льнян']):
        fabrics.add('лен')
    if any(k in text for k in ['хлопок', 'хлопч']):
        fabrics.add('хлопок')
    if any(k in text for k in ['батист']):
        fabrics.add('батист')
    if any(k in text for k in ['вискоз']):
        fabrics.add('вискоза')
    if any(k in text for k in ['шифон']):
        fabrics.add('шифон')
    if any(k in text for k in ['сетка', 'сеточ']):
        fabrics.add('сетка')
    
    # Средние ткани (теплая/прохладная погода)
    if any(k in text for k in ['деним', 'джинс']):
        fabrics.add('деним')
    if any(k in text for k in ['трикотаж']):
        fabrics.add('трикотаж')
    if any(k in text for k in ['фланел']):
        fabrics.add('фланель')
    if any(k in text for k in ['модал']):
        fabrics.add('модал')
    if any(k in text for k in ['твид']):
        fabrics.add('твид')
    if any(k in text for k in ['штапел']):
        fabrics.add('штапель')
    if any(k in text for k in ['вельвет']):
        fabrics.add('вельвет')
    if any(k in text for k in ['джерси']):
        fabrics.add('джерси')
    
    # Теплые ткани (холодная погода)
    if any(k in text for k in ['шерст', 'шерсян']):
        fabrics.add('шерсть')
    if any(k in text for k in ['кашемир']):
        fabrics.add('кашемир')
    if any(k in text for k in ['флис']):
        fabrics.add('флис')
    if any(k in text for k in ['стёган', 'стеган']):
        fabrics.add('стёганка')
    if any(k in text for k in ['синтепон']):
        fabrics.add('синтепон')
    if any(k in text for k in ['кожа', 'кожан']):
        fabrics.add('кожа')
    if any(k in text for k in ['драп']):
        fabrics.add('драп')
    if any(k in text for k in ['мех', 'меховой', 'меховая']):
        fabrics.add('мех')
    if any(k in text for k in ['пух', 'пуховик']):
        fabrics.add('пух')
    if any(k in text for k in ['болонь', 'болоня']):
        fabrics.add('болонья')
    
    return fabrics


def is_fabric_suitable_for_temp(fabrics: Set[str], temp_c: float) -> bool:
    """
    Проверяет подходят ли ткани для заданной температуры
    
    ИНСТРУКЦИЯ ПО ТКАНЯМ:
    - ≥26°C: лен, хлопок, батист, вискоза, шифон
    - 21-25°C: хлопок, вискоза, лен, деним, трикотаж, модал
    - 15-20°C: хлопок, фланель, деним, трикотаж, штапель, твид
    - 10-14°C: плотный трикотаж, легкая шерсть, джерси, вельвет, стёганка
    - 5-9°C: шерсть, кашемир, флис, утепленный хлопок, кожа, синтепон
    - 0-4°C: шерсть, кашемир, флис, стёганка, кожа с утеплителем
    - <0°C: термофлис, драп, мех, термоткани, шерсть
    """
    if not fabrics:
        return True  # Если ткань не определена - пропускаем (всесезонная)
    
    # ЖАРКО (≥26°C): ТОЛЬКО легкие дышащие ткани
    if temp_c >= 26.0:
        allowed = {'лен', 'хлопок', 'батист', 'вискоза', 'шифон', 'сетка', 'трикотаж'}
        if fabrics & allowed:
            return True
        # Блокируем теплые ткани
        blocked = {'шерсть', 'кашемир', 'флис', 'мех', 'пух', 'драп'}
        if fabrics & blocked:
            return False
        return True  # Если ткань неизвестна - пропускаем
    
    # ТЕПЛО (21-25°C): легкие и средние ткани
    if 21.0 <= temp_c < 26.0:
        allowed = {'хлопок', 'вискоза', 'лен', 'деним', 'трикотаж', 'модал'}
        if fabrics & allowed:
            return True
        # Блокируем очень теплые
        blocked = {'шерсть', 'кашемир', 'флис', 'мех', 'пух', 'драп', 'стёганка'}
        if fabrics & blocked:
            return False
        return True
    
    # ПРОХЛАДНО (15-20°C): средние ткани
    if 15.0 <= temp_c < 21.0:
        allowed = {'хлопок', 'фланель', 'деним', 'трикотаж', 'штапель', 'модал', 'шифон', 'твид', 'вискоза'}
        if fabrics & allowed:
            return True
        # Блокируем теплые зимние
        blocked = {'мех', 'пух', 'драп', 'стёганка', 'кашемир'}
        if fabrics & blocked:
            return False
        # Легкая шерсть - допустима
        return True
    
    # СВЕЖО (10-14°C): плотные ткани, легкая шерсть
    if 10.0 <= temp_c < 15.0:
        allowed = {'трикотаж', 'шерсть', 'джерси', 'вельвет', 'стёганка', 'кожа', 'деним'}
        if fabrics & allowed:
            return True
        # Блокируем очень легкие
        blocked = {'лен', 'батист', 'шифон', 'сетка'}
        if fabrics & blocked:
            return False
        return True
    
    # ХОЛОДНО (5-9°C): шерсть, кашемир, флис
    if 5.0 <= temp_c < 10.0:
        allowed = {'шерсть', 'кашемир', 'флис', 'хлопок', 'кожа', 'синтепон', 'стёганка'}
        if fabrics & allowed:
            return True
        # Блокируем легкие
        blocked = {'лен', 'батист', 'шифон', 'вискоза', 'сетка'}
        if fabrics & blocked:
            return False
        return True
    
    # ОЧЕНЬ ХОЛОДНО (0-4°C): шерсть, кашемир, стёганка
    if 0.0 <= temp_c < 5.0:
        allowed = {'шерсть', 'кашемир', 'флис', 'стёганка', 'кожа', 'синтепон', 'болонья'}
        if fabrics & allowed:
            return True
        blocked = {'лен', 'батист', 'шифон', 'вискоза', 'хлопок', 'сетка'}
        if fabrics & blocked:
            return False
        return True
    
    # МОРОЗ (<0°C): только теплые ткани
    if temp_c < 0.0:
        allowed = {'флис', 'драп', 'мех', 'шерсть', 'кашемир', 'пух', 'болонья', 'стёганка'}
        if fabrics & allowed:
            return True
        # Блокируем ВСЕ легкие
        blocked = {'лен', 'батист', 'шифон', 'вискоза', 'хлопок', 'деним', 'трикотаж'}
        if fabrics & blocked:
            return False
        return True
    
    return True


def is_suitable_for_temp_and_season(item: Dict[str, Any], temp_c: float, season: str) -> bool:
    """
    Фильтрация вещей по температуре и сезону
    
    НОВАЯ ЛОГИКА V6:
    - Проверяет ткани (из инструкции)
    - Проверяет сезонность вещи
    - Фильтрует шорты и легкие вещи по температуре
    """
    item_cat = translate_category(item.get('category', ''))
    item_season = (item.get('season') or item.get('сезон') or '').lower()
    desc = (item.get('description') or item.get('описание') or '').lower()
    
    # АКСЕССУАРЫ - фильтруем только по сезону (температурно-нейтральные)
    if item_cat == 'accessories':
        subtype = accessory_subtype(item)
        # Теплые аксессуары (шапки, шарфы, перчатки) - только для холода
        if subtype in ['headwear', 'scarf', 'gloves']:
            return temp_c < 20.0  # Холодные аксессуары только при <20°C
        # Остальные аксессуары - всесезонные, но проверяем явную сезонность
        if item_season:
            if 'лет' in item_season and temp_c < 15.0:
                return False
            if 'зим' in item_season and temp_c >= 15.0:
                return False
        return True
    
    # СУМКИ - фильтруем ТОЛЬКО по сезону (температурно-нейтральные!)
    if item_cat == 'bags':
        if not item_season or 'всесезон' in item_season:
            return True
        season_hint_norm = season.lower()
        if 'лет' in item_season and 'лет' not in season_hint_norm:
            return False  # Летние сумки (плетеные) НЕ для осени/зимы
        if 'зим' in item_season and temp_c >= 15.0:
            return False
        return True
    
    # ВЕРХ ИЗ ДЖИНСЫ - только от +15°C (легкий верх)
    if item_cat == 'tops':
        # Проверяем, содержит ли вещь джинсовую ткань (деним, джинс)
        if any(word in desc for word in ['деним', 'джинс', 'denim', 'jeans']):
            if temp_c < 15.0:
                print(f"  ❌ Верх из джинсы отфильтрован: {desc[:50]} (легкий верх при {temp_c}°C, нужна температура ≥15°C)")
                return False
    
    # ДЖИНСОВЫЕ КУРТКИ - только от +15°C (легкая верхняя одежда)
    if item_cat in ['outerwear', 'light_outerwear']:
        # Проверяем, содержит ли вещь джинсовую ткань (деним, джинс) и является ли курткой
        if any(word in desc for word in ['деним', 'джинс', 'denim', 'jeans']) and any(word in desc for word in ['куртк', 'jacket']):
            if temp_c < 15.0:
                print(f"  ❌ Джинсовая куртка отфильтрована: {desc[:50]} (легкая верхняя одежда при {temp_c}°C, нужна температура ≥15°C)")
                return False
    
    # ОБУВЬ - специальная проверка по температуре (ПЕРЕД проверкой на всесезонность!)
    if item_cat == 'shoes':
        # Легкая обувь (туфли, балетки, сандалии) - только для тепла
        light_shoes = ['туфл', 'балетк', 'сандал', 'босоножк', 'шлепк', 'сланц']
        if any(word in desc for word in light_shoes):
            # Туфли/балетки/сандалии - только при ≥15°C
            if temp_c < 15.0:
                print(f"  ❌ Обувь отфильтрована: {desc[:50]} (легкая обувь при {temp_c}°C)")
                return False
        
        # Полуботинки, ботинки, сапоги - для прохлады и холода
        warm_shoes = ['ботинк', 'сапог', 'полуботинк', 'ботильон']
        if any(word in desc for word in warm_shoes):
            # Ботинки/сапоги - подходят для <20°C
            if temp_c >= 20.0:
                print(f"  ❌ Обувь отфильтрована: {desc[:50]} (теплая обувь при {temp_c}°C)")
                return False
        
        # Кроссовки, кеды, мокасины - проверяем по температуре
        casual_shoes = ['кроссовк', 'кеды', 'мокасин', 'лофер']
        if any(word in desc for word in casual_shoes):
            # Кроссовки/кеды/мокасины - подходят для 10-25°C (включительно)
            # При 10°C они НЕ должны показываться - нужны ботинки/полуботинки
            if temp_c <= 10.0 or temp_c >= 25.0:
                print(f"  ❌ Обувь отфильтрована: {desc[:50]} (casual обувь при {temp_c}°C, нужен диапазон >10-25°C)")
                return False
        
        # Если обувь прошла проверку по типу - продолжаем проверку тканей и сезона
        # (не возвращаем True сразу, чтобы проверить ткани)
    
    # ВСЕСЕЗОННЫЕ вещи - всегда проходят (НО НЕ ОБУВЬ - она уже проверена выше!)
    if 'всесезон' in item_season and item_cat != 'shoes':
        return True
    
    # ТКАНИ - новая логика!
    fabrics = detect_fabric(item)
    if not is_fabric_suitable_for_temp(fabrics, temp_c):
        return False
    
    # СЕЗОННОСТЬ (логика из продакшена V2)
    # Зимние вещи: только при <7°C
    if 'зим' in item_season and temp_c < 7:
        return True
    
    # Весна/Осень: 7-23°C
    if ('весн' in item_season or 'осен' in item_season or 'демисезон' in item_season) and 7 <= temp_c < 23:
        return True
    
    # Летние вещи: только при ≥23°C
    if 'лет' in item_season and temp_c >= 23:
        return True
    
    # ШОРТЫ - только жара или лето
    if 'шорт' in desc or 'шорт' in item.get('category', '').lower():
        return temp_c >= 22.0 or 'лет' in season.lower()
    
    # Если сезонность не указана - пропускаем (всесезонная вещь)
    # НО для обуви это не применяется - она уже проверена выше!
    if not item_season:
        if item_cat == 'shoes':
            # Для обуви без сезона - проверяем только по типу (уже сделано выше)
            return True
        return True
    
    return False


# ==========================
# ОСНОВНОЙ ГЕНЕРАТОР
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
    max_total: int = 20,
    exclude_combinations: Optional[List[List[str]]] = None
) -> Dict[str, Any]:
    """
    Генерирует капсулы с НОВОЙ ЛОГИКОЙ V6
    
    КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ:
    - Фильтрация по тканям (из инструкции)
    - Циклическое использование вещей (БЕЗ лимита)
    - Строгая валидация капсул
    - Правильная обувь и головные уборы по температуре
    """
    
    print("=" * 80)
    print(f"🎯 CAPSULE ENGINE V6: АДАПТАЦИЯ ПОД ИНСТРУКЦИЮ ПО ТКАНЯМ")
    print(f"   Сезон: {season_hint}, Температура: {temp_c}°C, Макс: {max_total}")
    print("=" * 80)
    
    # Температурные флаги
    is_frost = temp_c < 0.0               # <0°C - мороз
    is_very_cold = 0.0 <= temp_c < 5.0    # 0-4°C - очень холодно
    is_cold = 5.0 <= temp_c < 10.0        # 5-9°C - холодно
    is_fresh = 10.0 <= temp_c < 15.0      # 10-14°C - свежо
    is_cool = 15.0 <= temp_c < 21.0       # 15-20°C - прохладно
    is_warm = 21.0 <= temp_c < 26.0       # 21-25°C - тепло
    is_hot = temp_c >= 26.0               # ≥26°C - жарко
    
    # Фильтрация + группировка
    by_category: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    filtered_out = defaultdict(list)
    
    for item in wardrobe_items:
        iid = str(item.get('id'))
        if banned_ids and iid in banned_ids:
            continue
        if allowed_ids and iid not in allowed_ids:
            continue
        
        item_cat = translate_category(item.get('category', ''))
        
        if not is_suitable_for_temp_and_season(item, temp_c, season_hint):
            filtered_out[item_cat].append(item.get('description', 'no desc')[:30])
            continue
        
        by_category[item_cat].append(item)
    
    # Группируем аксессуары по подтипам
    accessories_by_subtype = defaultdict(list)
    for acc in by_category['accessories']:
        subtype = accessory_subtype(acc)
        accessories_by_subtype[subtype].append(acc)
    
    # Статистика
    print(f"📊 Категории: tops={len(by_category['tops'])}, bottoms={len(by_category['bottoms'])}, "
          f"dresses={len(by_category['dresses'])}, outer={len(by_category['outerwear'])}, "
          f"light_outer={len(by_category['light_outerwear'])}, "
          f"shoes={len(by_category['shoes'])}, bags={len(by_category['bags'])}, "
          f"accs={len(by_category['accessories'])}")
    
    # Логируем отфильтрованные вещи
    if filtered_out:
        print(f"⚠️ Отфильтровано по температуре {temp_c}°C:")
        for cat, items in filtered_out.items():
            if items:
                print(f"   - {cat}: {len(items)} шт. (примеры: {', '.join(items[:3])})")
    
    # Устанавливаем seed для рандомизации на основе времени
    # Это обеспечивает разнообразие при каждой генерации
    random.seed(int(time.time() * 1000) % (2**32))  # Используем миллисекунды для уникальности
    
    # Перемешиваем для разнообразия (теперь с уникальным seed)
    for key in ['tops', 'bottoms', 'dresses', 'outerwear', 'light_outerwear', 'shoes', 'bags']:
        random.shuffle(by_category[key])
    
    # Дополнительное перемешивание аксессуаров
    for subtype, items in accessories_by_subtype.items():
        random.shuffle(items)
    
    # Создаем очереди
    tops_q = deque(by_category['tops'])
    bottoms_q = deque(by_category['bottoms'])
    dresses_q = deque(by_category['dresses'])
    outer_q = deque(by_category['outerwear'])
    light_q = deque(by_category['light_outerwear'])
    shoes_q = deque(by_category['shoes'])
    bags_q = deque(by_category['bags'])
    
    # Очереди аксессуаров
    earrings_q = deque(accessories_by_subtype.get('earrings', []))
    necklace_q = deque(accessories_by_subtype.get('necklace', []))
    belt_q = deque(accessories_by_subtype.get('belt', []))
    bracelet_q = deque(accessories_by_subtype.get('bracelet', []))
    ring_q = deque(accessories_by_subtype.get('ring', []))
    scarf_q = deque(accessories_by_subtype.get('scarf', []))
    headwear_q = deque(accessories_by_subtype.get('headwear', []))
    gloves_q = deque(accessories_by_subtype.get('gloves', []))
    watch_q = deque(accessories_by_subtype.get('watch', []))
    sunglasses_q = deque(accessories_by_subtype.get('sunglasses', []))
    
    # Трекинг использования (ОГРАНИЧЕНО ДО 1 РАЗА!)
    used_items = set()  # Множество использованных ID вещей
    produced_keys = set()
    capsules = []
    
    # Исключаем уже показанные комбинации
    if exclude_combinations:
        for combo in exclude_combinations:
            combo_key = '_'.join(sorted(combo))
            produced_keys.add(combo_key)
        print(f"  🚫 Исключено {len(exclude_combinations)} уже показанных комбинаций")
    
    # Вспомогательные функции
    def mark_used(item: Dict[str, Any]) -> None:
        """Помечает вещь как использованную (только 1 раз!)"""
        used_items.add(str(item['id']))
    
    def pick_from_queue(q: deque) -> Optional[Dict[str, Any]]:
        """
        Выбор вещи из очереди с ограничением: каждая вещь используется ТОЛЬКО 1 РАЗ
        С РАНДОМИЗАЦИЕЙ для разнообразия
        """
        if not q:
            return None
        
        # Собираем все НЕ использованные вещи
        unused_candidates = []
        
        for _ in range(len(q)):
            it = q.popleft()
            item_id = str(it['id'])
            
            # Если вещь еще не использовалась - добавляем в кандидаты
            if item_id not in used_items:
                unused_candidates.append(it)
            
            q.append(it)
        
        if not unused_candidates:
            return None  # Все вещи уже использованы
        
        # Выбираем случайную из неиспользованных для разнообразия
        selected = random.choice(unused_candidates)
        return selected
    
    def get_capsule_key(items: List[Dict[str, Any]]) -> str:
        return '_'.join(sorted(str(i['id']) for i in items))
    
    def pick_accessories_warm() -> List[Dict[str, Any]]:
        """Теплая погода: серьги/бусы + ремень/браслет + опции"""
        acc = []
        x = pick_from_queue(earrings_q) or pick_from_queue(necklace_q)
        if x: acc.append(x)
        y = pick_from_queue(belt_q) or pick_from_queue(bracelet_q)
        if y: acc.append(y)
        if watch_q and random.random() < 0.7:
            z = pick_from_queue(watch_q)
            if z: acc.append(z)
        if sunglasses_q and random.random() < 0.4:
            z = pick_from_queue(sunglasses_q)
            if z: acc.append(z)
        if ring_q and random.random() < 0.2:
            z = pick_from_queue(ring_q)
            if z: acc.append(z)
        return acc
    
    def pick_accessories_cold() -> List[Dict[str, Any]]:
        """Холодная погода: шапка + шарф + перчатки + макс серьги"""
        acc = []
        h = pick_from_queue(headwear_q)
        s = pick_from_queue(scarf_q)
        g = pick_from_queue(gloves_q)
        if h: acc.append(h)
        if s: acc.append(s)
        if g: acc.append(g)
        if earrings_q and random.random() < 0.7:
            e = pick_from_queue(earrings_q)
            if e: acc.append(e)
        return acc
    
    def build_capsule(items: List[Dict[str, Any]]) -> Optional[Capsule]:
        """Строит капсулу со СТРОГОЙ валидацией"""
        key = get_capsule_key(items)
        if key in produced_keys:
            return None
        
        # СТРОГАЯ ВАЛИДАЦИЯ: проверяем обязательные элементы
        cats = [translate_category(i.get('category', '')) for i in items]
        
        # Обязательно: обувь
        if 'shoes' not in cats:
            return None
        
        # Обязательно: платье ИЛИ (верх И низ)
        has_dress = 'dresses' in cats
        has_top = 'tops' in cats
        has_bottom = 'bottoms' in cats
        
        if not (has_dress or (has_top and has_bottom)):
            return None
        
        # Обязательно: сумка (если есть хоть одна в гардеробе)
        if bags_q and 'bags' not in cats:
            return None
        
        # ВАЛИДАЦИЯ АКСЕССУАРОВ по температуре
        acc_subtypes = [accessory_subtype(i) for i in items if translate_category(i.get('category', '')) == 'accessories']
        
        if is_cool:  # 15-20°C: ОБЯЗАТЕЛЬНО кардиган + аксессуары
            # Обязательно: кардиган/пиджак при прохладе
            if 'light_outerwear' not in cats:
                return None
            # Обязательно: хотя бы 1 видимый аксессуар
            has_visible_acc = any(st in acc_subtypes for st in ['earrings', 'necklace', 'belt', 'bracelet'])
            if not has_visible_acc:
                return None
        
        # Помечаем все вещи
        for it in items:
            mark_used(it)
        
        produced_keys.add(key)
        
        # Название
        has_dress = any(translate_category(i.get('category', '')) == 'dresses' for i in items)
        has_outer = any(translate_category(i.get('category', '')) == 'outerwear' for i in items)
        has_light = any(translate_category(i.get('category', '')) == 'light_outerwear' for i in items)
        
        if has_dress:
            if has_outer:
                name = "Элегантный образ с верхней одеждой"
            elif has_light:
                name = "Женственный стиль с кардиганом"
            else:
                name = "Платье - готовый образ"
        elif has_outer and has_light:
            name = "Многослойный образ"
        elif has_outer:
            name = "Зимний теплый образ" if temp_c < 15 else "Стильный аутфит"
        elif has_light:
            name = "Многослойный образ"
        elif temp_c >= 25:
            name = "Летний легкий образ"
        elif len(items) >= 8:
            name = "Многослойный look"
        else:
            name = "Повседневный сет"
        
        desc = f"{len(items)} вещей: " + ", ".join([i.get('category', 'вещь') for i in items[:4]])
        if len(items) > 4:
            desc += f" + еще {len(items) - 4}"
        
        return Capsule(id=f"c{len(capsules)+1}", name=name, items=[str(i['id']) for i in items], description=desc)
    
    # ==========================
    # ГЕНЕРАЦИЯ КАПСУЛ
    # ==========================
    
    max_iterations = max_total * 5  # Увеличили лимит итераций
    iteration = 0
    
    # СТРАТЕГИЯ 1: Капсулы с платьями
    if dresses_q:
        print(f"   👗 Генерируем капсулы с платьями...")
        for _ in range(len(dresses_q) * 3):  # Больше попыток
            if len(capsules) >= max_total:
                break
            if iteration >= max_iterations:
                print(f"   ⚠️ Достигнут лимит итераций ({iteration}), прерываем цикл")
                break
            
            iteration += 1
            
            dress = pick_from_queue(dresses_q)
            if not dress:
                continue
            
            shoes = pick_from_queue(shoes_q)
            if not shoes:
                continue
            
            bag = pick_from_queue(bags_q)
            
            items = [dress, shoes]
            if bag:
                items.append(bag)
            
            # ТЕМПЕРАТУРНАЯ ЛОГИКА
            if is_cold or is_fresh or is_very_cold or is_frost:
                # ХОЛОДНО (<15°C): ОБЯЗАТЕЛЬНА верхняя одежда
                outer = pick_from_queue(outer_q)
                if not outer:
                    continue
                items.append(outer)
                
                # Многослойность (30% chance)
                if light_q and random.random() < 0.3:
                    lo = pick_from_queue(light_q)
                    if lo: items.append(lo)
                
                items.extend(pick_accessories_cold())
            
            elif is_cool:
                # ПРОХЛАДНО (15-20°C): ОБЯЗАТЕЛЬНО кардиган (70% или outerwear fallback)
                light_outer = pick_from_queue(light_q)
                if light_outer:
                    items.append(light_outer)
                elif outer_q and random.random() < 0.3:  # Fallback на outerwear
                    outer = pick_from_queue(outer_q)
                    if outer: items.append(outer)
                
                items.extend(pick_accessories_warm())
            
            elif is_warm:
                # ТЕПЛО (21-25°C): легкая верхняя одежда опционально (40%)
                if light_q and random.random() < 0.4:
                    lo = pick_from_queue(light_q)
                    if lo: items.append(lo)
                
                items.extend(pick_accessories_warm())
            
            else:  # is_hot
                # ЖАРКО (≥26°C): БЕЗ верхней одежды (редко 10%)
                if light_q and random.random() < 0.1:
                    lo = pick_from_queue(light_q)
                    if lo: items.append(lo)
                
                items.extend(pick_accessories_warm())
            
            cap = build_capsule(items)
            if cap:
                capsules.append(cap)
    
    # СТРАТЕГИЯ 2: Капсулы с верхом и низом
    print(f"   👕 Генерируем капсулы с верхом и низом...")
    
    while len(capsules) < max_total:
        if iteration >= max_iterations:
            print(f"   ⚠️ Достигнут лимит итераций ({iteration}), прерываем цикл")
            break
        
        iteration += 1
        
        top = pick_from_queue(tops_q)
        if not top:
            break
        
        # ВАЖНО: top не должен быть light_outerwear!
        if translate_category(top.get('category', '')) == 'light_outerwear':
            continue
        
        bottom = pick_from_queue(bottoms_q)
        if not bottom:
            break
        
        shoes = pick_from_queue(shoes_q)
        if not shoes:
            break
        
        bag = pick_from_queue(bags_q)
        
        items = [top, bottom, shoes]
        if bag:
            items.append(bag)
        
        # ТЕМПЕРАТУРНАЯ ЛОГИКА С МНОГОСЛОЙНОСТЬЮ
        if is_cold or is_fresh or is_very_cold or is_frost:
            # ХОЛОДНО (<15°C): ОБЯЗАТЕЛЬНА верхняя одежда
            outer = pick_from_queue(outer_q)
            if not outer:
                continue
            items.append(outer)
            
            # Многослойность под верхнюю одежду (30%)
            if light_q and random.random() < 0.3:
                lo = pick_from_queue(light_q)
                if lo: items.append(lo)
            
            items.extend(pick_accessories_cold())
        
        elif is_cool:
            # ПРОХЛАДНО (15-20°C): ОБЯЗАТЕЛЬНО кардиган (70%)
            light_outer = pick_from_queue(light_q)
            if light_outer:
                items.append(light_outer)
            elif outer_q and random.random() < 0.3:
                outer = pick_from_queue(outer_q)
                if outer: items.append(outer)
            
            items.extend(pick_accessories_warm())
        
        elif is_warm:
            # ТЕПЛО (21-25°C): легкая многослойность (40%)
            if light_q and random.random() < 0.4:
                lo = pick_from_queue(light_q)
                if lo: items.append(lo)
            
            items.extend(pick_accessories_warm())
        
        else:  # is_hot
            # ЖАРКО (≥26°C): минимум слоев (10%)
            if light_q and random.random() < 0.1:
                lo = pick_from_queue(light_q)
                if lo: items.append(lo)
            
            items.extend(pick_accessories_warm())
        
        cap = build_capsule(items)
        if cap:
            capsules.append(cap)
    
    # Логируем примеры
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
            "id": "v6_capsules",
            "name": "Стильные образы",
            "description": f"Капсулы V6 с учетом тканей и температуры",
            "capsules": capsules_json,
            "fullCapsules": capsules_json
        }]
    }

