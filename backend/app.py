from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
try:
    from rembg import remove as _rembg_remove
    def remove_bg(image):
        """Удаляет фон, возвращая PIL.Image в RGBA. В случае ошибки возвращает исходное изображение."""
        try:
            out = _rembg_remove(image)
            # rembg.remove может вернуть bytes (PNG) — конвертируем в PIL.Image
            if isinstance(out, (bytes, bytearray)):
                buf = io.BytesIO(out)
                img = Image.open(buf)
                # Гарантируем прозрачный фон в RGBA
                return img.convert('RGBA') if img.mode != 'RGBA' else img
            # Или уже PIL.Image
            if isinstance(out, Image.Image):
                return out.convert('RGBA') if out.mode != 'RGBA' else out
            return image
        except Exception:
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
                                reasons.append('холодные оттенки могут конфликтовать с тёплым цветотипом')

                    # Проверка типа фигуры
                    if 'яблок' in figura or figura.endswith('o'):
                        if any(k in desc for k in apple_bad):
                            reasons.append('низкая посадка/сильно облегающие фасоны подчёркивают живот')
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
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=900,
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
        
        # Generate capsules using AI
        capsules = generate_capsules_with_ai(wardrobe, profile, weather)
        
        return jsonify({
            'capsules': capsules,
            'message': 'Capsules generated successfully'
        })
        
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
        meta = {
            'total_capsules': total_caps,
            'insufficient': total_caps < 6
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
            'insufficient': total_caps < 6
        }
        return { 'capsules': result, 'meta': meta }

def is_valid_clothing_combination(item_ids, wardrobe):
    """Проверяет, является ли комбинация одежды логически корректной"""
    wardrobe_dict = {str(item['id']): item for item in wardrobe}
    
    # Получаем категории вещей в капсуле
    categories = []
    for item_id in item_ids:
        item = wardrobe_dict.get(str(item_id))
        if item:
            category = item.get('category', '').lower()
            categories.append(category)
    
    # Проверяем наличие платья
    dress_categories = ['платье', 'dress', 'сарафан']
    has_dress = any(cat in dress_categories for cat in categories)
    
    if has_dress:
        # Если есть платье, проверяем, что нет конфликтующих вещей
        conflicting_with_dress = [
            'блузка', 'блуза', 'рубашка', 'топ', 'футболка', 'свитер', 'кофта', 'водолазка',
            'юбка', 'джинсы', 'брюки', 'шорты', 'леггинсы',
            'blouse', 'shirt', 'top', 't-shirt', 'sweater', 'turtleneck',
            'skirt', 'jeans', 'pants', 'shorts', 'leggings'
        ]
        
        for cat in categories:
            if cat in conflicting_with_dress:
                print(f"❌ Платье не может сочетаться с {cat}")
                return False
    
    # Проверяем, что нет нескольких нижних частей одновременно
    bottom_categories = [
        'юбка', 'джинсы', 'брюки', 'шорты', 'леггинсы',
        'skirt', 'jeans', 'pants', 'shorts', 'leggings'
    ]
    bottom_count = sum(1 for cat in categories if cat in bottom_categories)
    
    if bottom_count > 1:
        print(f"❌ Нельзя надеть несколько нижних частей одновременно")
        return False

    # Требуем наличие низа, если нет платья
    if not has_dress and bottom_count == 0:
        print("❌ Образ без платья должен содержать один низ (юбка/брюки/джинсы/шорты)")
        return False
    
    # Проверяем, что нет нескольких верхних частей одновременно (кроме аксессуаров и верхней одежды)
    top_categories = [
        'блузка', 'блуза', 'рубашка', 'топ', 'футболка', 'свитер', 'кофта', 'водолазка',
        'blouse', 'shirt', 'top', 't-shirt', 'sweater', 'turtleneck'
    ]
    top_count = sum(1 for cat in categories if cat in top_categories)
    
    if top_count > 1:
        print(f"❌ Нельзя надеть несколько верхних частей одновременно")
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

        prompt = f"""
        Ты — персональный стилист с опытом работы с цветотипами и типами фигур. 

        **КЛИЕНТ:**
        Имя: {profile.get('name', 'Клиент')}
        Возраст: {profile.get('age', 'не указан')} лет
        Фигура: {user_figura}
        Цветотип: {user_colortype}
        Образ жизни: {profile.get('rod_zanyatii', 'не указан')}
        Стиль: {profile.get('predpochtenia', 'не указан')}
        ХОЧЕТ ПОДЧЕРКНУТЬ: {profile.get('like_zone', 'не указано')}
        ХОЧЕТ СКРЫТЬ: {profile.get('dislike_zone', 'не указано')}
        Запрос: {profile.get('change', 'подобрать подходящие образы')}

        **СТИЛИСТИЧЕСКИЕ РЕКОМЕНДАЦИИ ДЛЯ ФИГУРЫ "{user_figura}":**
        - Подчеркнуть: {figura_advice['подчеркнуть']}
        - Силуэты: {figura_advice['рекомендации']}

        **ЦВЕТОВЫЕ РЕКОМЕНДАЦИИ ДЛЯ "{user_colortype}":**
        - Идеальные цвета: {color_advice.get('идеальные', 'гармоничные оттенки')}
        - Избегать: {color_advice.get('избегать', 'неподходящие оттенки')}

        **ДОСТУПНЫЕ ВЕЩИ (анализируй цвета и фасоны из описаний):**
        {wardrobe_text}

        **ПОГОДА:**
        {weather_text}

        **ЗАДАЧА:**
        Создай ПОЛНОЦЕННЫЕ капсулы, которые:
        1. ПОДХОДЯТ ПО ЦВЕТОТИПУ: выбирай вещи с цветами "{color_advice.get('идеальные', 'подходящими')}"
        2. КОРРЕКТИРУЮТ ФИГУРУ: для "{user_figura}" используй силуэты, которые {figura_advice['подчеркнуть']}
        3. УЧИТЫВАЮТ ЗОНЫ: подчеркни {profile.get('like_zone', '')}, скрой {profile.get('dislike_zone', '')}
        4. СООТВЕТСТВУЮТ ОБРАЗУ ЖИЗНИ: {profile.get('rod_zanyatii', '')} нужен {profile.get('predpochtenia', '')} стиль
        5. ГАРМОНИРУЮТ ПО ЦВЕТАМ: сочетай оттенки из описаний вещей
        6. **ОБЯЗАТЕЛЬНО ВКЛЮЧАЮТ ОБУВЬ**: каждая капсула должна содержать подходящую обувь из категории "Обувь"
        7. **ЗАВЕРШЕННЫЙ ОБРАЗ**: топ+низ+обувь ИЛИ платье+обувь + по возможности сумка/аксессуары

        **КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА JSON:**
        
        1. **СТРОГО ВАЛИДНЫЙ JSON:**
           - НИКОГДА не используй неэкранированные кавычки в тексте
           - ВСЕ строки заключай в двойные кавычки
           - НЕ используй переносы строк внутри строк
           - НЕ забывай запятые между элементами
           - ПРАВИЛЬНО закрывай все скобки и кавычки

        2. **ПРАВИЛА ЭКРАНИРОВАНИЯ:**
           - Если в тексте есть кавычки - используй \\"
           - Никаких одинарных кавычек внутри JSON
           - Только короткие описания БЕЗ переносов строк

        3. **ЛОГИКА ОДЕЖДЫ - СТРОГО ЗАПРЕЩЕНО:**
           - ПЛАТЬЕ + любая другая основная одежда (блузка/рубашка/топ/свитер)
           - ПЛАТЬЕ + юбка/джинсы/брюки/шорты (платье заменяет всю нижнюю часть)
           - Юбка + джинсы/брюки/шорты одновременно
           - Несколько курток/пиджаков одновременно

        4. **ПРАВИЛА СОЗДАНИЯ ПОЛНОЦЕННЫХ КАПСУЛ:**
           - **СТРУКТУРА КАПСУЛЫ**: Основа (топ+низ ИЛИ платье) + ОБЯЗАТЕЛЬНО обувь + сумка/аксессуары
           - **ОБУВЬ ОБЯЗАТЕЛЬНА**: выбирай подходящую по стилю (балетки для элегантных образов, кроссовки для кэжуал)
           - АНАЛИЗИРУЙ ЦВЕТА: "болотный" + "бежевый" = ✅, сочетай гармоничные оттенки
           - УЧИТЫВАЙ СТИЛЬ: классика с классикой, кэжуал с кэжуал
           - МАТЕРИАЛЫ И СЕЗОН: хлопок+лен=лето, шерсть=демисезон
           - МИНИМУМ 3 вещи: основа + обувь + еще что-то
           - МАКСИМУМ 4 вещи для не перегружать образ

        **СТРОГИЙ ФОРМАТ JSON (БЕЗ MARKDOWN):**

        {{
          "categories": [
            {{
              "id": "casual",
              "name": "Повседневный стиль",
              "description": "Уютные образы для ежедневных дел",
              "fullCapsules": [
                {{
                  "id": "casual_1",
                  "name": "Комфортный образ",
                  "description": "Удобный образ для прогулки",
                  "items": ["id1", "id2", "id3"],
                  "category": "casual"
                }}
              ]
            }},
            {{
              "id": "business", 
              "name": "Деловой стиль",
              "description": "Элегантные образы для работы и встреч",
              "fullCapsules": []
            }},
            {{
              "id": "evening",
              "name": "Вечерний стиль", 
              "description": "Эффектные образы для выходов и событий",
              "fullCapsules": []
            }},
            {{
              "id": "romantic",
              "name": "Романтический стиль",
              "description": "Нежные образы для романтических встреч",
              "fullCapsules": []
            }}
          ]
        }}

        **КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:**
        - Создай 6-10 капсул общей сложности. Важно разнообразие: и с платьями, и с топ+низ.
        - Для категории "casual" создай 3-6 капсул. Если позволяют вещи — добавь по 1-2 капсулы в "business" и/или "evening".
        - КАЖДАЯ КАПСУЛА ДОЛЖНА СОДЕРЖАТЬ МИНИМУМ 3 ПРЕДМЕТА, ОПТИМАЛЬНО 3-4
        - КОМБИНИРУЙ РАЗНЫЕ КАТЕГОРИИ: топ+юбка+обувь, рубашка+брюки+сумка, платье+обувь(+аксессуар)
        - ОБЯЗАТЕЛЬНО КОПИРУЙ ID ТОЧНО из раздела "ДОСТУПНЫЕ ID ДЛЯ ИСПОЛЬЗОВАНИЯ"
        - ЗАПРЕЩЕНО придумывать ID типа "id1", "id2", "item_1" и т.д.
        - ИСПОЛЬЗУЙ ТОЛЬКО полные строки ID из списка доступных
        - НЕ создавай капсулы из 1 предмета - это НЕПРАВИЛЬНО
        - НЕ используй markdown блоки ```json
        - Отвечай ТОЛЬКО чистым JSON без дополнительного текста
        - Список ЗАПРЕЩЕННЫХ ID (не использовать ни в одной капсуле): {list(compute_unsuitable_ids(profile, wardrobe))}
        """
        
        print("Генерируем капсулы через GPT-4o-mini...")
        print(f"Длина промпта: {len(prompt)} символов")
        print(f"API ключ установлен: {'Да' if api_key else 'Нет'}")
        
        # 5. Отправляем запрос к GPT
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Ты персональный стилист. Создавай образы для {profile.get('name', 'клиента')} ({user_figura}, {user_colortype}). УЧИТЫВАЙ: подчеркнуть {profile.get('like_zone', '')}, скрыть {profile.get('dislike_zone', '')}. Анализируй ЦВЕТА и ФАСОНЫ из описаний. Для {user_colortype} используй {color_advice.get('идеальные', 'подходящие')} оттенки. Отвечай ТОЛЬКО валидным JSON без markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Понижаем температуру для более предсказуемого результата
                max_tokens=4000   # Увеличиваем лимит токенов
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
        # Лимит на повторное использование одной вещи: не более 3 раз на 10 капсул
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
                
                # Проверяем наличие обуви в капсуле
                has_shoes = False
                for item_id in valid_items:
                    item = wardrobe_dict.get(str(item_id))
                    if item and item.get('category', '').lower() == 'обувь':
                        has_shoes = True
                        break
                
                if not has_shoes:
                    print(f"Капсула {capsule.get('id', 'unknown')} отклонена: нет обуви")
                    continue
                
                # Оставляем только капсулы с 3+ вещами (включая обувь) и корректной структурой
                if len(valid_items) >= 3:
                    # Контроль частоты использования вещей
                    too_much = False
                    for iid in valid_items:
                        item_usage[iid] = item_usage.get(iid, 0) + 1
                        if item_usage[iid] > 5:
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
                    capsule['items'] = valid_items
                    valid_capsules.append(capsule)
                else:
                    print(f"Капсула {capsule.get('id', 'unknown')} отклонена: недостаточно валидных вещей ({len(valid_items)}, нужно минимум 3)")
            
            category['fullCapsules'] = valid_capsules
            category['examples'] = valid_capsules[:3]
        
        # 9. Если капсул слишком мало, дополняем простыми
        total_capsules = sum(len(cat['fullCapsules']) for cat in result['categories'])
        print(f"GPT сгенерировал {total_capsules} валидных капсул")
        
        if total_capsules < 8:
            print("Мало капсул от GPT, дополняем простыми")
            # ВАЖНО: используем уже отфильтрованный по сезону и пригодности гардероб
            fallback = create_simple_capsules(filtered_wardrobe, profile, weather)
            
            # Добавляем fallback капсулы
            if fallback and 'categories' in fallback:
                for fb_cat in fallback['categories']:
                    for result_cat in result['categories']:
                        if result_cat['id'] == fb_cat['id']:
                            result_cat['fullCapsules'].extend(fb_cat['fullCapsules'])
                            result_cat['examples'] = result_cat['fullCapsules'][:3]
                            break
        
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
    filtered = []
    
    for item in wardrobe:
        item_season = item.get('season', '').lower()
        if any(keyword in item_season for keyword in keywords):
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
                        reasons.append('дополнительный объем в плечах нежелателен')
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
        'рубашка': 'tops',
        'футболка': 'tops',
        'свитер': 'tops',
        'водолазка': 'tops',
        'блузка': 'tops',
        'кофта': 'tops',
        'джемпер': 'tops',
        
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
        
        # Аксессуары
        'сумка': 'accessories',
        'рюкзак': 'accessories',
        'шарф': 'accessories',
        'шапка': 'accessories',
        'пояс': 'accessories',
        'украшения': 'accessories',
        'часы': 'accessories'
    }
    
    # Приводим к нижнему регистру для сравнения
    category_lower = category.lower().strip()
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False) 