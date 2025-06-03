import { ref, onMounted } from 'vue'

export function useStatusOptions() {
  const statusOptions = ref([])
  const loading = ref(false)

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
    loading
  }
}