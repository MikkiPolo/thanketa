from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set, Tuple, Deque
from collections import defaultdict, deque
import random

# Импортируем необходимые функции из capsule_engine_v2
from capsule_engine_v2 import (
    translate_category, 
    is_season_ok, 
    is_style_ok, 
    figure_rules, 
    figure_pass,
    color_ok_for_palette,
    palette_for_cvetotip,
    extract_color,
    accessory_subtype,
    norm,
    allowed_item,
    normalize_style
)

@dataclass
class ItemCapsule:
    id: str
    name: str
    items: List[str]
    description: str

def pick_accessories_for_capsule(
    accs: List[Dict[str,Any]], 
    acc_per_outfit: Tuple[int,int], 
    used_items: Set[str]
) -> List[Dict[str,Any]]:
    """Выбирает аксессуары для капсулы, используя логику из capsule_engine_v2"""
    if not accs:
        return []
    
    # Группируем аксессуары по типам
    acc_by_type: Dict[str, Deque[Dict[str,Any]]] = defaultdict(deque)
    for a in accs:
        acc_by_type[accessory_subtype(a)].append(a)
    
    acc_type_ring: Deque[str] = deque(sorted(acc_by_type.keys()))
    
    target = random.randint(max(0, acc_per_outfit[0]), max(acc_per_outfit[0], acc_per_outfit[1]))
    got: List[Dict[str,Any]] = []
    tries = 0
    
    while len(got) < target and acc_type_ring and tries < 5 * len(acc_type_ring):
        tries += 1
        t = acc_type_ring[0]
        acc_type_ring.rotate(-1)
        dq = acc_by_type.get(t)
        if not dq:
            continue
        
        picked = False
        for _ in range(len(dq)):
            cand = dq[0]
            dq.rotate(-1)
            iid = str(cand["id"])
            if iid not in used_items and all(accessory_subtype(x) != t for x in got):
                got.append(cand)
                picked = True
                break
        
        if not picked:
            if all(str(x["id"]) in used_items for x in list(dq)):
                try:
                    acc_type_ring.remove(t)
                except ValueError:
                    pass
    
    return got

def generate_capsules_from_item(
    wardrobe_items: List[Dict[str,Any]],
    base_item: Dict[str,Any],
    *,
    season_hint: str,
    temp_c: float,
    predpochtenia: str,
    figura: str,
    cvetotip: str,
    excluded_items: Optional[List[str]] = None,
    max_capsules: int = 10,
    acc_per_outfit: Tuple[int,int] = (1,2),
    include_outerwear_below: float = 18.0
) -> Dict[str, Any]:
    """
    Генерирует капсулы на основе конкретной вещи, используя логику из capsule_engine_v2.
    
    Args:
        wardrobe_items: Весь гардероб пользователя
        base_item: Базовая вещь, вокруг которой строятся капсулы
        season_hint: Сезонная подсказка
        temp_c: Температура
        predpochtenia: Предпочтения по стилю
        figura: Тип фигуры
        cvetotip: Цветотип
        excluded_items: Исключенные вещи
        max_capsules: Максимальное количество капсул
        acc_per_outfit: Количество аксессуаров на образ
        include_outerwear_below: Температура, ниже которой добавляется верхняя одежда
    
    Returns:
        Словарь с категориями и капсулами
    """
    
    # Инициализация
    target_style = normalize_style(predpochtenia)
    palette = palette_for_cvetotip(cvetotip)
    excluded_set = set(excluded_items or [])
    
    # Находим базовую вещь в гардеробе
    base_item_id = str(base_item.get("id") or base_item.get("ID") or base_item.get("Id") or "")
    if not base_item_id:
        return {"categories": []}
    
    # Исключаем базовую вещь и уже использованные из гардероба
    available_items = [
        item for item in wardrobe_items 
        if str(item.get("id") or item.get("ID") or item.get("Id") or "") not in excluded_set
        and str(item.get("id") or item.get("ID") or item.get("Id") or "") != base_item_id
    ]
    
    print(f'🎯 Генерация капсул для базовой вещи: {base_item_id}')
    print(f'📊 Доступно вещей: {len(available_items)} (исключено: {len(excluded_set)})')
    
    # Фильтруем доступные вещи по совместимости (используем логику из capsule_engine_v2)
    compatible_items = []
    for item in available_items:
        if allowed_item(item, season_hint, temp_c, target_style, figura, excluded_set, None, palette):
            compatible_items.append(item)
    
    print(f'✅ Совместимых вещей: {len(compatible_items)}')
    
    # Распределяем по категориям
    by_group: Dict[str, List[Dict[str,Any]]] = defaultdict(list)
    for item in compatible_items:
        category = translate_category(item.get("category", ""))
        if category != "other":
            by_group[category].append(item)
    
    # Получаем категории
    tops = by_group["tops"]
    bottoms = by_group["bottoms"] 
    dresses = by_group["dresses"]
    outer = by_group["outerwear"]
    shoes = by_group["shoes"]
    accs = by_group["accessories"]
    
    base_category_raw = base_item.get("category", "")
    base_category = translate_category(base_category_raw)
    print(f'🔍 Базовая вещь категории RAW: "{base_category_raw}"')
    print(f'🔍 Базовая вещь категории TRANSLATED: "{base_category}"')
    print(f'📦 Доступно: tops={len(tops)}, bottoms={len(bottoms)}, dresses={len(dresses)}, outer={len(outer)}, shoes={len(shoes)}, accs={len(accs)}')
    
    # Проверяем, что базовая вещь совместима
    if not allowed_item(base_item, season_hint, temp_c, target_style, figura, excluded_set, None, palette):
        print(f'⚠️ Базовая вещь не совместима с параметрами')
        return {"categories": []}
    
    # Генерируем капсулы в зависимости от категории базовой вещи
    capsules = []
    
    if base_category == "dresses":
        capsules = generate_dress_capsules_with_base(
            base_item, shoes, outer, accs, max_capsules, acc_per_outfit, include_outerwear_below, temp_c
        )
    elif base_category == "tops":
        capsules = generate_top_capsules_with_base(
            base_item, bottoms, shoes, outer, accs, max_capsules, acc_per_outfit, include_outerwear_below, temp_c
        )
    elif base_category == "bottoms":
        capsules = generate_bottom_capsules_with_base(
            base_item, tops, shoes, outer, accs, max_capsules, acc_per_outfit, include_outerwear_below, temp_c
        )
    elif base_category == "shoes":
        capsules = generate_shoe_capsules_with_base(
            base_item, tops, bottoms, outer, accs, max_capsules, acc_per_outfit, include_outerwear_below, temp_c
        )
    elif base_category == "outerwear":
        capsules = generate_outerwear_capsules_with_base(
            base_item, tops, bottoms, shoes, accs, max_capsules, acc_per_outfit, temp_c
        )
    else:
        print(f'⚠️ Неизвестная категория базовой вещи: {base_category}')
        return {"categories": []}
    
    print(f'✅ Сгенерировано капсул: {len(capsules)}')
    
    return {
        "categories": [{
            "name": "Образы с базовой вещью",
            "capsules": capsules
        }]
    }

def generate_dress_capsules_with_base(
    base_dress: Dict[str,Any],
    shoes: List[Dict[str,Any]],
    outer: List[Dict[str,Any]],
    accs: List[Dict[str,Any]],
    max_capsules: int,
    acc_per_outfit: Tuple[int,int],
    include_outerwear_below: float,
    temp_c: float
) -> List[Dict[str,Any]]:
    """Генерирует капсулы на основе платья с фиксированной базовой вещью"""
    capsules = []
    used_shoes = set()
    used_outer = set()
    used_accessories = set()
    
    random.shuffle(shoes)
    random.shuffle(outer)
    
    for i in range(min(max_capsules, len(shoes))):
        shoe = shoes[i]
        used_shoes.add(str(shoe["id"]))
        
        items = [base_dress, shoe]
        
        # Добавляем верхнюю одежду если нужно
        if temp_c < include_outerwear_below and len(outer) > 0:
            outer_item = outer[i % len(outer)]
            items.append(outer_item)
            used_outer.add(str(outer_item["id"]))
        
        # Добавляем аксессуары
        accessories = pick_accessories_for_capsule(accs, acc_per_outfit, used_items=used_accessories)
        items.extend(accessories)
        # Обновляем использованные аксессуары
        for acc in accessories:
            used_accessories.add(str(acc["id"]))
        
        capsule = {
            "id": f"dress_c{i+1}",
            "name": f"Образ с платьем #{i+1}",
            "items": [str(item["id"]) for item in items],
            "description": f"Платье + {translate_category(shoe.get('category', ''))}"
        }
        capsules.append(capsule)
    
    return capsules

def generate_top_capsules_with_base(
    base_top: Dict[str,Any],
    bottoms: List[Dict[str,Any]],
    shoes: List[Dict[str,Any]],
    outer: List[Dict[str,Any]],
    accs: List[Dict[str,Any]],
    max_capsules: int,
    acc_per_outfit: Tuple[int,int],
    include_outerwear_below: float,
    temp_c: float
) -> List[Dict[str,Any]]:
    """Генерирует капсулы на основе топа с фиксированной базовой вещью"""
    capsules = []
    used_combinations = set()
    used_accessories = set()
    
    random.shuffle(bottoms)
    random.shuffle(shoes)
    
    for i in range(min(max_capsules, len(bottoms), len(shoes))):
        bottom = bottoms[i]
        shoe = shoes[i]
        
        combination_key = (str(bottom["id"]), str(shoe["id"]))
        if combination_key in used_combinations:
            continue
        used_combinations.add(combination_key)
        
        items = [base_top, bottom, shoe]
        
        # Добавляем верхнюю одежду если нужно
        if temp_c < include_outerwear_below and len(outer) > 0:
            outer_item = outer[i % len(outer)]
            items.append(outer_item)
        
        # Добавляем аксессуары
        accessories = pick_accessories_for_capsule(accs, acc_per_outfit, used_items=used_accessories)
        items.extend(accessories)
        # Обновляем использованные аксессуары
        for acc in accessories:
            used_accessories.add(str(acc["id"]))
        
        capsule = {
            "id": f"top_c{i+1}",
            "name": f"Образ с топом #{i+1}",
            "items": [str(item["id"]) for item in items],
            "description": f"Топ + {translate_category(bottom.get('category', ''))} + {translate_category(shoe.get('category', ''))}"
        }
        capsules.append(capsule)
    
    return capsules

def generate_bottom_capsules_with_base(
    base_bottom: Dict[str,Any],
    tops: List[Dict[str,Any]],
    shoes: List[Dict[str,Any]],
    outer: List[Dict[str,Any]],
    accs: List[Dict[str,Any]],
    max_capsules: int,
    acc_per_outfit: Tuple[int,int],
    include_outerwear_below: float,
    temp_c: float
) -> List[Dict[str,Any]]:
    """Генерирует капсулы на основе низа с фиксированной базовой вещью"""
    capsules = []
    used_combinations = set()
    used_accessories = set()
    
    random.shuffle(tops)
    random.shuffle(shoes)
    
    for i in range(min(max_capsules, len(tops), len(shoes))):
        top = tops[i]
        shoe = shoes[i]
        
        combination_key = (str(top["id"]), str(shoe["id"]))
        if combination_key in used_combinations:
            continue
        used_combinations.add(combination_key)
        
        items = [base_bottom, top, shoe]
        
        # Добавляем верхнюю одежду если нужно
        if temp_c < include_outerwear_below and len(outer) > 0:
            outer_item = outer[i % len(outer)]
            items.append(outer_item)
        
        # Добавляем аксессуары
        accessories = pick_accessories_for_capsule(accs, acc_per_outfit, used_items=used_accessories)
        items.extend(accessories)
        # Обновляем использованные аксессуары
        for acc in accessories:
            used_accessories.add(str(acc["id"]))
        
        capsule = {
            "id": f"bottom_c{i+1}",
            "name": f"Образ с низом #{i+1}",
            "items": [str(item["id"]) for item in items],
            "description": f"Низ + {translate_category(top.get('category', ''))} + {translate_category(shoe.get('category', ''))}"
        }
        capsules.append(capsule)
    
    return capsules

def generate_shoe_capsules_with_base(
    base_shoe: Dict[str,Any],
    tops: List[Dict[str,Any]],
    bottoms: List[Dict[str,Any]],
    outer: List[Dict[str,Any]],
    accs: List[Dict[str,Any]],
    max_capsules: int,
    acc_per_outfit: Tuple[int,int],
    include_outerwear_below: float,
    temp_c: float
) -> List[Dict[str,Any]]:
    """Генерирует капсулы на основе обуви с фиксированной базовой вещью"""
    capsules = []
    used_combinations = set()
    used_accessories = set()
    
    random.shuffle(tops)
    random.shuffle(bottoms)
    
    for i in range(min(max_capsules, len(tops), len(bottoms))):
        top = tops[i]
        bottom = bottoms[i]
        
        combination_key = (str(top["id"]), str(bottom["id"]))
        if combination_key in used_combinations:
            continue
        used_combinations.add(combination_key)
        
        items = [base_shoe, top, bottom]
        
        # Добавляем верхнюю одежду если нужно
        if temp_c < include_outerwear_below and len(outer) > 0:
            outer_item = outer[i % len(outer)]
            items.append(outer_item)
        
        # Добавляем аксессуары
        accessories = pick_accessories_for_capsule(accs, acc_per_outfit, used_items=used_accessories)
        items.extend(accessories)
        # Обновляем использованные аксессуары
        for acc in accessories:
            used_accessories.add(str(acc["id"]))
        
        capsule = {
            "id": f"shoe_c{i+1}",
            "name": f"Образ с обувью #{i+1}",
            "items": [str(item["id"]) for item in items],
            "description": f"Обувь + {translate_category(top.get('category', ''))} + {translate_category(bottom.get('category', ''))}"
        }
        capsules.append(capsule)
    
    return capsules

def generate_outerwear_capsules_with_base(
    base_outerwear: Dict[str,Any],
    tops: List[Dict[str,Any]],
    bottoms: List[Dict[str,Any]],
    shoes: List[Dict[str,Any]],
    accs: List[Dict[str,Any]],
    max_capsules: int,
    acc_per_outfit: Tuple[int,int],
    temp_c: float
) -> List[Dict[str,Any]]:
    """Генерирует капсулы на основе верхней одежды с фиксированной базовой вещью"""
    capsules = []
    used_combinations = set()
    used_accessories = set()
    
    random.shuffle(tops)
    random.shuffle(bottoms)
    random.shuffle(shoes)
    
    for i in range(min(max_capsules, len(tops), len(bottoms), len(shoes))):
        top = tops[i]
        bottom = bottoms[i]
        shoe = shoes[i]
        
        combination_key = (str(top["id"]), str(bottom["id"]), str(shoe["id"]))
        if combination_key in used_combinations:
            continue
        used_combinations.add(combination_key)
        
        items = [base_outerwear, top, bottom, shoe]
        
        # Добавляем аксессуары
        accessories = pick_accessories_for_capsule(accs, acc_per_outfit, used_items=used_accessories)
        items.extend(accessories)
        # Обновляем использованные аксессуары
        for acc in accessories:
            used_accessories.add(str(acc["id"]))
        
        capsule = {
            "id": f"outerwear_c{i+1}",
            "name": f"Образ с верхней одеждой #{i+1}",
            "items": [str(item["id"]) for item in items],
            "description": f"Верхняя одежда + {translate_category(top.get('category', ''))} + {translate_category(bottom.get('category', ''))} + {translate_category(shoe.get('category', ''))}"
        }
        capsules.append(capsule)
    
    return capsules