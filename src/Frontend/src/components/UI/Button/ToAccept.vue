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
import { ref, watch } from 'vue'
import { api } from "../../../boot/axios.js";

const {
  selectedDivId,
  selectedMinimalStatus,
  selectedValues,
  selectedSpecialStatuses
} = useFilterStore()
const loading = ref(false)

const emit = defineEmits(['applied', 'servicesFetched', 'carsFetched', 'tableDataFetched'])

watch(
  [selectedDivId, selectedMinimalStatus, selectedValues, selectedSpecialStatuses],
  ([divId, status, values, specialStatuses]) => {
    console.group('Текущие значения фильтров:')
    console.log('selectedDivId:', divId)
    console.log('selectedMinimalStatus:', status)
    console.log('selectedValues:', values)
    console.log('selectedSpecialStatuses:', specialStatuses)
    console.groupEnd()
  },
  { immediate: true }
)

const showAlert = (message, type = 'info') => {
  alert(`${type.toUpperCase()}: ${message}`)
}

const makeRequest = async (endpoint, params, requestBody = [0, null]) => {
  console.log(`Отправка POST-запроса на ${endpoint} с параметрами:`, params)
  console.log('Тело запроса:', requestBody)

  const response = await api.post(
    endpoint,
    requestBody,
    {
      params: params,
      headers: {
        'accept': 'application/json',
        'Content-Type': 'application/json'
      }
    }
  )

  return response.data
}

const handleApply = async () => {
  console.group('Применение фильтров:')
  console.log('selectedDivId:', selectedDivId.value)
  console.log('selectedMinimalStatus:', selectedMinimalStatus.value)
  console.log('selectedValues:', selectedValues.value)
  console.log('selectedSpecialStatuses:', selectedSpecialStatuses.value)
  console.groupEnd()

  loading.value = true

  try {
    const params = {}

    if (selectedMinimalStatus.value !== null && selectedMinimalStatus.value !== undefined) {
      params.request_status_id = selectedMinimalStatus.value
      params.request_status_param = selectedMinimalStatus.value
    }

    if (selectedDivId.value !== null && selectedDivId.value !== undefined) {
      params.organization_id = selectedDivId.value
    }

    if (selectedValues.value !== null && selectedValues.value !== undefined) {
      params.hide_service_work_with_zvr = selectedValues.value
    }

    if (selectedSpecialStatuses.value && selectedSpecialStatuses.value.length > 0) {
      params.special_statuses = selectedSpecialStatuses.value.join(',')
    }

    let requestBody = [0, null]
    if (selectedSpecialStatuses.value && selectedSpecialStatuses.value.length > 0) {
      requestBody = [0, ...selectedSpecialStatuses.value, null]
    }

    const mainResponse = await makeRequest(
      '/service_work/get_table',
      params,
      requestBody
    )

    // Фильтруем null значения и эмитим данные
    const filteredData = mainResponse.filter(item => item !== null);
    emit('tableDataFetched', filteredData);

    const commonParams = {
      request_status_param: params.request_status_param || 0,
      organization_id: params.organization_id || 0
    }

    if (selectedValues.value !== null && selectedValues.value !== undefined) {
      commonParams.hide_service_work_with_zvr = selectedValues.value
    }

    const servicesResponse = await makeRequest(
      '/service_name/all_service_names',
      commonParams,
      requestBody
    )
    emit('servicesFetched', servicesResponse)

    const carsResponse = await makeRequest(
      '/car/with_many_statuses',
      commonParams,
      requestBody
    )
    emit('carsFetched', carsResponse)

  } catch (error) {
    console.error('Ошибка при выполнении запроса:', error)
    showAlert('Произошла ошибка при применении фильтров', 'error')
    throw error
  } finally {
    loading.value = false
  }
}

defineExpose({
  handleApply
})
</script>

<style scoped>
.apply-button {
  background-color: transparent;
  color: white;
  padding: 8px 16px;
  border-color:#555555 ;
  cursor: pointer;
  max-width: 300px;
  height: 56px;
}

.apply-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>