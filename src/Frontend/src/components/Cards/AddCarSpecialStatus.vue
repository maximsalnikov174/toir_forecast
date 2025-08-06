<template>
  <q-card style="min-width: 300px">
    <q-card-section>
      <div class="text-h6">Выберите статус</div>

      <q-select
        v-model="selectedSpecialStatuses"
        :options="statusOptions"
        option-label="name"
        option-value="id"
        label="Статус"
        filled
        map-options
        emit-value
        :loading="loading"
        multiple
        clearable
      />
    </q-card-section>

    <q-card-actions align="right">
      <q-btn flat label="Закрыть" color="primary" v-close-popup />
    </q-card-actions>
  </q-card>
</template>

<script>
import { defineComponent } from 'vue'
import { useStatusOptions } from '../Functions/ButtonSelectGroupTs.js' // Или правильный путь к вашему файлу

export default defineComponent({
  name: 'AddCarSpecialStatus',
  emits: ['close'],
  setup() {
    const {
      statusOptions,
      selectedSpecialStatuses,
      loading
    } = useStatusOptions()

    return {
      statusOptions,
      selectedSpecialStatuses,
      loading
    }
  }
})
</script>