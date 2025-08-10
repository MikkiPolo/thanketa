import { createClient } from '@supabase/supabase-js'

// Конфигурация Supabase
const supabaseUrl = 'https://lipolo.store'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImV4cCI6MTc4NDQwNjYyOSwiaWF0IjoxNzUyODcwNjI5fQ.WT3UG-bmbfetuQYAYr91n3tvqZAE49YhKJoJZbzxnQc'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Тестовые данные
const testTelegramId = '714402266'
const testCapsule = {
  id: 'test_capsule_1',
  name: 'Тестовая капсула',
  description: 'Это тестовая капсула для проверки работы',
  category: 'casual',
  items: [
    {
      id: 'item_1',
      category: 'футболка',
      description: 'Белая футболка',
      image_id: 'test_image_1'
    },
    {
      id: 'item_2', 
      category: 'джинсы',
      description: 'Синие джинсы',
      image_id: 'test_image_2'
    }
  ]
}

async function testFavoritesTable() {
  console.log('🧪 Начинаем тестирование таблицы favorites...')
  
  // 1. Проверяем структуру таблицы
  console.log('\n1️⃣ Проверяем структуру таблицы...')
  const { data: columns, error: columnsError } = await supabase
    .from('favorites')
    .select('*')
    .limit(0)
  
  if (columnsError) {
    console.error('❌ Ошибка при проверке таблицы:', columnsError)
    return
  }
  
  console.log('✅ Таблица favorites доступна')
  
  // 2. Добавляем тестовую капсулу в избранное
  console.log('\n2️⃣ Добавляем тестовую капсулу в избранное...')
  const { data: insertData, error: insertError } = await supabase
    .from('favorites')
    .insert({
      telegram_id: testTelegramId,
      capsule_id: testCapsule.id,
      capsule_name: testCapsule.name,
      capsule_description: testCapsule.description,
      capsule_category: testCapsule.category,
      capsule_data: testCapsule
    })
    .select()
  
  if (insertError) {
    console.error('❌ Ошибка при добавлении:', insertError)
    return
  }
  
  console.log('✅ Капсула добавлена в избранное:', insertData[0])
  
  // 3. Получаем все избранные капсулы пользователя
  console.log('\n3️⃣ Получаем избранные капсулы...')
  const { data: favorites, error: selectError } = await supabase
    .from('favorites')
    .select('*')
    .eq('telegram_id', testTelegramId)
    .order('created_at', { ascending: false })
  
  if (selectError) {
    console.error('❌ Ошибка при получении избранного:', selectError)
    return
  }
  
  console.log('✅ Найдено избранных капсул:', favorites.length)
  favorites.forEach((fav, index) => {
    console.log(`   ${index + 1}. ${fav.capsule_name} (${fav.capsule_category})`)
  })
  
  // 4. Проверяем уникальность (пробуем добавить ту же капсулу)
  console.log('\n4️⃣ Проверяем уникальность (добавляем ту же капсулу)...')
  const { data: duplicateData, error: duplicateError } = await supabase
    .from('favorites')
    .insert({
      telegram_id: testTelegramId,
      capsule_id: testCapsule.id,
      capsule_name: 'Дублированная капсула',
      capsule_description: 'Это должно вызвать ошибку',
      capsule_category: 'business',
      capsule_data: testCapsule
    })
    .select()
  
  if (duplicateError) {
    console.log('✅ Уникальность работает (ожидаемая ошибка):', duplicateError.message)
  } else {
    console.log('❌ Ошибка: дублирование не предотвращено')
  }
  
  // 5. Добавляем еще одну капсулу
  console.log('\n5️⃣ Добавляем вторую капсулу...')
  const testCapsule2 = {
    ...testCapsule,
    id: 'test_capsule_2',
    name: 'Вторая тестовая капсула',
    category: 'business'
  }
  
  const { data: insertData2, error: insertError2 } = await supabase
    .from('favorites')
    .insert({
      telegram_id: testTelegramId,
      capsule_id: testCapsule2.id,
      capsule_name: testCapsule2.name,
      capsule_description: testCapsule2.description,
      capsule_category: testCapsule2.category,
      capsule_data: testCapsule2
    })
    .select()
  
  if (insertError2) {
    console.error('❌ Ошибка при добавлении второй капсулы:', insertError2)
  } else {
    console.log('✅ Вторая капсула добавлена:', insertData2[0])
  }
  
  // 6. Получаем статистику
  console.log('\n6️⃣ Получаем статистику...')
  const { data: statsData, error: statsError } = await supabase
    .from('favorites')
    .select('capsule_category')
    .eq('telegram_id', testTelegramId)
  
  if (statsError) {
    console.error('❌ Ошибка при получении статистики:', statsError)
  } else {
    const stats = statsData.reduce((acc, item) => {
      const category = item.capsule_category || 'other'
      acc[category] = (acc[category] || 0) + 1
      return acc
    }, {})
    
    console.log('✅ Статистика:', {
      total: statsData.length,
      byCategory: stats
    })
  }
  
  // 7. Удаляем тестовые данные
  console.log('\n7️⃣ Удаляем тестовые данные...')
  const { error: deleteError } = await supabase
    .from('favorites')
    .delete()
    .eq('telegram_id', testTelegramId)
  
  if (deleteError) {
    console.error('❌ Ошибка при удалении:', deleteError)
  } else {
    console.log('✅ Тестовые данные удалены')
  }
  
  console.log('\n🎉 Тестирование завершено!')
}

// Запускаем тест
testFavoritesTable().catch(console.error) 