import { ref, onMounted, watch } from 'vue'
import { api } from "../../boot/axios.js";
import { useAuthStore } from 'src/stores/useAuthStore'

export function useAuthorizedStatusOptions() {
  const statusOptions = ref([])
  const selectedSpecialStatuses = ref([])
  const loading = ref(false)
  const authStore = useAuthStore()

  watch(selectedSpecialStatuses, (newSelected) => {
    console.log('Выбранные статусы изменились:', newSelected)
  }, { deep: true })

  const fetchStatuses = async () => {
    loading.value = true
    try {
      const response = await api.get('/special_status/all_for_users_role', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
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
    selectedSpecialStatuses,
    loading
  }
}