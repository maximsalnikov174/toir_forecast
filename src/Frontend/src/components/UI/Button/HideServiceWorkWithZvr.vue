<template>
  <div style="max-width: 300px">
    <div>
      <q-select
        filled
        v-model="selectedValues"
        :options="yesNoOptions"
        option-label="label"
        option-value="value"
        label="С ЗВР"
        emit-value
        map-options
        clearable
      />
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useFilterStore } from '../../Functions/FilterStoreAcceptButton.js'

// Опции для выбора Да/Нет
const yesNoOptions = [
  { label: 'Нет', value: true },
  { label: 'Да', value: false }
]

// Выбранные значения (true/false)
const { selectedValues } = useFilterStore()

// Если нужно сохранять массив значений (для multiple)
// const selectedValues = ref([])

// Вотчер для отслеживания изменений
watch(selectedValues, (newVal) => {
  console.log('Выбрано:', newVal)
  // Здесь можно добавить дополнительную логику обработки
}, { immediate: true })
</script>