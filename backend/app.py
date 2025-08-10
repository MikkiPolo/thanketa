from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
try:
    # Используем явную сессию и тюним маттинг для более качественной сегментации
    from rembg.bg import remove as _rembg_remove, new_session as _rembg_new_session
    _REMBG_SESSION = None

    def _ensure_rembg_session():
        global _REMBG_SESSION
        if _REMBG_SESSION is None:
            try:
                _REMBG_SESSION = _rembg_new_session(model_name='u2net')
                print('✅ rembg session initialized (u2net)')
            except Exception as _se:
                print(f'❌ rembg session init failed: {_se}')
                _REMBG_SESSION = None

    def remove_bg(image):
        """Удаляет фон, возвращая PIL.Image RGBA. В случае ошибки возвращает исходное изображение."""
        try:
            _ensure_rembg_session()
            kwargs = {}
            if _REMBG_SESSION is not None:
                kwargs.update({
                    'session': _REMBG_SESSION,
                    'alpha_matting': True,
                    'alpha_matting_foreground_threshold': 240,
                    'alpha_matting_background_threshold': 10,
                    'alpha_matting_erode_size': 10,
                    'post_process_mask': True,
                })
            out = _rembg_remove(image, **kwargs)
            # rembg.remove может вернуть bytes (PNG) — конвертируем в PIL.Image
            if isinstance(out, (bytes, bytearray)):
                buf = io.BytesIO(out)
                img = Image.open(buf)
                return img.convert('RGBA') if img.mode != 'RGBA' else img
            if isinstance(out, Image.Image):
                return out.convert('RGBA') if out.mode != 'RGBA' else out
            return image
        except Exception as _re:
            print(f'⚠️ rembg failed, returning original image: {_re}')
            return image
    REMBG_AVAILABLE = True
except Exception as _e:
    # rembg/onnxruntime not available in slim image; fall back to no-op
    def remove_bg(image):
        return image
    REMBG_AVAILABLE = False
from PIL import Image
import io
import base64
import uuid
import os
import requests
import asyncio
import threading
import time
from datetime import datetime
from dotenv import load_dotenv
from config import Config
from ai_wardrobe_analyzer import AIWardrobeAnalyzer, AIAnalyzerFactory, UserFeedback, AnalysisResult
import json
import hashlib
from typing import List, Dict, Any
import logging
from functools import lru_cache
import openai
import json as _json_for_cache

# Redis client (optional)
try:
    import redis as _redis
    _redis_client = _redis.from_url(getattr(Config, 'REDIS_URL', 'redis://localhost:6379'))
    _ = _redis_client.ping()
    print(f"✅ Redis подключен: {Config.REDIS_URL}")
except Exception as _re:
    print(f"⚠️ Redis недоступен или не сконфигурирован: {_re}")
    _redis_client = None

# Настройка логгера
logger = logging.getLogger(__name__)

# Поддержка HEIC файлов
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    print("✅ HEIC support enabled")
except ImportError:
    print("❌ HEIC support not available - install pillow-heif")

# Загружаем переменные окружения
load_dotenv()

# Валидируем конфигурацию
Config.validate_config()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB лимит

# Безопасные CORS настройки
ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:5174', 
    'http://localhost:5175',
    'http://192.168.1.42:5173',
    'http://192.168.1.42:5174',
    'http://192.168.1.42:5175',
    'http://192.168.1.42:*',  # Разрешаем любой порт с этого IP
    'https://linapolo.store',
    'http://linapolo.store'
]

# Добавляем origin из переменных окружения
if os.getenv('ALLOWED_ORIGIN'):
    ALLOWED_ORIGINS.append(os.getenv('ALLOWED_ORIGIN'))

CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# Добавляем логирование CORS
@app.before_request
def log_request_info():
    print(f"🌐 Request from: {request.origin}")
    print(f"🌐 Request headers: {dict(request.headers)}")
    print(f"🌐 Request method: {request.method}")
    print(f"🌐 Request URL: {request.url}")

# Инициализируем генератор капсул
try:
    if Config.AI_GENERATOR_TYPE == 'gpt':
        print(f"✅ Используем GPT-4o-mini для генерации капсул")
        capsule_generator = None
    else:
        generator_config = Config.get_generator_config()
        # Ленивая загрузка тяжёлых зависимостей только при необходимости
        from huggingface_generator import CapsuleGeneratorFactory  # noqa: WPS433
        capsule_generator = CapsuleGeneratorFactory.create_generator(
            Config.AI_GENERATOR_TYPE,
            **generator_config
        )
        print(f"✅ Генератор капсул инициализирован: {Config.AI_GENERATOR_TYPE}")
except Exception as e:
    print(f"❌ Ошибка инициализации генератора: {e}")
    capsule_generator = None

# Инициализируем AI анализатор гардероба
try:
    ai_analyzer = AIAnalyzerFactory.create_analyzer(
        ai_type=Config.AI_GENERATOR_TYPE,
        cache_url=Config.REDIS_URL if hasattr(Config, 'REDIS_URL') else "redis://localhost:6379"
    )
    print(f"✅ AI анализатор гардероба инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации AI анализатора: {e}")
    ai_analyzer = None

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'wardrobe-background-removal'
    })

@app.route('/remove-background', methods=['POST'])
def remove_background():
    """Удаление фона с изображения"""
    try:
        # Проверяем, что есть файл
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Проверяем тип файла
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, and WebP are supported'}), 400
        
        # Читаем изображение
        image = Image.open(file.stream)
        
        # Удаляем фон (если доступно); иначе возвращаем исходное
        result = remove_bg(image)
        
        # Конвертируем в байты
        img_byte_arr = io.BytesIO()
        result.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Возвращаем изображение
        return send_file(
            io.BytesIO(img_byte_arr),
            mimetype='image/png',
            as_attachment=True,
            download_name=f'no_background_{uuid.uuid4()}.png'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai-feedback', methods=['POST'])
def ai_feedback():
    """Прием обратной связи по AI анализу"""
    try:
        data = request.get_json(force=True)
        user_id = data.get('user_id', 'anonymous')
        item_id = data.get('item_id', '')
        rating = data.get('rating', 'neutral')
        correction = data.get('correction')

        # Собираем объекты для метрик
        feedback = UserFeedback(
            user_id=str(user_id),
            item_id=str(item_id),
            rating=rating,
            correction=correction,
            timestamp=datetime.now()
        )

        # Для простоты создаем пустой результат (точность возьмем из rating)
        # По умолчанию считаем типом GPT, если основной анализатор настроен как GPT, иначе rule_based
        inferred_ai_type = None
        try:
            from ai_wardrobe_analyzer import AIType
            inferred_ai_type = AIType.GPT if ai_analyzer and getattr(ai_analyzer, 'primary_ai', None) else AIType.RULE_BASED
        except Exception:
            inferred_ai_type = None

        analysis_result = AnalysisResult(
            category='feedback',
            season='',
            style='',
            colors=[],
            confidence=1.0 if rating == 'positive' else 0.1 if rating == 'negative' else 0.5,
            ai_type=inferred_ai_type,
            explanation=correction or '',
            timestamp=datetime.now()
        )

        # Записываем метрику
        if ai_analyzer and analysis_result.ai_type is not None:
            ai_analyzer.record_feedback(analysis_result, feedback)

        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Ошибка приема обратной связи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/ai-performance', methods=['GET'])
def ai_performance():
    """Возвращает агрегированные метрики AI"""
    try:
        if not ai_analyzer:
            return jsonify({'gpt': {'average_accuracy': 0.0, 'total_predictions': 0}})
        return jsonify(ai_analyzer.get_performance_stats())
    except Exception as e:
        print(f"❌ Ошибка метрик AI: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/ai-explanation', methods=['POST'])
def ai_explanation():
    """Возвращает краткое объяснение результата анализа"""
    try:
        data = request.get_json(force=True)
        analysis = data.get('analysis_result') or {}
        parts = []
        if analysis.get('category'):
            parts.append(f"Категория: {analysis['category']}")
        if analysis.get('season'):
            parts.append(f"Сезон: {analysis['season']}")
        if analysis.get('style'):
            parts.append(f"Стиль: {analysis['style']}")
        if analysis.get('color'):
            parts.append(f"Цвет: {analysis['color']}")
        explanation = ' • '.join(parts) or 'Анализ не содержит деталей'
        return jsonify({'explanation': explanation})
    except Exception as e:
        print(f"❌ Ошибка объяснения AI: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/wardrobe-recommendations', methods=['POST', 'OPTIONS'])
def wardrobe_recommendations():
    """Возвращает умные рекомендации по гардеробу на основе профиля и списка вещей.

    Тело запроса: { "profile": {...}, "wardrobe": [...] }
    Ответ: { "recommendations": "строка с пунктами рекомендаций" }
    """
    try:
        # Preflight CORS
        if request.method == 'OPTIONS':
            return ('', 204)
        data = request.get_json(force=True) or {}
        profile = data.get('profile') or {}
        wardrobe = data.get('wardrobe') or []

        if not wardrobe:
            return jsonify({
                'recommendations': 'Недостаточно данных для анализа. Сначала добавьте несколько вещей в гардероб.'
            })

        def build_fallback_recommendations() -> str:
            # Простые правила без ИИ
            recos = []
            figura = (profile.get('figura') or '')
            figura_lower = figura.lower()
            if figura_lower:
                if any(k in figura_lower for k in ['яблоко', 'o']):
                    recos.append('• Для типа фигуры «Яблоко» подойдут платья с завышенной талией и V-образный вырез')
                if any(k in figura_lower for k in ['треуголь', 'a']):
                    recos.append('• Сбалансируйте низ: выбирайте прямые/расклёшенные брюки и акцент на плечи')
                if any(k in figura_lower for k in ['песочн', 'x']):
                    recos.append('• Подчёркивайте талию ремнём и приталенными силуэтами')

            cvet = (profile.get('cvetotip') or '').lower()
            if cvet:
                if 'весн' in cvet or 'тёпл' in cvet or 'тепл' in cvet:
                    recos.append('• Тёплые оттенки (бежевый, персиковый, коралловый) подчеркнут цветотип')
                if 'лето' in cvet or 'холод' in cvet:
                    recos.append('• Холодные тона (голубой, серый, розовый) дадут свежесть образам')

            # Подсчёт категорий
            categories = {}
            for it in wardrobe:
                cat = (it.get('category') or '').strip()
                if cat:
                    categories[cat] = categories.get(cat, 0) + 1

            if len(wardrobe) < 20:
                recos.append('• Расширьте базовый гардероб: добавьте базовые топы, низы и универсальную обувь')
            if len(wardrobe) > 100:
                recos.append('• Сделайте ревизию: избавьтесь от вещей, которые не носите')

            accessories_count = sum(1 for it in wardrobe if (it.get('category') or '').lower() in [
                'сумка', 'украшения', 'аксессуары', 'пояс', 'шарф', 'часы'
            ])
            if accessories_count < 3:
                recos.append('• Добавьте аксессуары (ремень, сумка, украшения) — они собирают образ')

            if profile.get('like_zone'):
                recos.append(f"• Подчеркивайте {profile.get('like_zone')} акцентными деталями и посадкой")
            if profile.get('dislike_zone'):
                recos.append(f"• Для зоны {profile.get('dislike_zone')} выбирайте свободный крой и вертикальные линии")

            return '\n'.join(recos) if recos else '• Гардероб выглядит сбалансированным — продолжайте в том же духе'

        def build_unsuitable_items() -> list:
            """Определяет список вещей, которые могут не подходить, с краткой причиной."""
            unsuitable = []
            figura = (profile.get('figura') or '').lower()
            cvet = (profile.get('cvetotip') or '').lower()

            # Ключевые слова по цветотипам
            warm_keywords = ['оранж', 'желт', 'горчич', 'терракот', 'оливк', 'золот', 'коралл']
            cool_keywords = ['холодн', 'голуб', 'сине', 'серебр', 'фиолет', 'серый']

            # Ключевые слова по фигуре
            apple_bad = ['низкая посад', 'облегающ', 'узк', 'скинни', 'обтяг']
            inverted_bad = ['плечев', 'накладк', 'погоны', 'акцент на плеч']
            rectangle_bad = ['бесформ', 'оверсайз', 'прямой крой']

            for it in wardrobe:
                try:
                    desc = (it.get('description') or '').lower()
                    cat = (it.get('category') or '').lower()
                    reasons = []

                    # Проверка цветотипа
                    if cvet:
                        if 'холод' in cvet or 'зима' in cvet or 'лето' in cvet:
                            if any(k in desc for k in warm_keywords):
                                reasons.append('тёплые оттенки могут конфликтовать с холодным цветотипом')
                        if 'тёпл' in cvet or 'весн' in cvet or 'осен' in cvet:
                            if any(k in desc for k in cool_keywords):
                                reasons.append('холодные оттенки не рекомендуются при тёплом цветотипе')

                    # Проверка типа фигуры
                    if 'яблок' in figura or figura.endswith('o'):
                        if any(k in desc for k in apple_bad):
                            reasons.append('низкая посадка/сильно облегающие фасоны подчеркивают живот')
                    if 'перевернут' in figura or 'v' in figura:
                        if any(k in desc for k in inverted_bad):
                            reasons.append('дополнительный объём в плечах не рекомендуется при широких плечах')
                    if 'прямоуголь' in figura or 'h' in figura:
                        if any(k in desc for k in rectangle_bad):
                            reasons.append('бесформенный прямой крой скрывает талию')

                    if reasons:
                        unsuitable.append({
                            'id': str(it.get('id')),
                            'category': it.get('category', ''),
                            'description': it.get('description', ''),
                            'reason': '; '.join(reasons)
                        })
                except Exception:
                    continue

            # Ограничим список до 10 пунктов
            return unsuitable[:10]

        # Если доступен OPENAI_API_KEY — используем GPT
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                client = openai.OpenAI(api_key=api_key)
                
                # Готовим данные о вещах для анализа GPT
                items_for_model = []
                for it in wardrobe:
                    items_for_model.append({
                        'id': str(it.get('id')),
                        'category': it.get('category', ''),
                        'season': it.get('season', ''),
                        'description': it.get('description', '')
                    })

                system_prompt = (
                    "Ты — опытный персональный стилист. На основе профиля клиента и полного списка его вещей дай рекомендации и укажи вещи, которые НЕ подходят клиенту, с краткими причинами. "
                    "Отвечай СТРОГО валидным JSON без markdown."
                )
                user_prompt = (
                    "ПРОФИЛЬ:\n" + json.dumps(profile, ensure_ascii=False) + "\n\n" +
                    "ВЕЩИ:\n" + json.dumps(items_for_model, ensure_ascii=False) + "\n\n" +
                    "ЗАДАЧА: верни JSON строго такого вида: {\n"
                    "  \"recommendations\": \"строка с 5-10 пунктами, каждый начинается с '• ' (одной строкой с символом перевода строки между пунктами)\",\n"
                    "  \"unsuitable_items\": [ { \"id\": \"ID вещи из списка ВЕЩИ\", \"reason\": \"почему не подходит — кратко и по сути\" } ]\n"
                    "}. Без лишних ключей и без markdown. Если неподходящих вещей немного, верни пустой массив."
                )

                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=900
                )
                content = (resp.choices[0].message.content or '').strip()
                # Убираем возможные markdown-блоки
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

                try:
                    parsed = json.loads(content)
                    rec_text = (parsed.get('recommendations') or '').strip()
                    unsuitable_items = parsed.get('unsuitable_items') or []
                    # Нормализуем unsuitable_items к [{id, category, description, reason}]
                    id_to_item = {str(it.get('id')): it for it in wardrobe}
                    normalized_unsuitable = []
                    for u in unsuitable_items:
                        uid = str(u.get('id')) if isinstance(u, dict) else None
                        reason = u.get('reason') if isinstance(u, dict) else None
                        if uid and uid in id_to_item and reason:
                            src = id_to_item[uid]
                            normalized_unsuitable.append({
                                'id': uid,
                                'category': src.get('category', ''),
                                'description': src.get('description', ''),
                                'reason': reason
                            })
                    # Если GPT не вернул рекомендации, падём в фолбэк
                    if not rec_text:
                        rec_text = build_fallback_recommendations()
                    # Если GPT не вернул неподходящие — пусто (без эвристик, как просили)
                    return jsonify({ 'recommendations': rec_text, 'unsuitable_items': normalized_unsuitable })
                except Exception as parse_err:
                    print(f"❌ Парсинг JSON от GPT не удался: {parse_err}")
                    # Возвращаем текст как есть и пустой список неподходящих (без эвристик)
                    return jsonify({ 'recommendations': content, 'unsuitable_items': [] })
            except Exception as e:
                print(f"❌ Ошибка GPT рекомендаций: {e}")
                # Падает в фолбэк
                return jsonify({ 'recommendations': build_fallback_recommendations(), 'unsuitable_items': [] })

        # Если API ключа нет — фолбэк
        return jsonify({ 'recommendations': build_fallback_recommendations(), 'unsuitable_items': [] })
    except Exception as e:
        print(f"❌ Ошибка рекомендаций гардероба: {e}")
        return jsonify({ 'recommendations': 'Не удалось выполнить анализ. Попробуйте позже.', 'unsuitable_items': [] }), 200

@app.route('/analyze-wardrobe-item', methods=['POST'])
def analyze_wardrobe_item():
    """Анализ предмета гардероба с помощью AI"""
    try:
        # Проверяем, что есть файл
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided', 'success': False}), 400
        
        file = request.files['image']
        user_id = request.form.get('user_id', 'anonymous')
        
        # Проверяем тип файла
        allowed_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif')
        if not file.filename.lower().endswith(allowed_extensions):
            return jsonify({
                'error': 'Invalid file type. Only PNG, JPG, JPEG, WebP, HEIC are supported', 
                'success': False
            }), 400
        
        # Читаем содержимое файла в память
        file_content = file.read()
        
        # Проверяем размер файла (максимум 10MB)
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            return jsonify({
                'error': 'Файл слишком большой. Максимальный размер: 10MB', 
                'success': False
            }), 413
        
        # Создаем объект изображения из байтов
        try:
            image = Image.open(io.BytesIO(file_content))
            # Поправка ориентации по EXIF
            try:
                from PIL import ImageOps
                image = ImageOps.exif_transpose(image)
            except Exception:
                pass
            
            # Конвертируем HEIC в RGB если нужно
            if file.filename.lower().endswith(('.heic', '.heif')):
                # Конвертируем в RGB если изображение в другом формате
                if image.mode != 'RGB':
                    image = image.convert('RGB')
            
            # Убеждаемся, что изображение в формате RGB для дальнейшей обработки
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
                
        except Exception as e:
            print(f"❌ Ошибка открытия изображения: {e}")
            return jsonify({
                'error': f'Не удалось открыть изображение: {str(e)}', 
                'success': False
            }), 400
        
        # Уменьшаем изображение до разумного размера перед удалением фона
        try:
            max_side = 1024
            w, h = image.size
            if max(w, h) > max_side:
                image = image.copy()
                image.thumbnail((max_side, max_side))
        except Exception:
            pass

        # Удаляем фон (если доступно); иначе сохраняем как есть
        result_image = remove_bg(image)
        
        # Сжимаем и уменьшаем изображение перед base64 (JPEG 512x512)
        work_img = result_image
        # Сохраняем прозрачность, конвертируем в RGBA если нужно
        print(f"🔍 Режим изображения до конвертации: {work_img.mode}")
        if work_img.mode != 'RGBA':
            work_img = work_img.convert('RGBA')
            print(f"✅ Конвертировали в RGBA режим")

        work_img.thumbnail((512, 512))
        img_byte_arr = io.BytesIO()
        work_img.save(img_byte_arr, format='PNG', optimize=True)
        print(f"✅ Сохранили изображение в PNG формате с прозрачностью")
        img_byte_arr.seek(0)
        image_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # Если у нас есть AI анализатор, используем его
        analysis_result = None
        if ai_analyzer:
            try:
                # Передаем изображение в base64 для GPT Vision анализа
                analysis_result = ai_analyzer.analyze_item("", user_id, image_base64=image_base64)
                
                return jsonify({
                    'success': True,
                    'image_base64': image_base64,
                    'analysis': {
                        'category': analysis_result.category if analysis_result.category != 'не распознано' else '',
                        'season': analysis_result.season if analysis_result.season != 'не распознано' else '',
                        'description': analysis_result.explanation if analysis_result.explanation != 'GPT не смог распознать предмет' else '',
                        'color': ', '.join(analysis_result.colors) if analysis_result.colors and analysis_result.colors[0] != 'не распознано' else '',
                        'style': analysis_result.style if analysis_result.style != 'не распознано' else '',
                        'confidence': analysis_result.confidence
                    }
                })
            except Exception as e:
                print(f"❌ Ошибка AI анализа: {e}")
                # Возвращаем пустые поля если GPT не смог распознать
                return jsonify({
                    'success': True,
                    'image_base64': image_base64,
                    'analysis': {
                        'category': '',
                        'season': '',
                        'description': '',
                        'color': '',
                        'style': '',
                        'confidence': 0.0
                    }
                })
        
    except Exception as e:
        print(f"❌ Ошибка обработки изображения: {e}")
        return jsonify({
            'error': f'Ошибка обработки изображения: {str(e)}', 
            'success': False
        }), 500

@app.route('/generate-capsules', methods=['POST'])
def generate_capsules():
    """Генерация капсул гардероба"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        wardrobe = data.get('wardrobe', [])
        profile = data.get('profile', {})
        weather = data.get('weather', {})
        
        if not wardrobe:
            return jsonify({'error': 'No wardrobe items provided'}), 400
        
        # Ключ кэша по профилю+гардеробу+погоде
        try:
            cache_key_src = {
                'wardrobe': wardrobe,
                'profile': profile,
                'weather': weather
            }
            cache_key_hash = hashlib.sha256(_json_for_cache.dumps(cache_key_src, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
            cache_key = f"capsules:{cache_key_hash}"
        except Exception:
            cache_key = None

        # Попытка отдать из кэша (можно отключить флагом no_cache=true)
        no_cache = str(data.get('no_cache') or data.get('force_refresh') or '').lower() in ['1','true','yes']
        if _redis_client and cache_key and not no_cache:
            try:
                cached = _redis_client.get(cache_key)
                if cached:
                    print(f"🟢 CACHE HIT: {cache_key}")
                    cached_obj = json.loads(cached)
                    return jsonify(cached_obj)
            except Exception:
                print(f"⚠️ CACHE ERROR (read): {cache_key}")
        else:
            if no_cache:
                print("⛔ no_cache=true — пропускаем кэш")
            elif not _redis_client:
                print("⚠️ Redis недоступен — кэш пропущен")
            elif not cache_key:
                print("⚠️ cache_key не создан — кэш пропущен")

        # Generate capsules using AI (без кэша)
        capsules_payload = generate_capsules_with_ai(wardrobe, profile, weather)

        # Backward/forward compatible shape: flatten to {capsules, meta}
        if isinstance(capsules_payload, dict) and 'capsules' in capsules_payload:
            capsules_obj = capsules_payload.get('capsules')
            meta_obj = capsules_payload.get('meta', {})
        else:
            # fallback if helper returned plain structure
            capsules_obj = capsules_payload
            meta_obj = {}

        response_obj = {
            'capsules': capsules_obj,
            'meta': meta_obj,
            'message': 'Capsules generated successfully'
        }

        # Сохраняем в кэш
        if _redis_client and cache_key:
            try:
                ttl = getattr(Config, 'REDIS_TTL', 6 * 60 * 60)
                _redis_client.setex(cache_key, ttl, json.dumps(response_obj, ensure_ascii=False))
                print(f"🟡 CACHE SET: {cache_key} ttl={ttl}")
            except Exception:
                print(f"⚠️ CACHE ERROR (write): {cache_key}")

        return jsonify(response_obj)
        
    except TimeoutError as e:
        print(f"Timeout generating capsules: {str(e)}")
        return jsonify({'error': 'Генерация капсул превысила время ожидания. Попробуйте еще раз.'}), 408
    except Exception as e:
        print(f"Error generating capsules: {str(e)}")
        return jsonify({'error': f'Error generating capsules: {str(e)}'}), 500

def generate_capsules_with_ai(wardrobe, profile, weather):
    """Generate wardrobe capsules using AI with timeout"""
    try:
        print("⚡ Начинаем generate_capsules_with_ai")
        print(f"📋 Вызываем generate_capsules_with_gpt с гардеробом из {len(wardrobe)} вещей")
        print("Генерируем капсулы через GPT-4o-mini...")
        result = generate_capsules_with_gpt(wardrobe, profile, weather)
        print("✅ generate_capsules_with_gpt завершен успешно")
        # Оборачиваем с метаданными
        try:
            total_caps = sum(len(cat.get('fullCapsules', [])) for cat in result.get('categories', []))
        except Exception:
            total_caps = 0
        meta_hint = result.get('meta_hint') if isinstance(result, dict) else None
        meta = {
            'total_capsules': total_caps,
            'insufficient': total_caps < 6,
            'source': (meta_hint or {}).get('source', 'gpt'),
            'reason': (meta_hint or {}).get('reason')
        }
        return { 'capsules': result, 'meta': meta }
            
    except Exception as e:
        print(f"❌ Ошибка в generate_capsules_with_ai: {e}")
        import traceback
        print(f"🔍 Полный traceback: {traceback.format_exc()}")
        
        # Fallback к простой логике
        print("🔄 Переходим к fallback логике...")
        result = create_simple_capsules(wardrobe, profile, weather)
        print("✅ Fallback завершен успешно")
        try:
            total_caps = sum(len(cat.get('fullCapsules', [])) for cat in result.get('categories', []))
        except Exception:
            total_caps = 0
        meta = {
            'total_capsules': total_caps,
            'insufficient': total_caps < 6,
            'source': 'fallback',
            'reason': str(e)
        }
        return { 'capsules': result, 'meta': meta }

def is_valid_clothing_combination(item_ids, wardrobe):
    """Проверяет, является ли комбинация одежды логически корректной.
    Все проверки выполняются по нормализованным категориям через translate_category.
    """
    wardrobe_dict = {str(item['id']): item for item in wardrobe}

    # Получаем нормализованные категории вещей в капсуле
    norm_categories = []
    for item_id in item_ids:
        item = wardrobe_dict.get(str(item_id))
        if item:
            norm_categories.append(translate_category(item.get('category', '')))

    has_dress = any(cat == 'dresses' for cat in norm_categories)

    if has_dress:
        # Платье не сочетается с низами и вторым «верхом» (топ/рубашка/свитер)
        if any(cat in ('bottoms', 'tops') for cat in norm_categories if cat != 'dresses'):
            print("❌ Платье не может сочетаться с топами или нижней частью")
            return False

    # Ровно один низ при отсутствии платья
    bottom_count = sum(1 for cat in norm_categories if cat == 'bottoms')
    if not has_dress and bottom_count == 0:
        print("❌ Образ без платья должен содержать один низ")
        return False
    if bottom_count > 1:
        print("❌ Нельзя надеть несколько нижних частей одновременно")
        return False

    # Не больше одного верха (outerwear допускается отдельно)
    top_count = sum(1 for cat in norm_categories if cat == 'tops')
    if top_count > 1:
        print("❌ Нельзя надеть несколько верхних частей одновременно")
        return False

    return True

def generate_capsules_with_gpt(wardrobe, profile, weather):
    """Генерирует капсулы гардероба с помощью GPT-4o-mini"""
    print("🚀 Начинаем generate_capsules_with_gpt")
    print(f"📦 Получен гардероб из {len(wardrobe)} вещей")
    print(f"👤 Профиль пользователя: {profile}")
    print(f"🌤️ Погода: {weather}")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY не найден!")
            raise Exception("OPENAI_API_KEY не настроен")
        
        print(f"🔑 API ключ найден (длина: {len(api_key)} символов)")
        
        client = openai.OpenAI(api_key=api_key)
        
        # 1. Определяем сезон детерминированно (без GPT)
        current_season = get_season_from_weather_simple(weather)
        
        # 2. Фильтруем гардероб по сезону и пригодности
        filtered_wardrobe = [it for it in wardrobe if str(it.get('is_suitable', True)).lower() != 'false']
        filtered_wardrobe = filter_wardrobe_by_season(filtered_wardrobe, current_season)
        
        if not filtered_wardrobe or len(filtered_wardrobe) < 5:
            print(f"Недостаточно вещей для сезона {current_season} ({len(filtered_wardrobe)} шт.), используем весь гардероб")
            filtered_wardrobe = wardrobe
        
        # 3. Группируем вещи по категориям для промпта
        wardrobe_by_category = {}
        for item in filtered_wardrobe:
            category = item.get('category', 'Другое')
            if category not in wardrobe_by_category:
                wardrobe_by_category[category] = []
            wardrobe_by_category[category].append(item)
        
        # 4. Создаем структурированный промпт с экранированием кавычек
        wardrobe_text = ""
        all_item_ids = []
        
        for category, items in wardrobe_by_category.items():
            wardrobe_text += f"\n**{category}:**\n"
            for item in items:
                item_id = str(item.get('id'))
                all_item_ids.append(item_id)
                # Экранируем кавычки в описании
                description = item.get('description', '').replace('"', '\\"').replace("'", "\\'")
                wardrobe_text += f"  - ID: \"{item_id}\", описание: {description}, сезон: {item.get('season', '')}\n"
        
        # Добавляем список всех доступных ID
        wardrobe_text += f"\n**ВНИМАНИЕ! ДОСТУПНЫЕ ID ДЛЯ ИСПОЛЬЗОВАНИЯ:**\n"
        for item_id in all_item_ids:
            wardrobe_text += f"  \"{item_id}\"\n"
        
        profile_text = f"""
        Имя: {profile.get('name', 'Не указано')}
        Возраст: {profile.get('age', 25)}
        Цветотип: {profile.get('cvetotip', 'Не указан')}
        Фигура: {profile.get('figura', 'Не указана')}
        Любимая зона: {profile.get('like_zone', 'Не указана')}
        Зона, которую желательно не подчёркивать: {profile.get('dislike_zone', 'Не указана')}
        """
        
        weather_text = f"""
        Температура: {weather.get('temperature', 20)}°C
        Описание: {weather.get('condition', 'ясно')}
        Сезон: {current_season}
        """
        
        # Создаем персонализированные рекомендации на основе профиля
        figura_tips = {
            'Перевернутый треугольник': {
                'подчеркнуть': 'талию и бедра',
                'скрыть': 'широкие плечи',
                'рекомендации': 'А-силуэт юбок, расклешенные брюки, акцент на нижнюю часть'
            },
            'Песочные часы': {
                'подчеркнуть': 'талию',
                'скрыть': 'ничего',
                'рекомендации': 'приталенные силуэты, подчеркивающие талию'
            },
            'Прямоугольник': {
                'подчеркнуть': 'создать талию',
                'скрыть': 'прямые линии',
                'рекомендации': 'пояса, баски, объемные рукава'
            }
        }
        
        colortype_colors = {
            'Теплая осень': {
                'идеальные': 'терракотовый, горчичный, оливковый, шоколадный, кирпичный, золотистый, бежевый, коричневый',
                'избегать': 'холодные синие, фиолетовые, серебристые оттенки'
            },
            'Холодная зима': {
                'идеальные': 'ярко-синий, изумрудный, фуксия, черный, белый, серебристый',
                'избегать': 'теплые желтые, оранжевые, коричневые'
            },
            'Мягкое лето': {
                'идеальные': 'пастельные, серо-голубой, лавандовый, мятный, пыльная роза',
                'избегать': 'яркие контрастные, оранжевые'
            },
            'Яркая весна': {
                'идеальные': 'яркие теплые, коралловый, персиковый, желтый, зеленый',
                'избегать': 'приглушенные, темные'
            }
        }
        
        user_figura = profile.get('figura', '')
        user_colortype = profile.get('cvetotip', '')
        figura_advice = figura_tips.get(user_figura, {'подчеркнуть': 'индивидуальные особенности', 'рекомендации': 'гармоничные силуэты'})
        color_advice = colortype_colors.get(user_colortype, {'идеальные': 'гармоничные оттенки'})

        unsuitable_ids_list = list(compute_unsuitable_ids(profile, wardrobe))
        system_prompt = '''System (жёсткие правила, всегда в приоритете)
Ты — персональный стилист. Создавай образы для клиента на основе его фигуры, цветотипа, стиля и гардероба.  

**Правила создания капсул:**
1. Капсула = завершённый образ:
   - топ + низ + обувь (+ аксессуары, сумка по возможности)  
   - ИЛИ платье + обувь (+ аксессуары, сумка по возможности)  
2. Запрещено:
   - платье + другая основная одежда (верх/низ)
   - юбка + джинсы/брюки/шорты одновременно
   - несколько курток/пиджаков одновременно
3. Цвета: использовать только оттенки, подходящие для цветотипа клиента.
4. Фигура: учитывать рекомендации по силуэтам и зонам, которые нужно подчеркнуть/скрыть.
5. В каждой капсуле обязательно есть обувь из категории "Обувь".
6. Не использовать вещи из списка запрещённых ID.
 7. Создай как можно больше уникальных капсул (минимум 12, без верхней границы). Не дублируй идентичные комбинации.
8. Одну и ту же вещь нельзя использовать более чем в 2 капсулах в рамках одного ответа.

**Правила JSON:**
- Всегда строго валидный JSON без markdown.
- Строки — в двойных кавычках.
- Кавычки внутри строк экранировать \".
- Без переносов строк в значениях.
- Структура:
{
  "categories": [
    {
      "id": "casual",
      "name": "Повседневный стиль",
      "capsules": [
        {
          "id": "c1",
          "name": "Название",
          "items": ["id1", "id2", "id3"],
          "description": "Краткое описание образа"
        }
      ]
    }
  ]
}'''

        user_prompt = f'''User (только данные и задача)
**Клиент:**  
Имя: {profile.get('name', 'Клиент')}  
Возраст: {profile.get('age', 'не указан')} лет  
Фигура: {user_figura}  
Цветотип: {user_colortype}  
Образ жизни: {profile.get('rod_zanyatii', 'не указано')}  
Стиль: {profile.get('predpochtenia', 'не указано')}  
Хочет подчеркнуть: {profile.get('like_zone', 'не указано')}  
Хочет скрыть: {profile.get('dislike_zone', 'не указано')}  
Запрос: {profile.get('change', 'подобрать подходящие образы')}  

**Рекомендации по фигуре "{user_figura}":**  
- Подчеркнуть: {figura_advice['подчеркнуть']}  
- Силуэты: {figura_advice['рекомендации']}  

**Рекомендации по цветотипу "{user_colortype}":**  
- Идеальные цвета: {color_advice.get('идеальные', 'гармоничные оттенки')}  
- Избегать: {color_advice.get('избегать', 'неподходящие оттенки')}  

**Гардероб (анализируй цвета и фасоны):**  
{wardrobe_text}  

**Погода:**  
{weather_text}  

**Запрещённые ID:**  
{unsuitable_ids_list}  

**Задача:**  
Создай 6–10 капсул, подходящих по цвету, фасону, образу жизни, фигуре и погоде.  
'''
        
        print("Генерируем капсулы через GPT-4o-mini...")
        prompt_length = len(system_prompt) + len(user_prompt)
        print(f"Длина промпта: {prompt_length} символов")
        # Логируем полный SYSTEM/USER промпт (для отладки)
        try:
            print("=== SYSTEM PROMPT ===")
            print(system_prompt)
            print("=== END SYSTEM PROMPT ===")
            print("=== USER PROMPT ===")
            print(user_prompt)
            print("=== END USER PROMPT ===")
        except Exception as _lp_err:
            print(f"⚠️ Не удалось вывести полный промпт: {_lp_err}")
        
        # 5. Отправляем запрос к GPT
        # Диагностика: выводим значения переменных, используемых в системном промпте
        try:
            sys_prompt_vars = {
                'name': profile.get('name', 'клиента'),
                'user_figura': user_figura,
                'user_colortype': user_colortype,
                'like_zone': profile.get('like_zone', ''),
                'dislike_zone': profile.get('dislike_zone', ''),
                'ideal_colors': color_advice.get('идеальные', 'подходящие')
            }
            print('=== SYSTEM PROMPT VARIABLES ===')
            print(json.dumps(sys_prompt_vars, ensure_ascii=False, indent=2))
            print('=== END SYSTEM PROMPT VARIABLES ===')
        except Exception as _spv_err:
            print(f"⚠️ Не удалось вывести переменные системного промпта: {_spv_err}")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            print("✅ GPT запрос успешно выполнен")
        except Exception as gpt_error:
            print(f"❌ Ошибка при запросе к GPT: {gpt_error}")
            raise gpt_error
        
        # 6. Парсим ответ
        content = response.choices[0].message.content.strip()
        
        # Выводим полный ответ GPT в консоль для отладки
        print(f"=== ПОЛНЫЙ ОТВЕТ GPT ===")
        print(content)
        print(f"=== КОНЕЦ ОТВЕТА GPT ===")
        
        # Убираем возможные markdown блоки (если GPT их все-таки добавил)
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        
        content = content.strip()
        
        print(f"=== ОБРАБОТАННЫЙ JSON ===")
        print(content)
        print(f"=== КОНЕЦ ОБРАБОТАННОГО JSON ===")
        
        # Валидация JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON от GPT: {e}")
            print(f"Проблемный ответ GPT (первые 800 символов): {content[:800]}...")
            raise Exception(f"GPT вернул невалидный JSON: {str(e)}")
        
        # 7. Валидация структуры
        if 'categories' not in result:
            raise Exception("Отсутствует поле 'categories' в ответе GPT")
        
        # 8. Проверяем и исправляем капсулы
        valid_ids = {item['id'] for item in filtered_wardrobe}
        print(f"Доступные ID вещей: {valid_ids}")
        
        wardrobe_dict = {str(item['id']): item for item in filtered_wardrobe}
        # Пулы по нормализованным категориям
        accessory_ids = [str(it['id']) for it in filtered_wardrobe if translate_category(it.get('category','')) == 'accessories']
        shoe_ids = [str(it['id']) for it in filtered_wardrobe if translate_category(it.get('category','')) == 'shoes']

                # Лимит на повторное использование одной вещи: не более 2 раз на подборку
        item_usage = {}
        excluded_ids_for_fix = compute_unsuitable_ids(profile, filtered_wardrobe)
        for category in result['categories']:
            if 'fullCapsules' not in category:
                continue
                
            valid_capsules = []
            for capsule in category['fullCapsules']:
                if 'items' not in capsule or not capsule['items']:
                    continue
                    
                # Проверяем, что все ID существуют
                valid_items = [item_id for item_id in capsule['items'] if item_id in valid_ids]
                invalid_items = [item_id for item_id in capsule['items'] if item_id not in valid_ids]
                
                if invalid_items:
                    print(f"Обнаружены несуществующие ID в капсуле {capsule.get('id', 'unknown')}: {invalid_items}")

                # Убираем запрещенные ID
                if any(i in excluded_ids_for_fix for i in valid_items):
                    print(f"Капсула {capsule.get('id','unknown')} содержит неподходящие вещи, пропускаем")
                    continue
                
                # Проверяем логику одежды
                if not is_valid_clothing_combination(valid_items, filtered_wardrobe):
                    print(f"Капсула {capsule.get('id', 'unknown')} отклонена: нелогичная комбинация одежды")
                    continue
                
                # Проверяем наличие обуви по нормализованным категориям
                has_shoes = any(translate_category(wardrobe_dict.get(str(item_id), {}).get('category','')) == 'shoes' for item_id in valid_items)
                if not has_shoes:
                    print(f"Капсула {capsule.get('id', 'unknown')} отклонена: нет обуви")
                    continue
                
                # Оставляем только капсулы с 3+ вещами (включая обувь) и корректной структурой
                if len(valid_items) >= 3:
                    # Контроль частоты использования вещей
                    too_much = False
                    for iid in valid_items:
                        item_usage[iid] = item_usage.get(iid, 0) + 1
                        if item_usage[iid] > 2:
                            too_much = True
                    if too_much:
                        print(f"Капсула {capsule.get('id', 'unknown')} отклонена: превышен лимит использования вещей")
                        # Откатываем инкремент
                        for iid in valid_items:
                            item_usage[iid] = max(0, item_usage.get(iid, 1) - 1)
                        continue
                    # Требуем либо платье, либо топ+низ
                    cats = [wardrobe_dict.get(str(i)).get('category','').lower() for i in valid_items if wardrobe_dict.get(str(i))]
                    has_dress_local = any(c in ['платье','dress','сарафан'] for c in cats)
                    has_top_local = any(c in ['блузка','блуза','рубашка','топ','футболка','свитер','кофта','водолазка','blouse','shirt','top','t-shirt','sweater','turtleneck'] for c in cats)
                    has_bottom_local = any(c in ['юбка','джинсы','брюки','шорты','леггинсы','skirt','jeans','pants','shorts','leggings'] for c in cats)
                    if not has_dress_local and not (has_top_local and has_bottom_local):
                        print(f"Капсула {capsule.get('id','unknown')} отклонена: нет платья и нет пары топ+низ")
                        # Откат счётчика
                        for iid in valid_items:
                            item_usage[iid] = max(0, item_usage.get(iid, 1) - 1)
                        continue

                    # По необходимости добавляем 1 аксессуар, если его нет
                    has_accessory = any(translate_category(wardrobe_dict.get(str(i), {}).get('category','')) == 'accessories' for i in valid_items)
                    if not has_accessory and accessory_ids:
                        add_acc = next((aid for aid in accessory_ids if aid not in valid_items), None)
                        if add_acc:
                            valid_items.append(add_acc)
                            item_usage[add_acc] = item_usage.get(add_acc, 0) + 1
                    capsule['items'] = valid_items
                    valid_capsules.append(capsule)
                else:
                    print(f"Капсула {capsule.get('id', 'unknown')} отклонена: недостаточно валидных вещей ({len(valid_items)}, нужно минимум 3)")
            
            category['fullCapsules'] = valid_capsules
            category['examples'] = valid_capsules[:3]
        
        # 9. Возвращаем только результат GPT (без автодобавления fallback)
        total_capsules = sum(len(cat.get('fullCapsules', [])) for cat in result.get('categories', []))
        print(f"GPT сгенерировал {total_capsules} валидных капсул (fallback не добавляется)")
        return result
        
    except Exception as e:
        print(f"Ошибка генерации капсул через GPT: {e}")
        # Fallback к простой логике
        return create_simple_capsules(wardrobe, profile, weather)

def get_current_season_with_gpt(weather_data):
    """Определяет текущий сезон с помощью GPT"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return "Круглогодично"
        
        client = openai.OpenAI(api_key=api_key)
        
        temp = weather_data.get('temperature', 20)
        condition = weather_data.get('condition', 'ясно')
        
        prompt = f"""
        Определи сезон на основе погоды:
        Температура: {temp}°C
        Условия: {condition}
        
        Возможные варианты: Лето, Зима, Весна, Осень, Демисезон, Круглогодично
        
        Верни только название сезона без дополнительного текста.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты метеоролог. Отвечай только названием сезона."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Ошибка определения сезона: {e}")
        return "Круглогодично"

def filter_wardrobe_by_season(wardrobe, season):
    """Фильтрует гардероб по сезону"""
    if season == "Круглогодично":
        return wardrobe
    
    season_mapping = {
        "Лето": ["лето", "летний"],
        "Зима": ["зима", "зимний"],
        "Весна": ["весна", "весенний"],
        "Осень": ["осень", "осенний"],
        "Демисезон": ["демисезон", "демисезонный"]
    }
    
    if season not in season_mapping:
        return wardrobe
    
    keywords = season_mapping[season]
    # Всесезонные (круглогодичные) вещи включаются для любого сезона
    all_season_keywords = ["круглогод", "всесезон"]
    filtered = []
    
    for item in wardrobe:
        item_season = item.get('season', '').lower()
        if any(keyword in item_season for keyword in keywords) or any(k in item_season for k in all_season_keywords):
            filtered.append(item)
    
    return filtered if filtered else wardrobe

def get_season_from_weather_simple(weather_data):
    """Детерминированное определение сезона по температуре и описанию погоды."""
    try:
        if not weather_data:
            return "Круглогодично"
        temp = weather_data.get('main', {}).get('temp') or weather_data.get('temperature')
        desc = (weather_data.get('weather', [{}])[0].get('description') if isinstance(weather_data.get('weather'), list) else weather_data.get('condition')) or ''
        if temp is None:
            return "Круглогодично"
        try:
            temp = float(temp)
        except Exception:
            return "Круглогодично"

        if temp >= 22:
            return "Лето"
        if temp <= 0:
            return "Зима"
        if 0 < temp < 12:
            return "Демисезон"
        return "Весна" if 'rain' not in str(desc).lower() else "Осень"
    except Exception:
        return "Круглогодично"

def compute_unsuitable_ids(profile: Dict[str, Any], wardrobe: List[Dict[str, Any]]) -> set:
    """Возвращает множество ID вещей, которые потенциально не подходят пользователю.

    Эвристики: тип фигуры (яблоко/перевернутый треугольник/прямоугольник),
    цветотип (тёплый/холодный) по ключевым словам в описании.
    """
    unsuitable_ids: set = set()
    try:
        figura = (profile.get('figura') or '').lower()
        cvet = (profile.get('cvetotip') or '').lower()

        warm_keywords = ['оранж', 'желт', 'горчич', 'терракот', 'оливк', 'золот', 'коралл']
        cool_keywords = ['холодн', 'голуб', 'сине', 'серебр', 'фиолет', 'серый']

        apple_bad = ['низкая посад', 'облегающ', 'узк', 'скинни', 'обтяг']
        inverted_bad = ['плечев', 'накладк', 'погоны', 'акцент на плеч']
        rectangle_bad = ['бесформ', 'оверсайз', 'прямой крой']

        for it in wardrobe:
            try:
                desc = (it.get('description') or '').lower()
                reasons = []
                # Цветотип
                if cvet:
                    if 'холод' in cvet or 'зима' in cvet or 'лето' in cvet:
                        if any(k in desc for k in warm_keywords):
                            reasons.append('теплые оттенки не рекомендуются при холодном цветотипе')
                    if 'тёпл' in cvet or 'весн' in cvet or 'осен' in cvet:
                        if any(k in desc for k in cool_keywords):
                            reasons.append('холодные оттенки не рекомендуются при тёплом цветотипе')
                # Фигура
                if 'яблок' in figura or figura.endswith('o'):
                    if any(k in desc for k in apple_bad):
                        reasons.append('низкая посадка/сильно облегающие фасоны подчеркивают живот')
                if 'перевернут' in figura or 'v' in figura:
                    if any(k in desc for k in inverted_bad):
                        reasons.append('дополнительный объем в плечах не рекомендуется при широких плечах')
                if 'прямоуголь' in figura or 'h' in figura:
                    if any(k in desc for k in rectangle_bad):
                        reasons.append('бесформенный прямой крой скрывает талию')

                if reasons:
                    unsuitable_ids.add(str(it.get('id')))
            except Exception:
                continue
    except Exception:
        return set()
    return unsuitable_ids

def translate_category(category):
    """Перевод русских категорий в английские"""
    category_mapping = {
        # Верхняя одежда
        'топ': 'tops',
        'топик': 'tops',
        'рубашка': 'tops',
        'поло': 'tops',
        'футболка': 'tops',
        'лонгслив': 'tops',
        'свитшот': 'tops',
        'свитер': 'tops',
        'водолазка': 'tops',
        'блузка': 'tops',
        'кофта': 'tops',
        'джемпер': 'tops',
        'майка': 'tops',
        'hoodie': 'tops',
        'худи': 'tops',
        
        # Нижняя одежда
        'брюки': 'bottoms',
        'юбка': 'bottoms',
        'джинсы': 'bottoms',
        'шорты': 'bottoms',
        'брюки-кюлоты': 'bottoms',
        
        # Платья
        'платье': 'dresses',
        'сарафан': 'dresses',
        
        # Верхняя одежда
        'куртка': 'outerwear',
        'пальто': 'outerwear',
        'пиджак': 'outerwear',
        'жакет': 'outerwear',
        'кардиган': 'outerwear',
        
        # Обувь
        'обувь': 'shoes',
        'туфли': 'shoes',
        'ботинки': 'shoes',
        'сапоги': 'shoes',
        'кроссовки': 'shoes',
        'сандалии': 'shoes',
        'балетки': 'shoes',
        'кеды': 'shoes',
        'лоферы': 'shoes',
        'мокасины': 'shoes',
        'ботильоны': 'shoes',
        
        # Аксессуары
        'сумка': 'accessories',
        'рюкзак': 'accessories',
        'шарф': 'accessories',
        'шапка': 'accessories',
        'пояс': 'accessories',
        'ремень': 'accessories',
        'украшения': 'accessories',
        'часы': 'accessories',
        'браслет': 'accessories',
        'кольцо': 'accessories',
        'серьги': 'accessories',
        'ожерелье': 'accessories',
        'кулон': 'accessories',
        'цепочка': 'accessories',
        'ободок': 'accessories'
    }
    
    # Приводим к нижнему регистру для сравнения
    category_lower = (category or '').lower().strip()
    return category_mapping.get(category_lower, 'accessories')

def create_simple_capsules(wardrobe, profile, weather):
    """Создание простых капсул без AI (fallback)"""
    capsules = []
    
    # Группируем вещи по категориям
    categories = {
        'tops': [],
        'bottoms': [],
        'dresses': [],
        'outerwear': [],
        'shoes': [],
        'accessories': []
    }
    
    # Исключаем неподходящие вещи
    excluded_ids = compute_unsuitable_ids(profile, wardrobe)
    for item in wardrobe:
        if str(item.get('id')) in excluded_ids:
            continue
        # Переводим категорию с русского на английский
        english_category = translate_category(item.get('category', 'other'))
        if english_category in categories:
            categories[english_category].append(item)
        else:
            categories['accessories'].append(item)
    
    # Создаем разнообразные капсулы
    capsule_id_counter = 1
    
        # Типы капсул - только если есть обувь
    if categories['shoes']:
        for tops_item in categories['tops'][:3]:  # Используем до 3 топов
            for bottoms_item in categories['bottoms'][:2]:  # Используем до 2 низов
                items = [tops_item['id'], bottoms_item['id']]
                
                # ОБЯЗАТЕЛЬНО добавляем обувь
                items.append(categories['shoes'][0]['id'])
                
                # Добавляем аксессуары если есть  
                if categories['accessories']:
                    items.append(categories['accessories'][0]['id'])
                
                capsule = {
                    'id': f'simple_{capsule_id_counter}',
                    'name': f'Образ {capsule_id_counter}',
                    'description': f'Комбинация {tops_item.get("description", "топа")} с {bottoms_item.get("description", "низом")}',
                    'items': items,
                    'category': 'casual'
                }
                capsules.append(capsule)
                capsule_id_counter += 1
                
                if len(capsules) >= 6:  # Ограничиваем количество
                    break
            if len(capsules) >= 6:
                break
    
    # Капсулы с платьями (разрешаем 2-4 предмета: платье + обувь (+ сумка + аксессуар))
    for dress_item in categories['dresses'][:4]:
        items = [dress_item['id']]
        
        # Добавляем обувь
        if categories['shoes']:
            items.append(categories['shoes'][0]['id'])
        
        # Добавляем аксессуары
        if categories['accessories']:
            items.append(categories['accessories'][0]['id'])
            if len(categories['accessories']) > 1 and len(items) < 4:
                items.append(categories['accessories'][1]['id'])
        
        # Добавляем верхнюю одежду если прохладно
        if weather.get('temperature', 20) < 15 and categories['outerwear']:
            items.append(categories['outerwear'][0]['id'])
        
        capsule = {
            'id': f'dress_{len(capsules) + 1}',
            'name': f'Платье {len(capsules) + 1}',
            'description': f'Элегантный образ с {dress_item.get("description", "платьем")}',
            'items': items,
            'category': 'evening'
        }
        capsules.append(capsule)
    
    # Группируем капсулы по категориям
    categories_dict = {
        'casual': {
            'id': 'casual',
            'name': 'Повседневные',
            'description': 'Комфортные образы на каждый день',
            'fullCapsules': []
        },
        'evening': {
            'id': 'evening', 
            'name': 'Вечерние',
            'description': 'Элегантные образы для особых случаев',
            'fullCapsules': []
        }
    }
    
    for capsule in capsules:
        category = capsule['category']
        if category in categories_dict:
            categories_dict[category]['fullCapsules'].append(capsule)
    
    # Добавляем examples
    for category in categories_dict.values():
        category['examples'] = category['fullCapsules'][:3]
    
    return {'categories': list(categories_dict.values())}

def get_category_name(category):
    """Получение названия категории на русском языке"""
    category_names = {
        'casual': 'Повседневные',
        'dress': 'Платья',
        'formal': 'Деловые',
        'sport': 'Спортивные',
        'evening': 'Вечерние'
    }
    return category_names.get(category, category.capitalize())

@app.route('/looks', methods=['POST'])
def generate_looks():
    """Возвращает один или несколько «луков» (композиций) для отрисовки на фронтенде.

    Тело запроса: {
      "name": "Название (опц)",
      "items": [ { "id": "..", "src": "https://...png", "category": "Футболка" }, ... ]
    }

    Ответ: {
      "looks": [
        {
          "id": "look_1",
          "name": "Лук",
          "canvas": { "ratio": 0.8 },
          "items": [ { "id": "..", "src": "..", "x": 50, "y": 36, "w": 46, "z": 2, "r": 0 } ]
        }
      ]
    }
    """
    try:
        data = request.get_json(force=True) or {}
        raw_items = data.get('items') or []
        look_name = data.get('name') or 'Образ'

        # Ключ кэша
        cache_key = None
        if _redis_client:
            try:
                cache_key_src = {
                    'name': look_name,
                    'items': [
                        {
                            'id': str(it.get('id')),
                            'src': it.get('src')
                        } for it in raw_items
                    ]
                }
                h = hashlib.sha256(_json_for_cache.dumps(cache_key_src, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
                cache_key = f"looks:{h}"
                cached = _redis_client.get(cache_key)
                if cached:
                    return jsonify(json.loads(cached))
            except Exception:
                cache_key = None

        # Нормализуем вход
        items = []
        for it in (raw_items or [])[:6]:
            try:
                items.append({
                    'id': str(it.get('id')),
                    'src': it.get('src') or '',
                    'category': str(it.get('category') or ''),
                })
            except Exception:
                continue

        # Простейший расклад по слотам (в процентах). ratio = 4:5 (0.8)
        slots = [
            { 'x': 28, 'y': 35, 'w': 40, 'z': 2 },  # топ/платье
            { 'x': 70, 'y': 60, 'w': 40, 'z': 2 },  # низ/outer
            { 'x': 28, 'y': 75, 'w': 32, 'z': 3 },  # обувь
            { 'x': 70, 'y': 28, 'w': 26, 'z': 3 },  # аксессуар
            { 'x': 52, 'y': 50, 'w': 28, 'z': 1 },  # доп аксессуар
            { 'x': 50, 'y': 82, 'w': 22, 'z': 1 },  # мелочь
        ]

        # Приоритезируем: dress -> top -> bottom -> shoes -> accessories -> outer -> rest
        def cat(it):
            c = (it.get('category') or '').lower()
            if c in ['платье','dress','сарафан']: return 0
            if c in ['блузка','футболка','рубашка','свитер','топ','джемпер','кофта','водолазка']: return 1
            if c in ['юбка','брюки','джинсы','шорты','легинсы','леггинсы']: return 2
            if c in ['обувь','туфли','ботинки','кроссовки','сапоги','сандалии','мокасины','балетки']: return 3
            if c in ['сумка','аксессуары','украшения','пояс','шарф','часы','очки','серьги','колье','браслет','рюкзак']: return 4
            if c in ['пиджак','куртка','пальто','кардиган','жакет','жилет']: return 5
            return 6

        items_sorted = sorted(items, key=cat)
        placed = []
        for i, it in enumerate(items_sorted[:len(slots)]):
            slot = slots[i]
            placed.append({
                'id': it['id'],
                'src': it['src'],
                'x': slot['x'],
                'y': slot['y'],
                'w': slot['w'],
                'z': slot['z'],
                'r': 0
            })

        look = {
            'id': 'look_1',
            'name': look_name,
            'canvas': { 'ratio': 0.8 },
            'items': placed
        }
        resp = { 'looks': [look] }

        if _redis_client and cache_key:
            try:
                ttl = getattr(Config, 'REDIS_TTL', 86400)
                _redis_client.setex(cache_key, ttl, json.dumps(resp, ensure_ascii=False))
            except Exception:
                pass

        return jsonify(resp)
    except Exception as e:
        print(f"❌ Ошибка формирования луков: {e}")
        return jsonify({ 'looks': [] }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False) 