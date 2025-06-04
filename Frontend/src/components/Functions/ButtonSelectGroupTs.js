import { ref, onMounted, watch } from 'vue'

export function useStatusOptions() {
  const statusOptions = ref([])
  const selectedStatuses = ref([]) // Для хранения выбранных статусов
  const loading = ref(false)

  // Вотчер для отслеживания выбранных статусов
  watch(selectedStatuses, (newSelected) => {
    console.log('Выбранные статусы изменились:', newSelected)
  }, { deep: true })

  const fetchStatuses = async () => {
    loading.value = true
    try {
      const response = await fetch('http://127.0.0.1:8001/special_status/all', {
        method: 'GET',
        headers: {
          'accept': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Ошибка при загрузке статусов')
      }

      statusOptions.value = await response.json()
    } catch (error) {
      console.error('Ошибка загрузки данных:', error)
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchStatuses()
  })

  return {
    statusOptions,
    selectedStatuses, // Возвращаем для использования в компоненте
    loading
  }
}