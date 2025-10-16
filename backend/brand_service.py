"""
Сервис для работы с товарами брендов через прямое подключение к Supabase
"""

from typing import List, Dict, Any, Optional
import random
import os
from collections import defaultdict
from supabase import create_client, Client


def get_supabase_client() -> Optional[Client]:
    """Получить клиент Supabase"""
    try:
        url = os.getenv('VITE_SUPABASE_URL') or os.getenv('SUPABASE_URL')
        key = os.getenv('VITE_SUPABASE_ANON_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            print("⚠️ Supabase credentials not found in environment")
            return None
            
        return create_client(url, key)
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")
        return None


def get_all_brand_items() -> List[Dict[str, Any]]:
    """
    Получить ВСЕ товары брендов ОДИН РАЗ (для последующей фильтрации)
    
    Returns:
        Список ВСЕХ активных товаров брендов
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # Запрашиваем ВСЕ товары (без фильтров по категории/сезону)
        response = supabase.table('brand_items') \
            .select('id, brand_id, category, season, description, image_id, shop_link, price, currency') \
            .eq('is_approved', True) \
            .eq('is_active', True) \
            .execute()
        
        items = response.data if response.data else []
        
        # Конструируем image_url для каждого товара
        for item in items:
            if item.get('image_id') and item.get('brand_id'):
                # ПРАВИЛЬНАЯ структура: /brand_id/image_id.jpg
                item['image_url'] = f"https://lipolo.store/storage/v1/object/public/brand-items-images/{item['brand_id']}/{item['image_id']}.jpg"
            else:
                item['image_url'] = None
            item['is_brand_item'] = True
            item['brand_name'] = 'LiMango'
        
        print(f"✅ Загружено {len(items)} товаров брендов")
        
        # Логируем несколько примеров для отладки
        for i, item in enumerate(items[:3]):
            print(f"  📦 Пример {i+1}: {item.get('description', 'Без описания')[:50]}...")
            print(f"      image_url: {item.get('image_url', 'НЕТ')}")
            print(f"      image_id: {item.get('image_id', 'НЕТ')}")
            print(f"      is_brand_item: {item.get('is_brand_item', 'НЕТ')}")
        
        return items
    
    except Exception as e:
        print(f"❌ Ошибка загрузки товаров брендов: {e}")
        import traceback
        traceback.print_exc()
        return []


def mix_brand_items_v2(
    user_capsules: List[Dict[str, Any]],
    wardrobe: List[Dict[str, Any]],
    season: str,
    temperature: float = 20.0,
    mixing_percentage: float = 0.35
) -> List[Dict[str, Any]]:
    """
    НОВАЯ ЛОГИКА (V2): Подмешивает товары брендов в капсулы
    
    АЛГОРИТМ:
    1. Получить ВСЕ товары брендов ОДИН РАЗ
    2. Отфильтровать их ПО ТОЙ ЖЕ ЛОГИКЕ что и вещи пользователя (температура + сезон + ткани)
    3. Для каждой капсулы:
       - Анализировать ЧТО в ней есть (какие категории)
       - Выбрать категорию для замены
       - Найти вещь ЭТОЙ категории в капсуле
       - Заменить её на товар бренда ЭТОЙ ЖЕ категории
    
    Args:
        user_capsules: Список капсул пользователя
        wardrobe: Гардероб пользователя (для определения категорий вещей)
        season: Текущий сезон
        temperature: Температура
        mixing_percentage: Процент капсул для подмешивания (0.35 = 7 из 20)
    
    Returns:
        Капсулы с подмешанными товарами брендов
    """
    if not user_capsules:
        return user_capsules
    
    # 1. Получаем ВСЕ товары брендов ОДИН РАЗ
    all_brand_items = get_all_brand_items()
    if not all_brand_items:
        print("  ⚠️ Нет товаров брендов для подмешивания")
        return user_capsules
    
    # 2. Фильтруем товары брендов ПО ТОЙ ЖЕ ЛОГИКЕ что и вещи пользователя
    try:
        from capsule_engine_v6 import is_suitable_for_temp_and_season, translate_category, accessory_subtype
    except ImportError:
        print("  ⚠️ capsule_engine_v6 не найден, используем базовую фильтрацию")
        from capsule_engine_v4 import is_suitable_for_temp_and_season, translate_category, accessory_subtype
    
    filtered_brand_items = []
    for item in all_brand_items:
        if is_suitable_for_temp_and_season(item, temperature, season):
            filtered_brand_items.append(item)
    
    print(f"  ✅ Отфильтровано {len(filtered_brand_items)} из {len(all_brand_items)} товаров брендов (температура: {temperature}°C, сезон: {season})")
    
    if not filtered_brand_items:
        print("  ⚠️ После фильтрации не осталось товаров брендов")
        return user_capsules
    
    # 3. Группируем товары брендов по категориям
    brand_by_category = defaultdict(list)
    for item in filtered_brand_items:
        cat = translate_category(item.get('category', ''))
        if cat == 'accessories':
            subtype = accessory_subtype(item)
            brand_by_category[f'acc_{subtype}'].append(item)
        else:
            brand_by_category[cat].append(item)
    
    print(f"  📦 Товары брендов по категориям:")
    for cat, items in brand_by_category.items():
        if items:
            print(f"     - {cat}: {len(items)} шт.")
    
    # 4. Подмешиваем в случайные капсулы
    total_to_mix = max(7, int(len(user_capsules) * mixing_percentage))
    capsules_to_mix = random.sample(
        range(len(user_capsules)), 
        min(total_to_mix, len(user_capsules))
    )
    
    mixed_count = 0
    mixed_categories = set()
    
    # Создаем словарь для быстрого поиска вещей по ID
    wardrobe_dict = {str(item['id']): item for item in wardrobe}
    
    for idx in capsules_to_mix:
        capsule = user_capsules[idx]
        
        # Анализируем состав капсулы
        capsule_items = capsule.get('items', [])
        if not capsule_items:
            continue
        
        # АНАЛИЗИРУЕМ КАТЕГОРИИ вещей в капсуле
        item_categories = {}  # {index: (item_id, category)}
        
        for i, item_id in enumerate(capsule_items):
            # Пропускаем товары брендов (уже объекты)
            if isinstance(item_id, dict):
                continue
            
            # Находим вещь в гардеробе и определяем её категорию
            user_item = wardrobe_dict.get(str(item_id))
            if not user_item:
                continue
            
            item_cat = translate_category(user_item.get('category', ''))
            if item_cat == 'accessories':
                # Для аксессуаров - определяем подтип
                subtype = accessory_subtype(user_item)
                item_categories[i] = (item_id, f'acc_{subtype}')
            else:
                item_categories[i] = (item_id, item_cat)
        
        # Выбираем категорию для замены (приоритет: accessories > bags > shoes > tops > bottoms)
        priority_order = ['acc_belt', 'acc_bracelet', 'acc_necklace', 'acc_earrings', 'acc_sunglasses', 
                         'bags', 'shoes', 'tops', 'bottoms', 'outerwear']
        
        replaced = False
        
        for priority_cat in priority_order:
            # Проверяем есть ли товары бренда этой категории
            if priority_cat not in brand_by_category or not brand_by_category[priority_cat]:
                continue
            
            # Ищем вещь ЭТОЙ категории в капсуле
            for idx_in_capsule, (item_id, item_cat) in item_categories.items():
                if item_cat == priority_cat:
                    # НАШЛИ! Заменяем на товар бренда
                    brand_item = random.choice(brand_by_category[priority_cat])
                    capsule['items'][idx_in_capsule] = brand_item
                    replaced = True
                    mixed_count += 1
                    mixed_categories.add(priority_cat)
                    print(f"  ✅ Капсула {capsule.get('id')}: заменили {priority_cat} на товар бренда {brand_item.get('brand_name')}")
                    print(f"      🖼️ image_url: {brand_item.get('image_url', 'НЕТ')}")
                    print(f"      🏷️ description: {brand_item.get('description', 'НЕТ')[:50]}...")
                    break  # Одна замена на капсулу
            
            if replaced:
                break  # Переходим к следующей капсуле
    
    print(f"  📊 Подмешано {mixed_count} товаров из {len(mixed_categories)} разных категорий: {', '.join(sorted(mixed_categories))}")
    return user_capsules


def get_brand_items_for_mixing(
    category: str,
    season: str,
    temperature: float = 20.0,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    DEPRECATED: Используй get_all_brand_items() + фильтрацию
    
    Получить товары брендов для подмешивания в капсулы
    
    Args:
        category: Категория (light_tops, warm_tops, bottoms, shoes, bags, accessories, outerwear)
        season: Сезон (Лето, Зима, Весна, Осень)
        temperature: Температура (для будущей логики)
        limit: Максимальное количество товаров
    
    Returns:
        Список товаров брендов
    """
    
    # Маппинг внутренних категорий на категории в brand_items
    category_mapping = {
        'light_tops': 'Верх',
        'warm_tops': 'Верх',
        'tops': 'Верх',
        'bottoms': 'Низ',
        'shoes': 'Обувь',
        'bags': 'Сумка',
        'accessories': 'Аксессуары',
        'outerwear': 'Верхняя одежда',
        'dresses': 'Платье'
    }
    
    db_category = category_mapping.get(category, 'Верх')
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # Определяем подходящие сезоны для текущего сезона
        season_filters = []
        if season == 'Весна':
            season_filters = ['Весна', 'Демисезон', 'Всесезонный']
        elif season == 'Осень':
            season_filters = ['Осень', 'Демисезон', 'Всесезонный']
        elif season == 'Лето':
            season_filters = ['Лето', 'Всесезонный']
        elif season == 'Зима':
            season_filters = ['Зима', 'Всесезонный']
        else:
            season_filters = ['Всесезонный']
        
        # Формируем OR условие для всех подходящих сезонов
        season_condition = ','.join([f'season.eq.{s}' for s in season_filters])
        
        query = supabase.table('brand_items').select(
            'id, brand_id, category, season, description, image_id, shop_link, price, currency'
        ).eq('is_approved', True).eq('is_active', True).eq('category', db_category).or_(season_condition)
        
        response = query.limit(limit * 3).execute()
        
        if not response.data:
            return []
        
        # Случайная выборка
        items_data = response.data
        
        # ТЕМПЕРАТУРНАЯ ФИЛЬТРАЦИЯ: убираем теплые ткани при высокой температуре
        filtered_items = []
        warm_materials = ['шерст', 'кашемир', 'флис', 'вельвет', 'твид', 'пух', 'мех']
        light_materials = ['хлопок', 'лён', 'лен', 'вискоз', 'шёлк', 'шелк', 'сатин']
        
        for item in items_data:
            desc_lower = item.get('description', '').lower()
            
            # Проверка для ВЕРХНЕЙ ОДЕЖДЫ
            if db_category == 'Верхняя одежда':
                if temperature >= 18.0:
                    # ТЕПЛО (18-22°C) или ЖАРКО (>22°C) - ТОЛЬКО легкая верхняя одежда!
                    # Блокируем: шерстяное пальто, пуховики, зимние куртки
                    if any(warm_mat in desc_lower for warm_mat in warm_materials):
                        print(f"  ⛔ Фильтрация: {item.get('description')} (теплая ткань при {temperature}°C)")
                        continue
                    if any(word in desc_lower for word in ['зим', 'тепл', 'утепл']):
                        print(f"  ⛔ Фильтрация: {item.get('description')} (зимняя одежда при {temperature}°C)")
                        continue
                    # Пропускаем только легкие: ветровки, легкие куртки, жакеты
                    if not any(word in desc_lower for word in ['ветров', 'легк', 'жакет', 'кардиг', 'пиджак']):
                        print(f"  ⛔ Фильтрация: {item.get('description')} (не легкая верхняя одежда при {temperature}°C)")
                        continue
                elif temperature < 10.0:
                    # ХОЛОДНО (<10°C) - ТОЛЬКО теплая верхняя одежда!
                    if not any(warm_mat in desc_lower for warm_mat in warm_materials):
                        if not any(word in desc_lower for word in ['зим', 'тепл', 'утепл', 'пух']):
                            print(f"  ⛔ Фильтрация: {item.get('description')} (легкая одежда при {temperature}°C)")
                            continue
            
            # Проверка для ВЕРХА
            elif db_category == 'Верх':
                if temperature >= 22.0:
                    # ЖАРКО - только легкие ткани
                    if any(warm_mat in desc_lower for warm_mat in ['шерст', 'кашемир', 'флис']):
                        print(f"  ⛔ Фильтрация: {item.get('description')} (теплая ткань при {temperature}°C)")
                        continue
                elif temperature < 10.0:
                    # ХОЛОДНО - теплые ткани приоритетны
                    pass  # Не фильтруем
            
            filtered_items.append(item)
        
        # Если после фильтрации ничего не осталось - возвращаем как есть (лучше что-то, чем ничего)
        if not filtered_items:
            print(f"  ⚠️ Все товары отфильтрованы, возвращаем исходные")
            filtered_items = items_data
        
        # Случайная выборка из отфильтрованных
        if len(filtered_items) > limit:
            filtered_items = random.sample(filtered_items, limit)
        
        # Формируем результат
        result = []
        for item in filtered_items:
            # Формируем URL изображения
            image_path = f"{item['brand_id']}/{item['image_id']}.jpg"
            image_url = f"https://lipolo.store/storage/v1/object/public/brand-items-images/{image_path}"
            
            # Используем brand_id как название (можно улучшить позже с реальным справочником брендов)
            brand_name = 'LiMango'  # Захардкожено, так как у нас один бренд
            
            result.append({
                'id': item['id'],
                'brand_id': item['brand_id'],
                'brand_name': brand_name,
                'category': item['category'],
                'season': item['season'],
                'description': item['description'],
                'image_url': image_url,
                'shop_link': item['shop_link'],
                'price': item.get('price'),
                'currency': item.get('currency', 'RUB'),
                'is_brand_item': True
            })
        
        print(f"  ✅ Получено {len(result)} товаров брендов (категория: {db_category}, сезон: {season})")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка получения товаров брендов: {e}")
        return []


def fill_missing_items_with_brands(
    user_capsules: List[Dict[str, Any]],
    wardrobe: List[Dict[str, Any]],
    season: str,
    temperature: float = 20.0
) -> List[Dict[str, Any]]:
    """
    Дополняет капсулы недостающими обязательными вещами из товаров брендов
    
    ВАЖНО: Проверяет КАЖДУЮ капсулу индивидуально, а не весь гардероб!
    
    Обязательные категории:
    - bags (сумка) - только если у пользователя НЕТ сумок вообще
    - earrings + belt (для теплой погоды) - только если НЕТ в гардеробе
    - scarf + headwear + gloves (для холодной погоды) - только если НЕТ в гардеробе
    """
    from capsule_engine_v2 import translate_category, accessory_subtype
    
    # Проверяем какие категории есть в гардеробе пользователя ВООБЩЕ
    wardrobe_has = {}
    for item in wardrobe:
        cat = translate_category(item.get('category', ''))
        if cat == 'accessories':
            subtype = accessory_subtype(item)
            wardrobe_has[f'acc_{subtype}'] = True
        elif cat == 'bags':
            wardrobe_has['bags'] = True
        else:
            wardrobe_has[cat] = True
    
    # Определяем какие категории ВООБЩЕ отсутствуют в гардеробе (только эти дополняем!)
    globally_missing = []
    
    # Сумки - проверяем по категории (сумки в accessories, но проверяем по имени)
    has_bags = any('сумка' in item.get('category', '').lower() for item in wardrobe)
    print(f"  🔍 Проверка сумок: has_bags={has_bags}, всего вещей={len(wardrobe)}")
    if not has_bags:
        globally_missing.append('bags')
    
    if temperature >= 15.0:
        # Теплая погода: серьги и ремень (только если совсем нет в гардеробе)
        if not wardrobe_has.get('acc_earrings'):
            globally_missing.append('earrings')
        if not wardrobe_has.get('acc_belt'):
            globally_missing.append('belt')
    else:
        # Холодная погода: шарф, шапка, перчатки (только если совсем нет)
        if not wardrobe_has.get('acc_scarf'):
            globally_missing.append('scarf')
        if not wardrobe_has.get('acc_headwear'):
            globally_missing.append('headwear')
        if not wardrobe_has.get('acc_gloves'):
            globally_missing.append('gloves')
    
    # Если ничего не отсутствует - возвращаем капсулы как есть
    if not globally_missing:
        print(f"  ℹ️ В гардеробе есть все обязательные категории, пропускаем fill_missing")
        return user_capsules
    
    print(f"  ➕ Дополняем недостающие категории: {', '.join(globally_missing)}")
    
    # Загружаем товары брендов только для отсутствующих категорий
    missing_items = {}
    for missing_cat in globally_missing:
        if missing_cat == 'bags':
            missing_items['bags'] = get_brand_items_for_mixing('bags', season, temperature, 3)
        elif missing_cat in ['earrings', 'belt', 'scarf', 'headwear', 'gloves']:
            items = get_brand_items_for_mixing('accessories', season, temperature, 3)
            # Фильтруем по типу
            if missing_cat == 'earrings':
                missing_items[missing_cat] = [it for it in items if 'серьги' in it.get('description', '').lower() or 'бусы' in it.get('description', '').lower()]
            elif missing_cat == 'belt':
                missing_items[missing_cat] = [it for it in items if 'ремень' in it.get('description', '').lower() or 'пояс' in it.get('description', '').lower()]
            elif missing_cat == 'scarf':
                missing_items[missing_cat] = [it for it in items if 'шарф' in it.get('description', '').lower()]
            elif missing_cat == 'headwear':
                missing_items[missing_cat] = [it for it in items if 'шапк' in it.get('description', '').lower()]
            elif missing_cat == 'gloves':
                missing_items[missing_cat] = [it for it in items if 'перчатк' in it.get('description', '').lower() or 'варежк' in it.get('description', '').lower()]
    
    # Дополняем ВСЕ капсулы недостающими товарами брендов
    filled_capsules = []
    for capsule in user_capsules:
        items_list = list(capsule.get('items', []))
        
        # Добавляем недостающие товары
        for category, brand_items_list in missing_items.items():
            if brand_items_list and len(brand_items_list) > 0:
                brand_item = random.choice(brand_items_list)
                # Создаем полный объект товара бренда
                brand_item_obj = {
                    'id': brand_item['id'],
                    'category': brand_item['category'],
                    'description': brand_item['description'],
                    'season': brand_item['season'],
                    'imageUrl': brand_item.get('image_url', ''),  # Используем image_url из get_brand_items_for_mixing
                    'shop_link': brand_item.get('shop_link'),
                    'price': brand_item.get('price'),
                    'currency': brand_item.get('currency', 'RUB'),
                    'is_brand_item': True,
                    'brand_name': 'LiMango'
                }
                items_list.append(brand_item_obj)
        
        filled_capsule = {
            **capsule,
            'items': items_list,
            'has_brand_items': bool(missing_items)
        }
        filled_capsules.append(filled_capsule)
    
    if missing_items:
        print(f"  ➕ Дополнено недостающими категориями: {', '.join(missing_items.keys())}")
    
    return filled_capsules


def get_smart_category_priorities(
    temperature: float,
    has_outerwear: bool,
    available_categories: List[str],
    used_categories: List[str]
) -> Dict[str, int]:
    """
    УМНЫЙ выбор приоритетов категорий для подмешивания
    
    Зависит от:
    1. Температуры (холодно/тепло/жарко)
    2. Наличия верхней одежды в капсуле
    3. Доступных категорий в капсуле
    4. Уже использованных категорий (для разнообразия)
    
    Returns:
        Dict с весами категорий {category: weight}
    """
    
    priorities = {}
    
    # ========== ТЕМПЕРАТУРНАЯ ЛОГИКА ==========
    
    if temperature < 15.0:
        # ХОЛОДНАЯ ПОГОДА (<15°C)
        # Приоритет: верхняя одежда, обувь, аксессуары (НО НЕ перчатки к легкой капсуле!)
        
        base_weights = {
            'outerwear': 40,     # Куртки, пальто - максимальный приоритет
            'shoes': 25,         # Ботинки, сапоги
            'accessories': 20 if has_outerwear else 5,  # Аксессуары только если есть верхняя одежда
            'tops': 10,          # Свитера, водолазки
            'bags': 5,           # Сумки - низкий приоритет в холод
            'bottoms': 3,        # Брюки - самый низкий
            'dresses': 0         # Платья не подмешиваем в холод
        }
        
    elif temperature >= 22.0:
        # ЖАРКАЯ ПОГОДА (>22°C)
        # Приоритет: аксессуары (украшения), сумки, обувь (легкая)
        
        base_weights = {
            'accessories': 40,   # Украшения, очки - максимальный приоритет
            'bags': 30,          # Сумки - высокий приоритет
            'shoes': 15,         # Легкая обувь (сандалии)
            'tops': 10,          # Легкие топы
            'dresses': 5,        # Платья
            'bottoms': 3,        # Шорты, легкие брюки
            'outerwear': 0       # Верхняя одежда не подмешиваем в жару
        }
        
    else:
        # УМЕРЕННАЯ ПОГОДА (15-22°C) - ДЕМИСЕЗОН
        # Приоритет: сумки, аксессуары (украшения), обувь, верх, низ
        
        base_weights = {
            'bags': 35,          # Сумки - максимальный приоритет
            'accessories': 30,   # Украшения
            'shoes': 20,         # Обувь
            'tops': 10,          # Верх
            'bottoms': 8,        # Низ
            'dresses': 5,        # Платья
            'outerwear': 3       # Легкая верхняя одежда (ветровки)
        }
    
    # Фильтруем только доступные категории в капсуле
    for cat in available_categories:
        if cat in base_weights:
            base_weight = base_weights[cat]
            
            # РАЗНООБРАЗИЕ: если категория уже использовалась - снижаем вес
            if cat in used_categories:
                # Чем больше раз использовали - тем меньше вес
                usage_count = used_categories.count(cat)
                penalty = 0.5 ** usage_count  # Экспоненциальное снижение
                priorities[cat] = max(1, int(base_weight * penalty))
            else:
                # Неиспользованная категория - УДВАИВАЕМ вес
                priorities[cat] = base_weight * 2
    
    return priorities


def mix_brand_items_into_capsules(
    user_capsules: List[Dict[str, Any]],
    wardrobe: List[Dict[str, Any]],
    season: str,
    temperature: float = 20.0,
    mixing_percentage: float = 0.35
) -> List[Dict[str, Any]]:
    """
    Подмешивает товары брендов в капсулы пользователя
    
    УМНЫЙ МНОГОФУНКЦИОНАЛЬНЫЙ МЕХАНИЗМ:
    
    1. Количество: 7 из 20 капсул (35%)
    2. Приоритеты зависят от ТЕМПЕРАТУРЫ и СОСТАВА капсулы
    3. Разнообразие: разные категории в разных капсулах
    4. Релевантность: не подмешиваем перчатки к летней капсуле!
    
    КАТЕГОРИИ (все существующие):
    - Верх (tops)
    - Низ (bottoms)
    - Обувь (shoes)
    - Платье (dresses)
    - Аксессуары (accessories)
    - Сумка (bags) - ОТДЕЛЬНО от аксессуаров!
    - Верхняя одежда (outerwear)
    
    ПРИОРИТЕТЫ ПО ТЕМПЕРАТУРЕ:
    - Холодно (<15°C): outerwear > accessories (теплые) > shoes > tops
    - Тепло (15-22°C): bags > accessories (украшения) > shoes > tops > bottoms
    - Жарко (>22°C): accessories > bags > tops > shoes
    
    Args:
        user_capsules: Список капсул пользователя
        wardrobe: Гардероб пользователя
        season: Текущий сезон
        temperature: Температура
        mixing_percentage: Процент капсул (по умолчанию 35% = 7 из 20)
    
    Returns:
        Обновленный список капсул с товарами брендов
    """
    
    if not user_capsules:
        return user_capsules
    
    # Определяем количество капсул для подмешивания (минимум 7!)
    total_to_mix = max(7, int(len(user_capsules) * mixing_percentage))
    print(f"🛍️ Подмешивание товаров брендов в {total_to_mix} из {len(user_capsules)} капсул")
    
    # Случайно выбираем капсулы для подмешивания
    capsules_to_mix = random.sample(
        range(len(user_capsules)), 
        min(total_to_mix, len(user_capsules))
    )
    
    # Создаем словарь вещей гардероба для быстрого доступа
    wardrobe_dict = {str(item['id']): item for item in wardrobe}
    
    # Отслеживаем использованные категории для разнообразия
    used_categories = []
    mixed_capsules = []
    mixed_count = 0
    
    for idx, capsule in enumerate(user_capsules):
        if idx not in capsules_to_mix:
            mixed_capsules.append(capsule)
            continue
        
        # Анализируем состав капсулы
        capsule_items = capsule.get('items', [])
        if not capsule_items:
            mixed_capsules.append(capsule)
            continue
        
        # Определяем категории вещей в капсуле и проверяем температурную релевантность
        from capsule_engine_v2 import translate_category
        
        categories_in_capsule = {}  # категория -> item_id
        has_outerwear = False
        
        for item_id in capsule_items:
            if isinstance(item_id, dict):
                # Это уже товар бренда, пропускаем
                continue
            
            item = wardrobe_dict.get(str(item_id))
            if item:
                cat = translate_category(item.get('category', ''))
                
                # Определяем есть ли верхняя одежда
                if cat == 'outerwear':
                    has_outerwear = True
                
                # Сохраняем категорию и ID для замены
                if cat not in categories_in_capsule:
                    categories_in_capsule[cat] = item_id
        
        # УМНЫЙ ВЫБОР КАТЕГОРИИ В ЗАВИСИМОСТИ ОТ ТЕМПЕРАТУРЫ
        category_priorities = get_smart_category_priorities(
            temperature=temperature,
            has_outerwear=has_outerwear,
            available_categories=list(categories_in_capsule.keys()),
            used_categories=used_categories
        )
        
        if not category_priorities:
            mixed_capsules.append(capsule)
            continue
        
        # Выбираем категорию с учетом приоритетов
        categories_list = list(category_priorities.keys())
        weights_list = list(category_priorities.values())
        replacement_category = random.choices(categories_list, weights=weights_list, k=1)[0]
        
        # Получаем товары брендов для этой категории
        brand_items = get_brand_items_for_mixing(
            category=replacement_category,
            season=season,
            temperature=temperature,
            limit=5
        )
        
        if not brand_items:
            mixed_capsules.append(capsule)
            continue
        
        # Выбираем случайный товар бренда
        brand_item = random.choice(brand_items)
        
        # Находим вещь для замены в капсуле
        # ДЛЯ АКСЕССУАРОВ: проверяем подтип, чтобы НЕ заменять серьги на ремень!
        from capsule_engine_v4 import accessory_subtype
        
        brand_item_subtype = None
        if replacement_category == 'accessories':
            # Определяем подтип товара бренда
            brand_desc = brand_item.get('description', '').lower()
            if 'серьги' in brand_desc or 'бусы' in brand_desc:
                brand_item_subtype = 'earrings_or_necklace'
            elif 'ремень' in brand_desc or 'пояс' in brand_desc:
                brand_item_subtype = 'belt'
            elif 'шарф' in brand_desc:
                brand_item_subtype = 'scarf'
            elif 'шапк' in brand_desc:
                brand_item_subtype = 'headwear'
            elif 'перчатк' in brand_desc or 'варежк' in brand_desc:
                brand_item_subtype = 'gloves'
            elif 'очки' in brand_desc:
                brand_item_subtype = 'sunglasses'
            elif 'часы' in brand_desc:
                brand_item_subtype = 'watch'
            elif 'браслет' in brand_desc:
                brand_item_subtype = 'bracelet'
        
        item_to_replace = None
        for item_id in capsule_items:
            if isinstance(item_id, dict):
                continue  # Пропускаем товары брендов
            
            item = wardrobe_dict.get(str(item_id))
            if item and translate_category(item.get('category', '')) == replacement_category:
                # ДЛЯ АКСЕССУАРОВ: проверяем совпадение подтипа
                if replacement_category == 'accessories' and brand_item_subtype:
                    item_subtype = accessory_subtype(item)
                    # Проверяем совпадение подтипа (серьги меняем на серьги, ремень на ремень)
                    if brand_item_subtype == 'earrings_or_necklace' and item_subtype not in ['earrings', 'necklace']:
                        continue
                    elif brand_item_subtype == 'belt' and item_subtype != 'belt':
                        continue
                    elif brand_item_subtype == 'scarf' and item_subtype != 'scarf':
                        continue
                    elif brand_item_subtype == 'headwear' and item_subtype != 'headwear':
                        continue
                    elif brand_item_subtype == 'gloves' and item_subtype != 'gloves':
                        continue
                    elif brand_item_subtype == 'sunglasses' and item_subtype != 'sunglasses':
                        continue
                    elif brand_item_subtype == 'watch' and item_subtype != 'watch':
                        continue
                    elif brand_item_subtype == 'bracelet' and item_subtype != 'bracelet':
                        continue
                
                item_to_replace = item_id
                break
        
        if not item_to_replace:
            mixed_capsules.append(capsule)
            continue
        
        # Создаем новую капсулу с товаром бренда
        # Вместо замены ID, создаем полный объект вещи для товара бренда
        new_items_list = []
        for item_id in capsule_items:
            if item_id == item_to_replace:
                # Добавляем товар бренда как полноценную вещь
                brand_item_as_wardrobe = {
                    'id': brand_item['id'],
                    'category': brand_item['category'],
                    'description': brand_item['description'],
                    'season': brand_item['season'],
                    'imageUrl': brand_item['image_url'],
                    'shop_link': brand_item.get('shop_link'),
                    'price': brand_item.get('price'),
                    'currency': brand_item.get('currency', 'RUB'),
                    'is_brand_item': True,
                    'brand_name': brand_item.get('brand_name', 'LiMango')
                }
                new_items_list.append(brand_item_as_wardrobe)
            else:
                new_items_list.append(item_id)
        
        mixed_capsule = {
            **capsule,
            'items': new_items_list,  # Смешанный список: ID обычных вещей + полные объекты товаров брендов
            'has_brand_item': True,
            'brand_item_id': brand_item['id'],
            'replaced_category': replacement_category
        }
        
        mixed_capsules.append(mixed_capsule)
        mixed_count += 1
        
        # Добавляем категорию в список использованных для разнообразия
        used_categories.append(replacement_category)
        
        print(f"  ✅ Капсула {capsule.get('id', idx)}: заменили {replacement_category} на товар бренда {brand_item.get('brand_name', 'Unknown')}")
    
    # Итоговая статистика
    unique_categories = len(set(used_categories))
    print(f"  📊 Подмешано {mixed_count} товаров из {unique_categories} разных категорий: {', '.join(set(used_categories))}")
    
    return mixed_capsules

