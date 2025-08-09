import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HuggingFaceCapsuleGenerator:
    """Генератор капсул с использованием Hugging Face моделей"""
    
    def __init__(self, model_name="microsoft/DialoGPT-medium", use_gpu=True):
        """
        Инициализация генератора
        
        Args:
            model_name: Название модели Hugging Face
            use_gpu: Использовать GPU если доступен
        """
        self.model_name = model_name
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        
        logger.info(f"Загружаем модель {model_name} на {self.device}")
        
        try:
            # Загружаем токенизатор и модель
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Перемещаем модель на нужное устройство
            self.model.to(self.device)
            
            # Создаем пайплайн для генерации
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Модель загружена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    def generate_capsules(self, wardrobe: List[Dict], profile: Dict, weather: Dict = None) -> Dict:
        """Генерирует капсулы с помощью Hugging Face модели"""
        try:
            # Создаем промпт
            prompt = self._create_prompt(wardrobe, profile, weather)
            
            # Генерируем ответ
            response = self._generate_text(prompt)
            
            # Парсим ответ
            capsules = self._parse_response(response)
            
            return capsules
            
        except Exception as e:
            logger.error(f"Ошибка генерации капсул: {e}")
            return self._generate_fallback_capsules(wardrobe, profile, weather)
    
    def _create_prompt(self, wardrobe: List[Dict], profile: Dict, weather: Dict) -> str:
        """Создает промпт для модели"""
        
        # Форматируем гардероб
        wardrobe_text = "\n".join([
            f"- {item.get('category', 'Неизвестно')}: {item.get('description', '')}"
            for item in wardrobe[:10]  # Ограничиваем количество вещей
        ])
        
        # Форматируем профиль
        profile_text = f"""
        Имя: {profile.get('name', 'Не указано')}
        Возраст: {profile.get('age', 'Не указан')}
        Тип фигуры: {profile.get('figura', 'Не указан')}
        """
        
        prompt = f"""
        Создай капсулы гардероба:
        
        Гардероб: {wardrobe_text}
        Профиль: {profile_text}
        
        Создай JSON с капсулами:
        """
        
        return prompt
    
    def _generate_text(self, prompt: str) -> str:
        """Генерирует текст с помощью модели"""
        try:
            # Генерируем текст
            result = self.generator(
                prompt,
                max_length=1000,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            return result[0]['generated_text']
            
        except Exception as e:
            logger.error(f"Ошибка генерации текста: {e}")
            raise
    
    def _parse_response(self, response: str) -> Dict:
        """Парсит ответ модели"""
        try:
            # Ищем JSON в ответе
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("JSON не найден в ответе")
            
            json_str = response[start_idx:end_idx]
            capsules = json.loads(json_str)
            
            return capsules
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа: {e}")
            raise
    
    def _generate_fallback_capsules(self, wardrobe: List[Dict], profile: Dict, weather: Dict) -> Dict:
        """Fallback генерация капсул"""
        # Простая логика без ИИ
        return {
            "categories": [
                {
                    "id": "casual",
                    "name": "Повседневный стиль",
                    "description": "Уютные образы для ежедневных дел",
                    "examples": [],
                    "fullCapsules": []
                }
            ]
        }


class SemanticCapsuleGenerator:
    """Генератор капсул с использованием семантического поиска"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Инициализация генератора
        
        Args:
            model_name: Название модели sentence transformers
        """
        self.model_name = model_name
        
        logger.info(f"Загружаем модель {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            logger.info("Модель загружена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    def generate_capsules(self, wardrobe: List[Dict], profile: Dict, weather: Dict = None) -> Dict:
        """Генерирует капсулы с помощью семантического поиска"""
        try:
            # Создаем эмбеддинги для вещей
            item_embeddings = self._create_item_embeddings(wardrobe)
            
            # Создаем эмбеддинги для стилей
            style_embeddings = self._create_style_embeddings()
            
            # Находим похожие вещи для каждого стиля
            capsules = self._match_items_to_styles(wardrobe, item_embeddings, style_embeddings)
            
            return capsules
            
        except Exception as e:
            logger.error(f"Ошибка генерации капсул: {e}")
            return self._generate_fallback_capsules(wardrobe, profile, weather)
    
    def _create_item_embeddings(self, wardrobe: List[Dict]) -> np.ndarray:
        """Создает эмбеддинги для вещей гардероба"""
        # Создаем текстовые описания вещей
        item_texts = []
        for item in wardrobe:
            text = f"{item.get('category', '')} {item.get('description', '')} {item.get('season', '')}"
            item_texts.append(text)
        
        # Создаем эмбеддинги
        embeddings = self.model.encode(item_texts)
        return embeddings
    
    def _create_style_embeddings(self) -> Dict[str, np.ndarray]:
        """Создает эмбеддинги для стилей"""
        styles = {
            "casual": "повседневный стиль уютный комфортный",
            "business": "деловой стиль элегантный официальный",
            "evening": "вечерний стиль элегантный праздничный",
            "romantic": "романтический стиль нежный женственный",
            "weekend": "выходной стиль расслабленный свободный",
            "travel": "путешествие практичный удобный"
        }
        
        style_texts = list(styles.values())
        style_embeddings = self.model.encode(style_texts)
        
        return {style: embedding for style, embedding in zip(styles.keys(), style_embeddings)}
    
    def _match_items_to_styles(self, wardrobe: List[Dict], item_embeddings: np.ndarray, style_embeddings: Dict[str, np.ndarray]) -> Dict:
        """Сопоставляет вещи со стилями на основе семантической близости"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        result = {"categories": []}
        
        for style_name, style_embedding in style_embeddings.items():
            # Вычисляем косинусное сходство
            similarities = cosine_similarity([style_embedding], item_embeddings)[0]
            
            # Находим топ-5 наиболее похожих вещей
            top_indices = np.argsort(similarities)[::-1][:5]
            
            # Создаем капсулу
            capsule_items = [wardrobe[i] for i in top_indices if i < len(wardrobe)]
            
            category = {
                "id": style_name,
                "name": self._get_style_name(style_name),
                "description": self._get_style_description(style_name),
                "examples": [
                    {
                        "id": f"{style_name}_1",
                        "name": f"{self._get_style_name(style_name)} - Образ 1",
                        "items": [str(item.get('id', '')) for item in capsule_items[:3]],
                        "description": f"Семантически подобранный образ",
                        "reasoning": f"Вещи подобраны на основе семантической близости к стилю '{style_name}'"
                    }
                ],
                "fullCapsules": [
                    {
                        "id": f"{style_name}_full_1",
                        "name": f"{self._get_style_name(style_name)} - Капсула 1",
                        "items": [str(item.get('id', '')) for item in capsule_items],
                        "description": f"Полная капсула в стиле {style_name}",
                        "reasoning": f"Капсула создана с помощью семантического поиска"
                    }
                ]
            }
            
            result["categories"].append(category)
        
        return result
    
    def _get_style_name(self, style_id: str) -> str:
        """Возвращает название стиля"""
        names = {
            "casual": "Повседневный стиль",
            "business": "Деловой образ",
            "evening": "Вечерний выход",
            "romantic": "Романтическое свидание",
            "weekend": "Выходные",
            "travel": "Путешествия"
        }
        return names.get(style_id, style_id)
    
    def _get_style_description(self, style_id: str) -> str:
        """Возвращает описание стиля"""
        descriptions = {
            "casual": "Уютные образы для ежедневных дел",
            "business": "Элегантные решения для работы",
            "evening": "Стильные образы для особых случаев",
            "romantic": "Нежные и привлекательные образы",
            "weekend": "Расслабленные образы для отдыха",
            "travel": "Практичные образы для поездок"
        }
        return descriptions.get(style_id, "")
    
    def _generate_fallback_capsules(self, wardrobe: List[Dict], profile: Dict, weather: Dict) -> Dict:
        """Fallback генерация капсул"""
        return {
            "categories": [
                {
                    "id": "casual",
                    "name": "Повседневный стиль",
                    "description": "Уютные образы для ежедневных дел",
                    "examples": [],
                    "fullCapsules": []
                }
            ]
        }


# Фабрика генераторов
class CapsuleGeneratorFactory:
    """Фабрика для создания генераторов капсул"""
    
    @staticmethod
    def create_generator(generator_type: str, **kwargs):
        """
        Создает генератор капсул указанного типа
        
        Args:
            generator_type: Тип генератора ('ollama', 'huggingface', 'semantic')
            **kwargs: Дополнительные параметры
        """
        if generator_type == "ollama":
            from capsule_generator import LocalCapsuleGenerator
            return LocalCapsuleGenerator(**kwargs)
        
        elif generator_type == "huggingface":
            return HuggingFaceCapsuleGenerator(**kwargs)
        
        elif generator_type == "semantic":
            return SemanticCapsuleGenerator(**kwargs)
        
        else:
            raise ValueError(f"Неизвестный тип генератора: {generator_type}") 