import { ref, onMounted } from 'vue'

export function MinimalStatusSelect() {
  const selectedMinimalStatus = ref(null)
  const MinimalStatus = ref([])

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
