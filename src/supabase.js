import { createClient } from '@supabase/supabase-js'

// Получаем данные из переменных окружения
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://lipolo.store'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

if (!supabaseAnonKey) {
  console.warn('VITE_SUPABASE_ANON_KEY не установлен в переменных окружения')
}

// Supabase инициализирован (логирование отключено для безопасности)

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Функции для работы с анкетами
export const profileService = {
  // Получить профиль по telegram_id
  async getProfile(telegramId) {
    const { data, error } = await supabase
      .from('user_profile')
      .select('*')
      .eq('telegram_id', telegramId)
      .single()
    
    if (error) {
      console.error('Error fetching profile:', error)
      return null
    }
    
    return data
  },

  // Сохранить/обновить профиль
  async saveProfile(profileData) {
    const { data, error } = await supabase
      .from('user_profile')
      .upsert(profileData, { onConflict: 'telegram_id' })
    
    if (error) {
      console.error('Error saving profile:', error)
      throw error
    }
    
    return data
  }
}

// Функции для работы с гардеробом
export const wardrobeService = {
  // Получить гардероб по telegram_id
  async getWardrobe(telegramId) {
    const { data, error } = await supabase
      .from('wardrobe')
      .select('*')
      .eq('telegram_id', telegramId)
      .order('id', { ascending: false })

    if (error) {
      console.error('Error fetching wardrobe:', error)
      return []
    }

    return data || []
  },

  // Пометить вещь как подходящую/неподходящую с сохранением причины в ban_reason
  async setItemSuitability(id, isSuitable, reason = null) {
    const payload = { is_suitable: !!isSuitable }
    // Если помечаем как неподходящую — записываем причину в ban_reason
    if (isSuitable === false) {
      payload.ban_reason = (typeof reason === 'string' && reason.length > 0) ? reason : null
    }
    const { data, error } = await supabase
      .from('wardrobe')
      .update(payload)
      .eq('id', id)
      .select()
    if (error) {
      console.error('Error updating suitability:', error)
      throw error
    }
    return data?.[0]
  },

  // Добавить вещь в гардероб
  async addItem(itemData) {
    const { data, error } = await supabase
      .from('wardrobe')
      .insert(itemData)
      .select()

    if (error) {
      console.error('Error adding item:', error)
      throw error
    }

    return data[0]
  },

  // Обновить вещь
  async updateItem(id, itemData) {
    const { data, error } = await supabase
      .from('wardrobe')
      .update(itemData)
      .eq('id', id)
      .select()

    if (error) {
      console.error('Error updating item:', error)
      throw error
    }

    return data[0]
  },

  // Удалить вещь
  async deleteItem(id) {
    const { error } = await supabase
      .from('wardrobe')
      .delete()
      .eq('id', id)

    if (error) {
      console.error('Error deleting item:', error)
      throw error
    }

    return true
  },

              // Загрузить изображение в Storage
            async uploadImage(telegramId, imageId, imageBlob) {
              try {
                const { data, error } = await supabase.storage
                  .from('wardrobe-images')
                  .upload(`${telegramId}/${imageId}.png`, imageBlob, {
                    contentType: 'image/png',
                    upsert: true
                  })

                if (error) {
                  console.error('Error uploading image:', error)
                  
                  // Обработка специфических ошибок
                  if (error.message?.includes('413') || error.message?.includes('Request Entity Too Large')) {
                    throw new Error('Файл слишком большой. Попробуйте другое изображение или уменьшите его размер.');
                  }
                  
                  if (error.message?.includes('CORS') || error.message?.includes('Failed to fetch')) {
                    throw new Error('Ошибка сети. Проверьте подключение к интернету и попробуйте снова.');
                  }
                  
                  throw error
                }

                return data
              } catch (error) {
                console.error('Error uploading image:', error)
                throw error
              }
            },

            // Получить URL изображения
            getImageUrl(telegramId, imageId) {
              // Возвращаем PNG URL, но если файл не существует, браузер попробует JPG через onError
              const { data } = supabase.storage
                .from('wardrobe-images')
                .getPublicUrl(`${telegramId}/${imageId}.png`)

              // Добавляем параметр времени для принудительного обновления кэша
              return `${data.publicUrl}?v=${Date.now()}`
            },

            // Удалить изображение из Storage
            async deleteImage(telegramId, imageId) {
              const { error } = await supabase.storage
                .from('wardrobe-images')
                .remove([`${telegramId}/${imageId}.png`])

              if (error) {
                console.error('Error deleting image:', error)
                throw error
              }

              return true
            }
} 

// Функции для работы с избранными капсулами
export const favoritesService = {
  // Получить все избранные капсулы пользователя
  async getFavorites(telegramId) {
    const { data, error } = await supabase
      .from('favorites')
      .select('*')
      .eq('telegram_id', telegramId)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching favorites:', error)
      return []
    }

    return data || []
  },

  // Добавить капсулу в избранное
  async addToFavorites(telegramId, capsule) {
    const favoriteData = {
      telegram_id: telegramId,
      capsule_id: capsule.id,
      capsule_name: capsule.name,
      capsule_description: capsule.description,
      capsule_category: capsule.category,
      capsule_data: capsule // Полные данные капсулы
    }

    const { data, error } = await supabase
      .from('favorites')
      .upsert(favoriteData, { onConflict: 'telegram_id,capsule_id' })
      .select()

    if (error) {
      console.error('Error adding to favorites:', error)
      throw error
    }

    return data[0]
  },

  // Удалить капсулу из избранного
  async removeFromFavorites(telegramId, capsuleId) {
    const { error } = await supabase
      .from('favorites')
      .delete()
      .eq('telegram_id', telegramId)
      .eq('capsule_id', capsuleId)

    if (error) {
      console.error('Error removing from favorites:', error)
      throw error
    }

    return true
  },

  // Проверить, есть ли капсула в избранном
  async isInFavorites(telegramId, capsuleId) {
    const { data, error } = await supabase
      .from('favorites')
      .select('id')
      .eq('telegram_id', telegramId)
      .eq('capsule_id', capsuleId)
      .single()

    if (error && error.code !== 'PGRST116') {
      console.error('Error checking favorites:', error)
      return false
    }

    return !!data
  },

  // Получить избранные капсулы по категории
  async getFavoritesByCategory(telegramId, category) {
    const { data, error } = await supabase
      .from('favorites')
      .select('*')
      .eq('telegram_id', telegramId)
      .eq('capsule_category', category)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching favorites by category:', error)
      return []
    }

    return data || []
  },

  // Получить статистику избранного
  async getFavoritesStats(telegramId) {
    const { data, error } = await supabase
      .from('favorites')
      .select('capsule_category')
      .eq('telegram_id', telegramId)

    if (error) {
      console.error('Error fetching favorites stats:', error)
      return {}
    }

    // Подсчитываем количество по категориям
    const stats = data.reduce((acc, item) => {
      const category = item.capsule_category || 'other'
      acc[category] = (acc[category] || 0) + 1
      return acc
    }, {})

    return {
      total: data.length,
      byCategory: stats
    }
  }
} 