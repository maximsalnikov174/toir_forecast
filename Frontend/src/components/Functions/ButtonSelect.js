// src/composables/useOrganizationSelect.js
import { ref, onMounted } from 'vue'

export function useOrganizationSelect() {
  const selectedOrgId = ref(null)
  const organizations = ref([])

  const fetchOrganizations = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8001/organization/all', {
        headers: {
          'accept': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Ошибка при загрузке организаций')
      }

      organizations.value = await response.json()
    } catch (error) {
      console.error('Ошибка:', error)
    }
  }

  onMounted(() => {
    fetchOrganizations()
  })

  return {
    selectedOrgId,
    organizations
  }
}