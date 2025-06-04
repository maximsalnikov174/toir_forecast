<template>
  <button
    class="apply-button"
    @click="handleApply"
    :disabled="loading"
  >
    <span v-if="!loading">Применить</span>
    <span v-else>Загрузка...</span>
  </button>
</template>

<script setup>
import { useFilterStore } from '../../Functions/FilterStoreAcceptButton'
import axios from 'axios'
import { ref, watch } from 'vue'

const { selectedDivId, selectedMinimalStatus, selectedValues } = useFilterStore()
const loading = ref(false)

const emit = defineEmits(['applied'])

// Вотчеры для отслеживания изменений фильтров
watch([selectedDivId, selectedMinimalStatus, selectedValues], ([divId, status, values]) => {
  console.group('Текущие значения фильтров:')
  console.log('selectedDivId:', divId)
  console.log('selectedMinimalStatus:', status)
  console.log('selectedValues:', values)
  console.groupEnd()
}, { immediate: true })

const showAlert = (message, type = 'info') => {
  alert(`${type.toUpperCase()}: ${message}`)
}

const handleApply = async () => {
  // Выводим текущие значения в консоль перед отправкой
  console.group('Применение фильтров:')
  console.log('selectedDivId:', selectedDivId.value)
  console.log('selectedMinimalStatus:', selectedMinimalStatus.value)
  console.log('selectedValues:', selectedValues.value)
  console.groupEnd()

  // Проверка, что хотя бы один параметр задан
  if (
    selectedMinimalStatus.value === null &&
    selectedDivId.value === null &&
    selectedValues.value === null
  ) {
    showAlert('Пожалуйста, выберите хотя бы один фильтр', 'warning')
    return
  }

  loading.value = true

  try {
    const params = {}

    if (selectedMinimalStatus.value !== null && selectedMinimalStatus.value !== undefined) {
      params.request_status_id = selectedMinimalStatus.value
    }

    if (selectedDivId.value !== null && selectedDivId.value !== undefined) {
      params.organization_id = selectedDivId.value
    }

    if (selectedValues.value !== null && selectedValues.value !== undefined) {
      params.hide_service_work_with_zvr = selectedValues.value
    }

    const requestBody = [0, null]

    console.log('Отправка POST-запроса с параметрами:', params)
    console.log('Тело запроса:', requestBody)

    const response = await axios.post(
      'http://127.0.0.1:8001/service_work/get_table',
      requestBody,
      {
        params: params,
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json'
        }
      }
    )

    emit('applied', response.data)
    showAlert('Фильтры успешно применены', 'success')
    return response.data

  } catch (error) {
    console.error('Ошибка при выполнении запроса:', error)
    showAlert('Произошла ошибка при применении фильтров', 'error')
    throw error
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.apply-button {
  border-radius: 9999px;
  background-color: #1976d2;
  color: white;
  padding: 8px 16px;
  border: none;
  cursor: pointer;
  max-width: 300px;
  transition: opacity 0.3s;
}

.apply-button:hover {
  opacity: 0.9;
}

.apply-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>