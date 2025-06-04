import { ref } from 'vue'

export function useFilterStore() {
  const selectedDivId = ref()
  const selectedMinimalStatus = ref()
  const selectedValues = ref()

  return {
    selectedDivId,
    selectedMinimalStatus,
    selectedValues
  }
}