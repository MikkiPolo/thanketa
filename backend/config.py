import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Настройки ИИ
    AI_GENERATOR_TYPE = os.getenv('AI_GENERATOR_TYPE', 'ollama')  # ollama, huggingface, semantic, gpt
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'phi3:mini')  # Быстрая модель для высокой нагрузки
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '1500'))  # Уменьшили для скорости
    
    # Настройки Ollama
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '15'))  # Уменьшили таймаут
    
    # Настройки Hugging Face
    HF_USE_GPU = os.getenv('HF_USE_GPU', 'true').lower() == 'true'
    HF_MODEL_NAME = os.getenv('HF_MODEL_NAME', 'microsoft/DialoGPT-medium')
    
    # Настройки семантического поиска
    SEMANTIC_MODEL_NAME = os.getenv('SEMANTIC_MODEL_NAME', 'all-MiniLM-L6-v2')
    
    # Fallback настройки
    USE_FALLBACK_GENERATION = os.getenv('USE_FALLBACK_GENERATION', 'true').lower() == 'true'
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'ai_capsules.log')
    
    # Кэширование
    ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 час
    
    # Redis настройки
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    REDIS_TTL = int(os.getenv('REDIS_TTL', '86400'))  # 24 часа для AI результатов
    
    # Производительность
    MAX_WARDROBE_ITEMS = int(os.getenv('MAX_WARDROBE_ITEMS', '50'))
    MAX_CAPSULES_PER_CATEGORY = int(os.getenv('MAX_CAPSULES_PER_CATEGORY', '8'))
    
    @classmethod
    def get_generator_config(cls):
        """Возвращает конфигурацию для генератора капсул"""
        if cls.AI_GENERATOR_TYPE == 'ollama':
            return {
                'model_name': cls.AI_MODEL_NAME,
                'temperature': cls.AI_TEMPERATURE,
                'max_tokens': cls.AI_MAX_TOKENS,
                'host': cls.OLLAMA_HOST,
                'timeout': cls.OLLAMA_TIMEOUT
            }
        
        elif cls.AI_GENERATOR_TYPE == 'huggingface':
            return {
                'model_name': cls.HF_MODEL_NAME,
                'use_gpu': cls.HF_USE_GPU,
                'temperature': cls.AI_TEMPERATURE,
                'max_length': cls.AI_MAX_TOKENS
            }
        
        elif cls.AI_GENERATOR_TYPE == 'semantic':
            return {
                'model_name': cls.SEMANTIC_MODEL_NAME
            }
        
        elif cls.AI_GENERATOR_TYPE == 'gpt':
            return {
                'model_name': 'gpt-4o-mini',
                'temperature': cls.AI_TEMPERATURE,
                'max_tokens': cls.AI_MAX_TOKENS
            }
        
        else:
            raise ValueError(f"Неизвестный тип генератора: {cls.AI_GENERATOR_TYPE}")
    
    @classmethod
    def validate_config(cls):
        """Проверяет корректность конфигурации"""
        errors = []
        
        # Проверяем тип генератора
        if cls.AI_GENERATOR_TYPE not in ['ollama', 'huggingface', 'semantic', 'gpt']:
            errors.append(f"Неизвестный тип генератора: {cls.AI_GENERATOR_TYPE}")
        
        # Проверяем температуру
        if not 0 <= cls.AI_TEMPERATURE <= 2:
            errors.append(f"Температура должна быть от 0 до 2, получено: {cls.AI_TEMPERATURE}")
        
        # Проверяем максимальное количество токенов
        if cls.AI_MAX_TOKENS <= 0:
            errors.append(f"Максимальное количество токенов должно быть положительным, получено: {cls.AI_MAX_TOKENS}")
        
        if errors:
            raise ValueError(f"Ошибки конфигурации: {'; '.join(errors)}")
        
        return True 