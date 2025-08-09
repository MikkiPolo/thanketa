// Конфигурация для работы с backend
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001';

// Добавляем версию для обхода кэша в Telegram Mini App
export const BACKEND_URL_WITH_VERSION = BACKEND_URL + '?v=' + Date.now();

// Старые URL для n8n (если нужны)
export const N8N_FETCH_URL = import.meta.env.VITE_N8N_FETCH_URL || 'https://lipolo.ru/webhook/anketa'
export const N8N_SAVE_URL = import.meta.env.VITE_N8N_SAVE_URL || 'https://lipolo.ru/webhook-test/anketa_save'

// API endpoints - используем относительные пути для nginx прокси
export const API_ENDPOINTS = {
  HEALTH: '/health',
  REMOVE_BACKGROUND: '/remove-background',
  ANALYZE_WARDROBE: '/analyze-wardrobe-item',
  UPLOADS: '/uploads',
  GENERATE_CAPSULES: '/generate-capsules',
  AI_FEEDBACK: '/ai-feedback',
  AI_PERFORMANCE: '/ai-performance',
  AI_EXPLANATION: '/ai-explanation',
  WARDROBE_RECOMMENDATIONS: '/wardrobe-recommendations'
};