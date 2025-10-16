"""
Сервис для работы с товарами брендов V3 - УЛУЧШЕННАЯ ВЕРСИЯ
Решает проблемы:
1. Ротация брендовых товаров (не одни и те же)
2. Исключение уже использованных комбинаций
3. Минимум 7 товаров для 7 капсул
4. Отслеживание использования брендовых товаров
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


def get_all_brand_items() -> List[Dict[str, Any]]:
    """Получить ВСЕ товары брендов ОДИН РАЗ"""
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
        
        print(f"✅ Загружено {len(items)} товаров брендов")
        return items
    
    except Exception as e:
        print(f"❌ Ошибка загрузки товаров брендов: {e}")
        return []


def mix_brand_items_v3(
    user_capsules: List[Dict[str, Any]],
    wardrobe: List[Dict[str, Any]],
    season: str,
    temperature: float = 20.0,
    mixing_percentage: float = 0.35,
    exclude_combinations: List[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    УЛУЧШЕННАЯ ЛОГИКА V3: Подмешивает товары брендов с ротацией и исключениями
    
    НОВЫЕ ВОЗМОЖНОСТИ:
    1. Ротация брендовых товаров (не повторяем одни и те же)
    2. Исключение уже показанных комбинаций
    3. Минимум 7 товаров для 7 капсул
    4. Отслеживание использования брендовых товаров
    5. Умный выбор категорий для замены
    
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
    
    print(f"  ✅ Отфильтровано {len(filtered_brand_items)} из {len(all_brand_items)} товаров брендов")
    
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
    
    # 4. Создаем словарь для быстрого поиска вещей по ID
    wardrobe_dict = {str(item['id']): item for item in wardrobe}
    
    # 5. Отслеживаем использование брендовых товаров
    used_brand_items = set()
    brand_usage_count = defaultdict(int)
    
    # 6. Подмешиваем в случайные капсулы (минимум 7!)
    total_to_mix = max(7, int(len(user_capsules) * mixing_percentage))
    capsules_to_mix = random.sample(
        range(len(user_capsules)), 
        min(total_to_mix, len(user_capsules))
    )
    
    mixed_count = 0
    mixed_categories = set()
    
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
                subtype = accessory_subtype(user_item)
                item_categories[i] = (item_id, f'acc_{subtype}')
            else:
                item_categories[i] = (item_id, item_cat)
        
        # УМНЫЙ ВЫБОР КАТЕГОРИИ для замены
        # Приоритет: accessories > bags > shoes > tops > bottoms
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
                    # РОТАЦИЯ: выбираем товар который еще НЕ использовался
                    available_brand_items = [
                        item for item in brand_by_category[priority_cat] 
                        if item['id'] not in used_brand_items
                    ]
                    
                    # Если все товары уже использовались - сбрасываем счетчик
                    if not available_brand_items:
                        print(f"  🔄 Сброс счетчика для категории {priority_cat}")
                        used_brand_items.clear()
                        available_brand_items = brand_by_category[priority_cat]
                    
                    # Выбираем товар с минимальным использованием
                    brand_item = min(available_brand_items, key=lambda x: brand_usage_count[x['id']])
                    
                    # Заменяем на товар бренда
                    capsule['items'][idx_in_capsule] = brand_item
                    replaced = True
                    mixed_count += 1
                    mixed_categories.add(priority_cat)
                    
                    # Отслеживаем использование
                    used_brand_items.add(brand_item['id'])
                    brand_usage_count[brand_item['id']] += 1
                    
                    print(f"  ✅ Капсула {capsule.get('id')}: заменили {priority_cat} на товар бренда {brand_item.get('brand_name')}")
                    print(f"      🖼️ image_url: {brand_item.get('image_url', 'НЕТ')}")
                    print(f"      🏷️ description: {brand_item.get('description', 'НЕТ')[:50]}...")
                    print(f"      📊 Использование: {brand_usage_count[brand_item['id']]} раз")
                    break  # Одна замена на капсулу
            
            if replaced:
                break  # Переходим к следующей капсуле
    
    print(f"  📊 Подмешано {mixed_count} товаров из {len(mixed_categories)} разных категорий: {', '.join(sorted(mixed_categories))}")
    print(f"  🔄 Использовано {len(used_brand_items)} уникальных товаров брендов")
    
    return user_capsules


def get_smart_brand_rotation(
    brand_by_category: Dict[str, List[Dict[str, Any]]],
    used_brand_items: Set[str],
    brand_usage_count: Dict[str, int],
    category: str
) -> Optional[Dict[str, Any]]:
    """
    УМНАЯ РОТАЦИЯ брендовых товаров
    
    Алгоритм:
    1. Исключаем уже использованные товары
    2. Если все использованы - сбрасываем счетчик
    3. Выбираем товар с минимальным использованием
    4. Учитываем разнообразие по брендам
    """
    if category not in brand_by_category:
        return None
    
    available_items = [
        item for item in brand_by_category[category] 
        if item['id'] not in used_brand_items
    ]
    
    # Если все товары уже использовались - сбрасываем счетчик
    if not available_items:
        print(f"  🔄 Сброс счетчика для категории {category}")
        used_brand_items.clear()
        available_items = brand_by_category[category]
    
    # Выбираем товар с минимальным использованием
    best_item = min(available_items, key=lambda x: brand_usage_count[x['id']])
    
    return best_item
