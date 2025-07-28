import { ref, onMounted, watch } from 'vue'
import { api } from "../../boot/axios.js";

export function useStatusOptions() {
  const statusOptions = ref([])
  const selectedSpecialStatuses = ref([]) // Переименовали для согласованности
  const loading = ref(false)

  watch(selectedSpecialStatuses, (newSelected) => {
    console.log('Выбранные статусы изменились:', newSelected)
  }, { deep: true })

  const fetchStatuses = async () => {
    loading.value = true
    try {
      const response = await api.get('/special_status/all')
      statusOptions.value = response.data
    } catch (error) {
      console.error('Ошибка загрузки данных:', error)
      statusOptions.value = []
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchStatuses()
  })

  return {
    statusOptions,
    selectedSpecialStatuses, // Теперь экспортируем это значение
    loading
  }
}