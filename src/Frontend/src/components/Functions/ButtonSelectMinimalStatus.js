import { ref, onMounted, watch } from 'vue' // Добавляем импорт watch
import { useFilterStore } from '../Functions/FilterStoreAcceptButton.js'
import { api } from "../../boot/axios.js"

export function MinimalStatusSelect() {
  const { selectedMinimalStatus } = useFilterStore()
  const MinimalStatus = ref([])

  // Добавляем вотчер для отслеживания изменений selectedMinimalStatus
  watch(selectedMinimalStatus, (newValue) => {
    console.log('Selected Minimal Status changed:', newValue)
  }, { immediate: true })

  const fetchMinimalStatus = async () => {
    try {
      const response = await api.get('/service_status/all', {
        headers: {
          'accept': 'application/json'
        }
      })

      MinimalStatus.value =  response.data
    } catch (error) {
      console.error('Ошибка:', error)
      MinimalStatus.value =[]
    }
  }

  onMounted(() => {
    fetchMinimalStatus()
  })

  return {
    selectedMinimalStatus,
    MinimalStatus
  }
}