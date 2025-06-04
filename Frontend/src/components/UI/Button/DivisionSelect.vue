<template>
  <q-select
    standout
    v-model="selectedDivId"
    :options="divisions"
    option-label="name"
    option-value="id"
    label="Выберите подразделение"
    emit-value
    map-options
    clearable
    style="max-width: 300px;"
    class="q-mb-md"
  />
</template>

<script setup>
import { DivisionFuctionSelect } from '../../Functions/ButtonSelectDivision.js'

const { selectedDivId, divisions } = DivisionFuctionSelect()
console.log(selectedDivId)
</script>
