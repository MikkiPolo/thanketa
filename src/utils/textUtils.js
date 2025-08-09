// Утилиты для работы с текстом

/**
 * Нормализует текст (первая буква заглавная, остальные строчные)
 * @param {string} text - Исходный текст
 * @returns {string} Нормализованный текст
 */
export const normalizeText = (text) => {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

/**
 * Валидирует возраст (только цифры, от 1 до 120)
 * @param {string} age - Возраст в виде строки
 * @returns {boolean} Валидность возраста
 */
export const validateAge = (age) => {
  if (!age) return false;
  const ageNum = parseInt(age);
  return !isNaN(ageNum) && ageNum >= 1 && ageNum <= 120;
};

/**
 * Очищает возраст от нецифровых символов
 * @param {string} age - Возраст в виде строки
 * @returns {string} Очищенный возраст
 */
export const cleanAge = (age) => {
  if (!age) return '';
  const cleaned = age.replace(/\D/g, '');
  const ageNum = parseInt(cleaned);
  if (ageNum > 120) return '120';
  return cleaned;
}; 