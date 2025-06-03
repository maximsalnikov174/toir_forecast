<template>
  <q-select
    standout
    v-model="selectedOrgId"
    :options="organizations"
    option-label="name"
    option-value="id"
    label="Выберите организацию"
    emit-value
    map-options
    clearable
    style="max-width: 300px;"
    class="q-mb-md"
  />
</template>

<script setup>
import { DivisionFuctionSelect } from '../../Functions/ButtonSelectDivision.js'

const { selectedOrgId, organizations } = DivisionFuctionSelect()
</script>
