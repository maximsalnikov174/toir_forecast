<template>
  <q-select
    standout
    v-model="selectedMinimalStatus"
    :options="MinimalStatus"
    option-label="status_name"
    option-value="id"
    label="Выберите минимальный статус"
    emit-value
    map-options
    clearable
    style="max-width: 300px;"
    class="q-mb-md"
  />
</template>

<script setup>
import { MinimalStatusSelect } from '../../Functions/ButtonSelectMinimalStatus.js'

const { selectedMinimalStatus, MinimalStatus } = MinimalStatusSelect()
</script>
