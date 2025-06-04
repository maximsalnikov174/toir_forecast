import { ref, onMounted } from 'vue'
import { useFilterStore } from '../Functions/FilterStoreAcceptButton'

export function DivisionFuctionSelect() {
  const { selectedDivId } = useFilterStore()
  const divisions = ref([])

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

      divisions.value = await response.json()
    } catch (error) {
      console.error('Ошибка:', error)
    }
  }

  onMounted(() => {
    fetchDivision()
  })

  return {
    selectedDivId,
    divisions
  }

}
