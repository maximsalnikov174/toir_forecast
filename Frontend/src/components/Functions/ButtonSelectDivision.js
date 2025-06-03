import { ref, onMounted } from 'vue'

export function DivisionFuctionSelect() {
  const selectedOrgId = ref(null)
  const organizations = ref([])

  const fetchDivision = async () => {
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
    fetchDivision()
  })

  return {
    selectedOrgId,
    organizations
  }
}
