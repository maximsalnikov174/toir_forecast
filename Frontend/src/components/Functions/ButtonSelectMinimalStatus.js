import { ref, onMounted, watch } from 'vue' // Добавляем импорт watch
import { useFilterStore } from '../Functions/FilterStoreAcceptButton.js'

export function MinimalStatusSelect() {
  const { selectedMinimalStatus } = useFilterStore()
  const MinimalStatus = ref([])

  // Добавляем вотчер для отслеживания изменений selectedMinimalStatus
  watch(selectedMinimalStatus, (newValue) => {
    console.log('Selected Minimal Status changed:', newValue)
  }, { immediate: true })

  const fetchMinimalStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8001/service_status/all', {
        headers: {
          'accept': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Ошибка при загрузке организаций')
      }

      MinimalStatus.value = await response.json()
    } catch (error) {
      console.error('Ошибка:', error)
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