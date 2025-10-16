/**
 * Конфигурация Supabase для Brand Items
 * 
 * Использует self-hosted Supabase на lipolo.store
 */

import { createClient } from '@supabase/supabase-js';

// Self-hosted Supabase URLs
const SUPABASE_URL = 'https://lipolo.store';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImV4cCI6MTc4NDQwNjYyOSwiaWF0IjoxNzUyODcwNjI5fQ.WT3UG-bmbfetuQYAYr91n3tvqZAE49YhKJoJZbzxnQc';

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

console.log('✅ Supabase config initialized:', SUPABASE_URL);

