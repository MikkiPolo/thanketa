from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set, Tuple, Deque
from collections import defaultdict, deque
import re
import random

# ==============================
#    НОРМАЛИЗАЦИЯ КАТЕГОРИЙ
# ==============================

def translate_category(raw: str) -> str:
    """Локальная нормализация категорий для rule-engine.
    Возвращает одно из: tops,bottoms,dresses,outerwear,shoes,accessories,other
    """
    s = (raw or "").strip().lower().replace("ё", "е")

    tops = {"топ","топик","рубашка","поло","футболка","лонгслив","свитшот",
            "свитер","водолазка","блузка","кофта","джемпер","майка","hoodie","худи"}
    bottoms = {"брюки","юбка","джинсы","шорты","брюки-кюлоты","кюлоты"}
    dresses = {"платье","сарафан"}
    outer = {"куртка","пальто","пиджак","жакет","кардиган","бомбер","плащ","тренч"}
    shoes = {"обувь","туфли","ботинки","сапоги","кроссовки","сандалии","балетки",
             "кеды","лоферы","мокасины","ботильоны","мюли","сланцы","шлепки","шлепанцы"}
    accessories = {"сумка","рюкзак","шарф","шапка","пояс","ремень","украшения",
                   "часы","браслет","кольцо","серьги","ожерелье","кулон","цепочка","ободок",
                   "платок","галстук","очки","панама","бандана"}

    def in_set(wordset: Set[str]) -> bool:
        return any(w in s for w in wordset)

    if in_set(tops): return "tops"
    if in_set(bottoms): return "bottoms"
    if in_set(dresses): return "dresses"
    if in_set(outer): return "outerwear"
    if in_set(shoes): return "shoes"
    if in_set(accessories): return "accessories"
    return "other"

# ==============================
#           ПАЛИТРЫ
# ==============================

NEUTRALS = {
    "белый","молочный","кремовый","экрю","бежевый","песочный","рыжий",
    "коричневый","темно-коричневый","карамель","хаки","серый","светло-серый",
    "чёрный","черный","деним","светло-голубой","светло-коричневый","табачный"
}
WARM_AUTUMN = NEUTRALS | {"оливковый","оливка","терракотовый","горчичный","кирпичный","охра","шоколадный","медный","бронзовый","бордовый"}
WARM_SPRING = NEUTRALS | {"персиковый","коралловый","абрикосовый","теплый розовый","тёплый розовый","светло-оливковый","теплый зеленый","теплый зелёный","светло-лимонный","мятный"}
COOL_SUMMER = NEUTRALS | {"пудрово-розовый","лавандовый","голубой","пыльно-голубой","стальной","сиреневый","пастельно-синий","пыльная роза","тауп"}
COOL_WINTER = NEUTRALS | {"чисто-белый","холодный черный","холодный чёрный","изумруд","сапфир","рубиновый","фуксия","электрик","холодный синий","винный"}

PALETTES_12 = {
    "светлая весна":  WARM_SPRING | {"светло-персиковый","бледно-коралловый","светло-мятный"},
    "тёплая весна":   WARM_SPRING | {"медовый","соломенный"},
    "яркая весна":    WARM_SPRING | {"яркий коралл","яркий мятный","яркий абрикос"},
    "светлое лето":   COOL_SUMMER  | {"бледно-розовый","ледяной голубой"},
    "холодное лето":  COOL_SUMMER  | {"стальной синий","прохладный розовый","серо-голубой"},
    "мягкое лето":    COOL_SUMMER  | {"пастельный лиловый"},
    "тёмная осень":   WARM_AUTUMN  | {"темный оливковый","горький шоколад"},
    "тёплая осень":   WARM_AUTUMN  | {"тыквенный","темно-горчичный","жженый оранж"},
    "мягкая осень":   WARM_AUTUMN  | {"шалфей","пыльный персик"},
    "холодная зима":  COOL_WINTER  | {"ледяная фуксия","ледяной розовый","холодный изумруд"},
    "яркая зима":     COOL_WINTER  | {"ярко-изумрудный","ультрамарин"},
    "тёмная зима":    COOL_WINTER  | {"глубокий синий"},
}

def palette_for_cvetotip(raw: Optional[str]) -> Set[str]:
    s = (raw or "").strip().lower().replace("ё","е")
    if "осен" in s: base = WARM_AUTUMN
    elif "весн" in s: base = WARM_SPRING
    elif "лет" in s: base = COOL_SUMMER
    elif "зим" in s: base = COOL_WINTER
    else: base = NEUTRALS
    for k,v in PALETTES_12.items():
        if k in s: return v
    if "осен" in s:
        if "мягк" in s: return PALETTES_12["мягкая осень"]
        if "темн" in s: return PALETTES_12["тёмная осень"]
        if "тепл" in s: return PALETTES_12["тёплая осень"]
    if "весн" in s:
        if "ярк" in s: return PALETTES_12["яркая весна"]
        if "свет" in s: return PALETTES_12["светлая весна"]
        if "тепл" in s: return PALETTES_12["тёплая весна"]
    if "лет" in s:
        if "мягк" in s: return PALETTES_12["мягкое лето"]
        if "свет" in s: return PALETTES_12["светлое лето"]
        if "холод" in s:return PALETTES_12["холодное лето"]
    if "зим" in s:
        if "ярк" in s: return PALETTES_12["яркая зима"]
        if "темн" in s: return PALETTES_12["тёмная зима"]
        if "холод" in s:return PALETTES_12["холодная зима"]
    return base

# ==============================
#     ВСПОМОГАТЕЛЬНОЕ
# ==============================

def norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()

COLOR_WORDS = sorted(
    set().union(*PALETTES_12.values()) | NEUTRALS | {
        "розовый","бордовый","горчичный","охра","хаки","оливка","индиго",
        "бежево-розовый","бежево-коричневый","рыже-коричневый","кофейный","карамельный"
    }, key=len, reverse=True
)
COLOR_RX = re.compile("|".join(map(re.escape, COLOR_WORDS)), re.I)

def extract_color(item: Dict[str,Any]) -> str:
    for key in ("color","цвет","description","описание","name","название"):
        val = item.get(key)
        if not val: continue
        m = COLOR_RX.search(str(val))
        if m: return m.group(0).lower()
    return ""

def is_season_ok(item: Dict[str,Any], season_hint: str, temp_c: float) -> bool:
    season = norm(item.get("season") or item.get("сезон"))
    if not season: return True
    if "всесезон" in season: return True
    if "лет" in season and "лет" in norm(season_hint): return True
    if "зим" in season and temp_c <= 7: return True
    if ("весн" in season or "осен" in season) and 5 <= temp_c <= 18: return True
    d = norm(item.get("description") or item.get("описание"))
    if any(k in d for k in ["лёгк","легк","шифон","лен","льнян"]) and temp_c >= 18: return True
    if any(k in d for k in ["шерст","плотн"]) and temp_c <= 10: return True
    return False

def normalize_style(pred: Optional[str]) -> str:
    s = norm(pred)
    mapping = {
        "повседневный":"Повседневный","casual":"Повседневный","кэжуал":"Повседневный",
        "минимализм":"Минимализм","минималистичный":"Минимализм",
        "спорт-шик":"Спорт-шик","sport-chic":"Спорт-шик",
        "романтичный":"Романтичный","деловой":"Деловой","классический":"Классический",
        "стрит":"Стрит","street":"Стрит","бизнес-кэжуал":"Бизнес-кэжуал",
    }
    return mapping.get(s, "Повседневный")

def is_style_ok(item: Dict[str,Any], target_style: str) -> bool:
    desc = norm(item.get("description") or item.get("описание"))
    group = translate_category(item.get("category",""))
    if target_style == "Минимализм":
        bad = ("принт","клетк","цветоч","бахром","стразы","аппликац")
        return not any(w in desc for w in bad)
    if target_style in ("Деловой","Бизнес-кэжуал"):
        if group == "shoes" and any(k in desc for k in ("кроссов","кеды","сланцы","шлеп")):
            return False
        if group == "tops" and "футбол" in desc:
            return False
        return True
    return True

def figure_rules(figura_raw: str) -> Dict[str, Set[str]]:
    f = norm(figura_raw)
    if any(k in f for k in ["перевернут","обрат","инверт"]) and "треуг" in f:
        return {"top_bad":{"пышные рукава","жесткие плечи","широкие плечи"},
                "top_good":{"v-образ","мягкий","драпиров","спущенное плечо"},
                "bottom_good":{"а-сил","расклеш","клеш","прямой","свободн","макси","бермуд"},
                "dress_good":{"а-сил","пояс","притал","v-образ","расклеш"}}
    if any(k in f for k in ["треуг","груша"]):
        return {"top_good":{"объем","структур","плечики","v-образ","квадратный вырез"},
                "bottom_bad":{"облегающ по бедрам","узкие по бедрам"},
                "bottom_good":{"а-сил","расклеш","прямой","средняя посадка","высокая посадка"},
                "dress_good":{"а-сил","притал","v-образ"}}
    if "песоч" in f:
        return {"overall_good":{"притал","пояс"},
                "top_good":{"облегающ","полупритал"},
                "bottom_good":{"прямой","слегка расклеш","высокая посадка"},
                "dress_good":{"притал","облегающ","запах"}}
    if any(k in f for k in ["овал","яблок"]):
        return {"top_good":{"v-образ","легкий оверсайз","драпиров","вертикаль"},
                "top_bad":{"облегающ живот","короткие топы"},
                "bottom_good":{"прямой","слегка расклеш","средняя посадка"},
                "dress_good":{"запах","эмпайр","a-сил","v-образ"}}
    if "прямоуг" in f or "атлет" in f:
        return {"overall_good":{"пояс","притал"},
                "top_good":{"объем сверху","баска","драпиров"},
                "bottom_good":{"клеш","а-сил","высокая посадка"},
                "dress_good":{"притал","запах","а-сил"}}
    return {}

def figure_pass(group: str, desc: str, rules: Dict[str,Set[str]]) -> bool:
    d = norm(desc)
    if group == "tops":
        if "top_bad" in rules and any(k in d for k in rules["top_bad"]): return False
        if "top_good" in rules and any(k in d for k in rules["top_good"]): return True
    if group == "bottoms":
        if "bottom_bad" in rules and any(k in d for k in rules["bottom_bad"]): return False
        if "bottom_good" in rules and any(k in d for k in rules["bottom_good"]): return True
    if group == "dresses":
        if "dress_good" in rules and any(k in d for k in rules["dress_good"]): return True
    if "overall_good" in rules and any(k in d for k in rules["overall_good"]): return True
    return True

def accessory_subtype(item: Dict[str,Any]) -> str:
    c = norm(item.get("category"))
    d = norm(item.get("description") or item.get("описание"))
    s = c + " " + d
    if "сумк" in s or "рюкзак" in s: return "bag"
    if "ремень" in s or "пояс" in s: return "belt"
    if "серьг" in s: return "earrings"
    if "брасл" in s: return "bracelet"
    if "колье" in s or "ожерел" in s or "кулон" in s or "цепоч" in s: return "necklace"
    if "кольц" in s: return "ring"
    if "часы" in s: return "watch"
    if "платок" in s or "шарф" in s: return "scarf"
    if "галстук" in s: return "tie"
    if "шапк" in s or "панам" in s or "ободок" in s or "шляп" in s: return "headwear"
    if "очки" in s: return "glasses"
    return "other"

def color_ok_for_palette(color: str, palette: Set[str]) -> bool:
    c = norm(color)
    return (c in palette) or (c in NEUTRALS) or (c == "")

def allowed_item(
    item: Dict[str,Any],
    season_hint: str, temp_c: float,
    target_style: str, figura: str,
    banned_ids: Set[str],
    allowed_ids: Optional[Set[str]],
    color_palette: Set[str]
) -> bool:
    iid = str(item.get("id") or item.get("ID") or item.get("Id") or "")
    if not iid or iid in banned_ids: return False
    if allowed_ids and iid not in allowed_ids: return False
    group = translate_category(item.get("category",""))
    if group == "other": return False
    if not is_season_ok(item, season_hint, temp_c): return False
    if not is_style_ok(item, target_style): return False
    if group in ("tops","bottoms","dresses"):
        if not color_ok_for_palette(extract_color(item), color_palette): return False
    if not figure_pass(group, item.get("description",""), figure_rules(figura)): return False
    return True

@dataclass
class Capsule:
    id: str
    name: str
    items: List[str]
    description: str

def generate_capsules(
    wardrobe_items: List[Dict[str,Any]],
    *,
    season_hint: str = "Лето",
    temp_c: float = 22.0,
    predpochtenia: str = "Повседневный",
    figura: str = "Прямоугольник",
    cvetotip: str = "Теплая осень",
    banned_ids: Optional[List[str]] = None,
    allowed_ids: Optional[List[str]] = None,
    max_per_item: int = 3,
    acc_per_outfit: Tuple[int,int] = (1,2),
    include_outerwear_below: float = 18.0,
    max_total: Optional[int] = None,
    exclude_combinations: Optional[List[List[str]]] = None
) -> Dict[str, Any]:

    target_style = normalize_style(predpochtenia)
    palette = palette_for_cvetotip(cvetotip)
    ban = set(banned_ids or [])
    allow = set(allowed_ids) if allowed_ids else None

    pool = [it for it in wardrobe_items if allowed_item(
        it, season_hint, temp_c, target_style, figura, ban, allow, palette
    )]

    by_group: Dict[str, List[Dict[str,Any]]] = defaultdict(list)
    for it in pool:
        by_group[translate_category(it.get("category",""))].append(it)

    tops     = by_group["tops"]
    bottoms  = by_group["bottoms"]
    dresses  = by_group["dresses"]
    outer    = by_group["outerwear"]
    shoes    = by_group["shoes"]
    accs     = by_group["accessories"]

    if not shoes:
        return {"categories":[{"id":"casual","name":target_style,"capsules":[],"fullCapsules":[]}]} 

    # Перемешиваем пулы для разнообразия на каждом запросе
    random.shuffle(shoes)
    random.shuffle(tops)
    random.shuffle(bottoms)
    random.shuffle(dresses)
    random.shuffle(outer)

    shoes_q: Deque[Dict[str,Any]] = deque(shoes)
    tops_q: Deque[Dict[str,Any]] = deque(tops)
    bottoms_q: Deque[Dict[str,Any]] = deque(bottoms)
    dresses_q: Deque[Dict[str,Any]] = deque(dresses)
    outer_q: Deque[Dict[str,Any]] = deque(outer)

    acc_by_type: Dict[str, Deque[Dict[str,Any]]] = defaultdict(deque)
    for a in accs:
        acc_by_type[accessory_subtype(a)].append(a)
    acc_type_ring: Deque[str] = deque(sorted(acc_by_type.keys()))

    used_count: Dict[str,int] = defaultdict(int)
    produced: Set[Tuple[str,...]] = set()
    # Инициализируем множеством уже показанных комбинаций, чтобы не повторяться
    if exclude_combinations:
        try:
            for combo in exclude_combinations:
                if isinstance(combo, list) and combo:
                    key = tuple(sorted(str(i) for i in combo))
                    produced.add(key)
        except Exception:
            pass
    out: List[Capsule] = []

    def can_take(item_id: str) -> bool:
        return used_count[item_id] < max_per_item

    def mark(items: List[Dict[str,Any]]):
        for i in items:
            used_count[str(i["id")]] += 1

    def unique_key(items: List[Dict[str,Any]]) -> Tuple[str,...]:
        return tuple(sorted(str(i["id"]) for i in items if i))

    def name_for(items: List[Dict[str,Any]]) -> str:
        ids = [translate_category(i["category"]) for i in items]
        return "Платье — готовый образ" if "dresses" in ids else "Повседневный сет"

    def descr_for(items: List[Dict[str,Any]]) -> str:
        roles = []
        for x in items:
            roles.append(translate_category(x["category"]))
        return " + ".join(sorted(set(roles))) + "; аксессуары включены."

    def pick_from_queue(q: Deque[Dict[str,Any]]) -> Optional[Dict[str,Any]]:
        if not q: return None
        for _ in range(len(q)):
            it = q[0]; q.rotate(-1)
            if can_take(str(it["id"])):
                return it
        return None

    def pick_accessories(k_min: int, k_max: int) -> List[Dict[str,Any]]:
        if not acc_by_type: return []
        target = random.randint(max(0,k_min), max(k_min,k_max))
        got: List[Dict[str,Any]] = []
        tries = 0
        while len(got) < target and acc_type_ring and tries < 5 * len(acc_type_ring):
            tries += 1
            t = acc_type_ring[0]; acc_type_ring.rotate(-1)
            dq = acc_by_type.get(t)
            if not dq: continue
            picked = False
            for _ in range(len(dq)):
                cand = dq[0]; dq.rotate(-1)
                iid = str(cand["id"])
                if can_take(iid) and all(accessory_subtype(x) != t for x in got):
                    got.append(cand)
                    picked = True
                    break
            if not picked:
                if all(not can_take(str(x["id"])) for x in list(dq)):
                    try:
                        acc_type_ring.remove(t)
                    except ValueError:
                        pass
        return got

    def need_outerwear() -> bool:
        return temp_c < include_outerwear_below and bool(outer_q)

    def commit(items: List[Dict[str,Any]]):
        if not any(translate_category(x["category"])=="shoes" for x in items):
            return False
        key = unique_key(items)
        if key in produced:
            return False
        for i in items:
            if not can_take(str(i["id"])):
                return False
        for i in items:
            used_count[str(i["id"])] += 1
        cid = f"c{len(out)+1}"
        out.append(Capsule(cid, name_for(items), [str(i["id"]) for i in items], descr_for(items)))
        produced.add(key)
        return True

    made_any = True
    while made_any:
        made_any = False
        if max_total and len(out) >= max_total: break

        if dresses_q and shoes_q:
            for _ in range(len(dresses_q)):
                d = pick_from_queue(dresses_q)
                if not d: break
                for __ in range(len(shoes_q)):
                    sh = pick_from_queue(shoes_q)
                    if not sh: break
                    items = [d, sh]
                    ow = pick_from_queue(outer_q) if need_outerwear() else None
                    if ow: items.append(ow)
                    items.extend(pick_accessories(acc_per_outfit[0], acc_per_outfit[1]))
                    if commit(items):
                        made_any = True
                        if max_total and len(out) >= max_total: break
                if max_total and len(out) >= max_total: break

        if tops_q and bottoms_q and shoes_q:
            for _ in range(len(bottoms_q)):
                b = pick_from_queue(bottoms_q)
                if not b: break
                for __ in range(len(tops_q)):
                    t = pick_from_queue(tops_q)
                    if not t: break
                    sh = pick_from_queue(shoes_q)
                    if not sh:
                        break
                    items = [t, b, sh]
                    ow = pick_from_queue(outer_q) if need_outerwear() else None
                    if ow: items.append(ow)
                    items.extend(pick_accessories(acc_per_outfit[0], acc_per_outfit[1]))
                    if commit(items):
                        made_any = True
                        if max_total and len(out) >= max_total: break
                if max_total and len(out) >= max_total: break

    capsules_json = [{"id": c.id, "name": c.name, "items": c.items, "description": c.description} for c in out]
    return {
        "categories": [
            {"id":"casual","name":target_style,"capsules":capsules_json,"fullCapsules":capsules_json}
        ]
    }


