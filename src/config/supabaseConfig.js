/**
 * Конфигурация Supabase для Brand Items
 * 
 * Использует self-hosted Supabase на lipolo.store
 */

import { createClient } from '@supabase/supabase-js';

// Self-hosted Supabase URLs
const SUPABASE_URL = 'https://lipolo.store';
// ВАЖНО: Используем anon key из переменных окружения, а не service_role key!
// Service_role key дает полный доступ к БД и НЕ должен использоваться на фронтенде
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Создаем клиент Supabase
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false // Не нужна авторизация для публичных данных
  },
  db: {
    schema: 'public'
  },
  global: {
    headers: {
      'Content-Type': 'application/json'
    }
  }
});

// URL для Flask API метрик (impression/click)
export const API_BASE_URL = 'https://linapolo.ru/api/public';

// URL для изображений
export const STORAGE_URL = 'https://lipolo.store/storage/v1/object/public/brand-items-images';

// Supabase config initialized (логирование отключено для безопасности)

