<template>
  <div style="max-width: 300px">
    <div>
      <q-select
        filled
        v-model="selectedSpecialStatuses"
        multiple
        :options="statusOptions"
        option-label="name"
        option-value="id"
        label="Группы ТС"
        emit-value
        map-options
        clearable
        :loading="loading"
      />
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useStatusOptions } from '../../Functions/ButtonSelectGroupTs.js'
import { useFilterStore } from '../../Functions/FilterStoreAcceptButton'

const { statusOptions, loading, selectedSpecialStatuses } = useStatusOptions()
const { selectedSpecialStatuses: storeSelectedStatuses } = useFilterStore()

// Синхронизируем локальное состояние с хранилищем
watch(selectedSpecialStatuses, (newVal) => {
  storeSelectedStatuses.value = newVal
}, { deep: true })
</script>