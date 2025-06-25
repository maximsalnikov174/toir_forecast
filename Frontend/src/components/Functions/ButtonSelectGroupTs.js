import { ref, onMounted, watch } from 'vue'
import { api } from "../../boot/axios.js";

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
      const response = await api.get('/special_status/all')

      // В Axios данные всегда в response.data
      statusOptions.value = response.data

    } catch (error) {
      console.error('Ошибка загрузки данных:', error)
      // Можно добавить обработку ошибки, например:
      statusOptions.value = [] // Очищаем список в случае ошибки
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchStatuses()
  })

  return {
    statusOptions,
    selectedStatuses,
    loading
  }
}