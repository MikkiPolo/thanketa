// Тест конфигурации
import { BACKEND_URL, API_ENDPOINTS } from './config.js';

console.log('=== ТЕСТ КОНФИГУРАЦИИ ===');
console.log('BACKEND_URL:', BACKEND_URL);
console.log('API_ENDPOINTS.ANALYZE_WARDROBE:', API_ENDPOINTS.ANALYZE_WARDROBE);
console.log('Полный URL:', `${BACKEND_URL}${API_ENDPOINTS.ANALYZE_WARDROBE}`);
console.log('VITE_BACKEND_URL:', import.meta.env.VITE_BACKEND_URL);
console.log('========================'); 