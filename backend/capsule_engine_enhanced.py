"""
Улучшенный движок генерации капсул с учетом:
- Цветовой гармонии
- Стилевых направлений
- Многослойности
- Поводов
- Балансировки силуэтов

БЕЗ использования GPT - только rule-based логика
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, deque
from capsule_engine_v2 import (
    translate_category, 
    accessory_subtype
)

# Используем V6 для генерации базовых капсул (правильная логика)
from capsule_engine_v6 import generate_capsules
from style_analyzer import (
    extract_colors,
    are_colors_harmonious,
    get_color_palette,
    detect_style,
    are_styles_compatible,
    detect_pattern,
    check_pattern_compatibility,
    detect_silhouette,
    check_silhouette_balance,
    detect_occasion,
    check_metal_consistency,
    score_capsule,
    NEUTRAL_COLORS,
    BRIGHT_COLORS
)


def generate_enhanced_capsules(
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
    Генерирует улучшенные капсулы с учетом стиля, цвета и гармонии
    
    Этапы:
    1. Генерируем базовые капсулы через v2 (50 штук)
    2. Оцениваем каждую капсулу по критериям
    3. Сортируем по оценке
    4. Группируем по поводам
    5. Возвращаем топ-20 лучших
    """
    
    print(f"🎨 Запуск улучшенной генерации капсул (enhanced engine)")
    print(f"   Сезон: {season_hint}, температура: {temp_c}°C")
    
    # ШАГ 1: Генерируем капсулы через V6 (правильная логика)
    print(f"📦 Генерируем {max_total} базовых капсул через V6...")
    
    base_capsules = generate_capsules(
        wardrobe_items=wardrobe_items,
        season_hint=season_hint,
        temp_c=temp_c,
        predpochtenia=predpochtenia,
        figura=figura,
        cvetotip=cvetotip,
        banned_ids=banned_ids,
        allowed_ids=allowed_ids,
        max_total=max_total  # Генерируем ровно 20 капсул
    )
    
    # Извлекаем капсулы из структуры v2
    all_capsules = []
    if 'categories' in base_capsules:
        for category in base_capsules['categories']:
            all_capsules.extend(category.get('fullCapsules', []))
    
    print(f"✅ Сгенерировано {len(all_capsules)} базовых капсул")
    
    if len(all_capsules) == 0:
        print("⚠️ Не удалось сгенерировать капсулы")
        return base_capsules
    
    # ШАГ 2: Обогащаем каждую капсулу данными о вещах
    print(f"🔍 Обогащаем капсулы данными о вещах...")
    
    wardrobe_dict = {str(item['id']): item for item in wardrobe_items}
    enriched_capsules = []
    
    for capsule in all_capsules:
        item_ids = capsule.get('items', [])
        items_full = []
        
        for item_id in item_ids:
            # Поддержка как строковых ID, так и объектов (для товаров брендов)
            if isinstance(item_id, dict):
                items_full.append(item_id)
            else:
                item = wardrobe_dict.get(str(item_id))
                if item:
                    items_full.append(item)
        
        if len(items_full) > 0:
            enriched_capsules.append({
                **capsule,
                'items_full': items_full
            })
    
    # ШАГ 3: Оцениваем каждую капсулу
    print(f"⭐ Оцениваем капсулы по критериям...")
    
    scored_capsules = []
    for capsule in enriched_capsules:
        score_data = score_capsule(capsule['items_full'], season_hint, temp_c)
        
        scored_capsules.append({
            **capsule,
            'score': score_data['total_score'],
            'score_details': score_data,
            'occasion': score_data['occasion'],
            'palette': score_data['palette']
        })
    
    # ШАГ 4: Сортируем по оценке (лучшие первыми)
    scored_capsules.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"📊 Топ-5 капсул по оценке:")
    for i, cap in enumerate(scored_capsules[:5], 1):
        print(f"   {i}. {cap.get('name', 'Капсула')}: {cap['score']}/100 ({cap['occasion']}, {cap['palette']})")
    
    # ШАГ 5: Группируем по поводам для разнообразия
    by_occasion = defaultdict(list)
    for cap in scored_capsules:
        by_occasion[cap['occasion']].append(cap)
    
    print(f"🎯 Распределение по поводам:")
    for occasion, caps in by_occasion.items():
        print(f"   {occasion}: {len(caps)} капсул")
    
    # ШАГ 6: Выбираем топ-20 с балансом по поводам
    final_capsules = []
    
    # Сначала берем лучшие из каждого повода (для разнообразия)
    occasions = list(by_occasion.keys())
    round_robin_index = 0
    
    while len(final_capsules) < max_total and any(by_occasion[occ] for occ in occasions):
        occasion = occasions[round_robin_index % len(occasions)]
        
        if by_occasion[occasion]:
            final_capsules.append(by_occasion[occasion].pop(0))
        
        round_robin_index += 1
    
    # Если не хватило - добираем оставшиеся лучшие
    if len(final_capsules) < max_total:
        remaining = [cap for caps in by_occasion.values() for cap in caps]
        remaining.sort(key=lambda x: x['score'], reverse=True)
        final_capsules.extend(remaining[:max_total - len(final_capsules)])
    
    # ШАГ 7: Добавляем иконки поводов к названиям
    occasion_icons = {
        'офис': '🏢',
        'прогулка': '☕',
        'вечер': '🍷',
        'спорт': '🏃',
        'повседневный': '👗'
    }
    
    for cap in final_capsules:
        occasion = cap.get('occasion', 'повседневный')
        icon = occasion_icons.get(occasion, '👗')
        original_name = cap.get('name', 'Капсула')
        
        # Обновляем название с иконкой и поводом
        cap['name'] = f"{icon} {original_name}"
        cap['description'] = f"{occasion.capitalize()} | Оценка: {cap['score']}/100 | {cap['palette']}"
    
    # ШАГ 8: Формируем результат в формате v2
    result = {
        'categories': [{
            'id': 'enhanced',
            'name': 'Стильные капсулы',
            'description': 'Капсулы с учетом цвета, стиля и гармонии',
            'fullCapsules': final_capsules[:max_total],
            'capsules': final_capsules[:max_total]
        }]
    }
    
    print(f"✨ Отобрано {len(final_capsules[:max_total])} лучших капсул")
    print(f"   Средняя оценка: {sum(c['score'] for c in final_capsules[:max_total]) / len(final_capsules[:max_total]):.1f}/100")
    
    return result


def add_layering_to_capsule(
    capsule: Dict[str, Any],
    wardrobe: List[Dict[str, Any]],
    temp_c: float
) -> Dict[str, Any]:
    """
    Добавляет дополнительные слои одежды в капсулу для многослойности
    
    Правила:
    - Холодно (<15°C): базовый слой + средний слой + верхняя одежда
    - Тепло (15-20°C): базовый слой + легкий средний слой
    - Жарко (>20°C): только базовый слой
    """
    items = capsule.get('items', [])
    items_full = capsule.get('items_full', [])
    
    # Проверяем какие слои уже есть
    has_base_layer = any(
        'футболк' in item.get('category', '').lower() or 
        'рубашк' in item.get('category', '').lower() or
        'блузк' in item.get('category', '').lower()
        for item in items_full
    )
    
    has_middle_layer = any(
        'свитер' in item.get('category', '').lower() or
        'кардиган' in item.get('category', '').lower() or
        'жилет' in item.get('category', '').lower()
        for item in items_full
    )
    
    has_outer_layer = any(
        translate_category(item.get('category', '')) == 'outerwear'
        for item in items_full
    )
    
    # Определяем что нужно добавить
    to_add = []
    
    if temp_c < 15 and not has_middle_layer and has_base_layer:
        # Холодно - добавляем средний слой (свитер, кардиган)
        middle_candidates = [
            item for item in wardrobe 
            if any(k in item.get('category', '').lower() for k in ['свитер', 'кардиган', 'жилет'])
            and str(item['id']) not in [str(i) if isinstance(i, str) else str(i.get('id')) for i in items]
        ]
        if middle_candidates:
            to_add.append(random.choice(middle_candidates))
    
    # Добавляем новые слои
    if to_add:
        new_items = list(items)
        new_items_full = list(items_full)
        
        for item in to_add:
            new_items.append(str(item['id']))
            new_items_full.append(item)
        
        return {
            **capsule,
            'items': new_items,
            'items_full': new_items_full,
            'has_layering': True
        }
    
    return capsule


def filter_by_color_harmony(
    capsules: List[Dict[str, Any]],
    min_score: int = 50
) -> List[Dict[str, Any]]:
    """
    Фильтрует капсулы по цветовой гармонии
    
    Оставляет только капсулы с оценкой >= min_score
    """
    filtered = [cap for cap in capsules if cap.get('score', 0) >= min_score]
    
    print(f"🎨 Фильтрация по цветовой гармонии: {len(filtered)}/{len(capsules)} прошли (min_score={min_score})")
    
    return filtered

