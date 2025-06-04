import { ref } from 'vue'

// Создаем рефы вне функции, чтобы сохранять состояние
const selectedDivId = ref(null)
const selectedMinimalStatus = ref(null)
const selectedValues = ref(null)

export function useFilterStore() {
  return {
    selectedDivId,
    selectedMinimalStatus,
    selectedValues
  }
}