"""
Сервис для работы с товарами брендов V5 - ГИБКОЕ РАСПРЕДЕЛЕНИЕ

НОВАЯ ЛОГИКА (из 20 капсул):
- 7 капсул: ТОЛЬКО вещи пользователя
- 6 капсул: 1 товар бренда
- 3 капсулы: 2 товара бренда
- 3 капсулы: 3 товара бренда
- 1 капсула: ПОЛНОСТЬЮ из брендов

ИТОГО: 20 капсул с разным уровнем подмешивания
"""

from typing import List, Dict, Any, Optional
import random
import os
from collections import defaultdict
import requests


def get_all_brand_items_by_season(season: str) -> List[Dict[str, Any]]:
    """Получить ВСЕ товары брендов по сезону через ПУБЛИЧНЫЙ API"""
    try:
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
        
        print(f"📡 V5: Запрос к API: {api_url}")
        
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        # Данные уже готовы: image_url и shop_link уже есть!
        for item in items:
            item['is_brand_item'] = True
            if 'shop_link' not in item or not item['shop_link']:
                item['shop_link'] = None
            if 'impressions_count' not in item:
                item['impressions_count'] = 0
        
        print(f"✅ V5: Загружено {len(items)} товаров брендов через публичный API")
        print(f"   Алгоритм: {data.get('algorithm', 'unknown')}")
        return items
    
    except Exception as e:
        print(f"❌ V5: Ошибка загрузки товаров брендов через API: {e}")
        print(f"🔄 V5: Пробуем FALLBACK на brand_service_v4...")
        
        # FALLBACK: используем функцию из brand_service_v4
        try:
            from brand_service_v4 import get_all_brand_items_by_season as get_v4
            items = get_v4(season)
            print(f"✅ V5 FALLBACK: Загружено {len(items)} товаров через V4")
            return items
        except Exception as fallback_error:
            print(f"❌ V5 FALLBACK тоже не сработал: {fallback_error}")
            return []


def map_brand_category_to_engine_category(brand_category: str) -> str:
    """Маппинг категорий из базы брендов в категории движка"""
    mapping = {
        'Верх': 'tops',
        'Низ': 'bottoms', 
        'Обувь': 'shoes',
        'Сумка': 'bags',
        'Верхняя одежда': 'outerwear',
        'Аксессуары': 'accessories'
    }
    return mapping.get(brand_category, 'other')


def identify_accessory_subtype(description: str) -> str:
    """Определяет подтип аксессуара по описанию"""
    desc_lower = description.lower()
    
    if 'серьг' in desc_lower or 'кольц' in desc_lower and 'уш' in desc_lower:
        return 'earrings'
    elif 'ожерел' in desc_lower or 'колье' in desc_lower or 'цепь' in desc_lower or 'цепоч' in desc_lower:
        return 'necklace'
    elif 'брасл' in desc_lower:
        return 'bracelet'
    elif 'ремен' in desc_lower or 'пояс' in desc_lower:
        return 'belt'
    elif 'кольцо' in desc_lower and 'уш' not in desc_lower:
        return 'ring'
    elif 'часы' in desc_lower:
        return 'watch'
    elif 'очки' in desc_lower:
        return 'sunglasses'
    elif 'шапк' in desc_lower or 'берет' in desc_lower or 'панам' in desc_lower or 'шляп' in desc_lower:
        return 'headwear'
    elif 'шарф' in desc_lower or 'платок' in desc_lower:
        return 'scarf'
    elif 'перчат' in desc_lower or 'варежк' in desc_lower:
        return 'gloves'
    else:
        return 'other'


def mix_brand_items_v5(
    user_capsules: List[Dict[str, Any]],
    wardrobe: List[Dict[str, Any]],
    season: str,
    temperature: float = 20.0,
    exclude_combinations: Optional[List[List[str]]] = None
) -> List[Dict[str, Any]]:
    """
    НОВАЯ ЛОГИКА V5: Гибкое распределение брендовых товаров
    
    Из 20 капсул:
    - 7 капсул: ТОЛЬКО вещи пользователя
    - 6 капсул: 1 товар бренда
    - 3 капсулы: 2 товара бренда
    - 3 капсулы: 3 товара бренда
    - 1 капсула: ПОЛНОСТЬЮ из брендов
    
    Args:
        user_capsules: капсулы пользователя (должно быть >= 19)
        wardrobe: гардероб пользователя
        season: сезон
        temperature: температура
        exclude_combinations: уже показанные комбинации
    
    Returns:
        Список из 20 капсул с разным уровнем подмешивания
    """
    if len(user_capsules) < 19:
        print(f"  ⚠️ Недостаточно капсул пользователя ({len(user_capsules)}), нужно минимум 19")
        return user_capsules
    
    # 1. Загружаем товары брендов
    all_brand_items = get_all_brand_items_by_season(season)
    if not all_brand_items:
        print("  ⚠️ Нет товаров брендов для подмешивания")
        return user_capsules
    
    # 2. Фильтруем по температуре
    try:
        from capsule_engine_v6 import is_suitable_for_temp_and_season
    except ImportError:
        from capsule_engine_v4 import is_suitable_for_temp_and_season
    
    filtered_items = [item for item in all_brand_items if is_suitable_for_temp_and_season(item, temperature, season)]
    print(f"  ✅ Отфильтровано {len(filtered_items)} из {len(all_brand_items)} товаров брендов")
    
    if not filtered_items:
        print("  ⚠️ После фильтрации не осталось товаров брендов")
        return user_capsules
    
    # 3. Группируем по категориям
    brand_by_category = defaultdict(list)
    for item in filtered_items:
        engine_cat = map_brand_category_to_engine_category(item.get('category', ''))
        
        if engine_cat == 'accessories':
            subtype = identify_accessory_subtype(item.get('description', '').lower())
            brand_by_category[f'acc_{subtype}'].append(item)
        else:
            brand_by_category[engine_cat].append(item)
    
    print(f"  📦 Товары брендов по категориям:")
    for cat, items in sorted(brand_by_category.items()):
        if items:
            print(f"     - {cat}: {len(items)} шт.")
    
    # 4. Создаем словарь для быстрого поиска
    wardrobe_dict = {str(item['id']): item for item in wardrobe}
    
    # 5. Импортируем функцию для определения категорий
    try:
        from capsule_engine_v6 import translate_category, accessory_subtype
    except ImportError:
        from capsule_engine_v4 import translate_category, accessory_subtype
    
    # 6. РАСПРЕДЕЛЕНИЕ КАПСУЛ
    total = len(user_capsules)
    
    # Перемешиваем капсулы для случайного распределения
    capsules_shuffled = list(enumerate(user_capsules))
    random.shuffle(capsules_shuffled)
    
    # Группируем по типам подмешивания
    pure_user_capsules = capsules_shuffled[:7]  # 7 капсул без брендов
    one_brand_capsules = capsules_shuffled[7:13]  # 6 капсул с 1 товаром
    two_brand_capsules = capsules_shuffled[13:16]  # 3 капсулы с 2 товарами
    three_brand_capsules = capsules_shuffled[16:19]  # 3 капсулы с 3 товарами
    full_brand_capsule_idx = capsules_shuffled[19] if len(capsules_shuffled) > 19 else None  # 1 полная
    
    print(f"  🎯 Распределение капсул:")
    print(f"     - 7 чистых: индексы {[idx for idx, _ in pure_user_capsules]}")
    print(f"     - 6 с 1 товаром: индексы {[idx for idx, _ in one_brand_capsules]}")
    print(f"     - 3 с 2 товарами: индексы {[idx for idx, _ in two_brand_capsules]}")
    print(f"     - 3 с 3 товарами: индексы {[idx for idx, _ in three_brand_capsules]}")
    if full_brand_capsule_idx:
        print(f"     - 1 полная: индекс {full_brand_capsule_idx[0]}")
    
    # 7. Отслеживание использованных товаров
    used_brand_items = set()
    brand_usage_count = defaultdict(int)
    used_categories_global = set()
    
    mixed_count = 0
    
    # 8. ФУНКЦИЯ ДЛЯ ПОДМЕШИВАНИЯ N ТОВАРОВ В КАПСУЛУ
    def mix_n_items_into_capsule(capsule_idx: int, capsule: Dict, n_items: int) -> int:
        """Подмешивает N товаров бренда в капсулу"""
        nonlocal mixed_count, used_brand_items, brand_usage_count, used_categories_global
        
        # Анализируем состав капсулы
        capsule_items = capsule.get('items', [])
        if not capsule_items:
            return 0
        
        # Определяем категории вещей в капсуле
        item_categories = {}  # {index: (item_id, category)}
        
        for i, item_id in enumerate(capsule_items):
            if isinstance(item_id, dict):
                continue
            
            user_item = wardrobe_dict.get(str(item_id))
            if not user_item:
                continue
            
            item_cat = translate_category(user_item.get('category', ''))
            if item_cat == 'accessories':
                subtype = accessory_subtype(user_item)
                item_categories[i] = (item_id, f'acc_{subtype}')
            else:
                item_categories[i] = (item_id, item_cat)
        
        # Определяем приоритет категорий для замены
        has_dress = any(cat == 'dresses' for _, cat in item_categories.values())
        is_cold = temperature < 15.0
        
        priority_order = []
        
        # 1. Сумка
        if 'bags' in item_categories.values():
            priority_order.append('bags')
        
        # 2. Обувь
        if 'shoes' in item_categories.values():
            priority_order.append('shoes')
        
        # 3. Верх/Низ (если нет платья)
        if not has_dress:
            if any(cat == 'tops' for _, cat in item_categories.values()):
                priority_order.append('tops')
            if any(cat == 'bottoms' for _, cat in item_categories.values()):
                priority_order.append('bottoms')
        
        # 4. Верхняя одежда (если холодно)
        if is_cold and any(cat == 'outerwear' for _, cat in item_categories.values()):
            priority_order.append('outerwear')
        
        # 5. Аксессуары
        if is_cold:
            for acc_type in ['acc_scarf', 'acc_headwear', 'acc_gloves']:
                if any(cat == acc_type for _, cat in item_categories.values()):
                    priority_order.append(acc_type)
        else:
            for acc_type in ['acc_earrings', 'acc_belt', 'acc_necklace', 'acc_bracelet']:
                if any(cat == acc_type for _, cat in item_categories.values()):
                    priority_order.append(acc_type)
        
        # Собираем доступные замены
        available_replacements = []
        for idx_in_capsule, (item_id, item_cat) in item_categories.items():
            if item_cat in priority_order:
                available_replacements.append((item_cat, idx_in_capsule, item_id))
        
        if not available_replacements:
            return 0
        
        # Приоритизируем неиспользованные категории
        replacements_sorted = []
        for cat, idx, item_id in available_replacements:
            if cat not in used_categories_global:
                replacements_sorted.insert(0, (cat, idx, item_id))
            else:
                replacements_sorted.append((cat, idx, item_id))
        
        # Подмешиваем N товаров
        replaced_in_capsule = 0
        
        for cat, idx_in_capsule, _ in replacements_sorted[:n_items]:
            # Проверяем, есть ли товары этой категории
            if cat not in brand_by_category or not brand_by_category[cat]:
                continue
            
            # Выбираем товар
            available_brand_items = [
                item for item in brand_by_category[cat]
                if item['id'] not in used_brand_items
            ]
            
            if not available_brand_items:
                # Все товары использованы, берем наименее использованный
                available_brand_items = brand_by_category[cat]
            
            brand_item = min(
                available_brand_items,
                key=lambda x: (
                    brand_usage_count[x['id']],
                    x.get('impressions_count', 0)
                )
            )
            
            # Заменяем
            capsule['items'][idx_in_capsule] = brand_item
            used_brand_items.add(brand_item['id'])
            brand_usage_count[brand_item['id']] += 1
            used_categories_global.add(cat)
            mixed_count += 1
            replaced_in_capsule += 1
            
            print(f"  ✅ Капсула c{capsule_idx}: заменили {cat} на {brand_item.get('brand_name')} (показы: {brand_item.get('impressions_count', 0)})")
        
        capsule['has_brand_item'] = True
        capsule['brand_items_count'] = replaced_in_capsule
        
        return replaced_in_capsule
    
    # 9. ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ПОЛНОСТЬЮ БРЕНДОВОЙ КАПСУЛЫ
    def create_full_brand_capsule() -> Optional[Dict[str, Any]]:
        """Создает капсулу полностью из товаров брендов"""
        capsule_items = []
        categories_needed = ['tops', 'bottoms', 'shoes', 'bags']
        
        if temperature < 15.0:
            categories_needed.append('outerwear')
            categories_needed.extend(['acc_scarf', 'acc_headwear'])
        else:
            categories_needed.extend(['acc_earrings', 'acc_belt'])
        
        for cat in categories_needed:
            if cat not in brand_by_category or not brand_by_category[cat]:
                continue
            
            available = [item for item in brand_by_category[cat] if item['id'] not in used_brand_items]
            if not available:
                available = brand_by_category[cat]
            
            item = min(available, key=lambda x: (brand_usage_count[x['id']], x.get('impressions_count', 0)))
            capsule_items.append(item)
            used_brand_items.add(item['id'])
            brand_usage_count[item['id']] += 1
        
        if len(capsule_items) >= 4:  # Минимум: верх, низ, обувь, сумка
            return {
                'id': 'brand_full',
                'items': capsule_items,
                'name': 'Образ от LiMango',
                'has_brand_item': True,
                'is_brand_capsule': True,
                'brand_items_count': len(capsule_items)
            }
        return None
    
    # 10. ПОДМЕШИВАНИЕ
    print(f"  🔄 Начинаем подмешивание V5...")
    
    # 10.1. Капсулы с 1 товаром (6 шт)
    for idx, capsule in one_brand_capsules:
        mix_n_items_into_capsule(idx, capsule, 1)
    
    # 10.2. Капсулы с 2 товарами (3 шт)
    for idx, capsule in two_brand_capsules:
        mix_n_items_into_capsule(idx, capsule, 2)
    
    # 10.3. Капсулы с 3 товарами (3 шт)
    for idx, capsule in three_brand_capsules:
        mix_n_items_into_capsule(idx, capsule, 3)
    
    # 10.4. Полная брендовая капсула (1 шт)
    result_capsules = user_capsules[:19]  # Берем только первые 19
    
    full_brand = create_full_brand_capsule()
    if full_brand:
        result_capsules.append(full_brand)
        print(f"  ✅ Создана полная брендовая капсула с {full_brand['brand_items_count']} товарами")
    else:
        print(f"  ⚠️ Не удалось создать полную брендовую капсулу")
        # Добавляем 20-ю капсулу пользователя
        if len(user_capsules) >= 20:
            result_capsules.append(user_capsules[19])
    
    print(f"  📊 Итого подмешано {mixed_count} товаров брендов")
    print(f"  🔄 Использовано {len(used_brand_items)} уникальных товаров")
    
    return result_capsules

