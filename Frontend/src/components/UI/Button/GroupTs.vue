<template>
  <div style="max-width: 300px">
    <div >
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
import { ref } from 'vue'
import { useStatusOptions } from '../../Functions/ButtonSelectGroupTs.js'

const { statusOptions, loading } = useStatusOptions()
const selectedSpecialStatuses = ref([])
</script>