import { ref } from 'vue'

// Создаем рефы вне функции, чтобы сохранять состояние
const selectedDivId = ref(null)
const selectedMinimalStatus = ref(null)
const selectedValues = ref(null)
const selectedSpecialStatuses = ref([]) // Добавили для хранения специальных статусов

export function useFilterStore() {
  return {
    selectedDivId,
    selectedMinimalStatus,
    selectedValues,
    selectedSpecialStatuses // Добавляем в экспорт
  }
}