"""
Сервис для работы с товарами брендов V4 - ПРАКТИЧНАЯ ЛОГИКА
Решает проблему: у нас есть только 6 категорий в базе, но нужно подмешивать в 7 капсул

НОВАЯ ЛОГИКА:
1. Приоритет: Сумка > Обувь > Верх/Низ > Верхняя одежда (если холодно)
2. Аксессуары: добиваем остальное (серьги, ремень, шарф, шапка)
3. Ротация: разные товары в каждой генерации
4. Минимум 7 товаров для 7 капсул
"""

from typing import List, Dict, Any, Optional, Set
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


def get_all_brand_items_by_season(season: str) -> List[Dict[str, Any]]:
    """Получить ВСЕ товары брендов по сезону через ПУБЛИЧНЫЙ API"""
    try:
        import requests
        
        # Маппинг сезонов на русский язык для API
        season_map = {
            'Весна': 'Весна',
            'Лето': 'Лето',
            'Осень': 'Осень',
            'Зима': 'Зима'
        }
        
        season_ru = season_map.get(season, 'Осень')
        
        # Запрос к публичному API (БЕЗ категории - только сезон!)
        api_url = f"https://linapolo.ru/api/public/items/capsule?season={season_ru}"
        
        print(f"📡 Запрос к API: {api_url}")
        
        response = requests.get(api_url, timeout=30)  # Увеличили timeout до 30 сек
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        # Данные уже готовы: image_url и shop_link уже есть!
        for item in items:
            item['is_brand_item'] = True
            # brand_name уже есть из API
            # Если shop_link отсутствует, устанавливаем None
            if 'shop_link' not in item or not item['shop_link']:
                item['shop_link'] = None
        
        print(f"✅ Загружено {len(items)} товаров брендов через публичный API")
        print(f"   Алгоритм: {data.get('algorithm', 'unknown')}")
        return items
    
    except Exception as e:
        print(f"❌ Ошибка загрузки товаров брендов через API: {e}")
        print(f"🔄 Пробуем FALLBACK на прямой запрос к Supabase...")
        
        # FALLBACK: прямой запрос к Supabase
        try:
            supabase = get_supabase_client()
            if not supabase:
                return []
            
            response = supabase.table('brand_items') \
                .select('id, brand_id, category, season, description, image_id, shop_link, price, currency') \
                .eq('is_approved', True) \
                .eq('is_active', True) \
                .execute()
            
            items = response.data if response.data else []
            
            for item in items:
                if item.get('image_id') and item.get('brand_id'):
                    item['image_url'] = f"https://lipolo.store/storage/v1/object/public/brand-items-images/{item['brand_id']}/{item['image_id']}.jpg"
                else:
                    item['image_url'] = None
                item['is_brand_item'] = True
                item['brand_name'] = 'LiMango'
                if 'shop_link' not in item or not item['shop_link']:
                    item['shop_link'] = None
                # Устанавливаем impressions_count = 0 для Supabase товаров
                if 'impressions_count' not in item:
                    item['impressions_count'] = 0
            
            print(f"✅ FALLBACK: Загружено {len(items)} товаров брендов из Supabase")
            return items
        except Exception as fallback_error:
            print(f"❌ FALLBACK тоже не сработал: {fallback_error}")
            return []


def map_brand_category_to_engine_category(brand_category: str) -> str:
    """
    Маппинг категорий из базы брендов в категории движка
    
    База брендов: Аксессуары, Верх, Верхняя одежда, Низ, Обувь, Сумка
    Движок: tops, bottoms, dresses, outerwear, light_outerwear, shoes, bags, accessories
    """
    mapping = {
        'Верх': 'tops',
        'Низ': 'bottoms', 
        'Обувь': 'shoes',
        'Сумка': 'bags',
        'Верхняя одежда': 'outerwear',
        'Аксессуары': 'accessories'
    }
    return mapping.get(brand_category, 'other')


def get_accessory_subtype_from_description(description: str) -> str:
    """
    Определяет подтип аксессуара по описанию
    
    Возвращает: earrings, necklace, bracelet, ring, belt, scarf, headwear, gloves, watch, sunglasses, other
    """
    desc_lower = description.lower()
    
    if any(word in desc_lower for word in ['серьги', 'серёжк']):
        return 'earrings'
    if any(word in desc_lower for word in ['колье', 'бусы', 'ожерел', 'цепоч', 'подвес']):
        return 'necklace'
    if any(word in desc_lower for word in ['браслет']):
        return 'bracelet'
    if any(word in desc_lower for word in ['кольцо', 'перстен']):
        return 'ring'
    if any(word in desc_lower for word in ['ремень', 'пояс']):
        return 'belt'
    if any(word in desc_lower for word in ['шарф', 'платок', 'палант', 'снуд']):
        return 'scarf'
    if any(word in desc_lower for word in ['шапка', 'берет', 'кепка', 'панам', 'шляпа', 'капор']):
        return 'headwear'
    if any(word in desc_lower for word in ['перчатк', 'варежк', 'митенк']):
        return 'gloves'
    if any(word in desc_lower for word in ['часы']):
        return 'watch'
    if any(word in desc_lower for word in ['очки', 'солнце']):
        return 'sunglasses'
    
    return 'other'


def mix_brand_items_v4(
    user_capsules: List[Dict[str, Any]],
    wardrobe: List[Dict[str, Any]],
    season: str,
    temperature: float = 20.0,
    mixing_percentage: float = 0.35,
    exclude_combinations: List[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    ПРАКТИЧНАЯ ЛОГИКА V4: Подмешивает товары брендов с умным приоритетом
    
    ПРИОРИТЕТ ПОДМЕШИВАНИЯ:
    1. Сумка (всегда нужна)
    2. Обувь (всегда нужна)
    3. Верх/Низ (если нет платья)
    4. Верхняя одежда (только если холодно <15°C)
    5. Аксессуары (добиваем остальное)
    
    Args:
        user_capsules: Список капсул пользователя
        wardrobe: Гардероб пользователя
        season: Текущий сезон
        temperature: Температура
        mixing_percentage: Процент капсул для подмешивания (0.35 = 7 из 20)
        exclude_combinations: Уже показанные комбинации для исключения
    
    Returns:
        Капсулы с подмешанными товарами брендов
    """
    if not user_capsules:
        return user_capsules
    
    # 1. Получаем ВСЕ товары брендов ОДИН РАЗ
    # Загружаем товары брендов через ПУБЛИЧНЫЙ API (по сезону)
    all_brand_items = get_all_brand_items_by_season(season)
    if not all_brand_items:
        print("  ⚠️ Нет товаров брендов для подмешивания")
        return user_capsules
    
    # 2. Фильтруем товары брендов ПО ТОЙ ЖЕ ЛОГИКЕ что и вещи пользователя
    try:
        from capsule_engine_v6 import is_suitable_for_temp_and_season
    except ImportError:
        print("  ⚠️ capsule_engine_v6 не найден, используем базовую фильтрацию")
        from capsule_engine_v4 import is_suitable_for_temp_and_season
    
    filtered_brand_items = []
    for item in all_brand_items:
        if is_suitable_for_temp_and_season(item, temperature, season):
            filtered_brand_items.append(item)
    
    print(f"  ✅ Отфильтровано {len(filtered_brand_items)} из {len(all_brand_items)} товаров брендов")
    
    if not filtered_brand_items:
        print("  ⚠️ После фильтрации не осталось товаров брендов")
        return user_capsules
    
    # 3. Группируем товары брендов по категориям движка
    brand_by_category = defaultdict(list)
    for item in filtered_brand_items:
        engine_cat = map_brand_category_to_engine_category(item.get('category', ''))
        
        if engine_cat == 'accessories':
            # Для аксессуаров определяем подтип
            subtype = get_accessory_subtype_from_description(item.get('description', ''))
            brand_by_category[f'acc_{subtype}'].append(item)
        else:
            brand_by_category[engine_cat].append(item)
    
    print(f"  📦 Товары брендов по категориям:")
    for cat, items in brand_by_category.items():
        if items:
            print(f"     - {cat}: {len(items)} шт.")
    
    # 4. Создаем словарь для быстрого поиска вещей по ID
    wardrobe_dict = {str(item['id']): item for item in wardrobe}
    
    # 5. Отслеживаем использование брендовых товаров (ГЛОБАЛЬНО!)
    used_brand_items = set()
    brand_usage_count = defaultdict(int)
    
    # 6. Подмешиваем в случайные капсулы (минимум 7!)
    total_to_mix = max(7, int(len(user_capsules) * mixing_percentage))
    capsules_to_mix = list(range(len(user_capsules)))
    random.shuffle(capsules_to_mix)
    capsules_to_mix = capsules_to_mix[:min(total_to_mix, len(user_capsules))]
    
    mixed_count = 0
    mixed_categories = set()
    
    # НОВАЯ ЛОГИКА: отслеживаем, какие категории уже использованы
    used_categories_global = set()
    
    print(f"  🎯 Выбрано {len(capsules_to_mix)} капсул для подмешивания: {capsules_to_mix}")
    
    for idx in capsules_to_mix:
        capsule = user_capsules[idx]
        
        print(f"  🔄 Обрабатываем капсулу {idx} (ID: {capsule.get('id')})")
        print(f"  📊 Глобально использовано: {len(used_brand_items)} товаров")
        
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
            
            # Используем translate_category из движка
            try:
                from capsule_engine_v6 import translate_category, accessory_subtype
            except ImportError:
                from capsule_engine_v4 import translate_category, accessory_subtype
            
            item_cat = translate_category(user_item.get('category', ''))
            if item_cat == 'accessories':
                subtype = accessory_subtype(user_item)
                item_categories[i] = (item_id, f'acc_{subtype}')
            else:
                item_categories[i] = (item_id, item_cat)
        
        # УМНЫЙ ПРИОРИТЕТ ПОДМЕШИВАНИЯ
        priority_order = []
        
        # 1. Сумка (всегда приоритет)
        if 'bags' in brand_by_category and brand_by_category['bags']:
            priority_order.append('bags')
        
        # 2. Обувь (всегда приоритет)
        if 'shoes' in brand_by_category and brand_by_category['shoes']:
            priority_order.append('shoes')
        
        # 3. Верх/Низ (если нет платья)
        has_dress = any(cat == 'dresses' for _, cat in item_categories.values())
        if not has_dress:
            if 'tops' in brand_by_category and brand_by_category['tops']:
                priority_order.append('tops')
            if 'bottoms' in brand_by_category and brand_by_category['bottoms']:
                priority_order.append('bottoms')
        
        # 4. Верхняя одежда (только если холодно)
        if temperature < 15.0 and 'outerwear' in brand_by_category and brand_by_category['outerwear']:
            priority_order.append('outerwear')
        
        # 5. Аксессуары (добиваем остальное)
        if temperature >= 15.0:
            # Теплая погода: серьги, ремень, браслет
            for acc_type in ['acc_earrings', 'acc_belt', 'acc_bracelet']:
                if acc_type in brand_by_category and brand_by_category[acc_type]:
                    priority_order.append(acc_type)
        else:
            # Холодная погода: шарф, шапка, перчатки
            for acc_type in ['acc_scarf', 'acc_headwear', 'acc_gloves']:
                if acc_type in brand_by_category and brand_by_category[acc_type]:
                    priority_order.append(acc_type)
        
        # РАЗНООБРАЗИЕ: перемешиваем приоритеты для разных капсул
        if idx % 7 == 0:  # Каждая 7-я капсула
            # Приоритет: обувь, сумка, аксессуары
            priority_order = [cat for cat in priority_order if cat in ['shoes', 'bags']] + \
                            [cat for cat in priority_order if cat not in ['shoes', 'bags']]
        elif idx % 7 == 1:  # Каждая 7-я капсула
            # Приоритет: аксессуары, обувь, сумка
            priority_order = [cat for cat in priority_order if cat.startswith('acc_')] + \
                            [cat for cat in priority_order if cat not in ['bags'] and not cat.startswith('acc_')] + \
                            [cat for cat in priority_order if cat == 'bags']
        elif idx % 7 == 2:  # Каждая 7-я капсула
            # Приоритет: верх, низ, обувь, сумка, аксессуары
            priority_order = [cat for cat in priority_order if cat in ['tops', 'bottoms']] + \
                            [cat for cat in priority_order if cat not in ['tops', 'bottoms']]
        elif idx % 7 == 3:  # Каждая 7-я капсула
            # Приоритет: обувь, аксессуары, сумка
            priority_order = [cat for cat in priority_order if cat in ['shoes']] + \
                            [cat for cat in priority_order if cat.startswith('acc_')] + \
                            [cat for cat in priority_order if cat == 'bags']
        elif idx % 7 == 4:  # Каждая 7-я капсула
            # Приоритет: сумка, обувь, аксессуары
            priority_order = [cat for cat in priority_order if cat == 'bags'] + \
                            [cat for cat in priority_order if cat == 'shoes'] + \
                            [cat for cat in priority_order if cat.startswith('acc_')]
        elif idx % 7 == 5:  # Каждая 7-я капсула
            # Приоритет: аксессуары, сумка, обувь
            priority_order = [cat for cat in priority_order if cat.startswith('acc_')] + \
                            [cat for cat in priority_order if cat == 'bags'] + \
                            [cat for cat in priority_order if cat == 'shoes']
        # else: оставляем оригинальный порядок
        
        print(f"  🎯 Приоритет для капсулы {idx}: {priority_order}")
        
        # Ищем категорию для замены
        replaced = False
        
        # НОВАЯ ЛОГИКА: собираем ВСЕ доступные категории для замены
        available_replacements = []  # [(priority_cat, idx_in_capsule, item_id)]
        
        for priority_cat in priority_order:
            # Проверяем есть ли товары бренда этой категории
            if priority_cat not in brand_by_category or not brand_by_category[priority_cat]:
                continue
            
            # Ищем вещь ЭТОЙ категории в капсуле
            for idx_in_capsule, (item_id, item_cat) in item_categories.items():
                if item_cat == priority_cat:
                    available_replacements.append((priority_cat, idx_in_capsule, item_id))
        
        # Если есть доступные замены - выбираем категорию, которая еще НЕ использовалась
        if available_replacements:
            print(f"  🎯 Доступно {len(available_replacements)} категорий для замены: {[r[0] for r in available_replacements]}")
            print(f"  📊 Уже использованы глобально: {used_categories_global}")
            
            # Приоритет: категории, которые еще НЕ использовались
            unused_replacements = [r for r in available_replacements if r[0] not in used_categories_global]
            
            if unused_replacements:
                priority_cat, idx_in_capsule, item_id = unused_replacements[0]
                print(f"  ✅ Выбрана НОВАЯ категория: {priority_cat}")
            else:
                # Все категории уже использованы - берем первую по приоритету
                priority_cat, idx_in_capsule, item_id = available_replacements[0]
                print(f"  ✅ Выбрана категория (повтор): {priority_cat}")
            
            # РОТАЦИЯ: выбираем товар который еще НЕ использовался
            available_brand_items = [
                item for item in brand_by_category[priority_cat] 
                if item['id'] not in used_brand_items
            ]
            
            print(f"  🔍 Категория {priority_cat}: доступно {len(available_brand_items)} из {len(brand_by_category[priority_cat])}")
            print(f"  📊 Уже использованы: {len(used_brand_items)} товаров")
            
            # Если все товары уже использовались - ПРОПУСКАЕМ эту капсулу
            if not available_brand_items:
                print(f"  ⚠️ Все товары категории {priority_cat} уже использованы в этой генерации, пропускаем капсулу")
                continue  # Пропускаем эту категорию, пробуем следующую
            
            # Выбираем товар с минимальным использованием
            # ПРИОРИТЕТ:
            # 1. Товары с минимальным локальным использованием (brand_usage_count)
            # 2. Товары с минимальным глобальным показом (impressions_count из API)
            brand_item = min(
                available_brand_items, 
                key=lambda x: (
                    brand_usage_count[x['id']],  # Сначала по локальному использованию
                    x.get('impressions_count', 0)  # Потом по глобальным показам
                )
            )
            
            print(f"  🎲 Выбран товар: {brand_item.get('description', '')[:30]}... (использование: {brand_usage_count[brand_item['id']]}, показы: {brand_item.get('impressions_count', 0)})")
            
            # Заменяем на товар бренда
            capsule['items'][idx_in_capsule] = brand_item
            replaced = True
            mixed_count += 1
            mixed_categories.add(priority_cat)
            used_categories_global.add(priority_cat)  # Отслеживаем глобально
            
            # Отслеживаем использование
            brand_item_id = brand_item.get('id')
            print(f"  🔍 ID товара: {brand_item_id}")
            print(f"  📊 До добавления: использовано {len(used_brand_items)} товаров")
            
            used_brand_items.add(brand_item_id)
            brand_usage_count[brand_item_id] += 1
            
            print(f"  📊 После добавления: использовано {len(used_brand_items)} товаров")
            print(f"  ✅ Капсула {capsule.get('id')}: заменили {priority_cat} на товар бренда {brand_item.get('brand_name')}")
            print(f"      🖼️ image_url: {brand_item.get('image_url', 'НЕТ')}")
            print(f"      🔗 shop_link: {brand_item.get('shop_link', 'НЕТ')}")
            print(f"      🏷️ description: {brand_item.get('description', 'НЕТ')[:50]}...")
            print(f"      📊 Использование: {brand_usage_count[brand_item_id]} раз")
    
    print(f"  📊 Подмешано {mixed_count} товаров из {len(mixed_categories)} разных категорий: {', '.join(sorted(mixed_categories))}")
    print(f"  🔄 Использовано {len(used_brand_items)} уникальных товаров брендов")
    
    return user_capsules


def supplement_capsules_with_brand_items(
    user_capsules: List[Dict[str, Any]],
    target_count: int,
    season: str,
    temperature: float = 20.0
) -> List[Dict[str, Any]]:
    """
    ДОПОЛНЯЕТ капсулы брендовыми товарами, если у пользователя недостаточно вещей
    
    Args:
        user_capsules: существующие капсулы пользователя
        target_count: целевое количество капсул (например, 20)
        season: сезон
        temperature: температура
    
    Returns:
        Дополненный список капсул
    """
    missing_count = target_count - len(user_capsules)
    
    if missing_count <= 0:
        print(f"  ✅ У пользователя достаточно вещей ({len(user_capsules)} капсул)")
        return user_capsules
    
    print(f"  🛍️ Не хватает {missing_count} капсул, дополняем брендовыми товарами...")
    
    # Загружаем товары брендов
    all_brand_items = get_all_brand_items_by_season(season)
    if not all_brand_items:
        print("  ⚠️ Нет товаров брендов для дополнения")
        return user_capsules
    
    # Фильтруем по температуре
    try:
        from capsule_engine_v6 import is_suitable_for_temp_and_season
    except ImportError:
        from capsule_engine_v4 import is_suitable_for_temp_and_season
    
    filtered_items = [item for item in all_brand_items if is_suitable_for_temp_and_season(item, temperature, season)]
    
    # Группируем по категориям
    brand_by_category = defaultdict(list)
    for item in filtered_items:
        engine_cat = map_brand_category_to_engine_category(item.get('category', ''))
        
        if engine_cat == 'accessories':
            subtype = identify_accessory_subtype(item.get('description', '').lower())
            brand_by_category[f'acc_{subtype}'].append(item)
        else:
            brand_by_category[engine_cat].append(item)
    
    # Генерируем новые капсулы из брендовых товаров
    new_capsules = []
    used_items = set()
    
    for i in range(missing_count):
        capsule_items = []
        
        # Базовый состав: верх, низ, обувь, сумка
        categories_needed = ['tops', 'bottoms', 'shoes', 'bags']
        
        # Если холодно - добавляем верхнюю одежду
        if temperature < 15.0:
            categories_needed.append('outerwear')
            # Холодные аксессуары
            categories_needed.extend(['acc_scarf', 'acc_headwear', 'acc_gloves'])
        else:
            # Теплые аксессуары
            categories_needed.extend(['acc_earrings', 'acc_belt'])
        
        # Собираем капсулу
        for cat in categories_needed:
            if cat not in brand_by_category or not brand_by_category[cat]:
                continue
            
            # Берем товар, который еще не использовали
            available = [item for item in brand_by_category[cat] if item['id'] not in used_items]
            if not available:
                available = brand_by_category[cat]  # Если все использованы, берем любой
            
            item = min(available, key=lambda x: x.get('impressions_count', 0))
            capsule_items.append(item)
            used_items.add(item['id'])
        
        if capsule_items:
            new_capsule = {
                'id': f'brand_c{i+1}',
                'items': capsule_items,
                'name': f'Образ от LiMango #{i+1}',
                'has_brand_item': True,
                'is_brand_capsule': True  # Флаг, что вся капсула из брендов
            }
            new_capsules.append(new_capsule)
    
    print(f"  ✅ Создано {len(new_capsules)} новых капсул из брендовых товаров")
    
    return user_capsules + new_capsules
