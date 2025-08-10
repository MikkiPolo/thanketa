import { createClient } from '@supabase/supabase-js'

// Конфигурация Supabase
const supabaseUrl = 'https://lipolo.store'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImV4cCI6MTc4NDQwNjYyOSwiaWF0IjoxNzUyODcwNjI5fQ.WT3UG-bmbfetuQYAYr91n3tvqZAE49YhKJoJZbzxnQc'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function getWardrobe(telegramId) {
  console.log(`Получаем гардероб для telegram_id: ${telegramId}`)
  
  const { data, error } = await supabase
    .from('wardrobe')
    .select('*')
    .eq('telegram_id', telegramId)
    .order('id', { ascending: false })

  if (error) {
    console.error('Ошибка получения гардероба:', error)
    return []
  }

  console.log('Гардероб получен:', data)
  return data || []
}

async function getProfile(telegramId) {
  console.log(`Получаем профиль для telegram_id: ${telegramId}`)
  
  const { data, error } = await supabase
    .from('user_profile')
    .select('*')
    .eq('telegram_id', telegramId)
    .single()

  if (error) {
    console.error('Ошибка получения профиля:', error)
    return null
  }

  console.log('Профиль получен:', data)
  return data
}

async function testRealData() {
  const telegramId = '714402266'
  
  console.log('=== ТЕСТИРОВАНИЕ РЕАЛЬНЫХ ДАННЫХ ===')
  
  // Получаем профиль
  const profile = await getProfile(telegramId)
  
  // Получаем гардероб
  const wardrobe = await getWardrobe(telegramId)
  
  console.log('\n=== РЕЗУЛЬТАТ ===')
  console.log('Профиль:', profile)
  console.log('Количество вещей в гардеробе:', wardrobe.length)
  
  if (wardrobe.length > 0) {
    console.log('\n=== ПРИМЕРЫ ВЕЩЕЙ ===')
    wardrobe.slice(0, 5).forEach((item, index) => {
      console.log(`${index + 1}. ID: ${item.id}, Название: ${item.name}, Категория: ${item.category}, Описание: ${item.description}`)
    })
  }
  
  return { profile, wardrobe }
}

// Запускаем тест
testRealData().catch(console.error) 